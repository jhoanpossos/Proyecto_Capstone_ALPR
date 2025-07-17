# api.py
from fastapi import FastAPI, HTTPException
import pyodbc
import logging

# Configura un logger simple
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ESTAS CREDENCIALES VIVEN Y MUEREN AQUÍ, EN EL SERVIDOR. NUNCA EN TU PROYECTO PRINCIPAL ---
CONNECTION_STRING = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:servidor-alpr-test-final.database.windows.net,1433;"
    "Database=Registro_Placas;"
    "Uid=jhoan;"
    "Pwd=Capston_2025!;"  # Reemplaza con tu contraseña real si es diferente
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

app = FastAPI()

def get_db_connection():
    """Función para obtener una conexión a la base de datos."""
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        return conn
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al conectar con la base de datos.")

@app.get("/")
def read_root():
    return {"status": "API del Sistema ALPR funcionando"}

@app.get("/verificar_placa/{placa}")
def verificar_placa_endpoint(placa: str):
    """Verifica si una placa está registrada en la base de datos."""
    logger.info(f"Recibida solicitud para verificar placa: {placa}")
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT Placa FROM VehiculosRegistrados WHERE Placa = ?"
    cursor.execute(query, placa)
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        logger.info(f"Placa '{placa}' encontrada.")
        return {"registrada": True}
    else:
        logger.info(f"Placa '{placa}' no encontrada.")
        return {"registrada": False}

@app.post("/guardar_lectura")
def guardar_lectura_endpoint(data: dict):
    """Guarda una placa detectada en la base de datos."""
    placa = data.get('placa')
    if not placa:
        raise HTTPException(status_code=400, detail="Falta el campo 'placa'.")
    
    logger.info(f"Recibida solicitud para guardar placa: {placa}")
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO PlacasDetectadas (Placa) VALUES (?)"
    cursor.execute(query, placa)
    conn.commit()
    conn.close()
    
    logger.info(f"Placa '{placa}' guardada con éxito.")
    return {"status": "ok", "placa_guardada": placa}