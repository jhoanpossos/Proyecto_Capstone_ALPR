# test_db.py
from database_sql import conectar_sql_server, verificar_placa_registrada

print("Intentando conectar a Azure SQL...")
conn = conectar_sql_server()

if conn:
    print("\\nPrueba de conexión exitosa.")
    # Intentamos buscar una placa de las que insertaste en el script SQL
    print("Buscando placa 'XYZ456'...")
    vehiculo = verificar_placa_registrada(conn, 'XYZ456')

    if vehiculo:
        print(f"✅ Éxito: Se encontró el vehículo: {vehiculo}")
    else:
        print("❌ Error: No se encontró el vehículo. Revisa si la tabla 'VehiculosRegistrados' se creó y pobló correctamente.")

    conn.close()
    print("\nConexión cerrada.")
else:
    print("\nFalló la conexión. Revisa la cadena de conexión en 'database_sql.py' y la configuración del firewall en Azure.")