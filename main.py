import cv2
import time
import numpy as np
import os
from ultralytics import YOLO
from stable_baselines3 import PPO

# --- Importaciones de nuestros módulos ---
# Se importa todo desde tu archivo, que ahora es el núcleo del control y la simulación
from arduino_python import FuzzyController, conectar_arduino, enviar_comando_arduino, cerrar_conexion_arduino, actualizar_y_manejar_eventos_simulador
from database_sql import conectar_sql_server, verificar_placa_registrada, guardar_en_base_de_datos
from preprocesamiento import preprocesar_placa, detectar_texto
from simulation_manager import SimulationManager

# --- 1. SETUP ---
print("⚙️  Iniciando sistema en MODO SIMULACIÓN...")

try:
    agente_ppo = PPO.load("sistema_control_adaptativo/agentes_entrenados/ppo_fuzzy_ocr_controller.zip")
    yolo_model = YOLO("runs/detect/placas_v14/weights/best.pt")
    fuzzy_controller = FuzzyController()
    sim_manager = SimulationManager(environments_base_path='sistema_control_adaptativo/entornos/')
    print("✅ Modelos y gestores cargados.")
except Exception as e:
    print(f"❌ Error al cargar modelos o gestores: {e}")
    exit()

conn = conectar_sql_server()
# Esta función inicia el Arduino real O la simulación visual
arduino = conectar_arduino()

if conn is None or arduino is None:
    print("❌ Finalizando por error de conexión.")
    exit()

# --- 2. BUCLE PRINCIPAL DE SIMULACIÓN ---
running = True
# Variables para mantener el estado de la visualización
display_frame = np.zeros((600, 800, 3), dtype="uint8") # Fondo por defecto
roi_to_display = None

print("🚀 Sistema listo. Presiona 'D' para simular o 'Q' para salir.")

while running:
    # La función del módulo arduino ahora maneja el refresco de la ventana y los eventos de salida
    running = actualizar_y_manejar_eventos_simulador(display_frame, roi_to_display)

    # El bucle espera 20ms por si se presiona una tecla
    key = cv2.waitKey(20) & 0xFF

    # Activar el ciclo de control con la tecla 'd'
    if key == ord('d'):
        
        # --- CICLO DE CONTROL INTELIGENTE SIMULADO ---
        env_name = sim_manager.get_random_environment_name()
        sim_manager.load_environment(env_name)
        
        # Usamos la imagen con faros como el "frame" inicial que el sistema analiza
        initial_frame = sim_manager.sorted_images_by_intensity[1].copy()
        display_frame = cv2.resize(initial_frame, (800, 600)) # La mostramos como fondo
        
        # ---- Lógica de IA ----
        ambient_light = np.mean(cv2.cvtColor(initial_frame, cv2.COLOR_BGR2GRAY))
        observation = np.array([ambient_light / 2.55, 0], dtype=np.float32)
        action, _ = agente_ppo.predict(observation, deterministic=True)
        fuzzy_controller.tune(action)
        flash_power = fuzzy_controller.compute(observation[0], 0)
        intensity = flash_power / 255.0
        
        # Enviar comando de flash al simulador
        enviar_comando_arduino(arduino, f"SET_FLASH:{int(flash_power)}")
        
        # Generar y procesar la imagen final
        final_image = sim_manager.simulate_lighting(intensity)
        display_frame = cv2.resize(final_image, (800, 600)) # Actualizamos el fondo con la imagen final
        
        results = yolo_model(final_image, imgsz=320, conf=0.5, verbose=False)
        if results and results[0].boxes:
            box = results[0].boxes[0]
            roi = final_image[int(box.xyxy[0][1]):int(box.xyxy[0][3]), int(box.xyxy[0][0]):int(box.xyxy[0][2])]
            roi_to_display = roi.copy() # Guardamos el ROI para mostrarlo
            
            texto_placa, confianza = detectar_texto(preprocesar_placa(roi))

            if texto_placa:
                vehiculo = verificar_placa_registrada(conn, texto_placa)
                if vehiculo:
                    enviar_comando_arduino(arduino, "OPEN") # Enviar comando a la simulación
                    guardar_en_base_de_datos(conn, texto_placa)
        
        # Apagar el "flash" en la simulación después del ciclo
        time.sleep(1) # Pequeña pausa para ver el resultado
        enviar_comando_arduino(arduino, "SET_FLASH:0")


# --- 3. LIMPIEZA ---
print("Cerrando sistema...")
cerrar_conexion_arduino(arduino)
if conn:
    conn.close()