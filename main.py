import cv2
import time
import numpy as np
import os
from ultralytics import YOLO
from stable_baselines3 import PPO

# --- Importaciones de nuestros módulos ---
from arduino_python import FuzzyController, conectar_arduino, enviar_comando_arduino, cerrar_conexion_arduino, actualizar_y_manejar_eventos_simulador, log_messages
from database_sql import conectar_sql_server, verificar_placa_registrada, guardar_en_base_de_datos
from preprocesamiento import detectar_texto
from simulation_manager import SimulationManager

# --- SETUP ---
print("⚙️  Iniciando sistema con Agente Experto...")
try:
    agente_ppo = PPO.load("sistema_control_adaptativo/agentes_entrenados/ppo_agente_experto.zip")
    yolo_model = YOLO("runs/detect/placas_v14/weights/best.pt")
    fuzzy_controller = FuzzyController()
    sim_manager = SimulationManager(environments_base_path='sistema_control_adaptativo/entornos/')
    print("✅ Modelos y gestores cargados.")
except Exception as e:
    print(f"❌ Error al cargar modelos o gestores: {e}")
    exit()

conn = conectar_sql_server()
arduino = conectar_arduino() 
if conn is None: exit()

# --- BUCLE PRINCIPAL ---
running = True
display_frame, roi_to_display = None, None
log_messages[:] = ["Presiona 'D' para simular, 'Q' para salir."]
print("🚀 Sistema listo.")

while running:
    running = actualizar_y_manejar_eventos_simulador(display_frame, roi_to_display)
    key = cv2.waitKey(20) & 0xFF

    if key == ord('d'):
        roi_to_display = None
        
        env_name = sim_manager.get_random_environment_name()
        sim_manager.load_environment(env_name)
        log_messages[:] = [f"🚗 Vehículo en entorno: '{env_name}'"]
        
        initial_frame = sim_manager.sorted_images_by_intensity[1].copy()
        display_frame = initial_frame.copy()
        
        log_messages.append("--- Iniciando Diagnóstico ---")
        
        # --- FUNCIÓN AUXILIAR MEJORADA ---
        def get_ocr_results_from_image(image):
            """Ahora devuelve texto y confianza."""
            results = yolo_model(image, verbose=False)
            if results and results[0].boxes:
                box = results[0].boxes[0]
                roi = image[int(box.xyxy[0][1]):int(box.xyxy[0][3]), int(box.xyxy[0][0]):int(box.xyxy[0][2])]
                texto, confianza = detectar_texto(roi)
                # Devolvemos el texto y la confianza. Si son None, se convierten en "" y 0.
                return texto or "", confianza or 0, roi
            return "", 0, None

        # Sondeo Flash Bajo
        texto_bajo, conf_bajo, _ = get_ocr_results_from_image(sim_manager.simulate_lighting(0.25))
        log_messages.append(f"Sondeo Bajo (25%): '{texto_bajo}' (Conf: {conf_bajo:.1f}%)")
        
        # Sondeo Flash Alto
        texto_alto, conf_alto, _ = get_ocr_results_from_image(sim_manager.simulate_lighting(0.75))
        log_messages.append(f"Sondeo Alto (75%): '{texto_alto}' (Conf: {conf_alto:.1f}%)")

        # El Agente Experto toma su decisión
        ambient_light = np.mean(cv2.cvtColor(initial_frame, cv2.COLOR_BGR2GRAY))
        observation = np.array([ambient_light / 2.55, conf_bajo, conf_alto], dtype=np.float32)
        
        action, _ = agente_ppo.predict(observation, deterministic=True)
        fuzzy_controller.tune(action)
        flash_power = fuzzy_controller.compute(observation[0], observation[2])
        enviar_comando_arduino(arduino, f"SET_FLASH:{int(flash_power)}")
        
        # Generar y procesar la imagen final
        final_image = sim_manager.simulate_lighting(flash_power / 255.0)
        display_frame = final_image.copy()
        
        texto_final, conf_final, roi_final = get_ocr_results_from_image(final_image)
        roi_to_display = roi_final.copy() if roi_final is not None else None
        
        if texto_final:
            log_messages.append(f"✅ Lectura Final: {texto_final} (Conf: {conf_final:.1f}%)")
            if verificar_placa_registrada(conn, texto_final):
                log_messages.append("➡️  Vehículo AUTORIZADO. Abriendo barrera...")
                enviar_comando_arduino(arduino, "OPEN")
        else:
            log_messages.append("❌ No se pudo obtener una lectura final.")

        time.sleep(1)
        enviar_comando_arduino(arduino, "SET_FLASH:0")
        log_messages.append("----------------------------")
        log_messages.append("Presiona 'D' para un nuevo vehículo...")

# --- LIMPIEZA ---
cerrar_conexion_arduino(arduino)
if conn: conn.close()
print("Programa finalizado.")