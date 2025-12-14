import requests # Bibliothek um HTTP-Anfragen zu senden (GET/POST) also so wie eine Art browser
                # um /start, /stop, /status auf dem ESP32 abzurufen
import time     # Zeitmessungen und Testdauer kontrollieren

# die IP-Adresse vom ESP in seinem eigenen WLAN
# der Laptop verbindet sich mit dem ESP32 Wlan und dann erreicht Streamlit den ESP übver diese Adresse
# das WiFi.softAP() nutzt immer standardmäßig diese IP:
ESP_IP = "192.168.4.1"

def run_reaction_test(duration_sec=120, mode="Standard"): #standardmäßig ine testdauer von 120 s also 2 min und der Testmodus auf Standard
    """
    Startet den Reaktionstest über WLAN
    und liest währenddessen Status & Fehler aus
    """
    # rechnet sek in ms um weil der /start endpoint die dauer in ms erwartet
    duration_ms = duration_sec * 1000

    # Test starten - Ausgabe für Debug
    print("Starte Test über WLAN...")
    # es wird eine HTTP-GET Anfrage gesendet mit /start als ESP-Endpoint
    requests.get(
        # URL f+r den ESP32 zum starten
        f"http://{ESP_IP}/start",
        # fügt den URL Parameter duration mit der Testdauer in ms hinzu - was dann z.b: /start?duration=120000 ergibt und der ESP liest dann genau server.arg("duration")
        params={"duration": duration_ms},
        timeout=3  # maximale wartezeit - falls esp bis dahin nicht antwortet dann wird ein fehler ausgelöst
    )

    # speichert aktuelle uhrzeit um die laufzeit des tests zu kontrollieren
    start_time = time.time()
    # Variable für gesamtfehleranzahl
    total_errors = 0

    # solange die testdauer nicht überschritten ist also der test noch läuft
    while time.time() - start_time < duration_sec:
        # eine art Fehler-Schutzblock also falls das WLAn mal kurz weg ist dann stürzt das programm nicth ab
        try:
            # Status abfragen - sendet eine HTTP-GET Anfrage an den /status endpoint des ESP32
            # der esp antwortet mit einem JSON objekt das den aktuellen status und die fehleranzahl enthält
            r = requests.get(f"http://{ESP_IP}/status", timeout=1)
            data = r.json()  #antwort in JSOn umwndeln
            # fehleranzahl aus der Antwort holn
            total_errors = data.get("errors", total_errors)
        # falls kurz WLAn weg dann einf überspringen
        except Exception:
            pass

        time.sleep(0.2)  # schützt vor zu vielen anfragen in kurzer zeit

    # Test stoppen
    requests.get(f"http://{ESP_IP}/stop", timeout=3)

    # Reaktionsdaten abholen
    try:
        r = requests.get(f"http://{ESP_IP}/results", timeout=3)
        results = r.json()
    except Exception:
        results = []

    return results, total_errors

