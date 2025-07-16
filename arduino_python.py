import serial
import time
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import cv2

# --- VARIABLES GLOBALES PARA LA SIMULACIÓN ---
SIMULATION_MODE = False
dashboard = None
log_messages = ["Presiona 'D' para simular deteccion, 'Q' para salir."]
barrier_angle, target_angle = 0, 0
flash_brightness = 0

# --- CLASE DEL CONTROLADOR DIFUSO (Sin cambios) ---
class FuzzyController:
    # ... (el código de la clase FuzzyController se mantiene exactamente igual) ...
    def __init__(self):
        self.luz_ambiental = ctrl.Antecedent(np.arange(0, 101, 1), 'luz_ambiental')
        self.confianza_ocr = ctrl.Antecedent(np.arange(0, 101, 1), 'confianza_ocr')
        self.potencia_flash = ctrl.Consequent(np.arange(0, 256, 1), 'potencia_flash')
        self.tune([50, 80, 40, 70])
    def tune(self, params):
        conf_media_fin, conf_alta_inicio, luz_media_fin, luz_clara_inicio = params
        self.confianza_ocr['baja'] = fuzz.trimf(self.confianza_ocr.universe, [0, 0, conf_media_fin])
        self.confianza_ocr['media'] = fuzz.trimf(self.confianza_ocr.universe, [0, conf_media_fin, conf_alta_inicio])
        self.confianza_ocr['alta'] = fuzz.trimf(self.confianza_ocr.universe, [conf_alta_inicio, 100, 100])
        self.luz_ambiental['oscura'] = fuzz.trimf(self.luz_ambiental.universe, [0, 0, luz_media_fin])
        self.luz_ambiental['media'] = fuzz.trimf(self.luz_ambiental.universe, [0, luz_media_fin, luz_clara_inicio])
        self.luz_ambiental['clara'] = fuzz.trimf(self.luz_ambiental.universe, [luz_clara_inicio, 100, 100])
        self.potencia_flash['baja'] = fuzz.trimf(self.potencia_flash.universe, [0, 0, 85])
        self.potencia_flash['media'] = fuzz.trimf(self.potencia_flash.universe, [80, 170, 255])
        self.potencia_flash['alta'] = fuzz.trimf(self.potencia_flash.universe, [200, 255, 255])
        rule1 = ctrl.Rule(self.confianza_ocr['baja'], self.potencia_flash['alta'])
        rule2 = ctrl.Rule(self.confianza_ocr['media'] & self.luz_ambiental['oscura'], self.potencia_flash['media'])
        rule3 = ctrl.Rule(self.confianza_ocr['alta'] | self.luz_ambiental['clara'], self.potencia_flash['baja'])
        self.control_system = ctrl.ControlSystem([rule1, rule2, rule3])
        self.simulation = ctrl.ControlSystemSimulation(self.control_system)
    def compute(self, input_luz, input_confianza):
        self.simulation.input['luz_ambiental'] = input_luz
        self.simulation.input['confianza_ocr'] = input_confianza
        try:
            self.simulation.compute()
            return self.simulation.output['potencia_flash']
        except:
            return 50.0

# --- FUNCIONES DE HARDWARE Y SIMULACIÓN (VERSIÓN CON VISUALIZACIÓN DE ROI) ---

def iniciar_simulador_visual():
    global dashboard
    dashboard = np.zeros((600, 800, 3), dtype="uint8")
    cv2.namedWindow("Simulador de Sistema ALPR (OpenCV)")
    print("✅ Modo simulación visual con OpenCV activado.")

def conectar_arduino(port='/dev/ttyACM0', baudrate=9600):
    global SIMULATION_MODE
    try:
        import serial
        arduino = serial.Serial(port, baudrate, timeout=1)
        SIMULATION_MODE = False
        print(f"✅ Conexión con Arduino real establecida en {port}.")
        return arduino
    except (ImportError, serial.SerialException, NameError):
        SIMULATION_MODE = True
        print(f"⚠️  No se encontró Arduino. Iniciando simulación visual.")
        iniciar_simulador_visual()
        return {"status": "simulado"}

def enviar_comando_arduino(arduino, comando):
    global target_angle, flash_brightness, log_messages
    if not SIMULATION_MODE:
        if arduino and 'is_open' in dir(arduino) and arduino.is_open:
            arduino.write(f"{comando}\\n".encode())
    else:
        log_messages.append(f"➡️  Comando: {comando}")
        if comando == "OPEN":
            target_angle = -90
        elif comando.startswith("SET_FLASH:"):
            try:
                power = int(comando.split(":")[1])
                flash_brightness = power
            except:
                flash_brightness = 0

def actualizar_y_manejar_eventos_simulador(main_frame=None, roi_frame=None):
    """ Dibuja la simulación y ahora también puede mostrar el ROI."""
    global barrier_angle, target_angle, flash_brightness, log_messages, dashboard
    
    if not SIMULATION_MODE:
        if main_frame is not None:
            cv2.imshow("Deteccion en Vivo", main_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): return False
        return True

    # Si se recibe una imagen de ROI, mostrarla en una nueva ventana
    if roi_frame is not None and roi_frame.size > 0:
        cv2.imshow("ROI Detectado", roi_frame)
    
    # Lógica de animación
    if barrier_angle > target_angle: barrier_angle -= 3
    if barrier_angle < -90: target_angle = 0

    # Dibujar dashboard
    dashboard.fill(50)
    # ... (resto de la lógica de dibujo es igual)
    cv2.rectangle(dashboard, (375, 500), (425, 550), (0, 0, 0), -1)
    rad = np.deg2rad(barrier_angle)
    end_x = int(400 + 350 * np.cos(rad))
    end_y = int(525 + 350 * np.sin(rad))
    cv2.line(dashboard, (400, 525), (end_x, end_y), (80, 80, 255), 15)
    flash_color = (0, flash_brightness, flash_brightness)
    cv2.circle(dashboard, (50, 50), 30, flash_color, -1)
    for i, msg in enumerate(log_messages[-15:]):
        cv2.putText(dashboard, msg, (20, 20 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
    cv2.imshow("Simulador de Sistema ALPR (OpenCV)", dashboard)

    if cv2.waitKey(1) & 0xFF == ord('q'): return False
    return True

def cerrar_conexion_arduino(arduino):
    if not SIMULATION_MODE:
        if arduino and 'is_open' in dir(arduino) and arduino.is_open:
            arduino.close()
    cv2.destroyAllWindows()