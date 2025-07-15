import pygame
import numpy as np
import cv2
import time
from ultralytics import YOLO
from stable_baselines3 import PPO

# Importar nuestros módulos
from arduino_python import FuzzyController
from database_sql import conectar_sql_server, verificar_placa_registrada
from preprocesamiento import preprocesar_placa, detectar_texto

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
print("⚙️  Cargando todos los modelos y configurando el sistema...")
# Cargar modelos de IA
try:
    agente_ppo = PPO.load("sistema_control_adaptativo/agentes_entrenados/ppo_fuzzy_ocr_controller.zip")
    yolo_model = YOLO("runs/detect/placas_v14/weights/best.pt")
    fuzzy_controller = FuzzyController()
    print("✅ Modelos de IA cargados.")
except Exception as e:
    print(f"❌ Error al cargar modelos: {e}")
    exit()

# Conectar a la base de datos
conn = conectar_sql_server()
if conn is None:
    print("❌ No se pudo conectar a la base de datos. Finalizando.")
    exit()

# Iniciar la cámara
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Error al abrir la cámara.")
    exit()

# --- 2. CONFIGURACIÓN DE PYGAME (EL SIMULADOR VISUAL) ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simulador de Sistema ALPR")
font = pygame.font.Font(None, 24)
clock = pygame.time.Clock()

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
RED = (255, 80, 80)
GREEN = (80, 255, 80)
BLUE = (100, 100, 255)

# Estado de la simulación
log_messages = ["Presiona 'D' para simular la detección de un carro..."]
barrier_angle = 0  # 0 = cerrada, -90 = abierta
target_angle = 0
flash_brightness = 0
is_processing = False

# --- 3. BUCLE PRINCIPAL (PYGAME + LÓGICA DE CONTROL) ---
running = True
while running:
    # Manejo de eventos (ej. cerrar la ventana)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Simular la llegada de un carro al presionar 'D'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_d and not is_processing:
            is_processing = True
            log_messages = ["🚗 Vehículo detectado!"]
            
            # --- COMIENZA EL CICLO DE CONTROL INTELIGENTE ---
            # 1. Tomar foto inicial y analizar
            ret, frame = cap.read()
            if ret:
                log_messages.append("📸 Analizando condiciones iniciales...")
                ambient_light = np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
                observation = np.array([ambient_light / 2.55, 0], dtype=np.float32)

                # 2. El agente PPO decide la acción
                action, _ = agente_ppo.predict(observation, deterministic=True)
                log_messages.append(f"🤖 Agente decidió acción: [{action[0]:.0f}, {action[1]:.0f}, ...]")
                fuzzy_controller.tune(action)

                # 3. El controlador Fuzzy calcula la potencia
                flash_power = fuzzy_controller.compute(observation[0], observation[1])
                flash_brightness = int(flash_power) # Actualizar visualización del flash
                log_messages.append(f"💡 Flash activado a potencia: {flash_brightness}")
                
                # Simular pequeña pausa para el flash y tomar foto final
                time.sleep(0.5)
                ret_final, final_frame = cap.read()
                flash_brightness = 0 # Apagar flash visual

                # 4. Procesar la imagen final
                if ret_final:
                    results = yolo_model(final_frame, imgsz=320, conf=0.5, verbose=False)
                    placa_reconocida = False
                    if results and len(results[0].boxes) > 0:
                        box = results[0].boxes[0]
                        roi = final_frame[int(box.xyxy[0][1]):int(box.xyxy[0][3]), int(box.xyxy[0][0]):int(box.xyxy[0][2])]
                        texto_placa, confianza = detectar_texto(preprocesar_placa(roi))
                        if texto_placa:
                            placa_reconocida = True
                            log_messages.append(f"✅ Placa reconocida: {texto_placa} (Conf: {confianza:.1f}%)")
                            vehiculo = verificar_placa_registrada(conn, texto_placa)
                            if vehiculo:
                                log_messages.append("➡️ Vehículo AUTORIZADO.")
                                log_messages.append("🚧 Abriendo barrera...")
                                target_angle = -90 # Comando para abrir la barrera
                            else:
                                log_messages.append("➡️ Vehículo NO REGISTRADO.")
                    if not placa_reconocida:
                        log_messages.append("❌ No se pudo leer la placa.")
                
            # Reiniciar para el próximo carro después de un tiempo
            time.sleep(5) # Pausa antes de poder detectar otro carro
            is_processing = False
            log_messages = ["Presiona 'D' para simular la detección de un carro..."]


    # --- ACTUALIZAR ESTADO DE LA ANIMACIÓN ---
    # Mover la barrera suavemente hacia su ángulo objetivo
    if barrier_angle > target_angle:
        barrier_angle -= 2
    elif barrier_angle < target_angle:
        barrier_angle += 2
    # Lógica para cerrar la barrera automáticamente
    if barrier_angle <= -90:
        target_angle = 0


    # --- DIBUJAR TODO EN LA PANTALLA ---
    screen.fill(GRAY)
    
    # Dibujar base de la barrera
    pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH / 2 - 25, SCREEN_HEIGHT - 100, 50, 50))
    
    # Dibujar brazo de la barrera
    len_brazo = 250
    rad_angle = np.deg2rad(barrier_angle)
    end_x = (SCREEN_WIDTH / 2) + len_brazo * np.cos(rad_angle)
    end_y = (SCREEN_HEIGHT - 75) + len_brazo * np.sin(rad_angle)
    pygame.draw.line(screen, RED, (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 75), (end_x, end_y), 15)

    # Dibujar indicador del flash
    flash_color = (flash_brightness, flash_brightness, 0)
    pygame.draw.circle(screen, flash_color, (50, 50), 30)
    
    # Dibujar log de texto
    for i, msg in enumerate(log_messages[-10:]): # Mostrar solo los últimos 10 mensajes
        text_surface = font.render(msg, True, WHITE)
        screen.blit(text_surface, (20, 100 + i * 25))

    # Actualizar la pantalla
    pygame.display.flip()
    
    # Limitar a 60 FPS
    clock.tick(60)

# --- LIMPIEZA ---
cap.release()
conn.close()
pygame.quit()
print("Simulación finalizada.")