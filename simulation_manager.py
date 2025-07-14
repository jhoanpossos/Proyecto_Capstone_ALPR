
import cv2
import numpy as np
import os
import random

class SimulationManager:
    def __init__(self, environments_base_path):
        self.base_path = environments_base_path
        self.available_environments = [d for d in os.listdir(self.base_path) 
                                       if os.path.isdir(os.path.join(self.base_path, d))]
        if not self.available_environments:
            raise FileNotFoundError(f"No se encontraron directorios de entornos en '{self.base_path}'")
        print(f"✅ Gestor de Simulación inicializado. {len(self.available_environments)} entornos encontrados.")
        self.current_env_name = None
        self.images = {}
        self.sorted_images_by_intensity = []

    def load_environment(self, env_name):
        if env_name not in self.available_environments:
            raise ValueError(f"El entorno '{env_name}' no existe.")
        self.current_env_name = env_name
        env_path = os.path.join(self.base_path, env_name)
        self.images = {}
        for filename in os.listdir(env_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                path = os.path.join(env_path, filename)
                img = cv2.imread(path)
                if img is not None:
                    self.images[filename] = img
        if len(self.images) < 2:
            raise ValueError(f"El entorno '{env_name}' debe contener al menos 2 imágenes.")
        self.sorted_images_by_intensity = sorted(self.images.values(), key=lambda img: np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 2]))

    def get_random_environment_name(self):
        return random.choice(self.available_environments)

    def simulate_lighting(self, intensity, activation_threshold=0.25):
        if not self.current_env_name:
            raise RuntimeError("Carga un entorno con 'load_environment()' primero.")
        intensity = np.clip(float(intensity), 0.0, 1.0)
        darkest_img = self.sorted_images_by_intensity[0]
        headlight_img = self.sorted_images_by_intensity[1]
        if intensity <= activation_threshold:
            base_dinamica = darkest_img.astype(np.float32)
        else:
            mix_factor = (intensity - activation_threshold) / (1.0 - activation_threshold)
            base_dinamica = cv2.addWeighted(darkest_img, 1.0 - mix_factor, headlight_img, mix_factor, 0).astype(np.float32)
        beta = (intensity - 0.5) * 50
        alpha = 1.0 + (intensity * 0.2)
        return cv2.convertScaleAbs(base_dinamica, alpha=alpha, beta=beta)
