import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import exposure
import os 

# --- 1. CONFIGURACIÓN INICIAL ---
folder_path = "." 

# Imagen para la comparación inicial (la base original con faros)
initial_comparison_base_img_name = "img_base.png" 

# Imagen diurna de referencia para el balance de blancos
day_image_filename_for_color_ref = "carro_dia.png" 

# --- AÑADIDO: Lista de imágenes que SÍ queremos usar para la interpolación de la base dinámica ---
# ¡IMPORTANTE! Aquí ajustamos los puntos de anclaje para la mezcla de la base.
# Queremos que la mezcla ocurra entre la más oscura y la de los faros.
# Puedes añadir más puntos si tienes imágenes intermedias.
images_for_dynamic_base_interpolation = [
    "ChatGPT Image 30 jun 2025, 05_06_32 p.m..png", # La más oscura (0.00 en la progresión)
    "img_base.png" # La de los faros encendidos (se hará visible más tarde)
]


# --- 2. CARGAR IMÁGENES DE LA CARPETA ---
all_files_in_folder = os.listdir(folder_path)
image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
image_paths = []
for filename in all_files_in_folder:
    if filename.lower().endswith(image_extensions):
        image_paths.append(os.path.join(folder_path, filename)) 

if not image_paths:
    raise FileNotFoundError(f"No se encontraron imágenes en la carpeta: '{folder_path}'")

images = {}
for path in image_paths:
    img = cv2.imread(path)
    if img is None:
        print(f"Advertencia: No se pudo cargar la imagen '{path}'. Se omitirá.")
        continue
    images[os.path.basename(path)] = img 

print(f"Imágenes cargadas desde '{folder_path}':")
for img_name in images.keys():
    print(f"- {img_name}")

if initial_comparison_base_img_name not in images:
    raise ValueError(f"La imagen base para comparación '{initial_comparison_base_img_name}' no se encontró o no se pudo cargar.")
if day_image_filename_for_color_ref not in images:
    raise ValueError(f"La imagen diurna de referencia '{day_image_filename_for_color_ref}' no se encontró o no se pudo cargar.")
for img_name in images_for_dynamic_base_interpolation:
    if img_name not in images:
        raise ValueError(f"La imagen '{img_name}' especificada para la interpolación de la base dinámica no se encontró o no se pudo cargar.")


# ------------------------------------------------------------------
# 3. AUTO-ETIQUETADO Y CARACTERIZACIÓN AUTOMÁTICA
# ------------------------------------------------------------------

# 3.1. Calcular métricas de luminosidad y color para todas las imágenes
luminosity_metrics = {}
for name, img_bgr in images.items():
    hsv_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    luminosity_channel = hsv_img[:, :, 2] 

    mean_v = np.mean(luminosity_channel)
    std_v = np.std(luminosity_channel) 

    img_float = img_bgr.astype(np.float32)
    mean_b = np.mean(img_float[:,:,0])
    mean_g = np.mean(img_float[:,:,1])
    mean_r = np.mean(img_float[:,:,2])

    luminosity_metrics[name] = {
        "mean_v": mean_v,
        "std_v": std_v,
        "mean_b": mean_b, "mean_g": mean_g, "mean_r": mean_r
    }

print("\n--- Métricas de Luminosidad y Color por Imagen de Referencia ---")
for name, metrics in luminosity_metrics.items():
    print(f"- {name}: MeanV={metrics['mean_v']:.2f}, StdV={metrics['std_v']:.2f}, "
          f"MeanB={metrics['mean_b']:.2f}, MeanG={metrics['mean_g']:.2f}, MeanR={metrics['mean_r']:.2f}")

# 3.2. Normalizar las métricas para obtener la "etiqueta" de intensidad (0-1)
min_v = float('inf')
max_v = float('-inf')
for metrics in luminosity_metrics.values():
    if metrics["mean_v"] < min_v:
        min_v = metrics["mean_v"]
    if metrics["mean_v"] > max_v:
        max_v = metrics["mean_v"]

