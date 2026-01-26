# IMPORTS
import requests
import streamlit as st   # Basisbibliothekl für die Web-App
import os   # für Dateipfade und Ordneroperationen
import json  # zum Laden und Speichern von JSON-Dateien
import pandas as pd  # für Tabellen und Dataframes
from esp32_read import ESP_IP, run_reaction_test   # Funktion um den Reaktionstest durchzuführen
import base64 # für Hintergrundbildkodierung
import numpy as np  # für numerische Operationen
import altair as alt # für erweiterungen in Diagrammen - interktiv 
from datetime import date, datetime   # für Alter berechnen und Datum speichern
import time

# ------------------------------------------------------
# Hintergrundbild + Overlay
# ------------------------------------------------------
def add_bg_with_overlay(image_file, darkness=0.5):
    '''Funktion die ein Hintergrundbild + Overlay in die App einbaut
    darkness: Wert zwischen 0 (kein Overlay) und 1 (komplett schwarz)
    image_file: Pfad zum Bild'''
    # öffnet Bilddatei im Binärmodus (rb = read binary) und bindet sie an f. 
    with open(image_file, "rb") as f:
        # liest den gesamten Binärinhalt der Bilddatei in data (Bytes)
        data = f.read()
    # kodiert die Bytes data in einen Base64-Byte-String
    # decode() wandelt ihn in einen normalen Python-String um -> eignet sich um das Bild inline in CSS/HTML zu verwenden
    encoded = base64.b64encode(data).decode()  # damit es als HTML-Bild eingebaut werden kann muss aus Bytes ein Base64 String gemacht werden

    # CSS Stil für Hintergrundbild + Overlay
    # erstellt mehrzeilige f-String-Variable css
    css = f"""
    <style>
    /* stApp ist die Klasse für den gesamten App-Hintergrund und setzt das Hintergrundbild der Streamlit-App via background-image auf den Base64-Data-URI
    sorgt dafür dass es das gesamte FGenster abdeckt (cover), zentriert bleibt usw. */
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        position: relative;   /* wird gesetzt, damit das Pseudo-Element (::before) später relativ dazu positioniert werden kann */
    }}

    /* Overlay mit einstellbarer Dunkelheit - das Hintergrundbild soll nicht zu sehr im vordergrund stehen
    erzeugt absolut positioniertes Pseudo-EWlement über der gesamten App, das mit background:rgba(0,0,0,{darkness}) einen halnbtransparenten schwarzen Layer erzeugt
    {darkness} wird durch den übergebenen Parameter ersetzt
    z-index:0 sorgt dafür dass es hinter dem eigentlichen App-Inhalt bleibt, sofern die z-index > 0 haben */
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,{darkness});
        z-index: 0;
    }}

    /* damit der ganze Inhalt über dem Overlay bleibt
    alle direkten Kinder von .stApp (also der gesamte App-Inhalt) werden relativ positioniert
    z-index:1 sorgt dafür dass der App-Inhalt über dem Overlay liegt */
    .stApp > * {{
        position: relative;
        z-index: 1;
    }}
    </style>
    """
    # Hintergrundbild + Overlay in die App einfügen - fügt das CSS in Streamlit-App ein
    # unsafe_allow_html=True erlaubt direktes einfügen von HTML/CSS (bracuth man für Inline-Styling)
    st.markdown(css, unsafe_allow_html=True)

# die Funktion aufrufen und ausführen mit dem gewünschten Bild und der Dunkelheit
add_bg_with_overlay(
    os.path.join(os.path.dirname(__file__), "Titelbild.jpg"),
    darkness=0.7   # je höher der Wert desto dunkler das Overlay
)

# ------------------------------------------------------
# Button-Design - Transparente Popover und Dropdowns
# ------------------------------------------------------
# fügt über st-markdown (HTML/CSS) ein Stylesheet ein, das das Erscheinungsbild von Streamlit-buttons anpasst
st.markdown("""
<style>

    /* ---------------------------------------------------
       TRANSPARENTES POPOVER
    --------------------------------------------------- */
    div[data-testid="stPopoverContent"] {
        background-color: rgba(255,255,255,0.15) !important;    /* macht buttons halbtransparentes weiß */
        backdrop-filter: blur(8px);                             /* unscharfer Hintergrund */  
        -webkit-backdrop-filter: blur(8px);                     /* unscharfer Hintergrund für Safari */
        border-radius: 10px;                                    /* abgerundete Ecken */
        border: 1px solid rgba(255,255,255,0.3);                /* leichter Rand */
    }

    /* Popover Textfarbe */
    div[data-testid="stPopoverContent"] * {
        color: white !important;                                /* macht den Text in den Popovers weiß */    
    }


    /* ---------------------------------------------------
       TRANSPARENTES DROPDOWN (SELECTBOX)
    --------------------------------------------------- */
    div[data-baseweb="select"] > div {
        background-color: rgba(255,255,255,0.15) !important;   /* macht das Dropdown halbtransparentes weiß */
        backdrop-filter: blur(8px);                             /* unscharfer Hintergrund */
        -webkit-backdrop-filter: blur(8px);                     /* unscharfer Hintergrund für Safari */  
        border-radius: 6px;                                     /* abgerundete Ecken */
        border: 1px solid rgba(255,255,255,0.3);                /* leichter Rand */
        color: white !important;                                /* macht den Text im Dropdown weiß */
    }

    /* Dropdown Pfeil */
    div[data-baseweb="select"] svg {
        fill: white !important;   /* macht den Pfeil im Dropdown weiß */
    }


    /* ---------------------------------------------------
       DROPDOWN OPTIONEN TRANSPARENT
    --------------------------------------------------- */
    div[role="listbox"] {
        background-color: rgba(255,255,255,0.15) !important;   /* macht die Optionen halbtransparentes weiß */
        backdrop-filter: blur(10px);                           /* unscharfer Hintergrund */
        -webkit-backdrop-filter: blur(10px);                    /* unscharfer Hintergrund für Safari */
        border-radius: 6px;                                     /* abgerundete Ecken */
        border: 1px solid rgba(255,255,255,0.2);                /* leichter Rand */
    }

    /* Einzelne Optionen */
    div[role="option"] {
        background-color: rgba(255,255,255,0.10) !important;   /* macht die Optionen leicht transparent */
        color: white !important;                               /* macht den Text in den Optionen weiß */
    }

    /* Hover-Effekt */
    div[role="option"]:hover {
        background-color: rgba(255,255,255,0.25) !important;    /* macht die Option beim drüberfahren etwas weniger transparent */
    }

</style>
""", unsafe_allow_html=True)   # erlaubt direktes einfügen von HTML/CSS (braucht man für Inline-Styling)


# ------------------------------------------------------
# Session-State
# ------------------------------------------------------
# Hauptordner für Nutzerprofile der automatisch erstellt wird
# definiert eine Konstante BASE_DIR mit dem Ordnernamen "nutzer" wo die benutzerdaten gespeichert werden
BASE_DIR = "nutzer"
# erstellt Verzeichnis nutzer, falls es noch nicht existiert - über estits_ok = True werden Fehler verhindert falls der Ordner schon existiert
os.makedirs(BASE_DIR, exist_ok=True)

