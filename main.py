
import cv2
import time
from ultralytics import YOLO
from arduino_python import conectar_arduino, enviar_comando_arduino, cerrar_conexion_arduino
from database_sql import conectar_sql_server, guardar_en_base_de_datos, verificar_placa_registrada, mostrar_interfaz_registro
from preprocesamiento import preprocesar_placa, detectar_texto

# --- SETUP ---
model = YOLO("runs/detect/placas_v14/weights/best.pt")
arduino = conectar_arduino()
conn = conectar_sql_server()

if conn is None:
    print("❌ No se pudo establecer conexión con SQL Server. Finalizando...")
    exit()

cap = cv2.VideoCapture(0)
placa_detectada = False
start_time = None
roi_estabilizada = None

print("Iniciando detección en tiempo real...")

# --- LOOP ---
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, imgsz=320, conf=0.5)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            roi = frame[y1:y2, x1:x2]

            if not placa_detectada:
                print("Placa detectada. Esperando estabilización...")
                start_time = time.time()
                roi_estabilizada = roi.copy()
                placa_detectada = True
            
            elif time.time() - start_time < 3:
                roi_estabilizada = roi.copy()

            elif time.time() - start_time >= 3:
                print("Capturando imagen y reconociendo caracteres...")
                img_preprocesada = preprocesar_placa(roi_estabilizada)
                if img_preprocesada is not None:
                    # La función detectar_texto ahora devuelve texto y confianza
                    placa_texto, confianza = detectar_texto(img_preprocesada)
                    
                    if placa_texto:
                        print(f"Placa reconocida: {placa_texto} (Confianza: {confianza:.2f}%)")
                        vehiculo = verificar_placa_registrada(conn, placa_texto)
                        
                        if vehiculo:
                            print(f"Placa autorizada. Vehículo: {vehiculo}")
                            guardar_en_base_de_datos(conn, placa_texto)
                            enviar_comando_arduino(arduino, "OPEN")
                        else:
                            print("Placa no registrada. Solicitar registro.")
                            mostrar_interfaz_registro(conn, placa_texto)
                        
                        placa_detectada = False
                        time.sleep(5)
                    else:
                        print("No se reconoció texto en la placa. Reintentando...")
                        placa_detectada = False
                        time.sleep(2)

    cv2.imshow("📷 Detección de placas", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- CLEANUP ---
cap.release()
cv2.destroyAllWindows()
cerrar_conexion_arduino(arduino)
if conn:
    conn.close()
