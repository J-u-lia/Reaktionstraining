# IMPORTS
import streamlit as st   # Basisbibliothekl für die Web-App
import os   # für Dateipfade und Ordneroperationen
import json  # zum Laden und Speichern von JSON-Dateien
import pandas as pd  # für Tabellen und Dataframes
from esp32_read import run_reaction_test   # Funktion um den Reaktionstest durchzuführen
import base64 # für Hintergrundbildkodierung

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
    "C:/Users/famro/git/Reaktionsspiel/Reaktionstraining/Titelbild.jpg",
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


# ------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------
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

def save_user_profile(vorname, nachname, alter, geschlecht):
    '''Funktion um ein Nutzerprofil zu speichern
    vorname: Vorname des Nutzers
    nachname: Nachname des Nutzers
    alter: Alter des Nutzers
    geschlecht: Geschlecht des Nutzers
    speichert die Profildaten als JSON-Datei im Nutzerordner'''
    # ermittelt Ordnername für Nutzer und erstellt ihn über os.makedirs falls er noch nicht vorhandne ist
    folder = user_folder(vorname, nachname)
    os.makedirs(folder, exist_ok=True)
    # er wird im Unterordner tests für Testdateien angelegt
    os.makedirs(os.path.join(folder, "tests"), exist_ok=True)

    # profildaten die bei Regisrtrierung angegeben werden
    # ist ein python Dictionary das profil heißt mit den übergebenen Profilinformationen
    profil = {
        "vorname": vorname,
        "nachname": nachname,
        "alter": alter,
        "geschlecht": geschlecht
    }

    # öffnet die Datei profil.json im Nutzerodner und speichert das profil als JSON mit Einrückungen von 4 Leerzeichen
    # Profildaten als JSON speichern
    with open(os.path.join(folder, "profil.json"), "w") as f:
        json.dump(profil, f, indent=4)

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
    # Eingabefelder für Vorname, Nachname, Alter und Geschlecht mit dem entsprechenden Key für eindeutige Session-State-Bindings
    vor = st.text_input("Vorname", key="reg_vor")
    nach = st.text_input("Nachname", key="reg_nach")
    alter = st.number_input("Alter", 1, 120, key="reg_alter")  # das alter geht von 1 bis 120
    geschlecht = st.selectbox(
        "Geschlecht",
        ["männlich", "weiblich", "divers"],
        key="reg_geschlecht"
    )

    # button zur bestätigung der Registrierung und dann das Profil durch safe_user_profil speichern 
    if st.button("Registrierung bestätigen", key="register_confirm"):
        save_user_profile(vor, nach, alter, geschlecht)
        st.success("Registrierung erfolgreich!")
        # läd das gerade erstellte Profil und setzt user, schließt Dialog und rerun() die APP damit der neu eingeloggte Zustand angezeigt wird
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
with header_right:
    with st.popover("Profil"):
        # wenn kein Nutzer in session_state.user ist dann werde due buttons Anmedlen und Registreiren angezeigt
        # beim anklicken wird active_dialog entsprechend gesetzt und die App neu geladen
        if st.session_state.user is None:
            # Nicht eingeloggt
            if st.button("Anmelden", key="popover_login"):
                st.session_state.active_dialog = "login"
                st.rerun()

            if st.button("Registrieren", key="popover_register"):
                st.session_state.active_dialog = "register"
                st.rerun()
        # wenn jemand eingeloggt ist dann sind 4 buttons zum auswählen verfügbar
        # profilinformationen - setut die seite auf profile
        # neuen test starten - setzt die seite auf test_start
        # bisherige tests - setzt die seite auf test_history
        # abmelden - setzt user auf None, page auf home und lädt die App neu
        else:
            # Eingeloggt
            if st.button("Profilinformationen", key="profile_info_btn"):
                st.session_state.page = "profile"

            if st.button("Neuen Test starten", key="start_test_menu"):
                st.session_state.page = "test_start"

            if st.button("Bisherige Tests", key="previous_tests_menu"):
                st.session_state.page = "test_history"

            if st.button("Abmelden", key="logout_btn"):
                st.session_state.user = None
                st.session_state.page = "home"
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

# HOME - wenn Seite Home dann den Willkommenstext anzeigen
if st.session_state.page == "home":
    st.write("Willkommen im Reaktionstestsystem!")

# PROFIL - wenn Seite profile und Nutzer eingeloggt dann die Unterüberschrift anzeigen und das Nutzerobjekt als formatiertes JSON ausgeben über st.json()
elif st.session_state.page == "profile" and st.session_state.user:
    st.subheader("Profilinformationen")
    st.json(st.session_state.user)