# ------------------------------------------------------
# Initialisierung der Session-State Variablen
# session states ist ein SPeicher in streamlit der dafür sorgt dass daten zwischen Nutzeraktionen erhalten bleiben
# wichtig dass bei neuladen Werte nicht verschwidnen sollen
# ------------------------------------------------------
# es wird gespeichert ob man eingeloggt ist, welcher Nutzer, welche Seite gerade angezeigt wird etc.
if "user" not in st.session_state:
    st.session_state.user = None   # man startet auf der App immer als nicht eingeloggter Nutzer
# steuert die aktuelle Seite der App
if "page" not in st.session_state:
    st.session_state.page = "home"  # man startet bei neuem Laden der App immer auf der Startseite
# steuert ob ein Dialog (Anmelden/Registrieren) aktiv ist
if "active_dialog" not in st.session_state:
    st.session_state.active_dialog = None   # kein Dialog aktiv beim Start
# steuert ob der editiermodus im Profil aktiv ist oder nicht
if "edit_profile" not in st.session_state:
    st.session_state.edit_profile = False



# ------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------
def calculate_age(birthdate: date) -> int:
    '''Funktion die das Alter anhand vom geburtsdatum berechnet.
    birthdate: Geburtsdatum als date-Objekt
    return: Alter in Jahren als int
    '''
    # heutiges Datum ermitteln
    today = date.today()
    # Alter berechnen
    return today.year - birthdate.year - (
        (today.month, today.day) < (birthdate.month, birthdate.day)
    )

def user_folder(vorname, nachname):
    '''Funktion die den Pfad zum Benutzerordner erzeugt
    vorname: Vorname des Nutzers
    nachname: Nachname des Nutzers
    beides in Kleibuchstaben
    return: Pfad zum Nutzerordner
    Pfad wird aus BASE_DIR + vorname_nachname zusammengesetzt'''
    # jeder Nutzer bekommt einen eigenen Ordner im BASE_DIR mit vorname_nachname
    # os.path.join verbindet die Teile zu einem gültigen Pfad und ist für betriebssystem-unabhängige Pfade wichtig
    return os.path.join(BASE_DIR, f"{nachname.lower()}_{vorname.lower()}")

def save_user_profile(vorname, nachname, geburtsdatum, geschlecht, avatar="Driver_1.png"):
    '''Funktion um ein Nutzerprofil zu speichern
    vorname: Vorname des Nutzers
    nachname: Nachname des Nutzers
    geburtsdatum: Geburtsdatum des Nutzers
    geschlecht: Geschlecht des Nutzers
    speichert die Profildaten als JSON-Datei im Nutzerordner'''
    # ermittelt Ordnername für Nutzer und erstellt ihn über os.makedirs falls er noch nicht vorhandne ist
    folder = user_folder(vorname, nachname)
    os.makedirs(folder, exist_ok=True)
    # er wird im Unterordner tests für Testdateien angelegt
    os.makedirs(os.path.join(folder, "tests"), exist_ok=True)

    # Basis-Testordner
    test_base = os.path.join(folder, "tests")
    os.makedirs(test_base, exist_ok=True)

    # Unterordner nach Spieltyp
    subfolders = ["classic", "f1start", "memory"]
    for sub in subfolders:
        os.makedirs(os.path.join(test_base, sub), exist_ok=True)


    alter = calculate_age(geburtsdatum)

    # profildaten die bei Regisrtrierung angegeben werden
    # ist ein python Dictionary das profil heißt mit den übergebenen Profilinformationen
    profil = {
        "vorname": vorname,
        "nachname": nachname,
        "alter": alter,
        "geburtsdatum": geburtsdatum.isoformat(),
        "geschlecht": geschlecht,
        "avatar": avatar
    }

    # öffnet die Datei profil.json im Nutzerodner und speichert das profil als JSON mit Einrückungen von 4 Leerzeichen
    # Profildaten als JSON speichern
    with open(os.path.join(folder, "profil.json"), "w") as f:
        json.dump(profil, f, indent=4)

def save_test_result(user, game_type, results, mode=None, duration_sec=None, total_errors=None):
    """
    Speichert ein Testergebnis für einen Nutzer.
    user: dict mit vorname/nachname
    game_type: "classic", "f1start", "memory"
    results: Liste von dicts z.B. [{"reaction_ms": 250}, ...]
    """
    folder = user_folder(user["vorname"], user["nachname"])
    test_dir = os.path.join(folder, "tests", game_type)
    os.makedirs(test_dir, exist_ok=True)

    # Automatische Nummerierung der Tests
    existing_files = [f for f in os.listdir(test_dir) if f.endswith(".json")]
    test_num = len(existing_files) + 1
    filename = f"test{test_num}_{game_type}.json"

    test_data = {
        "game": game_type,
        "mode": mode,
        "duration_sec": duration_sec,
        "results": results,
        "total_errors": total_errors
    }

    if mode:
        test_data["mode"] = mode
    if duration_sec is not None:
        test_data["duration_sec"] = duration_sec
    if total_errors is not None:
        test_data["total_errors"] = total_errors

    file_path = os.path.join(test_dir, filename)

    with open(file_path, "w") as f:
        json.dump(test_data, f, indent=4)

    return filename



def load_user(vorname, nachname):
    '''Funktion um ein Nutzerprofil zu laden
    vorname: Vorname des Nutzers
    nachname: Nachname des Nutzers
    return: geladene Profildaten als dict oder None wenn nicht gefunden
    '''
    # lädt die Profildaten aus der JSON-Datei wenn der Nutzer existiert
    # ermittelt den Nutzerordnerpfad
    folder = user_folder(vorname, nachname)
    # erzeugt den Pfad zur profil.json
    profil_path = os.path.join(folder, "profil.json")

    # wenn die Profil-Datei existiert, lade sie und gib die Daten zurück
    if os.path.exists(profil_path):
        with open(profil_path, "r") as f:
            return json.load(f)
    # wenn nicht gefunden, gib None zurück
    return None

def load_best_reaction_times(base_dir="nutzer", game_type=None):
    '''Funktion die alle Testdateien aller Nutzer ladet und von jedem Nutzer die besten Reaktionszeiten heraussucht
    base_dir: Basisordner in dem die Nutzerordner liegen
    return: Liste mit den besten Reaktionszeiten aller Nutzer
    '''
    best_times = []

    if not os.path.exists(base_dir):
        return best_times

    for user_folder_name in os.listdir(base_dir):

        user_dir = os.path.join(base_dir, user_folder_name)
        tests_base = os.path.join(user_dir, "tests")

        if not os.path.isdir(tests_base):
            continue

        # Alle Spielordner durchgehen
        for game in ["classic", "f1start", "memory"]:

            game_dir = os.path.join(tests_base, game)

            if not os.path.isdir(game_dir):
                continue

            for file in os.listdir(game_dir):

                if not file.endswith(".json"):
                    continue

                with open(os.path.join(game_dir, file), "r") as f:
                    data = json.load(f)

                # Filtern nach Spieltyp
                if game_type and data.get("game") != game_type:
                    continue

                reactions = [
                    r["reaction_ms"]
                    for r in data.get("results", [])
                    if "reaction_ms" in r
                ]

                if reactions:
                    best_times.append(min(reactions))

    return best_times


