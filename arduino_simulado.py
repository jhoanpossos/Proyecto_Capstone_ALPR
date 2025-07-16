# arduino_simulado.py
import time

def conectar_arduino(port=None, baudrate=None):
    """
    Simula una conexión exitosa con el Arduino.
    """
    print("✅ [SIMULACIÓN] Conexión con Arduino establecida.")
    # Devolvemos un objeto 'dummy' para que el código no falle.
    return {"status": "conectado"}

def enviar_comando_arduino(arduino, comando):
    """
    Simula el envío de un comando, imprimiéndolo en la terminal.
    """
    if arduino:
        print(f"➡️  [SIMULACIÓN ARDUINO] Recibido comando: {comando}")
        if comando == "OPEN":
            print("... Barrera simulada se abre por 10 segundos y se cierra.")
    else:
        print("❌ [SIMULACIÓN] Arduino no está conectado.")

def cerrar_conexion_arduino(arduino):
    """
    Simula el cierre de la conexión.
    """
    if arduino:
        print("✅ [SIMULACIÓN] Conexión con Arduino cerrada.")