import cv2
import numpy as np
import os
import re
from ultralytics import YOLO
from preprocesamiento import preprocesar_placa, detectar_texto

# --- 1. CONFIGURACIÓN ---
print("⚙️  Configurando Test de Confianza del OCR...")

# --- Rutas y Parámetros (sin Ground Truth) ---
folder_path = "pruebas ocr"
yolo_model_path = "runs/detect/placas_v14/weights/best.pt"
images_for_dynamic_base = [
    "ChatGPT Image 30 jun 2025, 05_06_32 p.m..png",
    "img_base.png"
]
activation_threshold = 0.25


# --- 2. LÓGICA DEL SIMULADOR ---
print("💡 Analizando imágenes de referencia...")
all_files_in_folder = os.listdir(folder_path)
image_extensions = ('.png', '.jpg', '.jpeg')
images = {}
for filename in all_files_in_folder:
    if filename.lower().endswith(image_extensions):
        path = os.path.join(folder_path, filename)
        img = cv2.imread(path)
        if img is not None: images[filename] = img

dynamic_base_images_sorted = sorted([images[name] for name in images_for_dynamic_base], key=lambda img: np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 2]))

def simular_iluminacion_dinamica(intensidad_deseada):
    intensidad = np.clip(float(intensidad_deseada), 0.0, 1.0)
    if intensidad <= activation_threshold:
        base_dinamica = dynamic_base_images_sorted[0].astype(np.float32)
    else:
        mix_factor = (intensidad - activation_threshold) / (1.0 - activation_threshold)
        base_dinamica = cv2.addWeighted(dynamic_base_images_sorted[0], 1.0 - mix_factor, dynamic_base_images_sorted[1], mix_factor, 0).astype(np.float32)
    
    beta = (intensidad - 0.5) * 50
    return cv2.convertScaleAbs(base_dinamica, alpha=1.0, beta=beta)

print("✅ Simulador listo.")


# --- 3. CARGA DEL MODELO OCR ---
print("🔎 Cargando modelo YOLO...")
model = YOLO(yolo_model_path)
print("✅ Modelo cargado.")


# --- 4. BUCLE DE PRUEBA FINAL (ENFOQUE EN CONFIANZA) ---
output_folder = "resultados_test_confianza"
os.makedirs(output_folder, exist_ok=True)
print(f"\n🚀 Iniciando test de confianza. Resultados en '{output_folder}'")

test_results = []

for intensity_level in np.linspace(0.0, 1.0, 11):
    simulated_image = simular_iluminacion_dinamica(intensity_level)
    ocr_results = model(simulated_image, imgsz=320, conf=0.5, verbose=False)
    
    placa_reconocida = "No detectada"
    confianza_ocr = 0.0
    
    if ocr_results and len(ocr_results[0].boxes) > 0:
        box = ocr_results[0].boxes[0]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(simulated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        roi = simulated_image[y1:y2, x1:x2]
        img_preprocesada = preprocesar_placa(roi)

        if img_preprocesada is not None:
            texto_placa, confianza = detectar_texto(img_preprocesada)
            if texto_placa:
                placa_reconocida = texto_placa
                confianza_ocr = confianza
    
    print(f"--- Intensidad: {intensity_level:.2f} | OCR: {placa_reconocida} | Confianza: {confianza_ocr:.1f}% ---")
    
    test_results.append({
        "intensidad": intensity_level, 
        "ocr": placa_reconocida, 
        "confianza": confianza_ocr
    })
    
    cv2.putText(simulated_image, f"Int: {intensity_level:.2f} OCR: {placa_reconocida} (Conf: {confianza_ocr:.1f}%)", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.imwrite(os.path.join(output_folder, f"test_confianza_{intensity_level:.2f}.png"), simulated_image)


# --- 5. RESUMEN FINAL DE MÉTRICAS ---
print("\n\n" + "="*60)
print("📊 RESUMEN FINAL DE PRUEBAS DE CONFIANZA")
print("="*60)

average_confidence = np.mean([res["confianza"] for res in test_results if res["confianza"] > 0])
print(f"🤔 Confianza Promedio (de Tesseract, en detecciones válidas): {average_confidence:.2f}%")

print("\n--- Detalle por Intensidad ---")
print(f"{'Intensidad':<12} | {'Texto Reconocido':<20} | {'Confianza (%)':<15}")
print("-"*60)
for res in test_results:
    print(f"{res['intensidad']:<12.2f} | {res['ocr']:<20} | {res['confianza']:<15.1f}")

print("\n✅ Todas las pruebas han finalizado.")