import pyodbc
import tkinter as tk
from tkinter import messagebox

def conectar_sql_server():
    """
    Se conecta a la base de datos que creaste en Azure.
    """
    try:
        # --- DATOS DE CONEXIÓN A AZURE ---
        # Asegúrate de que estos datos coincidan con los de tu servidor.
        server = 'servidor-alpr-test-final.database.windows.net'
        database = 'Registro_Placas'
        username = 'jhoan' # O el usuario que hayas configurado (ej. 'admin_alpr')
        password = 'Capston_2025!' # <-- PRUEBA CON ESTA PRIMERO, O CON LA OTRA OPCIÓN
        # ------------------------------------

        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server},1433;"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )

        conn = pyodbc.connect(connection_string)
        print("✅ Conexión con Azure SQL Database establecida.")
        return conn
        
    except Exception as e:
        print(f"❌ Error al conectar con Azure SQL Database: {e}")  
        return None

def guardar_en_base_de_datos(conn, placa):
    """
    Guarda una placa detectada en la tabla PlacasDetectadas.
    """
    try:
        cursor = conn.cursor()
        query = "INSERT INTO PlacasDetectadas (Placa) VALUES (?)"
        cursor.execute(query, placa)
        conn.commit()
        print(f"Placa '{placa}' registrada en la base de datos.")
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")

def verificar_placa_registrada(conn, placa):
    """
    Verifica si una placa existe en la tabla VehiculosRegistrados.
    """
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM VehiculosRegistrados WHERE Placa = ?"
        cursor.execute(query, placa)
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al verificar la placa: {e}")
        return None

# SE COMENTA LA INTERFAZ GRAFICA QUE SE MOSTRABA ANTERIORMENTE
# def mostrar_interfaz_registro(conn, placa):
#     """
#     Muestra una ventana para registrar un nuevo vehículo.
#     """
#     def registrar():
#         nombre = entry_nombre.get()
#         marca = entry_marca.get()
#         modelo = entry_modelo.get()
#         color = entry_color.get()

#         if not all([nombre, marca, modelo, color]):
#             messagebox.showerror("Error", "Por favor, completa todos los campos.")
#             return

#         try:
#             cursor = conn.cursor()
#             query = "INSERT INTO VehiculosRegistrados (Placa, NombreCompleto, Marca, Modelo, Color) VALUES (?, ?, ?, ?, ?)"
#             cursor.execute(query, (placa, nombre, marca, modelo, color))
#             conn.commit()
#             messagebox.showinfo("Éxito", f"Vehículo con placa '{placa}' registrado exitosamente.")
#             ventana.destroy()
#         except Exception as e:
#             messagebox.showerror("Error", f"Error al registrar el vehículo: {e}")

#     ventana = tk.Tk()
#     ventana.title("Registro de Vehículo")
#     ventana.geometry("400x300")
    
#     tk.Label(ventana, text=f"Placa detectada: {placa}", font=("Arial", 14)).pack(pady=10)
    
#     tk.Label(ventana, text="Nombre del dueño:").pack()
#     entry_nombre = tk.Entry(ventana, width=30)
#     entry_nombre.pack()

#     tk.Label(ventana, text="Marca del vehículo:").pack()
#     entry_marca = tk.Entry(ventana, width=30)
#     entry_marca.pack()

#     tk.Label(ventana, text="Modelo del vehículo:").pack()
#     entry_modelo = tk.Entry(ventana, width=30)
#     entry_modelo.pack()

#     tk.Label(ventana, text="Color del vehículo:").pack()
#     entry_color = tk.Entry(ventana, width=30)
#     entry_color.pack()
    
#     tk.Button(ventana, text="Registrar", command=registrar).pack(pady=20)
#     ventana.mainloop()