intensity_labels = {}
for name, metrics in luminosity_metrics.items():
    if (max_v - min_v) == 0: 
        intensity_labels[name] = 0.5 
    else:
        intensity_labels[name] = (metrics["mean_v"] - min_v) / (max_v - min_v)
    
    luminosity_metrics[name]["intensity_label"] = intensity_labels[name]

print("\n--- Etiquetas de Intensidad Generadas Automáticamente (para referencias) ---")
sorted_labels = sorted(intensity_labels.items(), key=lambda item: item[1])
for name, label in sorted_labels:
    print(f"- {name}: {label:.2f}")


# --- MODIFICADO: Extraer los puntos para la interpolación de la base dinámica ---
# Ahora usamos SOLO las imágenes de `images_for_dynamic_base_interpolation` para la mezcla de la base.
# Y aseguramos que el punto de "activación de faros" sea más alto.
dynamic_base_intensities_unsorted = np.array([intensity_labels[name] for name in images_for_dynamic_base_interpolation])
sorted_dynamic_base_indices = np.argsort(dynamic_base_intensities_unsorted)

dynamic_base_images_sorted = [images[images_for_dynamic_base_interpolation[i]] for i in sorted_dynamic_base_indices]
dynamic_base_intensities_sorted = dynamic_base_intensities_unsorted[sorted_dynamic_base_indices]

# AÑADIDO: Definir un "umbral de activación" para la mezcla de la imagen con faros.
# Por debajo de este umbral, usaremos solo la imagen más oscura.
# Por encima, empezaremos a mezclar con la imagen con faros.
# Esto crea una "zona muerta" o una transición más gradual.
activation_threshold_for_headlights = 0.25 # Puedes ajustar este valor (ej. 0.1, 0.3)
# Asegúrate de que la intensidad más baja en dynamic_base_intensities_sorted sea 0.00
# y la más alta sea la de img_base.png. Si tienes más de 2 imágenes, esto se complicaría.
# Por ahora, asumimos que images_for_dynamic_base_interpolation solo tiene la oscura y la de faros.


# 3.3. Derivar los valores de alpha, beta y ganancias de color correspondientes para la interpolación
intensities_for_interp_unsorted = np.array([metrics["intensity_label"] for metrics in luminosity_metrics.values()])
image_names_in_order = [os.path.basename(p) for p in image_paths] 
sorted_indices_full_set = np.argsort(intensities_for_interp_unsorted) 

intensities_for_interp_sorted = intensities_for_interp_unsorted[sorted_indices_full_set]

# Para alpha (contraste). Rangos ajustados para "luz artificial máxima".
std_v_values_unsorted = np.array([luminosity_metrics[name]["std_v"] for name in image_names_in_order])
min_std_v = np.min(std_v_values_unsorted)
max_std_v = np.max(std_v_values_unsorted)
if (max_std_v - min_std_v) == 0:
    alpha_values_at_points = np.ones_like(std_v_values_unsorted) * 1.0
else:
    alpha_values_at_points = 0.5 + (std_v_values_unsorted - min_std_v) / (max_std_v - min_std_v) * (1.2 - 0.5) 

# Para beta (brillo). Rangos ajustados para "luz artificial máxima".
mean_v_values_unsorted = np.array([luminosity_metrics[name]["mean_v"] for name in image_names_in_order])
min_mean_v = np.min(mean_v_values_unsorted)
max_mean_v = np.max(mean_v_values_unsorted)
if (max_mean_v - min_mean_v) == 0:
    beta_values_at_points = np.zeros_like(mean_v_values_unsorted)
else:
    beta_values_at_points = -10 + (mean_v_values_unsorted - min_mean_v) / (max_mean_v - min_mean_v) * (50 - (-10)) 


# Para las ganancias de color, se usa la imagen diurna de referencia.
mean_b_day_ref = luminosity_metrics[day_image_filename_for_color_ref]["mean_b"]
mean_g_day_ref = luminosity_metrics[day_image_filename_for_color_ref]["mean_g"]
mean_r_day_ref = luminosity_metrics[day_image_filename_for_color_ref]["mean_r"]

