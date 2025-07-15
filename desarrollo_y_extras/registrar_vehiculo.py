# registrar_vehiculo.py
import tkinter as tk
from tkinter import simpledialog, messagebox
from database_sql import conectar_sql_server

def registrar_vehiculo(conn, placa, nombre, marca, modelo, color):
    try:
        cursor = conn.cursor()
        query = "INSERT INTO VehiculosRegistrados (Placa, NombreCompleto, Marca, Modelo, Color) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(query, (placa, nombre, marca, modelo, color))
        conn.commit()
        messagebox.showinfo("Éxito", f"Vehículo con placa '{placa}' registrado exitosamente.")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al registrar el vehículo: {e}")
        return False

def main():
    # Pedir la placa al usuario
    placa = simpledialog.askstring("Placa", "Introduce la placa a registrar:", parent=root)
    if not placa:
        return

    # Crear la ventana principal de la interfaz
    ventana = tk.Toplevel(root)
    ventana.title("Registro de Nuevo Vehículo")
    
    tk.Label(ventana, text=f"Placa a registrar: {placa.upper()}", font=("Arial", 14)).pack(pady=10)
    
    tk.Label(ventana, text="Nombre del dueño:").pack()
    entry_nombre = tk.Entry(ventana, width=30)
    entry_nombre.pack()
    
    # ... (y así para los otros campos: marca, modelo, color) ...
    tk.Label(ventana, text="Marca:").pack()
    entry_marca = tk.Entry(ventana, width=30)
    entry_marca.pack()

    tk.Label(ventana, text="Modelo:").pack()
    entry_modelo = tk.Entry(ventana, width=30)
    entry_modelo.pack()
    
    tk.Label(ventana, text="Color:").pack()
    entry_color = tk.Entry(ventana, width=30)
    entry_color.pack()

    def on_registrar():
        if registrar_vehiculo(conn, placa.upper(), entry_nombre.get(), entry_marca.get(), entry_modelo.get(), entry_color.get()):
            ventana.destroy()

    tk.Button(ventana, text="Registrar Vehículo", command=on_registrar).pack(pady=20)


if __name__ == "__main__":
    conn = conectar_sql_server()
    if conn:
        root = tk.Tk()
        root.withdraw() # Ocultar la ventana raíz principal
        main()
        conn.close()
    else:
        print("No se pudo conectar a la base de datos.")