def load_best_reaction_time_of_user(user, game_type=None):
    '''Funktion die die beste Reaktionszeit vom akutell eingeloggten Nutzer holt. Bracuht man um die im gesamtn Diagramm sichtabr zu machen
    user: Nutzerprofil als dict
    return: beste Reaktionszeit des Nutzers in ms oder None wenn keine Tests vorhanden'''

    folder = user_folder(user["vorname"], user["nachname"])
    tests_base = os.path.join(folder, "tests")

    if not os.path.exists(tests_base):
        return None

    best = None

    for game in ["classic", "f1start", "memory"]:

        game_dir = os.path.join(tests_base, game)

        if not os.path.isdir(game_dir):
            continue

        for file in os.listdir(game_dir):

            if not file.endswith(".json"):
                continue

            with open(os.path.join(game_dir, file), "r") as f:
                data = json.load(f)

            if game_type and data.get("game") != game_type:
                continue

            for r in data.get("results", []):
                if "reaction_ms" in r:

                    val = r["reaction_ms"]

                    if best is None or val < best:
                        best = val

    return best


def load_memory_highscores(base_dir="nutzer"):
    """
    Lädt die besten Memory-Highscores aller Nutzer
    
    return:
        Liste mit Memory-Levels (int),
        z.B. [3, 5, 7, 7, 10]
    """
    highscores = []

    if not os.path.exists(base_dir):
        return highscores

    for user_folder_name in os.listdir(base_dir):

        user_dir = os.path.join(base_dir, user_folder_name)
        memory_dir = os.path.join(user_dir, "tests", "memory")

        if not os.path.isdir(memory_dir):
            continue

        max_level = None

        for file in os.listdir(memory_dir):

            if not file.endswith(".json"):
                continue

            with open(os.path.join(memory_dir, file), "r") as f:
                data = json.load(f)

            results = data.get("results", [])

            if results and "level" in results[0]:

                level = results[0]["level"]

                if max_level is None or level > max_level:
                    max_level = level

        if max_level is not None:
            highscores.append(max_level)

    return highscores



def load_memory_highscore_of_user(user):

    folder = user_folder(user["vorname"], user["nachname"])
    memory_dir = os.path.join(folder, "tests", "memory")

    if not os.path.exists(memory_dir):
        return None

    max_level = None

    for file in os.listdir(memory_dir):

        if not file.endswith(".json"):
            continue

        with open(os.path.join(memory_dir, file), "r") as f:
            data = json.load(f)

        results = data.get("results", [])

        if results and "level" in results[0]:

            level = results[0]["level"]

            if max_level is None or level > max_level:
                max_level = level

    return max_level



def image_to_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

if "img_nonce" not in st.session_state:
    st.session_state.img_nonce = time.time()

# ------------------------------------------------------
# LOGIN-DIALOG
# ------------------------------------------------------
@st.dialog("Anmelden")
def login_dialog():
    '''Deklariert eine Dialogfunktion für Streamlit mit dem Titel "Anmelden". Den Dekolrator braucht man dass die Funktion als wiederverwendbarer Dialog verfügbar ist
    Funktion die den Login-Dialog erstellt
    vorname: Eingabefeld für Vorname
    nachname: Eingabefeld für Nachname
    Login bestätigen Button lädt das Nutzerprofil und speichert es im Session-State
    '''
    # Eingabefelder für Vorname und Nachname mit dem enstprechenden Key für eindeutige Session-State-Bindings
    # key ist die eindeutige Kennung für das Eingabefeld im Session-State, braucht streamlit um Werte zuspeichern, widges auseinanderzuhalten, session-states richtig zuordnen, neuladen richtig durchzuführen
    # ohne key wüsste streamlit nht welches textfeld gemeint ist, welcher button schon geklickt wurde und zu welchem widget welcher wert gehört weil streamlit läuft immer neu
    vor = st.text_input("Vorname", key="login_vor")
    nach = st.text_input("Nachname", key="login_nach")

    # wenn der button Login bestätigen gedrückt wurde dann wird der block ausgeführt
    if st.button("Login bestätigen", key="login_confirm"):
        # Nutzerprofil laden
        user = load_user(vor, nach)
        # wenn ein user gefunden wurde dann wird das geadene profil in session-state.user gespeichert und den active_dialog auf None setzten also den Dialog schließeen
        # durch st.rerun() das Neuladen der App erzwingen damit der Status sofort aktualisiert wird
        if user:
            st.session_state.user = user
            st.session_state.active_dialog = None
            st.rerun()
        # wenn kein Nutzer gefunden wurde, wird eine Fehlermeldung angezeigt
        else:
            st.error("Nutzer nicht gefunden.")

    # trennt durch hinzufügen einer Linie und fügt einen Link zum Registrieren hinzu
    st.write("---")
    st.write("Noch keinen Account?")

    # wenn der button Jetzt registrieren gedrückt wurde, wird der aktive Dialog auf "register" gesetzt und die App neu geladen
    if st.button("Jetzt registrieren", key="goto_register"):
        st.session_state.active_dialog = "register"
        st.rerun()


# ------------------------------------------------------
# REGISTRIEREN-DIALOG
# ------------------------------------------------------
@st.dialog("Registrieren")
def register_dialog():
    '''Funktion die den Registrieren-Dialog erstellt
    dekodiert eine Dialogfunktion mit dem Titel "Registrieren"
    vorname: Eingabefeld für Vorname
    nachname: Eingabefeld für Nachname
    alter: Eingabefeld für Alter
    geschlecht: Auswahlfeld für Geschlecht
    Registrieren bestätigen Button speichert das Nutzerprofil und lädt es in den Session-State
    '''
    # --- Profilbild auswählen ---
    st.markdown("### Wähle ein Profilbild")

    avatars = os.listdir("avatars")

    # Session-State für ausgewählten Avatar und Galerie-Flag
    if "reg_selected_avatar" not in st.session_state:
        st.session_state.reg_selected_avatar = avatars[0]
    if "reg_show_gallery" not in st.session_state:
        st.session_state.reg_show_gallery = False

    # -------- Avatar-Vorschau, klickbar --------
    avatar_path = os.path.join("avatars", st.session_state.reg_selected_avatar)

    # Klickbar machen, Button unsichtbar
    if st.button("", key="reg_avatar_preview"):
        st.session_state.reg_show_gallery = not st.session_state.reg_show_gallery

    st.markdown("### Ausgewählter Avatar")

    st.image(
        avatar_path,
        width=120,
        caption="Klicken zum Ändern"
    )

    if st.button("Avatar ändern"):
        st.session_state.reg_show_gallery = not st.session_state.reg_show_gallery



    # -------- Galerie anzeigen, falls show_gallery True --------
    # Galerie anzeigen
    if st.session_state.reg_show_gallery:
        st.markdown("#### Wähle einen Avatar")

        cols = st.columns(5)  # 5 Avatare pro Reihe

        for i, avatar in enumerate(avatars):
            avatar_path = os.path.join("avatars", avatar)

            with cols[i % 5]:
                # klickbares Kästchen simulieren
                selected = st.session_state.reg_selected_avatar == avatar
                button_label = "✅" if selected else ""  # Häkchen wenn ausgewählt

                # st.button für Klick, Bild daneben
                if st.button(button_label, key=f"reg_avatar_{avatar}"):
                    st.session_state.reg_selected_avatar = avatar
                    st.session_state.reg_show_gallery = False
                    st.rerun()

                # Avatarbild anzeigen (nur Bild, kein Text)
                st.image(avatar_path, width=60)



    # Eingabefelder für Vorname, Nachname, Alter und Geschlecht mit dem entsprechenden Key für eindeutige Session-State-Bindings
    vor = st.text_input("Vorname", key="reg_vor")
    nach = st.text_input("Nachname", key="reg_nach")
    geburtsdatum = st.date_input(
        "Geburtsdatum",
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        key="reg_birthdate"
    )

    geschlecht = st.selectbox(
        "Geschlecht",
        ["männlich", "weiblich"],
        key="reg_geschlecht"
    )

    # button zur bestätigung der Registrierung und dann das Profil durch safe_user_profil speichern 
    if st.button("Registrierung bestätigen", key="register_confirm"):
        save_user_profile(
            vor, nach, geburtsdatum, geschlecht,
            avatar=st.session_state.reg_selected_avatar
        )
        # läd das gerade erstellte Profil und setzt user, schließt Dialog und rerun() die APP damit der neu eingeloggte Zustand angezeigt wird
        st.success("Registrierung erfolgreich!")
        st.session_state.user = load_user(vor, nach)
        st.session_state.active_dialog = None
        st.rerun()


