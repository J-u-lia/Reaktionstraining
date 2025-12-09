import serial # pyserial, Schnittstelle zu seriellen Port
import time     # Sleep ubnd zeitmessung
import json     # zum speichern pvon ergebnisse in JSPN-Datei
import re

def run_reaction_test(duration_sec=120, mode = "Standard", output_file="reaction_result.json"):
    """Funktion um Reaktionstest mit ESP32 durchzuführen."""
    ser = serial.Serial("COM3", 115200, timeout=1)   # öffnet seriellen Port mit einer gweissen Baud rate und 1 timeout - also nach 1s zurückkehren auch wnen nichts kommt
    time.sleep(2)   # 2 sekunden warten damit ESP32 zeit hat den Port zu initialisieren

    # die Bytes START\n in den seriellen Prot schreiben, das dann den EPS32 erreicht, der dann START erkennt
    print("Sende START...")
    ser.write(f"START {duration_sec * 1000}\n".encode())  # sendet START Befehl mit der Testdauer in ms

    start = time.time()  #speichert Startzeit
    results = []  # Liste um Ergebnisse zu speichern
    total_errors = 0 # Zähler für Gesamtfehler

    # solange die Testdauer nioch nicht abgeloffen ist soll gelesen werden
    while time.time() - start < duration_sec:
        line = ser.readline().decode(errors="ignore").strip() # liest eine Zeile vom seriellen Port, dekodiert sie und entfernt führende und nachfolgende Leerzeichen

        if not line:
            continue

        # wenn die Zeile mit LED beginnt, dann ist es eine Reaktionszeitmeldung
        if line.startswith("LED"):
            # Beispiel: LED 2 ausgeschaltet! Dauer: 534 ms
            parts = line.split()   # zerlegt Zeile in Worte
            led = int(parts[1]) #holt den LED index
            # In der Zeile nach einer Zahl suchen
            match = re.search(r"(\d+)\s*ms", line)
            if match:
                duration = int(match.group(1))
                results.append({"led": led, "reaction_ms": duration})
                print(f"Reaktion: LED {led} → {duration} ms")

            results.append({"led": led, "reaction_ms": duration})   # fügt ein dict zur results Liste dazu
            print(f"Reaktion: LED {led} → {duration} ms")

        # Fehler vom ESP32 erkennen
        # wenn die Nachricht mit ERROR beginnt dann ist es eine Fehlermeldung
        elif line.startswith("ERROR"):
            # die Zeile wird durch Leerzeichen getrennt - z.B "ERROR 3" -> ["ERROR", "3"]
            parts = line.split()
            # es wird "ERROR <Nummer>" erwartet, also falls mal etwas wie ERROR 3 7 kommt dann ist es nicht so schlimm und es wird ignoriert
            if len(parts) == 2:
                # die Fehlernummer wird extrahiert also man nimmt nur den zweiten Teil also die Zahl hinter ERROR und wandelt den string "Zahl" in eine Zahl um
                error_number = int(parts[1])
                # in der Liste results wird ein dict mit dem Schlüssel "error" und dem Wert der Fehlernummer hinzugefügt
                results.append({"error": error_number})
                print(f"Fehler erkannt! Fehlernummer: {error_number}")


    ser.write(b"STOP\n")   #stop an ESP32 senden und die verbindung abschließen
    ser.close()

    # Ergebnise in JSON-Datei speichern und die results Liste zurückgeben
    final_data = {
        "mode": mode,
        "duration_sec": duration_sec,
        "errors": total_errors,
        "results": results
    }

    with open(output_file, "w") as f:
        json.dump(final_data, f, indent=4)

    print("Test gespeichert:", output_file)
    return final_data
