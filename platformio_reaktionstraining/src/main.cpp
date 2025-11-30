#include <Arduino.h>

#define LED_PIN 18   // Pin, an dem die LED angeschlossen ist

void setup() {
  pinMode(LED_PIN, OUTPUT);  // Pin als Ausgang setzen
}

void loop() {
  digitalWrite(LED_PIN, HIGH);  // LED einschalten
  delay(500);                   // 500 ms warten
  digitalWrite(LED_PIN, LOW);   // LED ausschalten
  delay(500);                   // 500 ms warten
}