# ------------------------------------------------------
# HEADER (Profil-Button rechts)
# ------------------------------------------------------
# zwei spalten mit relativen Breiten von 7:1, der linke ist größer wiel der zum titel gehört
header_left, header_right = st.columns([7, 1])

# die linke spalte idt die HTML Überschrift - weiß gefärbt
with header_left:
    st.markdown("<h1 style='color:white;'>Reaktionstestsystem</h1>", unsafe_allow_html=True)

# die rechte spalte ist ein popover Menü für Profilaktionen (Anmelden, Registrieren, Profil anzeigen, Test starten, Tests anzeigen, Abmelden)
# ------------------------------------------------------
# SIDEBAR MENÜ (Buttons statt Popover)
# ------------------------------------------------------
with st.sidebar:
    st.header("Navigation")

    # -------------------------------------------------
    # PROFILBEREICH (NUR WENN EINGELOGGT)
    # -------------------------------------------------
    if st.session_state.user:
        avatar_file = st.session_state.user.get("avatar", "Driver_1.png")
        avatar_path = os.path.join("avatars", avatar_file)
        avatar_base64 = image_to_base64(avatar_path)

        html = (
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:15px;">'
            f'<div style="width:42px;height:42px;border-radius:50%;background:white;'
            f'display:flex;align-items:center;justify-content:center;">'
            f'<img src="data:image/png;base64,{avatar_base64}" '
            f'style="max-width:30px;max-height:30px;object-fit:contain;"></div>'
            f'<span style="color:white;font-weight:600;font-size:16px;">'
            f'{st.session_state.user["vorname"]}</span>'
            f'</div>'
        )

        st.markdown(html, unsafe_allow_html=True)
        st.write("---")

    # -------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------
    if st.button("🏠 Home"):
        st.session_state.page = "home"
        st.rerun()

    if st.session_state.user:
        if st.button("🎮 Neuer Test"):
            st.session_state.page = "test_start"
            st.rerun()

        if st.button("📜 Bisherige Tests"):
            st.session_state.page = "test_history"
            st.rerun()

        if st.button("👤 Profil"):
            st.session_state.page = "profile"
            st.rerun()

        st.write("---")

        # -------------------------------------------------
        # ABMELDEN (NUR WENN EINGELOGGT)
        # -------------------------------------------------
        if st.button("🚪 Abmelden"):
            st.session_state.user = None
            st.session_state.page = "home"
            st.rerun()




    else:
        # Login/Register Buttons sichtbar wenn nicht eingeloggt
        if st.button("🔑 Anmelden"):
            st.session_state.active_dialog = "login"
            st.rerun()
        if st.button("✍️ Registrieren"):
            st.session_state.active_dialog = "register"
            st.rerun()




# ------------------------------------------------------
# Dialog öffnen, wenn aktiv
# ------------------------------------------------------
# öffnet einen dialog wenn aktiv - prüft active_dialog
# wenn login dann login_dialog aufrufen
if st.session_state.active_dialog == "login":
    login_dialog()
# wenn register dann register_dialog aufrufen
elif st.session_state.active_dialog == "register":
    register_dialog()