gain_b_calculated_unsorted = []
gain_g_calculated_unsorted = []
gain_r_calculated_unsorted = []

for name in image_names_in_order: 
    metrics = luminosity_metrics[name]
    gb = (mean_b_day_ref / metrics["mean_b"]) if metrics["mean_b"] > 0 else 1.0
    gg = (mean_g_day_ref / metrics["mean_g"]) if metrics["mean_g"] > 0 else 1.0
    gr = (mean_r_day_ref / metrics["mean_r"]) if metrics["mean_r"] > 0 else 1.0

    gain_b_calculated_unsorted.append(gb)
    gain_g_calculated_unsorted.append(gg)
    gain_r_calculated_unsorted.append(gr)

gain_b_values_at_points = np.array(gain_b_calculated_unsorted)
gain_g_values_at_points = np.array(gain_g_calculated_unsorted)
gain_r_values_at_points = np.array(gain_r_calculated_unsorted)

alpha_values_at_points_sorted = alpha_values_at_points[sorted_indices_full_set]
beta_values_at_points_sorted = beta_values_at_points[sorted_indices_full_set]
gain_b_values_at_points_sorted = gain_b_values_at_points[sorted_indices_full_set]
gain_g_values_at_points_sorted = gain_g_values_at_points[sorted_indices_full_set]
gain_r_values_at_points_sorted = gain_r_values_at_points[sorted_indices_full_set]

# ------------------------------------------------------------------
# 4. FUNCIÓN PARA AJUSTAR ILUMINACIÓN (MODIFICADA para base dinámica y aparición gradual de placa)
# ------------------------------------------------------------------
def ajustar_iluminacion_automatica_dinamica(intensidad_deseada):
    """
    Simula la potencia de una fuente de luz (0‒1). La imagen base se selecciona o mezcla
    dinámicamente según la intensidad deseada para una mejor progresión, controlando
    brillo, contraste y balance de color hasta un nivel de "luz artificial máxima".
    Ajusta la mezcla de la imagen base para una aparición más gradual de la placa.

    Args:
        intensidad_deseada (float): El nivel de intensidad deseado (0.0 a 1.0).
                                    Donde 0 es mínima luz y 1 es máxima luz.
                                    
    Returns:
        numpy.array: La imagen simulada con la iluminación ajustada.
    """
    intensidad_deseada = np.clip(float(intensidad_deseada), 0.0, 1.0)

    # 1. Determinar la imagen base dinámica (o mezcla de bases)
    # Si la intensidad está por debajo del umbral, usar solo la imagen más oscura
    if intensidad_deseada <= activation_threshold_for_headlights:
        img_base_for_transform = dynamic_base_images_sorted[0].copy() # La imagen más oscura
    else:
        # Si está por encima del umbral, hacer la mezcla normal, pero recalibrando el factor de mezcla
        # para que la transición ocurra desde el umbral hasta la intensidad máxima.
        # Esto 'estira' la mezcla de las imágenes base por encima del umbral.
        
        # Calcular el factor de mezcla 'estirado' para la base
        # Este factor irá de 0 a 1 cuando intensidad_deseada vaya de activation_threshold_for_headlights a 1.0
        stretched_mix_factor = (intensidad_deseada - activation_threshold_for_headlights) / (1.0 - activation_threshold_for_headlights)
        stretched_mix_factor = np.clip(stretched_mix_factor, 0.0, 1.0) # Asegurar que esté entre 0 y 1

        # Si solo tenemos dos imágenes en dynamic_base_images_sorted (oscura y faros)
        img1_base = dynamic_base_images_sorted[0].copy() # La oscura
        img2_base = dynamic_base_images_sorted[-1].copy() # La de los faros

        img_base_for_transform = (1.0 - stretched_mix_factor) * img1_base + stretched_mix_factor * img2_base

    # Asegurarse de que la imagen base para la transformación sea float32 para cálculos
    img_base_for_transform = img_base_for_transform.astype(np.float32)

    # 2. Interpolar los parámetros alpha, beta y ganancias de color
    # (Estos se siguen interpolando sobre el rango COMPLETO de intensidades de TODAS las imágenes de referencia)
    alpha_interp = np.interp(intensidad_deseada, intensities_for_interp_sorted, alpha_values_at_points_sorted)
    beta_interp = np.interp(intensidad_deseada, intensities_for_interp_sorted, beta_values_at_points_sorted)

    gain_b_interp = np.interp(intensidad_deseada, intensities_for_interp_sorted, gain_b_values_at_points_sorted)
    gain_g_interp = np.interp(intensidad_deseada, intensities_for_interp_sorted, gain_g_values_at_points_sorted)
    gain_r_interp = np.interp(intensidad_deseada, intensities_for_interp_sorted, gain_r_values_at_points_sorted)

    # 3. Aplicar los ajustes (alpha, beta, ganancias) a la imagen base dinámica
    img_adjusted = img_base_for_transform * alpha_interp + beta_interp
    
    img_adjusted[:, :, 0] *= gain_b_interp 
    img_adjusted[:, :, 1] *= gain_g_interp 
    img_adjusted[:, :, 2] *= gain_r_interp 

    simulated_img = np.clip(img_adjusted, 0, 255).astype(np.uint8)
    
    return simulated_img

