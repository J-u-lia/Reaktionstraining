// Arduino bibliothek einbinden, damit so Funktionen wie pinMode() oder digitalWrite() funktionieren
#include <Arduino.h>
// WLAN Bibliotheken einbinden - aktiviert WLAN-Funktionen damit der ESP32 ein WLAN Access Point erstellen kann
#include <WiFi.h>
// Webserver Bibliothek einbinden - damit er HTTP-Anfragen empfangen kann und URLs wie /start, /status und so verarbeitn kann
#include <WebServer.h>

// WLAN Zugangsdaten
// über const char* wird eine Konstante Zeichenkette definiert
const char* ssid     = "Reaktionstest_ESP32";         // Name des WLANs
const char* password = "reaktion1234";               // Passwort des WLANs

WebServer server(80);  // Webserver auf Port 80

String resultsJson = "[]";  // Variable um die Ergebnisse im JSON-Format zu speichern

// Liste aller 7 LED-Pins
const int LED_PINS[7] = {15, 2, 4, 16, 17, 5, 19};
// Liste aller 7 Button-Pins
const int BTN_PINS[7] = {32, 33, 25, 26, 22, 23, 23};

//const int BTN_PINS[7] = {32, 12, 27, 26, 25, 33, 35};

// Zeitpunkte speichern wann LED eingeschaltet wurde
// speichert für jede LED den Startzeitpunkt wann sie eingeschalten wurde
unsigned long ledStartTime[7] = {0,0,0,0,0,0,0};


// unsigned long: 4Byte speicher und einen wertebreich von 0 bis 4294967295
// weil long heißt 4byte von -2147483648 bis +2.147483647 
// und unsigned heißt keine negativeb Zahlen dann addiert man es einf ins positive Bereich dazu
// unsigned ist praktischm, da z.b die zeit millis() immer pos ist

// Status-Array: true = LED an, false = LED aus
// merkt sich ob sie an oder aus ist
bool ledStatus[7] = {false, false, false, false, false, false, false};

bool testRunning = false;   // merkt ob Test gerade läuft oder nicht
unsigned long testStartTime = 0;         // Zeitpunkt wann Test gestartet wurde
unsigned long TEST_DURATION = 120000;  // Standardwert, wird von PC dann überschrieben

// neue globale Variable für die Fehlererkennung
int errorCount = 0;   // Fehler: Button gedrückt obwohl LED aus/Fehlstart bei F1

// Aufzählung (enum), erlaubt lesbare Zustände für Spielmodus
enum GameMode {
    GAME_NONE,
    GAME_CLASSIC,
    GAME_F1START
};

// speichert aktuell aktiven Spielmodus
GameMode currentGame = GAME_NONE;

// -------- F1 START VARIABLEN ----------

// Button-Indizes (unten links / unten rechts)
const int SHIFT_BTN = 22;  // Schaltwippen so quasi
const int F1_LED_PINS[5] = {15, 2, 4, 16, 17};

// LED-Indizes (oben + mitte)
const int F1_LED_COUNT = 5; // 2 oben + 3 mitte

// State-machine - jeder Zustand eine Phase vom F1-Start Spiel
enum F1State {
    F1_WAIT_START,
    F1_LIGHT_SEQUENCE,
    F1_LIGHTS_ON,
    F1_LIGHTS_OUT,
    F1_REACTION_DONE,
    F1_FALSE_START
};

F1State f1State = F1_WAIT_START;

unsigned long f1StepTime = 0;  // Timing der LED-Schritte
unsigned long f1LightsOutTime = 0;  // Zeitpunkt wann Lichter ausehen
int f1LedIndex = 0;

// einmal alle setup Funktionen aufrufen bevor der eigentliche Code im loop() startet
#// Vorwärtsdeklarationen der HTTP-Handler-Funktionen
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
        pinMode(SHIFT_BTN, INPUT_PULLUP);          // Schaltwippe als Eingang mit Pull-Up
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

    server.on("/start", handleStart);  // Test starten; liest Spielmodus, Dauer und setzt alles zurück, startet Countdown und Test
    server.on("/stop", handleStop);   // Test stoppen; setzt testRunning auf false
    server.on("/status", handleStatus);   // Status und fehler zurück geben
    server.on("/results", handleResults); // gibt gesammelte Ergebnisse zurück

    server.begin();  // abhier nimmt er Anfragen an
    Serial.println("HTTP Server gestartet");


}

