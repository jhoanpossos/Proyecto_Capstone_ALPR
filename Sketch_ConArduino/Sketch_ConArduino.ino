#include <Servo.h>

Servo myServo;
#define SERVO_PIN 9
#define FLASH_PIN 10 // Un pin PWM para el LED/Flash

void setup() {
  myServo.attach(SERVO_PIN);
  pinMode(FLASH_PIN, OUTPUT);
  Serial.begin(9600);
  Serial.println("Arduino listo.");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    // Lógica para abrir la barrera (la que ya tienes)
    if (command == "OPEN") {
      Serial.println("Comando OPEN recibido. Abriendo barrera.");
      myServo.write(90); 
      delay(10000);      
      myServo.write(0);  
      Serial.println("Barrera cerrada.");
    }
    
    // Lógica NUEVA para controlar el flash
    if (command.startsWith("SET_FLASH:")) {
      // Extrae el valor numérico después de "SET_FLASH:"
      int power = command.substring(10).toInt();
      // Aplica el valor al pin del flash (0-255)
      analogWrite(FLASH_PIN, power);
      Serial.print("Potencia de flash ajustada a: ");
      Serial.println(power);
    }
  }
}