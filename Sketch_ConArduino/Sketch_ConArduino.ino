#include <Servo.h>

// Crear un objeto Servo
Servo myServo;

// Pin al que está conectado el servo
#define SERVO_PIN 9

void setup() {
  // Inicializar el servo en el pin especificado
  myServo.attach(SERVO_PIN);

  // Configurar comunicación serial
  Serial.begin(9600);
  Serial.println("Arduino listo para recibir comandos.");
}

void loop() {
  // Verificar si hay datos disponibles en el puerto serial
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Leer el comando enviado por Python

    // Comando para abrir la barrera
    if (command == "OPEN") {
      Serial.println("Barrera levantada.");
      myServo.write(90); // Levantar la barrera (90 grados)
      delay(10000);      // Esperar 10 segundos
      myServo.write(0);  // Bajar la barrera (0 grados)
      Serial.println("Barrera bajada.");
    }
  }
}


