
from stable_baselines3 import PPO
from ocr_environment import OCREnvironment
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Usando dispositivo: {device}")

env = OCREnvironment()
model = PPO(
    "MlpPolicy", 
    env, 
    verbose=1, 
    tensorboard_log="sistema_control_adaptativo/logs_tensorboard/", 
    device=device
)

print("\n🚀 Iniciando entrenamiento del agente PPO...")
model.learn(total_timesteps=10000)
print("\n✅ Entrenamiento finalizado.")

model.save("sistema_control_adaptativo/agentes_entrenados/ppo_fuzzy_ocr_controller")
print("\n💾 Agente guardado en 'sistema_control_adaptativo/agentes_entrenados/'")
