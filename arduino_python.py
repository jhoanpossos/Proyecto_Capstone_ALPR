
import serial
import time
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class FuzzyController:
    def __init__(self):
        self.luz_ambiental = ctrl.Antecedent(np.arange(0, 101, 1), 'luz_ambiental')
        self.confianza_ocr = ctrl.Antecedent(np.arange(0, 101, 1), 'confianza_ocr')
        self.potencia_flash = ctrl.Consequent(np.arange(0, 256, 1), 'potencia_flash')
        # Se definen valores iniciales, pero el agente de RL los ajustará
        self.tune([50, 80, 40, 70])

    def tune(self, params):
        '''
        Ajusta las funciones de membresía del controlador difuso.
        Esta es la 'ACCIÓN' que el agente de RL podrá tomar.
        '''
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

def conectar_arduino(port='COM4', baudrate=9600):
    puertos_linux = ['/dev/ttyUSB0', '/dev/ttyACM0']
    try:
        arduino = serial.Serial(port, baudrate, timeout=1)
        print(f"Conexión con Arduino establecida en {port}.")
        return arduino
    except serial.SerialException:
        for p in puertos_linux:
            try:
                arduino = serial.Serial(p, baudrate, timeout=1)
                print(f"Conexión con Arduino establecida en {p}.")
                return arduino
            except serial.SerialException:
                continue
        print(f"Error: No se pudo conectar con Arduino.")
        return None

def enviar_comando_arduino(arduino, comando):
    if arduino and arduino.is_open:
        arduino.write(f"{comando}\n".encode())
        print(f"Comando enviado al Arduino: {comando}")

def cerrar_conexion_arduino(arduino):
    if arduino and arduino.is_open:
        arduino.close()
        print("Conexión con Arduino cerrada.")