# ------------------------------------------------------
# HAUPTSEITEN
# ------------------------------------------------------
# HOME - wenn Seite home dann die Startseitenüberschrift und den Erklärungstext anzeigen
#      - lade die besten Reaktionszeiten aller Nutzer und zeige sie in einem Diagramm an
#      - macht zwei spalten links und rechts für das Diagramm und den erklärtext 
if st.session_state.page == "home":

    tab_classic, tab_f1, tab_memory = st.tabs([
        "🎯 Klassisches Reaktionsspiel",
        "🏎️ F1-Start-Simulation",
        "🧠 Memory-Game"
    ])

    with tab_classic:

        # zuerst alle besten Reaktionszeiten aller Nutzer laden
        reaction_times = load_best_reaction_times(game_type="classic")
        st.markdown("### Klassisches Reaktionsspiel")

        # kurzer erklärungstext zur App
        st.markdown(
            """
            <p style="
                color: white;
                font-size: 1.2rem;
                max-width: 900px;
                margin-bottom: 40px;
            ">
                Sobald eine LED aufleuchtet, drücke den zugehörigen Button so schnell wie möglich.
                Dieses System misst deine Reaktionszeit und Fehlerquote in Echtzeit.
            </p>
            """,
            unsafe_allow_html=True
        )
    


        # wenn reaktionszeiten vorhanden sind, wird das diagramm und der erklärtext angezeigt
        if reaction_times:
            # dataframe aus den reaktionszeiten erstellen und dann den mittelwert aus den daten berechnen für den erklärtext 
            df = pd.DataFrame(reaction_times, columns=["reaction_ms"])
            avg = df["reaction_ms"].mean()

            # zwei spalten erstellen für linke seite diagramm und rechte seite erklärtext
            col_left, col_right = st.columns([1.2, 1])

            # ------------------------
            # LINKE SPALTE: KURVE + SPÄTER USER-PUNKT
            # ------------------------
            with col_left:
                # wenn jemand angemeldet ist dann wird die unterüberschrift angepasst
                if st.session_state.user:
                    st.subheader("Deine Reaktionszeit im Vergleich")
                else:
                    st.subheader("Verteilung der schnellsten Reaktionszeiten")

                # HISTOGRAMM -> LINIEN CHART MIT ALTAR

                # durch np.histogram() wird ein Histogramm auf den Daten df["reaction_ms"] erstellt
                # die 25 bins teilt den wertebereich von den reaktionszeiten in 25 gleich große Intervalle auf
                # es werden counts (Anzahö der werte in jedem bin) und bin_edges (die grenzwerte der bins) zurückgegeben
                counts, bin_edges = np.histogram(df["reaction_ms"], bins=25)
                # berechnet die mittelpunkte der Bins
                # er nimmt alle linken Ränder (bin_edges[:-1]) und addiert sie zu den rechten Rändern (bin_edges[1:]) und teilt durch 2
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                # erstellt jetzt das DataFrame das die Histogrammdaten speichert - reaction_ms sind die x-Werter und counts sind die y-Werte
                curve_df = pd.DataFrame({
                    "reaction_ms": bin_centers,
                    "count": counts
                })

                # Linien-Chart mit Altair erstellen mit den Daten aus curve_df
                # Speed-Kategorie hinzufügen - speed ist für die Farbe
                curve_df["speed"] = np.where(curve_df["reaction_ms"] <= 250, "schnell", "langsam")

                # Farben definieren
                color_scale = alt.Scale(
                    domain=["schnell", "langsam"],
                    range=["green", "blue"]
                )

                # Linie nach Farbe einfärben
                line = alt.Chart(curve_df).mark_line(interpolate="monotone").encode(
                    x=alt.X("reaction_ms:Q", title="Reaktionszeit (ms)"),
                    y=alt.Y("count:Q", title="Häufigkeit"),
                    color=alt.Color("speed:N", scale=color_scale, legend=None)  # kein Legenden-Label
                )


                # das liniendiagramm wird in einer variable chart gepsuechert damit man später einen kreis für den nutzer hinzuzufügen kann
                chart = line

                # prüfen ob ein nutzer eingeloggt ist oder nicht
                if st.session_state.user:
                    # die beste reaktionszeit des nutzers aus der datenbank oder Datei laden
                    best_user_time = load_best_reaction_time_of_user(
                        st.session_state.user,
                        game_type="classic"
                    )
                    # wenn eine beste zeit vorhanden ist, wird ein punkt im diagramm hinzugefügt
                    if best_user_time is not None:
                        # es wird die differenz zwischen nutzerzeit und allen Bin-Mittelpunkten ermittelt über das np.abs
                        # das .argmin() gibt den index des minimalen werts zurück also den bin der am nächsten an der nutzerzeit liegt
                        idx = np.abs(bin_centers - best_user_time).argmin()
                        # dann wird die häufigkeit für diesen bin angegeben
                        y_val = counts[idx]

                        # ein dataframe für den kreis des nutzers erstellen
                        user_df = pd.DataFrame({
                            "reaction_ms": [best_user_time],
                            "count": [y_val]
                        })
                        # einen roten kreis im diagramm für die nutzerzeit erstellen
                        point = alt.Chart(user_df).mark_point(
                            size=120,
                            color="red"
                        ).encode( # koordinaten aus dem dataframe
                            x="reaction_ms:Q",
                            y="count:Q"
                        )
                        # die linie und den punkt überlagern damit man di elinie und die beste zeit vom nutzer sieht
                        chart = line + point
                # das diagramm in der app anzeigen mit use_container_width=True damit es die ganze spaltenbreite nutzt
                st.altair_chart(chart, use_container_width=True)

            # ---------------------------------
            # RECHTE SPALTE: BESCHREIBUNGSTEXT
            # ---------------------------------
            with col_right:
                # auf der rechten seite wird wenn man im user satet ist also wenn jemand ngemeldet ist dann der text mit dem nutzerergebnis angezeigt
                if st.session_state.user:
                    best_user_time = load_best_reaction_time_of_user(
                        st.session_state.user,
                        game_type="classic"
                    )

                    st.markdown(
                        f"""
            ### Dein Ergebnis

            Deine **beste Reaktionszeit** liegt bei  
            **{best_user_time} ms**.

            Der rote Punkt im Diagramm zeigt,
            wo du im Vergleich zu allen anderen liegst.
            """
                    )
                # wenn niemand angemeldet ist dann wird der allgemeine erklärtext angezeigt
                else:
                    st.markdown(
                        f"""
            ### Über den Test

            Der Reaktionstest ist eine der einfachsten Möglichkeiten,  
            die menschliche Reaktionszeit objektiv zu überprüfen.

            Die **durchschnittliche Reaktionszeit** aller Teilnehmer  
            liegt bei **{avg:.1f} ms**.
            """
                    )

    with tab_f1:

        # -----------------------------
        # DATEN LADEN (NUR F1-START)
        # -----------------------------
        f1_times = load_best_reaction_times(game_type="f1start")
        st.markdown("### F1-Start-Simulation")

        # kurzer erklärungstext zur App
        st.markdown(
            """
            <p style="
                color: white;
                font-size: 1.2rem;
                max-width: 900px;
                margin-bottom: 40px;
            ">
                Bei der F1-Startsimulation musst du den blau leuchtenden Button genau dann drücken, 
                wenn die Startampel ausgeht. Ein zu frühes Drücken führt zu einem Fehlstart, 
                ein zu spätes Drücken verlängert deine Reaktionszeit. 
                Deine Startreaktion wird in Millisekunden gemessen, damit du sehen kannst, wie schnell du reagierst 
                und wie du im Vergleich zu anderen abschneidest. 
                Schnelle Reaktionen sind entscheidend, um die Führung beim Rennstart zu übernehmen.
            </p>
            """
            ,
            unsafe_allow_html=True
        )

        if f1_times:

            df = pd.DataFrame(f1_times, columns=["reaction_ms"])
            avg = df["reaction_ms"].mean()

            col_left, col_right = st.columns([1.2, 1])

            # =============================
            # LINKE SPALTE – DIAGRAMM
            # =============================
            with col_left:

                if st.session_state.user:
                    st.subheader("Deine Startreaktion im Vergleich")
                else:
                    st.subheader("Verteilung der Startreaktionszeiten")

                # =============================
                # HISTOGRAMM BERECHNEN
                # =============================
                counts, bin_edges = np.histogram(df["reaction_ms"], bins=25)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                curve_df = pd.DataFrame({
                    "reaction_ms": bin_centers,
                    "count": counts
                })

                # =============================
                # DATEN SPLITTEN (FARBWECHSEL)
                # =============================
                # nächster vorhandener Punkt zur Grenze
                border_x = 210
                border_idx = np.abs(bin_centers - border_x).argmin()

                border_row = curve_df.iloc[[border_idx]]

                fast_df = curve_df[curve_df["reaction_ms"] <= border_row["reaction_ms"].values[0]]
                slow_df = curve_df[curve_df["reaction_ms"] >= border_row["reaction_ms"].values[0]]


                # =============================
                # LINIE BIS 300 ms (GRÜN)
                # =============================
                line_fast = alt.Chart(fast_df).mark_line(
                    interpolate="monotone",
                    color="green"
                ).encode(
                    x=alt.X("reaction_ms:Q", title="Startreaktionszeit (ms)"),
                    y=alt.Y("count:Q", title="Häufigkeit")
                )

                line_slow = alt.Chart(slow_df).mark_line(
                    interpolate="monotone",
                    color="blue"
                ).encode(
                    x="reaction_ms:Q",
                    y="count:Q"
                )

                chart = line_fast + line_slow


                # =============================
                # USER-PUNKT (WENN ANGEMELDET)
                # =============================
                if st.session_state.user:
                    best_user_time = load_best_reaction_time_of_user(
                        st.session_state.user,
                        game_type="f1start"
                    )

                    if best_user_time is not None:
                        idx = np.abs(bin_centers - best_user_time).argmin()
                        y_val = counts[idx]

                        user_df = pd.DataFrame({
                            "reaction_ms": [best_user_time],
                            "count": [y_val]
                        })

                        point = alt.Chart(user_df).mark_point(
                            size=120,
                            color="red"
                        ).encode(
                            x="reaction_ms:Q",
                            y="count:Q"
                        )

                        chart = chart + point

                # =============================
                # CHART RENDERN
                # =============================
                st.altair_chart(chart, use_container_width=True)


            # =============================
            # RECHTE SPALTE – TEXT
            # =============================
            with col_right:

                if st.session_state.user:
                    best_user_time = load_best_reaction_time_of_user(
                        st.session_state.user,
                        game_type="f1start"
                    )

                    st.markdown(f"""
    ### Dein Start

    Deine **beste Startreaktionszeit**
    liegt bei  

    **{best_user_time} ms**.

    Der Punkt im Diagramm zeigt,
    wie du im Vergleich zu anderen
    Startern abschneidest.
    """)
                else:
                    st.markdown(f"""
    ### Reaktionszeit beim Rennstart

    Die **Reaktionszeit eines F1-Fahrers**
    liegt typischerweise zwischen  
    **100 und 200 ms**.

    Ein schneller Start kann entscheidend sein,
    vor allem auf Strecken, auf denen
    Überholen schwierig ist.

    Die **durchschnittliche Startreaktion**
    aller Teilnehmer liegt bei  
    **{avg:.1f} ms**.
    """)


    with tab_memory:

        # -----------------------------
        # MEMORY-HIGHSCORES LADEN
        # -----------------------------
        memory_scores = load_memory_highscores()
        # erwartet z.B.: [3, 5, 7, 7, 10, 4, 6]
        st.markdown("### Memory-Game")

        # kurzer erklärungstext zur App
        st.markdown(
            """
            <p style="
                color: white;
                font-size: 1.2rem;
                max-width: 900px;
                margin-bottom: 40px;
            ">
                Bei diesem Memory-Spiel musst du dir die angezeigte LED-Sequenz merken und anschließend die LEDs in der richtigen Reihenfolge nachdrücken. 
                Wenn du die Sequenz korrekt wiederholst, wird die Sequenz beim nächsten Durchgang länger, sodass sich dein Gedächtnis und deine Konzentration immer weiter verbessern. 
                Ziel ist es, so viele Level wie möglich zu schaffen und deinen persönlichen Highscore zu übertreffen.
            </p>
            """,
            unsafe_allow_html=True
        )


        if memory_scores:

            col_left, col_right = st.columns([1.2, 1])

            # =============================
            # LINKE SPALTE – DIAGRAMM
            # =============================
            with col_left:

                if st.session_state.user:
                    st.subheader("Dein Memory-Highscore im Vergleich")
                else:
                    st.subheader("Verteilung der Memory-Highscores")

                # Daten vorbereiten
                df = pd.DataFrame(memory_scores, columns=["level"])

                counts = df["level"].value_counts().sort_index()

                curve_df = pd.DataFrame({
                    "level": counts.index,
                    "count": counts.values
                })

                # Linie erstellen
                line = alt.Chart(curve_df).mark_line(
                    interpolate="monotone",
                    color="blue"
                ).encode(
                    x=alt.X("level:Q", title="Erreichtes Level"),
                    y=alt.Y("count:Q", title="Anzahl Benutzer")
                )

                chart = line

                # -----------------------------
                # USER-HIGHSCORE MARKIEREN
                # -----------------------------
                if st.session_state.user:
                    user_best = load_memory_highscore_of_user(
                        st.session_state.user
                    )

                    if user_best is not None:
                        user_count = counts.get(user_best, 0)

                        user_df = pd.DataFrame({
                            "level": [user_best],
                            "count": [user_count]
                        })

                        point = alt.Chart(user_df).mark_point(
                            size=150,
                            color="red"
                        ).encode(
                            x="level:Q",
                            y="count:Q"
                        )

                        chart = line + point

                st.altair_chart(chart, use_container_width=True)

            # =============================
            # RECHTE SPALTE – TEXT
            # =============================
            with col_right:

                if st.session_state.user:
                    user_best = load_memory_highscore_of_user(
                        st.session_state.user
                    )

                    st.markdown(f"""
    ### Deine Memory-Leistung

    Dein **bester Memory-Highscore**
    liegt bei  

    **Level {user_best}**.

    Der rote Punkt zeigt,
    wie du im Vergleich zu anderen
    Spielern abschneidest.
    """)
                else:
                    st.markdown("""
    ### Memory-Training

    Das Memory-Spiel trainiert  
    **Arbeitsgedächtnis, Konzentration
    und visuelle Wahrnehmung**.

    Regelmäßiges Training kann helfen,
    die Merkfähigkeit zu verbessern
    und geistig fit zu bleiben.
    """)



