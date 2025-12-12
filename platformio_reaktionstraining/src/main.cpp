// Arduino bibliothek einbinden, damit so Funktionen wie pinMode() oder digitalWrite() funktionieren
#include <Arduino.h>

// Liste aller 9 LED-Pins
const int LED_PINS[9] = {15, 2, 4, 18, 19, 21, 22, 13, 14};
const int BTN_PINS[9] = {32, 32, 32, 32, 32, 32, 32, 32, 32};

// Zeitpunkte speichern wann LED eingeschaltet wurde
// speichert für jede LED den Startzeitpunkt wann sie eingeschalten wurde
unsigned long ledStartTime[9] = {0,0,0,0,0,0,0,0,0};

// const int BTN_PINS[9] = {32, 12, 27, 26, 25, 33, 35, 34, 23};

// Status-Array: true = LED an, false = LED aus
// merkt sich ob sie an oder aus ist
bool ledStatus[9] = {false, false, false, false, false, false, false, false, false};

bool testRunning = false;   // merkt ob Test gerade läuft oder nicht
unsigned long testStartTime = 0;         // Zeitpunkt wann Test gestartet wurde
unsigned long TEST_DURATION = 120000;  // Standardwert, wird von PC dann überschrieben

// neue Variable für die Fehlererkennung
int errorCount = 0;   // Fehler: Button gedrückt obwohl LED aus

// wird einmal bei einschalten von ESP32 ausgeführt
void setup() {
    // Alle Pins als Ausgang setzen
    for (int i = 0; i < 9; i++) {       // Schleife über alle 9 LEDs und Buttons
        pinMode(LED_PINS[i], OUTPUT);   // setzt jeden LED-Pin auf Ausgang, damit man ihn EIN/AUS schalten können
        digitalWrite(LED_PINS[i], LOW);     // stellt sicher dass alle LEDs aussind

        pinMode(BTN_PINS[i], INPUT_PULLUP);         // setzt jeden Button-Pin auf Eingang mit internen Pull-Up; ein gedrückter Button ist LOW
    }
    // starte die serielle Verbindung zum PC/Streamlit
    Serial.begin(115200); // oder 9600, je nach Einstellung
    // initialisere den Zufallszahlgenerator, damit die lEDs in zufälliger Reihenfolge leuchten
    randomSeed(analogRead(0)); // Zufall initialisieren
}

void loop() {
    // seriellen Input lesen
    // prüft ob Daten vom PC angekommen sind
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');  // liest eine Zeile als String ein
        // wennn die Nachricht vom PC mit Start beginnt, dann mit TEST_STARTED antworten und eine Flag setzten 
        if (cmd.startsWith("START")) {
            TEST_DURATION = cmd.substring(6).toInt(); // Zeit auslesen, Zahl nach "START "
            testRunning = true;         // Test läuft jetzt
            // Zeitparameter vom PC übernehmen
            testStartTime = millis();
            errorCount = 0;     // Fehlerzähler zurücksetzen
            Serial.println("TEST_STARTED");     //Rückmeldung an PC
        }


        // wenn PC "STOP" gesendet hat dann mit TEST_STOPPED antworten
        if (cmd == "STOP") {
            testRunning = false;  //Test stoppen
            Serial.println("TEST_STOPPED");
            Serial.print("Gesamtfehler: ");  // Fehleranzeige
            Serial.println(errorCount);

        }
    }
    // wenn Test läuft und die Zeit vorbei ist, Test beenden
    if (testRunning && millis() - testStartTime > TEST_DURATION) {
        testRunning = false;
        Serial.println("TEST_FINISHED");
        Serial.print("Gesamtfehler: ");  // error anzeige
        Serial.println(errorCount);

    }

    // wenn test läuft
    if (testRunning) {
        
        // Überprüfen, ob ein Button gedrückt wurde, wenn einer gedrückt wurde, entsprechende LED ausschalten
        for (int i = 0; i < 9; i++) {  // für alle 9 Buzttons prüfen
            
            static unsigned long lastPress[9] = {0};

            if (digitalRead(BTN_PINS[i]) == LOW) {
                unsigned long now = millis();
                if (now - lastPress[i] > 80) {
                    lastPress[i] = now;

                    if (!ledStatus[i]) {  // Fehler: Button gedrückt, aber die LED war aus
                        errorCount++;
                        Serial.print("Gesamtfehler: ");
                        Serial.println(errorCount);
                    }
                    
                    else { // LED war an, alles ok
                        ledStatus[i] = false;
                        digitalWrite(LED_PINS[i], LOW);

                        unsigned long duration = now - ledStartTime[i];
                        Serial.print("LED ");
                        Serial.print(i);
                        Serial.print(" ausgeschaltet! Dauer: ");
                        Serial.print(duration);
                        Serial.println(" ms");
                    }
                }
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
} 