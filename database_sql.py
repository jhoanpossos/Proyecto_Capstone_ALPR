
import pyodbc
import tkinter as tk
from tkinter import messagebox

def conectar_sql_server():
    try:
        connection_string = (
            "Driver={ODBC Driver 18 for SQL Server};"
            "Server=tcp:servidor-alpr-test-final.database.windows.net,1433;"
            "Database=Registro_Placas;"
            "Uid=jhoan;"
            "Pwd=Capston_2025!;"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        conn = pyodbc.connect(connection_string)
        print("✅ Conexión con Azure SQL Database establecida.")
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con Azure SQL Database: {e}")
        return None

def guardar_en_base_de_datos(conn, placa):
    # El resto de las funciones de DB no necesitan cambios
    try:
        cursor = conn.cursor()
        query = "INSERT INTO PlacasDetectadas (Placa) VALUES (?)"
        cursor.execute(query, placa)
        conn.commit()
    except Exception: pass

def verificar_placa_registrada(conn, placa):
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM VehiculosRegistrados WHERE Placa = ?"
        cursor.execute(query, placa)
        return cursor.fetchone()
    except Exception:
        return None
