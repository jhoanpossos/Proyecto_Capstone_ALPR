import numpy as np
from stable_baselines3 import PPO
from simulation_manager import SimulationManager
from arduino_python import FuzzyController
from preprocesamiento import preprocesar_placa, detectar_texto
from ultralytics import YOLO
import cv2

print("⚙️  Cargando el agente entrenado y el entorno de prueba...")

try:
    # --- RUTA CORREGIDA ---
    agent_path = "sistema_control_adaptativo/agentes_entrenados/ppo_fuzzy_ocr_controller.zip"
    model = PPO.load(agent_path)
    # -------------------------

    sim_manager = SimulationManager(environments_base_path='sistema_control_adaptativo/entornos/')
    fuzzy_controller = FuzzyController()
    yolo_model = YOLO("runs/detect/placas_v14/weights/best.pt")
except Exception as e:
    print(f"❌ Error al cargar los modelos o gestores: {e}")
    exit()

print("✅ Agente y entorno listos.")
print("\n🚀 Configurando escenario de generalización...")

env_name_to_test = "entorno_generalizacion"
try:
    sim_manager.load_environment(env_name_to_test)
    print(f"🌍 Usando entorno de prueba: {env_name_to_test}")
except (ValueError, FileNotFoundError) as e:
    print(f"❌ Error al cargar el entorno: {e}")
    exit()

ambient_light = 50
initial_confidence = 0
observation = np.array([ambient_light, initial_confidence], dtype=np.float32)
print(f"Observación Inicial: Luz Ambiental={ambient_light}, Confianza OCR={initial_confidence}")

action, _ = model.predict(observation, deterministic=True)
print(f"\n🤖 El agente PPO decidió tomar la acción: {action}")

fuzzy_controller.tune(action)
flash_power = fuzzy_controller.compute(ambient_light, initial_confidence)
intensity = flash_power / 255.0
print(f"🕹️ Con los nuevos parámetros, el controlador Fuzzy pide una intensidad de flash de: {intensity:.2f}")

final_image = sim_manager.simulate_lighting(intensity)
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

cv2.imshow(f"Resultado en '{env_name_to_test}'", final_image)
cv2.waitKey(0)
cv2.destroyAllWindows()