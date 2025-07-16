import tkinter as tk
from tkinter import messagebox

# Funcion que muestra los campos requeridos para almacenar informacion
def mostrar_interfaz_registro(conn, placa, modo="agregar"):
    ventana = tk.Toplevel()
    ventana.title(f"{'Editar' if modo == 'editar' else 'Registrar'} Vehículo")
    ventana.geometry("400x300")

    tk.Label(ventana, text=f"Placa: {placa}", font=("Arial", 14)).pack(pady=10)

    tk.Label(ventana, text="Nombre del dueño:").pack()
    entry_nombre = tk.Entry(ventana, width=30)
    entry_nombre.pack()

    tk.Label(ventana, text="Marca del vehículo:").pack()
    entry_marca = tk.Entry(ventana, width=30)
    entry_marca.pack()

    tk.Label(ventana, text="Modelo del vehículo:").pack()
    entry_modelo = tk.Entry(ventana, width=30)
    entry_modelo.pack()

    tk.Label(ventana, text="Color del vehículo:").pack()
    entry_color = tk.Entry(ventana, width=30)
    entry_color.pack()

    # Valida si se quiere modiicar informacion registrada en la base de datos
    if modo == "editar":
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT NombreCompleto, Marca, Modelo, Color FROM VehiculosRegistrados WHERE Placa = ?", placa)
            resultado = cursor.fetchone()
            if resultado:
                entry_nombre.insert(0, resultado[0])
                entry_marca.insert(0, resultado[1])
                entry_modelo.insert(0, resultado[2])
                entry_color.insert(0, resultado[3])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la información: {e}")

    # Guarda la informacion ingresada por el usuario
    def guardar():
        nombre = entry_nombre.get()
        marca = entry_marca.get()
        modelo = entry_modelo.get()
        color = entry_color.get()

        if not all([nombre, marca, modelo, color]):
            messagebox.showerror("Error", "Completa todos los campos.")
            return

        try:
            cursor = conn.cursor()
            if modo == "editar":
                cursor.execute("""UPDATE VehiculosRegistrados 
                                  SET NombreCompleto = ?, Marca = ?, Modelo = ?, Color = ?
                                  WHERE Placa = ?""", (nombre, marca, modelo, color, placa))
            else:
                cursor.execute("""INSERT INTO VehiculosRegistrados 
                                  (Placa, NombreCompleto, Marca, Modelo, Color)
                                  VALUES (?, ?, ?, ?, ?)""", (placa, nombre, marca, modelo, color))
            conn.commit()
            messagebox.showinfo("Éxito", f"Vehículo {'editado' if modo == 'editar' else 'registrado'} correctamente.")
            ventana.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    tk.Button(ventana, text="Guardar", command=guardar).pack(pady=20)