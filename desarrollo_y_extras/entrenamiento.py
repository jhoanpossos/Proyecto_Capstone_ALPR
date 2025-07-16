
from ultralytics import YOLO

# Carga un modelo base (ej. yolov8n.pt)
model = YOLO('yolov8n.pt')

# Entrena el modelo con tu dataset
results = model.train(
    data='placas.v1i.yolov8/data.yaml',
    epochs=30,
    imgsz=320,
    batch=4,
    name='placas_v14',
    device='cpu' # Cambia a 'cuda' si tienes una GPU configurada
)

print("Entrenamiento de YOLO finalizado.")
