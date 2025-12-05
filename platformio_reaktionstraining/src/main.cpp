#include <Arduino.h>

// Liste aller 9 LED-Pins
const int LED_PINS[9] = {15, 2, 4, 18, 19, 21, 22, 13, 14};
const int BTN_PINS[9] = {32, 32, 32, 32, 32, 32, 32, 32, 32};

// Zeitpunkte speichern wann LED eingeschaltet wurde
unsigned long ledStartTime[9] = {0,0,0,0,0,0,0,0,0};

// const int BTN_PINS[9] = {32, 12, 27, 26, 25, 33, 35, 34, 23};

// Status-Array: true = LED an, false = LED aus
bool ledStatus[9] = {false, false, false, false, false, false, false, false, false};

void setup() {
    // Alle Pins als Ausgang setzen
    for (int i = 0; i < 9; i++) {
        pinMode(LED_PINS[i], OUTPUT);
        digitalWrite(LED_PINS[i], LOW);

        pinMode(BTN_PINS[i], INPUT_PULLUP);
    }

    Serial.begin(115200); // oder 9600, je nach Einstellung
    randomSeed(analogRead(0)); // Zufall initialisieren
}

void loop() {
    // Überprüfen, ob ein Button gedrückt wurde, wenn einer gedrückt wurde, entsprechende LED ausschalten
    for (int i = 0; i < 9; i++) {
        if (digitalRead(BTN_PINS[i]) == LOW && ledStatus[i]) { // Button gedrückt (LOW) und LED an (True)
            ledStatus[i] = false;            // LED ausschalten (auf false setzten)
            digitalWrite(LED_PINS[i], LOW);  // auf LOW setzen 
            // Zeitdifferenz von wann LED angeschalten wurde bis sie ausgeschaltet wrude
            unsigned long duration = millis() - ledStartTime[i]; // Zeitdifferenz berechnen
            Serial.print("LED ");
            Serial.print(i);
            Serial.print(" ausgeschaltet! Dauer: ");
            Serial.print(duration);
            Serial.println(" ms");
            delay(50); // Entprellen
        }
    }

    // Neue LED zufällig einschalten (nur aus LEDs)
    int offCount = 0;  // offCount ist Zähler der ausgeschalteten LEDs
    for (int i = 0; i < 9; i++) if (!ledStatus[i]) offCount++;  // wenn die LED aus ist, Zähler erhöhen (! = NOT)

    if (offCount > 8) { // nur einschalten, wenn alle LEDs aus sind
        int r;  // Variable für zufälligen Index
        // schleife soll ausgeführt werden solang eine LED leuchtet
        // wir wollen eine ausgeschaltete LED auswählen, solange wiederholen wie sie an ist
        do {
            r = random(0, 9);  // erstellt Zufallszahl zw 0 und 8
        } while (ledStatus[r]);
        
        // random(min, max) zeit in ms
        // min <= Zeit < max, daher max um 1 erhöhen
        long delayTime = random(500, 2001); // 0,5 bis 2 Sekunden warten
        delay(delayTime);
        // wenn die delayTime vorbei ist dann soll die zufällig ausgewählte LED eingeschaltet werden
        ledStatus[r] = true;           // LED Status auf wahr setzten
        digitalWrite(LED_PINS[r], HIGH); // LED einschalten
        ledStartTime[r] = millis(); // Startzeit merken wann LED eingeschaltet wurde


        Serial.print("LED ");
        Serial.print(r);
        Serial.print(" eingeschaltet nach ");
        Serial.print(delayTime);
        Serial.println(" ms");
    }

    delay(100); // kleine Pause für Stabilität
}