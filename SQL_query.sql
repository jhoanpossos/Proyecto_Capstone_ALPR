CREATE TABLE PlacasDetectadas (
    ID INT IDENTITY(1,1) PRIMARY KEY, -- Identificador �nico incremental
    Placa NVARCHAR(50) NOT NULL,      -- Texto de la placa detectada
    Fecha DATE NOT NULL DEFAULT GETDATE(), -- Fecha del registro (por defecto, la fecha actual)
    Hora TIME NOT NULL DEFAULT CONVERT(TIME, GETDATE()), -- Hora del registro (por defecto, la hora actual)
    TipoEntrada NVARCHAR(50) NOT NULL DEFAULT 'Entrada' -- Tipo de registro (por defecto, 'Entrada')
);

SELECT * FROM PlacasDetectadas;


CREATE TABLE VehiculosRegistrados (
    Placa NVARCHAR(50) PRIMARY KEY, -- Placa como clave primaria
    NombreCompleto NVARCHAR(100) NOT NULL, -- Nombre del due�o
    Marca NVARCHAR(50) NOT NULL, -- Marca del auto
    Modelo NVARCHAR(50) NOT NULL, -- Modelo del auto
    Color NVARCHAR(50) NOT NULL, -- Color del auto
    Fecha DATE NOT NULL DEFAULT GETDATE(), -- Fecha del registro (por defecto, la fecha actual)
    Hora TIME NOT NULL DEFAULT CONVERT(TIME, GETDATE()), -- Hora del registro (por defecto, la hora actual)
);