# ------------------------------------------------------------------
# 5. REALIZAR LA SIMULACIÓN Y GUARDAR RESULTADOS
# ------------------------------------------------------------------

initial_comparison_base_img_bgr = images[initial_comparison_base_img_name]

print(f"\n--- Iniciando simulación con base dinámica ---")

# --- SIMULACIÓN PARA UNA INTENSIDAD ESPECÍFICA ---
intensidad_a_simular = 0.5 
simulated_result_img = ajustar_iluminacion_automatica_dinamica(intensidad_a_simular)

plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.imshow(cv2.cvtColor(initial_comparison_base_img_bgr, cv2.COLOR_BGR2RGB))
plt.title(f"Imagen Base Fija para Comparación ({initial_comparison_base_img_name})")
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(cv2.cvtColor(simulated_result_img, cv2.COLOR_BGR2RGB))
plt.title(f"Simulación Dinámica Intensidad = {intensidad_a_simular:.2f}")
plt.axis('off')

plt.savefig(f"simulacion_dinamica_unica_intensidad_{intensidad_a_simular:.2f}.png")
plt.close()


# --- MOSTRAR UNA PROGRESIÓN DE INTENSIDAD SIMULADA ---
intensities_to_show_auto = np.linspace(0.0, 1.0, 6) 

plt.figure(figsize=(20, 6)) 
for i, intens in enumerate(intensities_to_show_auto):
    sim_img = ajustar_iluminacion_automatica_dinamica(intens)
    plt.subplot(1, len(intensities_to_show_auto), i + 1)
    plt.imshow(cv2.cvtColor(sim_img, cv2.COLOR_BGR2RGB))
    plt.title(f"Int: {intens:.2f}")
    plt.axis('off')
plt.suptitle(f"Progresión de Intensidad Simulada con Base Dinámica")

safe_base_filename = initial_comparison_base_img_name.replace('.', '_') 
plt.savefig(f"simulacion_progression_dinamica.png")
plt.close()


# --- OPCIONAL: Mostrar las imágenes originales cargadas, ordenadas por su intensidad calculada ---
# plt.figure(figsize=(20, 6))
# for i, (name, img) in enumerate(sorted(images.items(), key=lambda item: intensity_labels[item[0]])):
#     plt.subplot(1, len(images), i + 1)
#     plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
#     plt.title(f"Original: {name} (Int: {intensity_labels[name]:.2f})")
#     plt.axis('off')
# plt.suptitle("Imágenes Originales de Referencia (Ordenadas por Intensidad Calculada)")
# plt.savefig("referencias_originales_ordenadas.png")
# plt.close()