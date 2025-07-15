import tkinter as tk
from tkinter import messagebox
from registro import mostrar_interfaz_registro

# Funcion para mostrar la interfaz principal con las opciones para revisar y modificar los datos de las placas almacenadass
def mostrar_dashboard(root, conn):
    dashboard = tk.Toplevel()
    dashboard.title("Panel Principal")
    dashboard.geometry("500x400")

    # Mensaje que se muestra mientras se detecta una placa
    placa_var = tk.StringVar(value="Esperando detección...")

    tk.Label(dashboard, text="Placa detectada:", font=("Arial", 16)).pack(pady=10)
    tk.Label(dashboard, textvariable=placa_var, font=("Arial", 20, "bold")).pack(pady=10)

    # Funcion que se ejecuta cuando se edita la informacion de un vehiculo registrado
    def editar():
        placa = placa_var.get()
        if placa == "Esperando detección...":
            messagebox.showerror("Error", "Primero detecta una placa.")
            return
        mostrar_interfaz_registro(conn, placa, modo="editar")

    # Funcion que se ejecuta para eliminar un registro de la base de datos
    def eliminar():
        placa = placa_var.get()
        if placa == "Esperando detección...":
            messagebox.showerror("Error", "Primero detecta una placa.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM VehiculosRegistrados WHERE Placa = ?", placa)
            conn.commit()
            messagebox.showinfo("Éxito", f"Vehículo con placa '{placa}' eliminado.")
            placa_var.set("Esperando detección...")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")

    # Mostrar los botones para agregar, modificar o eliminar informacion en la base de datos de vehiculos
    tk.Button(dashboard, text="Agregar", command=lambda: mostrar_interfaz_registro(conn, placa_var.get(), modo="agregar")).pack(pady=5)
    tk.Button(dashboard, text="Editar", command=editar).pack(pady=5)
    tk.Button(dashboard, text="Eliminar", command=eliminar).pack(pady=5)