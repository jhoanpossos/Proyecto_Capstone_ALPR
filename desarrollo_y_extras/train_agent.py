from stable_baselines3 import PPO
from ocr_environment import OCREnvironment
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Usando dispositivo: {device}")

# 1. Crear el entorno personalizado (con la nueva lógica de diagnóstico)
env = OCREnvironment()

# 2. Crear el agente PPO
model = PPO(
    "MlpPolicy", 
    env, 
    verbose=1, 
    tensorboard_log="sistema_control_adaptativo/logs_tensorboard/", 
    device=device
)

print("\n🚀 Iniciando re-entrenamiento del agente con diagnóstico de entorno...")

# 3. Entrenar el agente por más tiempo
model.learn(total_timesteps=50000)

print("\n✅ Re-entrenamiento finalizado.")

# 4. Guardar el nuevo agente "experto"
model.save("sistema_control_adaptativo/agentes_entrenados/ppo_agente_experto")
print("\n💾 Agente experto guardado en 'sistema_control_adaptativo/agentes_entrenados/'")