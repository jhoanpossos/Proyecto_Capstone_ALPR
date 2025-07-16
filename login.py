import tkinter as tk
from tkinter import messagebox
from database_sql import conectar_sql_server
from dashboard import mostrar_dashboard

# Funcion que se ejecuta para mostrar la pantalla de inicio de sesion
# Para Valentina, verificar que esté adaptado correctamente a la base de datos en Azure
def mostrar_login(root):
    login_win = tk.Toplevel()
    login_win.title("Inicio de sesión")
    login_win.geometry("300x200")

    tk.Label(login_win, text="Usuario:").pack(pady=5)
    entry_user = tk.Entry(login_win)
    entry_user.pack()

    tk.Label(login_win, text="Contraseña:").pack(pady=5)
    entry_pass = tk.Entry(login_win, show="*")
    entry_pass.pack()

    # Funcion que valida las credenciales ingresadas para confirmar el acceso al sistema
    def autenticar():
        usuario = entry_user.get()
        contraseña = entry_pass.get()

        if not usuario or not contraseña:
            messagebox.showerror("Error", "Completa todos los campos.")
            return

        try:
            conn = conectar_sql_server()
            cursor = conn.cursor()
            query = "SELECT * FROM Usuarios WHERE Usuario = ? AND Contrasena = ?"
            cursor.execute(query, (usuario, contraseña))
            if cursor.fetchone():
                login_win.destroy()
                mostrar_dashboard(root, conn)
            else:
                messagebox.showerror("Acceso denegado", "Credenciales incorrectas.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {e}")

    tk.Button(login_win, text="Ingresar", command=autenticar).pack(pady=15)
