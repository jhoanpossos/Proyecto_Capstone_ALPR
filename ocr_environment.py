
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from simulation_manager import SimulationManager
from arduino_python import FuzzyController 
from preprocesamiento import preprocesar_placa, detectar_texto
from ultralytics import YOLO

class OCREnvironment(gym.Env):
    def __init__(self):
        super(OCREnvironment, self).__init__()
        self.sim_manager = SimulationManager(environments_base_path='sistema_control_adaptativo/entornos/')
        self.fuzzy_controller = FuzzyController()
        self.yolo_model = YOLO("runs/detect/placas_v14/weights/best.pt")
        self.action_space = spaces.Box(low=np.array([10, 51, 10, 51]), high=np.array([50, 90, 50, 90]), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=100, shape=(2,), dtype=np.float32)

    def step(self, action):
        self.fuzzy_controller.tune(action)
        ambient_light = np.random.uniform(5, 70)
        initial_confidence = 10 
        flash_power = self.fuzzy_controller.compute(ambient_light, initial_confidence)
        intensity = flash_power / 255.0
        simulated_image = self.sim_manager.simulate_lighting(intensity)
        
        ocr_results = self.yolo_model(simulated_image, imgsz=320, conf=0.5, verbose=False)
        final_confidence = 0.0
        if ocr_results and len(ocr_results[0].boxes) > 0:
            box = ocr_results[0].boxes[0]
            roi = simulated_image[int(box.xyxy[0][1]):int(box.xyxy[0][3]), int(box.xyxy[0][0]):int(box.xyxy[0][2])]
            img_preprocesada = preprocesar_placa(roi)
            if img_preprocesada is not None:
                _, confidence = detectar_texto(img_preprocesada)
                final_confidence = confidence if confidence is not None else 0.0

        reward = final_confidence
        terminated = True
        truncated = False
        observation = np.array([ambient_light, final_confidence], dtype=np.float32)
        info = {}
        return observation, reward, terminated, truncated, info

    def reset(self, seed=None):
        if seed is not None:
            super().reset(seed=seed)
        random_env = self.sim_manager.get_random_environment_name()
        self.sim_manager.load_environment(random_env)
        observation = np.array([50, 0], dtype=np.float32)
        info = {}
        return observation, info