# PROFIL - wenn Seite profile und Nutzer eingeloggt dann die Unterüberschrift anzeigen und das Nutzerobjekt als formatiertes JSON ausgeben über st.json()
elif st.session_state.page == "profile" and st.session_state.user:
    user = st.session_state.user

    # -------------------------
    # ANZEIGE-MODUS
    # -------------------------
    if not st.session_state.edit_profile:
        st.subheader("Profilinformationen")
        avatar_file = user.get("avatar", "Driver_1.png")
        avatar_path = os.path.join("avatars", avatar_file)
        avatar_b64 = image_to_base64(avatar_path)

        st.markdown(
            f"""
            <div style="
                width:180px;
                height:180px;
                border-radius:50%;
                background:white;
                margin:auto;
                display:flex;
                align-items:center;
                justify-content:center;
            ">
                <img src="data:image/png;base64,{avatar_b64}"
                    style="
                        width:130px;
                        height:130px;
                        object-fit:contain;
                    ">
            </div>
            """,
            unsafe_allow_html=True
        )





        birthdate = datetime.fromisoformat(user["geburtsdatum"]).date()

        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown(f"**Vorname:** {user['vorname']}")
            st.markdown(f"**Geburtsdatum:** {birthdate.strftime('%d.%m.%Y')}")
            st.markdown(f"**Geschlecht:** {user['geschlecht']}")

        with col_r:
            st.markdown(f"**Nachname:** {user['nachname']}")
            st.markdown(f"**Alter:** {user['alter']} Jahre")

        st.write("")

        if st.button("Profil bearbeiten"):
            st.session_state.edit_profile = True
            st.session_state.selected_avatar = st.session_state.user.get("avatar", "Driver_1.png")
            st.session_state.show_gallery = False
            st.rerun()




    # -------------------------
    # BEARBEITUNGS-MODUS
    # -------------------------
    else:
        st.markdown("### Profil bearbeiten")

        # -------- Avatar ändern --------
        avatars = os.listdir("avatars")

        if "show_gallery" not in st.session_state:
            st.session_state.show_gallery = False

        # Vorschau klickbar
        avatar_path = os.path.join("avatars", st.session_state.selected_avatar)
        if st.button("", key="profile_avatar_preview"):
            st.session_state.show_gallery = not st.session_state.show_gallery

        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:15px; cursor:pointer;">
                <div style="
                    width:140px;
                    height:140px;
                    margin:auto;
                    border-radius:50%;
                    background:white;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                    <img src="data:image/png;base64,{image_to_base64(avatar_path)}"
                        style="max-width:100px; max-height:100px; object-fit:contain;">
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Galerie
        if st.session_state.show_gallery:
            st.markdown("### Wähle ein Avatar")

            cols = st.columns(5)  # 5 Avatare pro Reihe

            for i, avatar in enumerate(avatars):
                avatar_path = os.path.join("avatars", avatar)

                with cols[i % 5]:
                    # prüfen ob Avatar ausgewählt ist
                    selected = st.session_state.selected_avatar == avatar
                    button_label = "✅" if selected else ""

                    # Klick auf Avatar
                    if st.button(button_label, key=f"profile_avatar_{avatar}"):
                        st.session_state.selected_avatar = avatar
                        st.session_state.show_gallery = False
                        st.rerun()

                    # Avatar anzeigen
                    st.image(avatar_path, width=60)


        new_vorname = st.text_input(
            "Vorname",
            value=user["vorname"]
        )

        new_nachname = st.text_input(
            "Nachname",
            value=user["nachname"]
        )

        birthdate_obj = datetime.fromisoformat(user["geburtsdatum"]).date()

        new_birthdate = st.date_input(
            "Geburtsdatum",
            value=birthdate_obj,
            min_value=date(1900, 1, 1),
            max_value=date.today()
        )

        new_alter = calculate_age(new_birthdate)


        new_geschlecht = st.selectbox(
            "Geschlecht",
            ["männlich", "weiblich"],
            index=0 if user["geschlecht"] == "männlich" else 1
        )

        col_save, col_cancel = st.columns(2)
        # --- Änderungen speichern ---
        with col_save:
            if st.button("Änderungen speichern"):
                updated_profile = {
                    "vorname": new_vorname,
                    "nachname": new_nachname,
                    "geburtsdatum": new_birthdate.isoformat(),
                    "alter": new_alter,
                    "geschlecht": new_geschlecht,
                    "avatar": st.session_state.selected_avatar
                }

                old_folder = user_folder(user["vorname"], user["nachname"])
                new_folder = user_folder(new_vorname, new_nachname)

                if old_folder != new_folder:
                    os.rename(old_folder, new_folder)

                with open(os.path.join(new_folder, "profil.json"), "w") as f:
                    json.dump(updated_profile, f, indent=4)

                # Session-State aktualisieren, damit Vorschau sofort das neue Bild zeigt
                st.session_state.user = load_user(new_vorname, new_nachname)
                st.session_state.edit_profile = False
                st.session_state.show_gallery = False  # Galerie schließen

                st.success("Profil aktualisiert")
                st.rerun()


        with col_cancel:
            if st.button("Abbrechen"):
                st.session_state.edit_profile = False
                st.rerun()