// HTTP-Endpunkt zum Starten des Tests
void handleStart() {
    // zuerst den Spielmodus aus dem URL rauslesen
    // durch server.hasArg schaut man ob die aktuelle HTTP Anfrage einen Parameter mit dem Namen game hat
    if (server.hasArg("game")) {
        // holt den Wert von game und übergibt es der Variable g (g ist jetzt entweder classic oder f1start)
        String g = server.arg("game");
        if (g == "classic") currentGame = GAME_CLASSIC;
        else if (g == "f1start") currentGame = GAME_F1START;
        // Standardmodus Classic
        else currentGame = GAME_CLASSIC;
    }
    else {
        currentGame = GAME_CLASSIC;
    }

    // streamlit sendet z.B /start?duration=120000 und ESP32 liest dann die Dauer stezt den Teststart und die Fehler zurück
    // es gibt nur eine Testdauer wenn das klassische Reaktionsspiel gespielt wird
    if (server.hasArg("duration") && currentGame == GAME_CLASSIC) {
        TEST_DURATION = server.arg("duration").toInt();
    }

    testRunning = false;
    resultsJson = "[]";   // alte Ergebnisse löschen
    errorCount = 0;

    // LEDs aus - damit kann sichergestellt werden dass vor dem Countdown alle aus sind
    for (int i = 0; i < 7; i++) {
        digitalWrite(LED_PINS[i], LOW);
        ledStatus[i] = false;
    }

    visualCountdown();  // Countdown anzeigen

    // F1-Reset
    f1State = F1_WAIT_START;

    testRunning = true;
    testStartTime = millis();  // Zeitpunkt merken wann Test gestartet wurde

    // Endpoint - Rückmeldung dass der Test gestartet wurde in json format damit das einheitlich ist 
    // ein Endpoint ist eine feste Adresse (URL) auf Gerät/Server - darüber können bestimmte Aktionen ausgeführt werden oder Daten abefragt
    // ist also wie der definiterte Zugangspunkt an dem eine Anfrage ankommt
    // der ESP hat 4 endpoints: /start; /stop; /status; /game;
    server.send(200, "application/json", "{\"status\":\"started\", \"game\":\"" + String(currentGame) + "\"}");
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

    // Array sauber schließen, falss mans vergessen hat wirds da gemacht
    if (json.startsWith("[") && !json.endsWith("]")) {
        json += "]";
    }

    server.send(200, "application/json", json);
}

