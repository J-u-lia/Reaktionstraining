# IMPORTS
import streamlit as st   # Basisbibliothekl für die Web-App
import os   # für Dateipfade und Ordneroperationen
import json  # zum Laden und Speichern von JSON-Dateien
import pandas as pd  # für Tabellen und Dataframes
from esp32_read import run_reaction_test   # Funktion um den Reaktionstest durchzuführen
import base64 # für Hintergrundbildkodierung
import numpy as np  # für numerische Operationen
import altair as alt # für erweiterungen in Diagrammen - interktiv 
from datetime import date, datetime   # für Alter berechnen und Datum speichern

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

def save_user_profile(vorname, nachname, geburtsdatum, geschlecht):
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

    alter = calculate_age(geburtsdatum)

    # profildaten die bei Regisrtrierung angegeben werden
    # ist ein python Dictionary das profil heißt mit den übergebenen Profilinformationen
    profil = {
        "vorname": vorname,
        "nachname": nachname,
        "alter": alter,
        "geburtsdatum": geburtsdatum.isoformat(),
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


def load_best_reaction_times(base_dir="nutzer"):
    '''Funktion die alle Testdateien aller Nutzer ladet und von jedem Nutzer die besten Reaktionszeiten heraussucht
    base_dir: Basisordner in dem die Nutzerordner liegen
    return: Liste mit den besten Reaktionszeiten aller Nutzer
    '''
    # macht eine leere Liste für die besten Zeiten aller Nutzer
    best_times = []

    # sollte der Basisordner nicht existieren, wird eine leere Liste zurückgegeben
    if not os.path.exists(base_dir):
        return best_times

    # wenn der Basisordner existiert, werden alle Nutzerordner darin durchlaufen
    for user_folder in os.listdir(base_dir):
        # es wird ein pfad erstellt zum testordner des jeweiligen nutzers
        test_dir = os.path.join(base_dir, user_folder, "tests")
        # wenn nicht vorhanden, wird der nächste Nutzerordner geprüft
        if not os.path.isdir(test_dir):
            continue
        # wenn der testordner existiert, werden alle dateien darin durchlaufen
        for file in os.listdir(test_dir):
            # wenn man ein file findet das mit .json endet, wird es geöffnet und die daten geladen
            if file.endswith(".json"):
                with open(os.path.join(test_dir, file), "r") as f:
                    data = json.load(f)
                # aus den geladenen daten werden alle reaktionszeiten in einer liste gesammelt
                reactions = [
                    r["reaction_ms"]
                    for r in data.get("results", [])
                    if "reaction_ms" in r
                ]
                # wenn reaktionszeiten gefunden wurden, wird die beste (minimum) in die best_times liste aufgenommen
                if reactions:
                    best_times.append(min(reactions))  # nur die beste Zeit
    return best_times

def load_best_reaction_time_of_user(user):
    '''Funktion die die beste Reaktionszeit vom akutell eingeloggten Nutzer holt. Bracuht man um die im gesamtn Diagramm sichtabr zu machen
    user: Nutzerprofil als dict
    return: beste Reaktionszeit des Nutzers in ms oder None wenn keine Tests vorhanden'''
    # findet den ordner vom aktuellen nutzer und durchsucht alle testdateien nach der besten reaktionszeit
    folder = user_folder(user["vorname"], user["nachname"])
    test_dir = os.path.join(folder, "tests")
    # wenn der testordner nicht existiert, wird None zurückgegeben
    if not os.path.exists(test_dir):
        return None
     
    best = None
    # wenn ein ordner existiert dann werden alle dateien darin durchlaufen
    for file in os.listdir(test_dir):
        # findet man ein file das auf .json endet, wird es geöffnet und die daten geladen
        if file.endswith(".json"):
            with open(os.path.join(test_dir, file), "r") as f:
                data = json.load(f)
            # aus den geladenen daten wird die beste reaktionszeit gesucht aus der liste der ergebnisse
            for r in data.get("results", []):
                # wenn eine reaktionszeit gefunden wurde, wird sie mit der bisher besten verglichen und ggf. aktualisiert wenn sie kleiner ist wie die aktuelle
                if "reaction_ms" in r:
                    val = r["reaction_ms"]
                    if best is None or val < best:
                        best = val

    return best


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
        save_user_profile(vor, nach, geburtsdatum, geschlecht)
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
        # Startseite - setzt die seite auf home und lädt die app neu
        # abmelden - setzt user auf None, page auf home und lädt die App neu
        else:
            # Eingeloggt
            if st.button("Profilinformationen", key="profile_info_btn"):
                st.session_state.page = "profile"

            if st.button("Neuen Test starten", key="start_test_menu"):
                st.session_state.page = "test_start"

            if st.button("Bisherige Tests", key="previous_tests_menu"):
                st.session_state.page = "test_history"

            if st.button("Startseite", key="startseite_menu_btn"):
                st.session_state.page = "home"
                st.rerun()       

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
# HOME - wenn Seite home dann die Startseitenüberschrift und den Erklärungstext anzeigen
#      - lade die besten Reaktionszeiten aller Nutzer und zeige sie in einem Diagramm an
#      - macht zwei spalten links und rechts für das Diagramm und den erklärtext 
if st.session_state.page == "home":
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
    
    # zuerst alle besten Reaktionszeiten aller Nutzer laden
    reaction_times = load_best_reaction_times()

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
            line = alt.Chart(curve_df).mark_line(   # durch marek_line wird ein Liniendiagramm erstellt
                interpolate="monotone",  # glättet die Kurve dass sie fließend aussieht
                color="white"       # die linie wird weiß gefärbt
            ).encode(   # definiert dei achsen
                x=alt.X("reaction_ms:Q", title="Reaktionszeit (ms)"),   # die x achse sind die reaktionszeiten in ms (q sagt quantitative x-achse)
                y=alt.Y("count:Q", title="Häufigkeit")               # die y achse ist die anzahl der vorkommnisse in jedem bin
            )

            # das liniendiagramm wird in einer variable chart gepsuechert damit man später einen kreis für den nutzer hinzuzufügen kann
            chart = line

            # prüfen ob ein nutzer eingeloggt ist oder nicht
            if st.session_state.user:
                # die beste reaktionszeit des nutzers aus der datenbank oder Datei laden
                best_user_time = load_best_reaction_time_of_user(
                    st.session_state.user
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
                    st.session_state.user
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





# PROFIL - wenn Seite profile und Nutzer eingeloggt dann die Unterüberschrift anzeigen und das Nutzerobjekt als formatiertes JSON ausgeben über st.json()
elif st.session_state.page == "profile" and st.session_state.user:
    user = st.session_state.user

    st.subheader("Profilinformationen")

    # -------------------------
    # ANZEIGE-MODUS
    # -------------------------
    if not st.session_state.edit_profile:

        left, right = st.columns([3, 1])

        with left:
            birthdate = datetime.fromisoformat(user["geburtsdatum"]).date()

            st.markdown(
                f"""
            **Vorname:** {user['vorname']}  
            **Nachname:** {user['nachname']}  
            **Geburtsdatum:** {birthdate.strftime('%d.%m.%Y')}  
            **Alter:** {user['alter']} Jahre  
            **Geschlecht:** {user['geschlecht']}
            """
            )


        with right:
            st.write("")  
            st.write("")  
            if st.button("Profil bearbeiten"):
                st.session_state.edit_profile = True
                st.rerun()

    # -------------------------
    # BEARBEITUNGS-MODUS
    # -------------------------
    else:
        st.markdown("### Profil bearbeiten")

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

        with col_save:
            if st.button("Änderungen speichern"):
                folder = user_folder(
                    user["vorname"],
                    user["nachname"]
                )

                updated_profile = {
                    "vorname": new_vorname,
                    "nachname": new_nachname,
                    "geburtsdatum": new_birthdate.isoformat(),
                    "alter": new_alter,
                    "geschlecht": new_geschlecht
                }

                with open(os.path.join(folder, "profil.json"), "w") as f:
                    json.dump(updated_profile, f, indent=4)

                # Session-State aktualisieren
                st.session_state.user = updated_profile
                st.session_state.edit_profile = False
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
    folder = user_folder(user["vorname"], user["nachname"])
    test_folder = os.path.join(folder, "tests")


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
        results, total_errors = run_reaction_test(duration_sec=dauer_sec)

        # zählt die vorhandenen Dateien im tests-Ordner und bestimmt so die nächste Testnummer
        # ist abegsichtert gegen wenn mal eine Dati gelöscht wurde
        existing = [f for f in os.listdir(test_folder) if f.startswith("test_")]
        test_num = len(existing) + 1

        # erzeugt pfad für die neue testdatei
        path = os.path.join(test_folder, f"test_{test_num}.json")
        
        # schreibt die results als JSON in die Datei
        # unterteilt auch davro welchen odus macn ausgewählt hat
        data_to_save = {
            "mode": test_modus,           # speichert Testmodus
            "duration_sec": dauer_sec,    # speichert Dauer
            "results": results,            # Reaktionsdaten
            "total_errors": total_errors   # Gesamtfehler
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)



        st.success(f"Test gespeichert als test_{test_num}.json")

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
            results = data.get("results", [])
            df = pd.DataFrame(results) if results else pd.DataFrame()

            st.dataframe(df)


            # Gesamtfehleranzahl anzeigen
            st.write(f"Gesamtfehler: {data.get('total_errors', 0)}")


            # Optionale Statistiken
            # wenn die spalte reactrion_ms vorhanden ist dann werden einige werte berechnet 
            if "reaction_ms" in df.columns and not df["reaction_ms"].empty:
                st.write("Durchschnitt:", round(df["reaction_ms"].mean(), 1), "ms")
                st.write("Schnellste Reaktion:", df["reaction_ms"].min(), "ms")
                st.write("Langsamste Reaktion:", df["reaction_ms"].max(), "ms")
            else:
                st.info("Keine gültigen Reaktionszeiten vorhanden.")