# TESTS - wenn Seite test_start und Nutzer eingeloggt dann Block für Teststart ausführen
elif st.session_state.page == "test_start" and st.session_state.user:
    # user ist das eingeloggte Profil, folder der Nutzerordner und test_folder der Pfad zum tests-unterordner
    user = st.session_state.user
    folder = user_folder(user["vorname"], user["nachname"])
    test_folder = os.path.join(folder, "tests")

    st.subheader("Reaktionstest - Testmodus auswählen")

    # ESTMODUS AUSWÄHLEN:
    test_modus = st.selectbox(
        "Wähle den Testmodus:",
        ["manueller Test (freie Dauer)",
         "Ermüdungstest (15 Minuten),"
         "Schnelltest (1 Minute)"]
    )

    # TESTDAUER FESTLEGEN:
    # wenn der Tetsmodus manuel ist dann kann man die zeeit selber aussuchen, man gibt sie in minuten ein
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
    elif test_modus == "Schnelltest (1 Minute)":
        dauer_sec = 60
        st.info("Der Schnelltest dauert **60 Sekunden**.")

    st.write("---")

    # wenn der start button gedrückt wurde dann wird die run_reaction_test(duration_sec=120) Funktion aufgerufen um den Test durchzuführen und die Ergebnise in result speichern
    if st.button("Test starten", key="start_test_button"):
        st.write("Test läuft…")
        # der Test dauert jetzt solange wie man es vorher durch dauer_sec festgelegt hat
        results = run_reaction_test(duration_sec=dauer_sec)

        # zählt die vorhandenen Dateien im tests-Ordner und bestimmt so die nächste Testnummer
        test_num = len(os.listdir(test_folder)) + 1
        # erzeugt pfad für die neue testdatei
        path = os.path.join(test_folder, f"test_{test_num}.json")
        
        # schreibt die results als JSON in die Datei
        # unterteilt auch davro welchen odus macn ausgewählt hat
        data_to_save = {
            "mode": test_modus,           # speichert Testmodus
            "duration_sec": dauer_sec,    # speichert Dauer
            "results": results            # Reaktionsdaten
        }

        with open(path, "w") as f:
            json.dump(data_to_save, f, indent=4)


        st.success(f"Test gespeichert als test_{test_num}.json")

        # wandelt die results in ein pandas DataFrame um und zeigt es in der App an
        df = pd.DataFrame(results)
        st.dataframe(df)

        # wenn ein error in den spalten vorhanden ist wird die anzahl der fehler angezeigt
        if "error" in df.columns:
            st.write("Anzahl Fehler:", df["error"].count())


        # berechnet einfache Statistiken anhand der Reaktionszeiten und zeigt sie an
        st.write("Durchschnitt:", df["reaction_ms"].mean(), "ms")
        st.write("Schnellste Reaktion:", df["reaction_ms"].min(), "ms")

# wenn Seite test_history und Nutzer eingeloggt dann das
elif st.session_state.page == "test_history" and st.session_state.user:
    # gleiche vorbereitungen wie oben
    user = st.session_state.user
    folder = user_folder(user["vorname"], user["nachname"])
    test_folder = os.path.join(folder, "tests")

    st.subheader("Bisherige Tests")

    # liest alle Dateien im tests-Ordner und fitert nur .json Dateien - Ergebnisliste test_files
    test_files = [f for f in os.listdir(test_folder) if f.endswith(".json")]

    # wenn keine tests vorhanden sind wird eine info box angezeigt
    if not test_files:
        st.info("Keine Tests vorhanden.")
    # sonst zeigt die selectbox Dropdown damit der benutzer einen test auswählen aus test_files kann
    else:
        # Dropdown-Menü für die Tests
        # selected_test ist der ausgewählte test
        selected_test = st.selectbox(
            "Wähle einen Test aus:",
            options=test_files,
            key="select_test_dropdown"
        )

        # wnn ein test ausgewählt wurde dann wird die json datei geöffnet und in ein data frame umgewandelt und angezeigt
        if selected_test:
            with open(os.path.join(test_folder, selected_test)) as f:
                data = json.load(f)

            st.write(f"**Details zu {selected_test}**")

            # der modus und die dauer werden angezeigt:
            st.write(f"**Modus:** {data['mode']}")
            st.write(f"**Dauer:** {data['duration_sec']} Sekunden")

            # es wird das df results eingelkesen
            df = pd.DataFrame(data["results"])
            st.dataframe(df)


            # wenn die spalte error vorhanden ist wird die anzahl der fehler angezeigt
            if "error" in df.columns:
                st.write("Anzahl Fehler:", df["error"].count())


            # Optionale Statistiken
            # wenn die spalte reactrion_ms vorhanden ist dann werden einige werte berechnet 
            if "reaction_ms" in df.columns:
                st.write("Durchschnitt:", df["reaction_ms"].mean(), "ms")
                st.write("Schnellste Reaktion:", df["reaction_ms"].min(), "ms")
                st.write("Langsamste Reaktion:", df["reaction_ms"].max(), "ms")