// Funktion die aufgerufen wird wenn man das klassische Reaktionsspiel speilen will
void runClassicGame() {
    // Überprüfen, ob ein Button gedrückt wurde, wenn einer gedrückt wurde, entsprechende LED ausschalten
    for (int i = 0; i < 7; i++) {  // für alle 7 Buzttons prüfen
        
        static unsigned long lastPress[7] = {0};
        // wenn ein Button gepressd wurde 
        if (digitalRead(BTN_PINS[i]) == LOW) {
            // Startpunkt merken um Entprellung zu machen
            unsigned long now = millis();
            // Entprellung: nur wenn seit dem letzten Drücken mehr als 80ms vergangen sind
            if (now - lastPress[i] > 80) {
                lastPress[i] = now;
                // schauen ob die lEd anwar oder nicht, wenn nicht dann fehler erhöhen
                if (!ledStatus[i]) {  // Fehler: Button gedrückt, aber die LED war aus
                    errorCount++;
                    Serial.print("Gesamtfehler: ");
                    Serial.println(errorCount);
                }
                
                else { // LED war an, alles ok
                    ledStatus[i] = false;
                    digitalWrite(LED_PINS[i], LOW);
                    // falss sie an war wird Reakionszeit berechnet
                    unsigned long duration = now - ledStartTime[i];
                    // JSON-Eintrag erzeugen
                    if (resultsJson == "[]") {
                        resultsJson = "[";
                    }
                    else {
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


// Funktion die aufgerufen wird wenn man das F1-Start-Simulator spielen will
void runF1StartGame() {
    // einlesen von der Schaltwippe ob sie gedrückt ist also Low heißt gedrückt 
    // lesbarer wie ständig digitalRead(..)
    bool shiftPressed = digitalRead(SHIFT_BTN) == LOW; // Schaltwippen
    // je nachdem welcher aktuelle Zustand wird genau einer der cases ausgeführt
    switch (f1State) {
        // aktuelle Zustand = F1_WAIT_START
        // Warten auf Start - kein Button gedrückt
        case F1_WAIT_START:
        // mit der ersten LED beginnen von den Pins her, damit er nicht einfahc iwo startet
            f1LedIndex = 0;
            // die Startzeit merken
            f1StepTime = millis();
            // und dann in den nächsten Zustand wechseln
            f1State = F1_LIGHT_SEQUENCE;
            break;
            // aktuelle Zustand = F1_LIGHT_SEQUENCE
        // LEDs gehen nacheinander an
        case F1_LIGHT_SEQUENCE:
        // schauen ob die Schaltwippe gedrückt wurde -->
            // Fehlstart: Kupplung zu früh losgelassen
            if (shiftPressed) {
                // in Zustand Fehlstart wechseln
                f1State = F1_FALSE_START;
                break;
            }
            // Zeit prüfen ob 500ms seit letztem Schritt vergangen sind
            if (millis() - f1StepTime > 500) {
                // nächste LED einschalten, den index um eins erhöhen und Zeitpunkt merken
                digitalWrite(F1_LED_PINS[f1LedIndex], HIGH);
                f1LedIndex++;
                f1StepTime = millis();
                // wenn alle 5 LEDs ansind dann eine random zeit wartn bis sie ausgehen also man addiert eine random zahl auf millis() also der ktuellen Zeit drauf
                if (f1LedIndex >= F1_LED_COUNT) {
                    f1LightsOutTime = millis() + random(500, 3000); // zufällige Wartezeit bis Lichter ausgehen
                    // in neuen State
                    f1State = F1_LIGHTS_ON;
                }
            }
            break;
        // aktuelle Zustand = F1_LIGHTS_ON
        // Alle LEDs an - warten bis sie aus gehen
        case F1_LIGHTS_ON:
            // Kupplung loslassen = Reaktion
            // wenn man sie aber jetzt loslast ist Fehlstart
            if (shiftPressed) {
                f1State = F1_FALSE_START;
                break;
            }
            // wnen man die Zeit erreicht hat di man sich vorher gespeichert hat dann alle Lichter aus 
            if (millis() >= f1LightsOutTime) {
                // Alle Lichter aus
                for (int i = 0; i < F1_LED_COUNT; i++) {
                    digitalWrite(F1_LED_PINS[i], LOW);
                }
                f1LightsOutTime = millis(); // Zeitpunkt merken wann Lichter ausgingen
                // Zustandswehcsel
                f1State = F1_LIGHTS_OUT;
            }
            break;
        // aktuelle Zustand = F1_LIGHTS_OUT
        case F1_LIGHTS_OUT:
        // jetzt den buttn drücken
            if (shiftPressed) {
                // reaktionszeit berechnen und in results speichern 
                unsigned long reaction = millis() - f1LightsOutTime;

                resultsJson = "[";
                resultsJson += "{";
                resultsJson += "\"reaction_ms\":" + String(reaction);
                resultsJson += "}";
                resultsJson += "]";
                // test soll sofoert aufhören und in den nächsten Zutand gehen
                testRunning = false;
                f1State = F1_REACTION_DONE;

            }
            break;
        // aktuelle Zustand = F1_FALSE_START
        case F1_FALSE_START:
        // errorcoutn erhöhen und den dann auch speichern und sobalt man falösch gedrückt hat soll der Test stoppen
            errorCount++;
            resultsJson = "[{\"error\":\"false_start\"}]";
            testRunning = false;
            break;
        // aktuelle Zustand = F1_WREACTION_DONE
        case F1_REACTION_DONE:
        // passiver Zustand
            // Warte auf Testende
            break;

    }
}

void loop() {
    // Webserver Anfragen bearbeiten - ohne das reagiert der ESP32 nicht auf HTTP-Anfragen
    // prüft ständig ob eine Anfrage kam, welcher URL und ruft dann die passende Funktion auf
    server.handleClient();
    // wenn das aktuelle Spiel was ausgewähtl wurde das F1start ist dann soll die Funktion aufgerufen werden und der Tets läuft
    if (currentGame == GAME_F1START) {
        if (testRunning) {
            runF1StartGame();
        }
        return;  // wenn F1-Start und Test nicht läuft, nichts weiter tun außer wenn der test noch läuft die Funktion aufrufen
    }
    
    // wenn Test läuft und die Zeit vorbei ist und das aktuelle Spiel Classic ist, Test beenden
    // weil bei F1 Star gibt es keine  testdauer
    if (testRunning && currentGame == GAME_CLASSIC && millis() - testStartTime > TEST_DURATION) {
        testRunning = false;  // Test beendet

        // alle LEDs aus & Status zurücksetzen
        for (int i = 0; i < 7; i++) {
            ledStatus[i] = false;
            digitalWrite(LED_PINS[i], LOW);
        }

        delay(100);
        testFinishedBlink();  // kurz das visuelle Signal, dass der Test aus ist

        Serial.println("TEST_FINISHED");
        Serial.print("Gesamtfehler: ");
        Serial.println(errorCount);
    }

    // wenn Test läuft
    if (testRunning) {
        // schauen welches spiel gerade läuft, weil currentGame ist ja ein enum und da gibt es die zwei Spiele
        switch (currentGame) {
            // wenn Classic läut dann die Funktion aufrufen
            case GAME_CLASSIC:
                runClassicGame();
                break;
            // wenn F1Start läuft dann die andere
            case GAME_F1START:
                runF1StartGame();
                break;
            // falls es einen unerwarteten Wert gibt für den Modus dann gar nichts soll passieren
            default:
                break;
        }
    }
}