# TESTS - wenn Seite test_start und Nutzer eingeloggt dann Block für Teststart ausführen
elif st.session_state.page == "test_start" and st.session_state.user:
    # user ist das eingeloggte Profil, folder der Nutzerordner und test_folder der Pfad zum tests-unterordner
    user = st.session_state.user

    st.subheader("Spiel auswählen")

    game_type = st.radio(
        "Welches Spiel möchtest du spielen?",
        ["🎯 klassisches Reaktionsspiel", "🏎️ F1-Start-Simulation", "🧠 Memory-Game"]
    )
    st.write("---")

    # wenn der Nutzer das klassische Reaktionsspiel ausgewählt hat dann wird der entsprechende Block ausgeführt
    if game_type == "🎯 klassisches Reaktionsspiel":
        st.subheader("Reaktionsspiel – Anleitung")

        st.markdown(
            """
    **Willkommen zum Reaktionsspiel!**  
    Teste deine Reaktionsgeschwindigkeit mit unseren 7 Arcade - Buttons.

    ---

    ### Spielablauf

    **Modus und Dauer wählen:**  
    Du kannst zwischen drei verschiedenen Modi auswählen (z. B. manuell, Ermüdung und Schnelltest – die Modi unterscheiden sich in der Testdauer).  

    **Test starten:**  
    Klicke auf den Button „Test starten“ in der Streamlit-App.

    **Spielen:**  
    Nach dem Start leuchtet in zufälligen Abständen eine der 7 LEDs auf.  
    Deine Aufgabe: So schnell wie möglich den entsprechenden Button drücken, dessen LED gerade leuchtet.  
    Sobald du richtig drückst, erlischt die LED und kurz darauf leuchtet eine neue (zufällige) LED auf.  
    Der Test läuft so lange, bis die gewählte Zeit abgelaufen ist.

    **Ergebnisse:**  
    Nach Ende des Tests werden dir folgende Daten angezeigt:  
    - Schnellste Reaktionszeit  
    - Durchschnittliche Reaktionszeit  
    - Anzahl der korrekten Reaktionen  
    - Error-Count  
    - Weitere Statistiken je nach Modus

    Viel Spaß beim Knacken deiner Bestzeit!
    """
        )

        st.write("---")


        st.subheader("Reaktionstest - Testmodus auswählen")

        # ESTMODUS AUSWÄHLEN:
        test_modus = st.selectbox(
            "Wähle den Testmodus:",
            ["manueller Test (freie Dauer)",
            "Ermüdungstest (15 Minuten)",
            "Schnelltest (20 Sekunden)"]
        )

        # TESTDAUER FESTLEGEN:
        # wenn der Tetsmodus manuel ist dann kann man die zeit selber aussuchen, man gibt sie in minuten ein
        if test_modus == "manueller Test (freie Dauer)":
            dauer_min = st.number_input(
                "Testdauer in Minuten eingeben:",
                min_value = 1,
                max_value = 60,
                value = 2,
            )
            # sie muss aber wieder in sec für den esp umgerechnet werden
            dauer_sec = dauer_min * 60

        # wenn der testmodus Ermüdungstest ist dann wird ein test von 15 min gestartet
        elif test_modus == "Ermüdungstest (15 Minuten)":
            dauer_sec = 15 * 60
            st.info("Der Ermüdungstest dauert **15 Minuten**.")

        # wenn der testmodus Schnelltest ist dann wird ein test von 1 min gestartet
        elif test_modus == "Schnelltest (20 Sekunden)":
            dauer_sec = 20
            st.info("Der Schnelltest dauert **20 Sekunden**.")

        st.write("---")

        # wenn der start button gedrückt wurde dann wird die run_reaction_test(duration_sec=120) Funktion aufgerufen um den Test durchzuführen und die Ergebnise in result speichern
        if st.button("Test starten", key="start_test_button"):
            st.write("Test läuft…")
            # der Test dauert jetzt solange wie man es vorher durch dauer_sec festgelegt hat
            results, total_errors, current_level = run_reaction_test(duration_sec=dauer_sec)

            # zählt die vorhandenen Dateien im tests-Ordner und bestimmt so die nächste Testnummer
            # ist abegsichtert gegen wenn mal eine Dati gelöscht wurde
            filename = save_test_result(user, "classic", results, mode=test_modus, duration_sec=dauer_sec, total_errors=total_errors)

            st.success(f"Test gespeichert als {filename}")



            # wandelt die results in ein pandas DataFrame um und zeigt es in der App an
            df = pd.DataFrame(results) if results else pd.DataFrame()
            st.dataframe(df)

            # die total_errors anzahl wird angezeigt
            st.write(f"Gesamtfehler: {total_errors}")


            # berechnet einfache Statistiken anhand der Reaktionszeiten und zeigt sie an
            # Falls Reaktionszeiten vorhanden → Statistik berechnen
            if "reaction_ms" in df.columns and not df["reaction_ms"].empty:
                st.write("Durchschnitt:", round(df["reaction_ms"].mean(), 1), "ms")
                st.write("Schnellste Reaktion:", df["reaction_ms"].min(), "ms")
                st.write("Langsamste Reaktion:", df["reaction_ms"].max(), "ms")
            else:
                st.info("Keine gültigen Reaktionszeiten vorhanden.")

    if game_type == "🏎️ F1-Start-Simulation":
        st.subheader("F1-Start-Simulation")
        st.markdown(
        """
**Ablauf:**
- Die Startampel geht an und der dafür vorgesehene Button leuchtet von Anfang an.
- Wenn die Lichter ausgehen, drücke diesen Button so schnell wie möglich.
- Deine Reaktionszeit wird gemessen!
        """
        )
        st.write("---")

        if st.button("F1-Start durchführen", key="start_f1_test_button"):
            st.write("Test läuft…")

            start_time = time.time() # Startzeit erfassen

            results, total_errors, current_level = run_reaction_test(
                # es wird keine duration_sec benötigt, da ja der Tets aufhört sobal man reagiert hat
                game="f1start"   
            )

            end_time = time.time() # Endzeit erfassen
            f1test_duration_sec = round(end_time - start_time, 2) # Testdauer berechnen

            # Test speichern (gleiches Schema!)
            filename = save_test_result(user, "f1start", results, duration_sec=f1test_duration_sec, total_errors=total_errors)

            st.success(f"Test gespeichert als {filename}")



            # Ergebnis anzeigen
            if results and isinstance(results, list) and len(results) > 0 and "reaction_ms" in results[0]:
                reaction_time = results[0]["reaction_ms"]
                st.success(f"Deine Startzeit war: {reaction_time} ms")
            else:
                st.error("Keine Reaktionszeit gemessen.")

            st.write(f"Gesamtfehler: {total_errors}")
            st.write(f"Dauer des Tests: {f1test_duration_sec} Sekunden")

    if game_type == "🧠 Memory-Game":

        st.subheader("Memory-Game")
        st.markdown("""
        **Ablauf:**
        - Merke dir die LED-Reihenfolge
        - Drücke sie in der gleichen Reihenfolge nach
        - Nach jeder Runde wird die Sequenz länger
        - Das Spiel endet beim ersten Fehler
        """)

        level_placeholder = st.empty()
        status_placeholder = st.empty()

        if st.button("Memory-Game starten"):
            st.write("Spiel läuft…")

            # ESP starten
            requests.get(
                f"http://{ESP_IP}/start",
                params={"game": "memory"},
                timeout=3
            )

            current_level = 1
            total_errors = 0

            old_highscore = load_memory_highscore_of_user(st.session_state.user)

            # 🔁 LIVE-POLLING
            while True:
                try:
                    r = requests.get(f"http://{ESP_IP}/status", timeout=1)
                    data = r.json()

                    current_level = data.get("level", current_level)
                    total_errors = data.get("errors", total_errors)

                    # 🔴 LIVE LEVEL
                    level_placeholder.markdown(
                        f"### Aktuelles Level: **{current_level}**"
                    )

                    if data.get("running") is False:
                        break

                except Exception:
                    pass

                time.sleep(0.3)

            # 📦 Ergebnisse holen
            try:
                r = requests.get(f"http://{ESP_IP}/results", timeout=3)
                results = r.json()
            except Exception:
                results = []

            # 💾 Test speichern
            filename = save_test_result(user, "memory", results, total_errors=total_errors)

            st.success(f"Test gespeichert als {filename}")



            # 🏆 Highscore prüfen
            if old_highscore is None or current_level > old_highscore:
                st.balloons()
                st.success(
                    f"🏆 **Neuer Highscore!**\n\n"
                    f"**Level {current_level}**"
                )



