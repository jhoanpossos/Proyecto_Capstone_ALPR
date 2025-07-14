CREATE TABLE VehiculosRegistrados (
    Placa NVARCHAR(50) PRIMARY KEY, -- Placa como clave primaria
    NombreCompleto NVARCHAR(100) NOT NULL, -- Nombre del dueño
    Marca NVARCHAR(50) NOT NULL, -- Marca del auto
    Modelo NVARCHAR(50) NOT NULL, -- Modelo del auto
    Color NVARCHAR(50) NOT NULL -- Color del auto
    Fecha DATE NOT NULL DEFAULT GETDATE(), -- Fecha del registro (por defecto, la fecha actual)
    Hora TIME NOT NULL DEFAULT CONVERT(TIME, GETDATE()), -- Hora del registro (por defecto, la hora actual)
);

INSERT INTO VehiculosRegistrados (Placa, NombreCompleto, Marca, Modelo, Color)
VALUES 
('CVY-000', 'Alejandro Mora', 'Honda', 'Civiv', 'Azul'),
('XYZ456', 'Ana Gómez', 'Honda', 'Civic', 'Negro'),
('LMN789', 'Carlos López', 'Ford', 'Escape', 'Rojo');