// Arduino bibliothek einbinden, damit so Funktionen wie pinMode() oder digitalWrite() funktionieren
#include <Arduino.h>
// WLAN Bibliotheken einbinden - aktiviert WLAN-Funktionen damit der ESP32 ein WLAN Access Point erstellen kann
#include <WiFi.h>
// Webserver Bibliothek einbinden - damit er HTTP-Anfragen empfangen kann und URLs wie /start, /status und so verarbeitn kann
#include <WebServer.h>

// WLAN Zugangsdaten
const char* ssid     = "Reaktionstest_ESP32";         // Name des WLANs
const char* password = "reaktion1234";               // Passwort des WLANs

WebServer server(80);  // Webserver auf Port 80

String resultsJson = "[]";  // Variable um die Ergebnisse im JSON-Format zu speichern

// Liste aller 7 LED-Pins
const int LED_PINS[7] = {22, 5, 17, 16, 4, 2, 15};
// Liste aller 7 Button-Pins
const int BTN_PINS[7] = {32, 33, 25, 26, 27, 27, 23};

//const int BTN_PINS[7] = {32, 12, 27, 26, 25, 33, 35};

// Zeitpunkte speichern wann LED eingeschaltet wurde
// speichert für jede LED den Startzeitpunkt wann sie eingeschalten wurde
unsigned long ledStartTime[7] = {0,0,0,0,0,0,0};


// Status-Array: true = LED an, false = LED aus
// merkt sich ob sie an oder aus ist
bool ledStatus[7] = {false, false, false, false, false, false, false};

bool testRunning = false;   // merkt ob Test gerade läuft oder nicht
unsigned long testStartTime = 0;         // Zeitpunkt wann Test gestartet wurde
unsigned long TEST_DURATION = 120000;  // Standardwert, wird von PC dann überschrieben

// neue Variable für die Fehlererkennung
int errorCount = 0;   // Fehler: Button gedrückt obwohl LED aus

void handleStart();
void handleStop();
void handleStatus();
void handleResults();

// vor echtem start des tests amchen die leds ein startsignal
void visualCountdown() {
    // 3x kurz blinken:
    for (int i = 0; i < 3; i++) {
        for (int l = 0; l < 7; l++) {
            digitalWrite(LED_PINS[l], HIGH);
        }
        delay(200);  // kurz an

        for (int l = 0; l < 7; l++) {
            digitalWrite(LED_PINS[l], LOW);
        }
        delay(300);  // kurze Pause
    }

    // 1x langes Leuchten
    for (int l = 0; l < 7; l++) {
        digitalWrite(LED_PINS[l], HIGH);
    }
    delay(800);  // lang an

    // alles aus
    for (int l = 0; l < 7; l++) {
        digitalWrite(LED_PINS[l], LOW);
    }

    delay(300); // kleine Pause vor Teststart
}

// am ende vom test blinken die leds kurz 2mal damit man weiß ok der test ist vorbei
void testFinishedBlink() {
    for (int i = 0; i < 2; i++) {   // 2x blinken
        for (int l = 0; l < 7; l++) {
            digitalWrite(LED_PINS[l], HIGH);
        }
        delay(250);

        for (int l = 0; l < 7; l++) {
            digitalWrite(LED_PINS[l], LOW);
        }
        delay(250);
    }
}


// wird einmal bei einschalten von ESP32 ausgeführt
void setup() {
    // Alle Pins als Ausgang setzen
    for (int i = 0; i < 7; i++) {       // Schleife über alle 7 LEDs und Buttons
        pinMode(LED_PINS[i], OUTPUT);   // setzt jeden LED-Pin auf Ausgang, damit man ihn EIN/AUS schalten können
        digitalWrite(LED_PINS[i], LOW);     // stellt sicher dass alle LEDs aussind

        pinMode(BTN_PINS[i], INPUT_PULLUP);         // setzt jeden Button-Pin auf Eingang mit internen Pull-Up; ein gedrückter Button ist LOW
    }

    // starte die serielle Verbindung zum PC/Streamlit
    Serial.begin(115200); // oder 9600, je nach Einstellung
    // initialisere den Zufallszahlgenerator, damit die lEDs in zufälliger Reihenfolge leuchten
    randomSeed(analogRead(0)); // Zufall initialisieren

    // definieren dass der ESP32 sein eigenes WLan erzeugt
    WiFi.softAP(ssid, password);  // Starte das Access Point mit SSID und Passwor
    Serial.println("WLAN Access Point gestartet");
    Serial.print("IP Adresse: ");
    Serial.println(WiFi.softAPIP());  // IP-Adresse des Access Points ausgeben

    server.on("/start", handleStart);  // Test starten
    server.on("/stop", handleStop);   // Test stoppen
    server.on("/status", handleStatus);   // Status und fehler zurück geben
    server.on("/results", handleResults);

    server.begin();  // abhier nimmt er Anfragen an
    Serial.println("HTTP Server gestartet");


}