# wenn Seite test_history und Nutzer eingeloggt dann das
elif st.session_state.page == "test_history" and st.session_state.user:

    user = st.session_state.user
    folder = user_folder(user["vorname"], user["nachname"])
    test_folder = os.path.join(folder, "tests")

    st.subheader("Bisherige Tests")

    # Spiel auswählen
    selected_game = st.radio(
        "Welche Tests anzeigen?",
        ["classic", "f1start", "memory"],
        format_func=lambda x: {
            "classic": "🎯 Klassisch",
            "f1start": "🏎️ F1-Start",
            "memory": "🧠 Memory"
        }[x]
    )

    # Ordner vom Spiel
    game_dir = os.path.join(test_folder, selected_game)

    # Testdateien sammeln
    test_files = []

    if os.path.isdir(game_dir):

        test_files = [
            f for f in os.listdir(game_dir)
            if f.endswith(".json")
        ]

    test_files.sort(reverse=True)

    # Wenn keine Tests
    if not test_files:

        st.info("Keine Tests für dieses Spiel vorhanden.")
        selected_test = None

    else:

        selected_test = st.selectbox(
            "Wähle einen Test aus:",
            test_files
        )

    # Wenn ein Test gewählt wurde
    if selected_test:

        file_path = os.path.join(game_dir, selected_test)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Spieltyp-Name
        game_type = data.get("game", selected_game)

        game_label_map = {
            "classic": "Klassisches Reaktionsspiel",
            "f1start": "F1-Start-Simulation",
            "memory": "Memory-Game"
        }

        game_label = game_label_map.get(game_type, game_type)

        # Daten holen
        results = data.get("results", [])
        total_errors = data.get("total_errors", 0)
        mode = data.get("mode", "—")
        duration = data.get("duration_sec")

        # Basisinfos
        st.write(f"**Spieltyp:** {game_label}")
        st.write(f"**Modus:** {mode}")

        if duration is not None:
            st.write(f"**Dauer:** {duration} Sekunden")
        else:
            st.write("**Dauer:** spielabhängig")

        # Memory Highscore
        if game_type == "memory":

            memory_highscore = load_memory_highscore_of_user(user)

            if memory_highscore is not None:
                st.write(f"**Highscore:** Level {memory_highscore}")

        st.write("---")

        # DataFrame
        df = pd.DataFrame(results) if results else pd.DataFrame()

        # F1
        if game_type == "f1start":

            if total_errors > 0:
                st.error("Fehlstart!")
            else:
                st.success("Sauberer Start!")

            if results and "reaction_ms" in results[0]:
                st.write(
                    f"Deine Startreaktionszeit: "
                    f"**{results[0]['reaction_ms']} ms**"
                )
            else:
                st.info("Keine gültigen Reaktionszeiten vorhanden.")

        # Classic
        elif game_type == "classic":

            st.dataframe(df)

            st.write(f"Gesamtfehler: {total_errors}")

            if "reaction_ms" in df.columns and not df["reaction_ms"].empty:

                st.write(
                    "Durchschnitt:",
                    round(df["reaction_ms"].mean(), 1),
                    "ms"
                )
                st.write("Schnellste:", df["reaction_ms"].min(), "ms")
                st.write("Langsamste:", df["reaction_ms"].max(), "ms")

            else:
                st.info("Keine gültigen Reaktionszeiten vorhanden.")

        # Memory
        elif game_type == "memory":

            if results and "level" in results[0]:
                st.success(
                    f"Erreichtes Memory-Level: "
                    f"{results[0]['level']}"
                )
            else:
                st.info("Kein gültiges Memory-Ergebnis vorhanden.")


            


            

