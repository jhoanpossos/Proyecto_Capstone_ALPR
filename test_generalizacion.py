import numpy as np
from stable_baselines3 import PPO
from simulation_manager import SimulationManager
from arduino_python import FuzzyController
from preprocesamiento import preprocesar_placa, detectar_texto
from ultralytics import YOLO
import cv2

# --- 1. CARGAR TODOS LOS COMPONENTES ---
print("⚙️  Cargando el agente entrenado y el entorno de prueba...")

try:
    # Cargar el agente PPO que guardamos
    model = PPO.load("ppo_fuzzy_ocr_controller.zip")

    # Cargar los módulos que el agente necesita para operar
    sim_manager = SimulationManager(environments_base_path='entornos/')
    fuzzy_controller = FuzzyController()
    yolo_model = YOLO("runs/detect/placas_v14/weights/best.pt")
except Exception as e:
    print(f"❌ Error al cargar los modelos o gestores: {e}")
    exit()

print("✅ Agente y entorno listos.")


# --- 2. CONFIGURAR EL ESCENARIO DE PRUEBA ---
print("\n🚀 Configurando escenario de generalización...")

# --- MODIFICACIÓN CLAVE ---
# Apuntamos directamente a tu nuevo entorno de prueba.
env_name_to_test = "entorno_generalizacion" 

try:
    sim_manager.load_environment(env_name_to_test)
    print(f"🌍 Usando entorno de prueba: {env_name_to_test}")
except (ValueError, FileNotFoundError) as e:
    print(f"❌ Error al cargar el entorno: {e}")
    print("Asegúrate de que la carpeta 'entorno_generalizacion' exista dentro de 'entornos/' y tenga las imágenes necesarias.")
    exit()

# Simulamos una observación inicial (ej. atardecer, confianza cero)
ambient_light = 50
initial_confidence = 0
observation = np.array([ambient_light, initial_confidence], dtype=np.float32)

print(f"Observación Inicial: Luz Ambiental={ambient_light}, Confianza OCR={initial_confidence}")


# --- 3. PEDIR AL AGENTE QUE TOME UNA DECISIÓN ---
# Usamos model.predict() para obtener la mejor acción aprendida
# deterministic=True asegura que elija la mejor acción, sin explorar
action, _states = model.predict(observation, deterministic=True)

print(f"\n🤖 El agente PPO decidió tomar la acción (ajustar parámetros): {action}")


# --- 4. APLICAR LA ACCIÓN Y VER EL RESULTADO ---
# Ajustamos el controlador difuso con la acción elegida por el agente
fuzzy_controller.tune(action)

# El controlador ahora "optimizado" calcula la potencia del flash
flash_power = fuzzy_controller.compute(ambient_light, initial_confidence)
intensity = flash_power / 255.0
print(f"🕹️ Con los nuevos parámetros, el controlador Fuzzy pide una intensidad de flash de: {intensity:.2f}")

# Generamos la imagen final con la iluminación optimizada
final_image = sim_manager.simulate_lighting(intensity)

# Medimos el resultado final
ocr_results = yolo_model(final_image, imgsz=320, conf=0.5, verbose=False)
final_text = "No detectada"
final_confidence = 0.0

if ocr_results and len(ocr_results[0].boxes) > 0:
    box = ocr_results[0].boxes[0]
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    cv2.rectangle(final_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    roi = final_image[y1:y2, x1:x2]
    img_preprocesada = preprocesar_placa(roi)
    if img_preprocesada is not None:
        texto, confianza = detectar_texto(img_preprocesada)
        if texto:
            final_text = texto
            final_confidence = confianza

print(f"\n✅ RESULTADO FINAL:")
print(f"Texto Reconocido: {final_text} (Confianza: {final_confidence:.2f}%)")

# Mostrar la imagen resultante
cv2.imshow(f"Resultado en '{env_name_to_test}'", final_image)
cv2.waitKey(0)
cv2.destroyAllWindows()