import pyodbc
import tkinter as tk
from tkinter import messagebox

# Función para conectar al servidor SQL Server.
def conectar_sql_server():
    try:
        # Configuración de la conexión
        conn = pyodbc.connect(
            "Driver={SQL Server};"
            "Server=DESKTOP-TR3KEU4;"
            "Database=VisionPark;"
            "Trusted_Connection=yes;"
        )
        print("Conexión con SQL Server establecida.")
        return conn     # Retornamos la conexión.

    except Exception as e:      # Mostramos un error si ocurre algún problema.
        print(f"Error al conectar con SQL Server: {e}")
        return None



conectar_sql_server()