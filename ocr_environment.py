import gymnasium as gym
from gymnasium import spaces
import numpy as np
import cv2  
from simulation_manager import SimulationManager
from arduino_python import FuzzyController 
from preprocesamiento import preprocesar_placa, detectar_texto
from ultralytics import YOLO

class OCREnvironment(gym.Env):
    """
    Entorno de RL donde el agente aprende a ajustar un controlador difuso.
    La observación se basa en un sondeo inicial con dos flashes para diagnosticar el entorno.
    """
    def __init__(self):
        super(OCREnvironment, self).__init__()
        
        self.sim_manager = SimulationManager(environments_base_path='sistema_control_adaptativo/entornos/')
        self.fuzzy_controller = FuzzyController()
        self.yolo_model = YOLO("runs/detect/placas_v14/weights/best.pt")
        
        self.action_space = spaces.Box(low=np.array([10, 51, 10, 51]), high=np.array([50, 90, 50, 90]), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=100, shape=(3,), dtype=np.float32)

    def _get_ocr_confidence(self, image):
        """Función auxiliar para obtener la confianza del OCR de una imagen."""
        results = self.yolo_model(image, imgsz=320, conf=0.5, verbose=False)
        if results and len(results[0].boxes) > 0:
            box = results[0].boxes[0]
            roi = image[int(box.xyxy[0][1]):int(box.xyxy[0][3]), int(box.xyxy[0][0]):int(box.xyxy[0][2])]
            _, confidence = detectar_texto(preprocesar_placa(roi))
            return confidence if confidence is not None else 0.0
        return 0.0

    def step(self, action):
        """El agente toma una acción y calculamos la recompensa."""
        self.fuzzy_controller.tune(action)
        
        flash_power = self.fuzzy_controller.compute(self.last_observation[0], self.last_observation[2])
        intensity = flash_power / 255.0
        
        final_image = self.sim_manager.simulate_lighting(intensity)
        final_confidence = self._get_ocr_confidence(final_image)

        reward = final_confidence
        terminated = True
        truncated = False
        new_observation = np.array([self.last_observation[0], final_confidence, final_confidence], dtype=np.float32)
        info = {}
        
        return new_observation, reward, terminated, truncated, info

    def reset(self, seed=None):
        """
        Inicia un nuevo episodio: carga un entorno y realiza el sondeo con dos flashes.
        """
        if seed is not None:
            super().reset(seed=seed)
        
        random_env = self.sim_manager.get_random_environment_name()
        self.sim_manager.load_environment(random_env)
        
        img_flash_bajo = self.sim_manager.simulate_lighting(0.25)
        conf_flash_bajo = self._get_ocr_confidence(img_flash_bajo)
        
        img_flash_alto = self.sim_manager.simulate_lighting(0.75)
        conf_flash_alto = self._get_ocr_confidence(img_flash_alto)

        ambient_light = np.mean(cv2.cvtColor(self.sim_manager.sorted_images_by_intensity[0], cv2.COLOR_BGR2GRAY))
        observation = np.array([ambient_light / 2.55, conf_flash_bajo, conf_flash_alto], dtype=np.float32)
        
        self.last_observation = observation
        info = {}
        
        return observation, info