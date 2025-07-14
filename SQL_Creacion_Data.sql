USE Registro_Placas; -- Selecciona la base de datos (asegúrate de que el nombre coincida)

CREATE TABLE PlacasDetectadas (
    ID INT IDENTITY(1,1) PRIMARY KEY, -- Identificador único incremental
    Placa NVARCHAR(50) NOT NULL,      -- Texto de la placa detectada
    Fecha DATE NOT NULL DEFAULT GETDATE(), -- Fecha del registro (por defecto, la fecha actual)
    Hora TIME NOT NULL DEFAULT CONVERT(TIME, GETDATE()), -- Hora del registro (por defecto, la hora actual)
    TipoEntrada NVARCHAR(50) NOT NULL DEFAULT 'Entrada' -- Tipo de registro (por defecto, 'Entrada')
);
