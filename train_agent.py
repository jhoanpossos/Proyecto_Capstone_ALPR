
from stable_baselines3 import PPO
from ocr_environment import OCREnvironment
import torch

# Verificar si CUDA está disponible y establecer el dispositivo
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Usando dispositivo: {device}")

# 1. Crear el entorno personalizado
env = OCREnvironment()

# 2. Crear el agente PPO
model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ppo_tensorboard/", device=device)

print("\n🚀 Iniciando entrenamiento del agente PPO...")

# 3. Entrenar el agente
model.learn(total_timesteps=10000)

print("\n✅ Entrenamiento finalizado.")

# 4. Guardar el agente entrenado
model.save("ppo_fuzzy_ocr_controller")
print("\n💾 Agente guardado como 'ppo_fuzzy_ocr_controller.zip'")