// HTTP-Endpunkt zum Starten des Tests
void handleStart() {
    // streamlit sendet z.B /start?duration=120000 und ESP32 liest dann die Dauer stezt den Teststart und die Fehler zurück
    if (server.hasArg("duration")) {
        TEST_DURATION = server.arg("duration").toInt();
    }

    testRunning = false;
    resultsJson = "[]";   // alte Ergebnisse löschen
    errorCount = 0;

    visualCountdown();  // Countdown anzeigen

    testRunning = true;
    testStartTime = millis();  // Zeitpunkt merken wann Test gestartet wurde

    // Endpoint - Rückmeldung dass der Test gestartet wurde in json format damit das einheitlich ist 
    // ein Endpoint ist eine feste Adresse (URL) auf Gerät/Server - darüber können bestimmte Aktionen ausgeführt werden oder Daten abefragt
    // ist also wie der definiterte Zugangspunkt an dem eine Anfrage ankommt
    // der ESP hat 3 endpoints: /start; /stop; /status
    server.send(200, "application/json", "{\"status\":\"started\"}");
}

void handleStop() {
    // Test stoppen 
    // streamlit sendet z.B /stop und ESP32 macht dann den Test aus
    testRunning = false;
    server.send(200, "application/json", "{\"status\":\"stopped\"}");
}

void handleStatus() {
    // Status zurückgeben ob Test läuft und wieviele Fehler
    String json = "{";
    json += "\"running\":" + String(testRunning ? "true" : "false") + ",";
    json += "\"errors\":" + String(errorCount);
    json += "}";

    server.send(200, "application/json", json);
}

void handleResults() {
    String json = resultsJson;

    // Array sauber schließen
    if (json.startsWith("[") && !json.endsWith("]")) {
        json += "]";
    }

    server.send(200, "application/json", json);
}


void loop() {
    // Webserver Anfragen bearbeiten - ohne das reagiert der ESP32 nicht auf HTTP-Anfragen
    // prüft ständig ob eine Anfrage kam, welcher URL und ruft dann die passende Funktion auf
    server.handleClient();

    // wenn Test läuft und die Zeit vorbei ist, Test beenden
    if (testRunning && millis() - testStartTime > TEST_DURATION) {
        testRunning = false;  // Test beendet

        // alle LEDs aus & Status zurücksetzen
        for (int i = 0; i < 7; i++) {
            ledStatus[i] = false;
            digitalWrite(LED_PINS[i], LOW);
        }

        delay(100);
        testFinishedBlink();  // kurz das visuelle signal das der test aus ist

        Serial.println("TEST_FINISHED");
        Serial.print("Gesamtfehler: ");
        Serial.println(errorCount);
    }

    // wenn test läuft
    if (testRunning) {
        
        // Überprüfen, ob ein Button gedrückt wurde, wenn einer gedrückt wurde, entsprechende LED ausschalten
        for (int i = 0; i < 7; i++) {  // für alle 7 Buzttons prüfen
            
            static unsigned long lastPress[7] = {0};

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
                        // JSON-Eintrag erzeugen
                        if (resultsJson == "[]") {
                            resultsJson = "[";
                        } else {
                            resultsJson += ",";
                        }

                        resultsJson += "{";
                        resultsJson += "\"led\":" + String(i) + ",";
                        resultsJson += "\"reaction_ms\":" + String(duration);
                        resultsJson += "}";

                        // LED ausschalten
                        ledStatus[i] = false;
                        digitalWrite(LED_PINS[i], LOW);

                    }
                }
            }

        }

        // Neue LED zufällig einschalten (nur aus LEDs)
        int offCount = 0;  // offCount ist Zähler der ausgeschalteten LEDs
        for (int i = 0; i < 7; i++) if (!ledStatus[i]) offCount++;  // wenn die LED aus ist, Zähler erhöhen (! = NOT)

        if (offCount > 6) { // nur einschalten, wenn alle LEDs aus sind
            int r;  // Variable für zufälligen Index
            // schleife soll ausgeführt werden solang eine LED leuchtet
            // wir wollen eine ausgeschaltete LED auswählen, solange wiederholen wie sie an ist
            do {
                r = random(0, 7);  // erstellt Zufallszahl zw 0 und 6
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