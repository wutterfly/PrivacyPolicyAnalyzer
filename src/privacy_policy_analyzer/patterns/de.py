from privacy_policy_analyzer.analysis.attributes import (
    AttributePattern,
    AttributePatterns,
    DatePattern,
    DurationPattern,
)
from privacy_policy_analyzer.crawl.splitter import SplitterPattern

#------------------------------------------------------------------------------------------

DE_SPLITTER_CONFIG: SplitterPattern = SplitterPattern.from_parts(
    replace_words=[
        ("„", '"' ),
        ("z\\. B\\.", "z.B."),
        ("d\\. h\\.", "d.h."),
        ("U\\. S\\.", "USA"),
        ("U\\.S\\.", "USA"),
        ("U\\.S\\.A\\.", "USA"),
        ("U\\. K\\.", "UK"),
        ("U\\.K\\.", "UK"),
    ],
    last_on_line=[
        "\\.$",
        "\\!$",
        "\\?$",
    ],
    not_last_on_line=[
        "^[0-9]+\\.$",
        "^[A-Za-z]\\.$",
        "^[VIX]{1,4}\\.$",
        "z\\.B\\.$",
        "z\\.Z\\.$",
        "usw\\.$",
        "bzw\\.$",
        "u\\.a\\.$",
        "etc\\.$",
        "d\\.h\\.$",
        "u\\.v\\.m\\.$",
        "ca\\.$",
        "ggf\\.$",
        "evtl\\.$",
        "z\\.T\\.$",
        "i\\.d\\.R\\.$",
        "i\\.A\\.$",
        "i\\.V\\.$",
        "i\\.V\\.m\\.$",
        "i\\.S\\.d\\.$",
        "o\\.Ä\\.$",
        "zzgl\\.$",
        "inkl\\.$",
        "ff\\.$",
        "vgl\\.$",
        "evtl\\.$",
        "u\\.U\\.$",
        "bspw\\.$",
        "Bsp\\.$",
        "sog\\.$",
        "s\\.g\\.$",
        "s\\.o\\.$",
        "s\\.u\\.$",
        "MwSt\\.$",
        "gem\\.$",
        "Nr\\.$",
        "Str\\.$",
        "Abb\\.$",
        "S.\\.$",
        "Abs\\.$",
        "Abschn\\.$",
        "St\\.$",
        "Hr\\.$",
        "Fr\\.$",
        "Dr\\.$",
        "Prof\\.$",
        "Inc\\.$",
        "Ltd\\.$",
        "vs\\.$",
        "etc\\.$",
        "Co\\.$",
        "Corp\\.$",
        "Art\\.$",
        "para\\.$",
        "lit\\.$",
        "^[A-Z]\\.[A-Z]\\.$",
    ],
    first_on_newline=["^·$", "^•$", "^●$", "^\\*$", "^o$"],
    not_first_on_newline=[],
    sentence_not_split_pattern=[
        "para\\. [0-9]\\. s\\.$",
        "Art\\. [0-9] para\\.\\s*[0-9] s\\.$",
        "Art\\. [0-9] para\\. [0-9]\\.( s\\.)?$",
        "Art\\. [0-9] para\\. s\\.$",
    ],
)
""" German language splitter configuration. """

#------------------------------------------------------------------------------------------

DE_PATTERN_CONFIG: AttributePatterns = AttributePatterns(
    data_type=AttributePattern.from_dict(
        {
            "PersonalData": [
                "(?<!nicht[- ])(?<!sensitive)(?<!sensitive[rn])(?<!sensible)(?<!sensible[rn])(?<!Spezialkategorien von )(persönliche[rn]?|personenbezogene[rn]?).{0,20}(Daten|Informationen|Details)",
                "(Daten|Informationen|Details) (über Sie|zu Ihrer Person)",
                "Sie betreffende[rn]? (Daten|Informationen|Details)",
                "zu Ihrer Person (gespeicherten|verarbeiteten|übertragenen|gelöschten|veröffentlichten) (Daten|Informationen|Details)"
            ],
            "SensitiveData": [
                "(sentitive|sensible)[rn]?(.{0,27})? (Daten|Informationen|Details)"
            ],
            "SpecialCategoryData": [
                "(Spezielle|spezifische|Sonder|besondere)[rn]? ?Kategorien(?=.{0,30}(Daten|Informationen|Details))"
            ],
            "GeneralInformation": [
                "allgemeine[rn]?(-.{0,27})? (Daten|Details)\\b"
            ],
            "PII": [
                "\\bPII\\b",
                "(?<!nicht[- ])persönlich identifizierbare[rn]? Informationen",
                "(?<!keine )(Daten|Informationen)(?=.{0,52}Sie)(?!.*nicht).{0,20}(?=.{0,30} (identifizieren|identifiziert))",
                "^(?!.*nicht).*Identifizierung .{0,20} natürlichen Person",
                "Informationen.{0,60}identifiziert werden (kann|können)",
                "zur Identifikation verwendet"
            ],
            "NPII": [
                "NPII",
                "Nicht persönlich identifizierbare[rn]? Informationen",
                "nicht[- ](personenbezogene|persönliche)[rn]? (Informationen|Daten)",
                "nicht als personenbezogen",
                "persönlich nicht identifizierbarer",
                "keine personenbezogenen (Daten|Informationen) (sind|darstellen)"
            ],
            "SetupInformation": [
                "Setup[- ]?information",
            ],
            "DeviceInformation": [
                "Geräte?(-.{0,27}| )?(information|daten)",
                "\\b(Informationen|Daten).{0,20}\\b(über|zu|ihrer)\\b.{0,20}Gerät",
                "verwendeten? (End)?gerät",
                "Gerätemuster"
            ],
            "DeviceName": [
                "(Geräte|Produkt|Modell)(-.{0,27})? name",
                "Name des (Geräte?s|Produkte?s|Mähers)",
                "Kameraname",
                "Namen.{0,30}(Ihrer|Ihren) Geräte?"
            ],
            "DeviceType": [
                "(Geräte|Produkt)(typ|modell|art)",
                "(Typ|Modell|Art) des (Geräte?s|Produkte?s)",
                "Tele(f|ph)onmodel",
                "Hardware(modell|typ|art)",
                "\\bModell(name)?\\b",
                "verwendete[rn]? (mobile[rn]? )?Geräte?"
            ],
            "ProductInfo": [
                "(Produkt|Artikel)(-.{0,27})?(information|daten|detail)",
                "\\b(Information(en)?|Details?|Angaben?) (über|zu|wie) .{0,64}(Produkt(e|en)?|Artikeln?)\\b(?!-)",
                "Produkte, die Sie (angesehen|gesucht|gekauft)",
                "^(?!.*Garantie).*gekauftes? Produkt"
            ],
            "ManufacturerInformation": [
                "(Geräte)?Hersteller(-.{0,27})?(informationen|details)",
                "(Informationen|Details).{0,20}Herstellers?",
            ],
            "TechnicalInformation": ["technische (Informationen|Daten)"],
            "OperatingSystem": [
                "Betriebssystem",
                "operatives System"
                ],
            "FirmwareVersion": ["Firmware[- ]?version"],
            "SoftwareVersion": ["(Software|System|SDK)[- ]?version"],
            "HardwareInformation": [
                "Hardware(-.{0,27})?(informationen|daten|details)",
                "(Informationen|Details).{0,40}hardware"
            ],
            "HardwareVersion": ["Hardware[- ]?version"],
            "BrowserInformation": [
                "Browser(-.{0,27}| )?(informationen|daten)",
                "Informationen (über|zu).{0,30}Browsers?\\b",
                "Browser.{0,30}wieder(zu)?erkennen",
                "Browserkonfigurationsdaten"
            ],
            "BrowserType": [
                "Browser(-.{0,27})?typ",
                "verwendete[rn]? Browsers?",
                "(Typ|Art) des Browsers?"
            ],
            "BrowserVersion": [
                "Browser(-.{0,27})?version",
                "Versions(informationen)?.{0,20}Browsers"
            ],
            "AppVersion": [
                "App(-.{0,27})?(?<!SDK-)version",
                "Version der.{0,20}Apps?"
            ],
            "AppStatus": ["App-?status"],
            "AppID": [
                "App[- ](ID|identifier|identifizierer|kennung)",
                "Kennung(en)? (einer|der) App",
                "Messager?-ID"
            ],
            "ActivationTime": [
                "(Geräte)?Aktivierungszeit",
                "(Geräte)?Aktivierungsdatum",
            ],
            "PartnerApp": [
                "Partner[- ]?App",
                "Third(-| )Party App"
            ],
            "InternetServiceProvider": [
                "Internet-?(dienst)?anbieter",
                "Internet-?dienstleister",
                "\\b(Internet)?provider[sn]?\\b",
                "\\bISP\\b",
                "(?=.*\\bIP\\b).*Dienstanbieter"
            ],
            "NetworkData": [
                "(?<!soziale )(?<!sozialen )Netzwerk(-.{0,27})?(daten|dateien|information)",
                "Netzwerkanfrageinformation(en)?",
                "(Website|Netzwerk)-?Verkehr"
            ],
            "NetworkStatus": ["Netzwerkstatus"],
            "NetworkOperator": ["Netz(werk)?betreiber"],
            "CustomerProprietaryNetworkInformation": [
                "customer proprietary network information",
                "kunden(eigene|bezogene) Netzwerk(informationen|daten)",
                "\\bCPNI\\b",
                "welche (Geräte|Produkte).{0,30}Heimnetzwerk",
                "Nutzung.{0,30}Heimnetzwerk"
            ],
            "OtherElectronicNetworkActivityInformation": [
                "other electronic network activity information",
                "(sonstige|andere) elektronische Netzwerkaktivitäteninformationen",
                "(sonstige|andere) (Daten|informationen).{0,30} elektronischen Netzwerke",
                "\\bOENAI\\b",
            ],
            "SMSStorage": ["SMS-Speicher"],
            "MobileNetworkData": ["mobilen? Netzwerk(-(?!.*Code).{0,81}| )?(daten|informationen)"],
            "MobileNetworkCode": [
                "Mobilfunknetzcode",
                "mobilen? Netzwerk(-.{0,27})?code"
            ],
            "MobileCountryCode": [
                "Mobilfunk-Ländercode",
                "mobilen?.{0,20}Ländercode"
            ],
            "ConnectionData": [
                "Verbindungs(daten|informationen)",
                "Dauer der Verbindungsherstellung"
            ],
            "DataAmount": [
                "Datenmenge",
                "Netzwerkbandbreitennutzung",
                "(Menge|Größe|Umfang).{0,32}gesendete[rn]? Daten",
                "Übertragene Datenmenge",
                "Datenvolumen"
            ],
            "NumberOfRequests": [
                "(An)?zahl der Abfragen",
                "getätigte Abfragen"
            ],
            "WiFiData": [
                "(Wi(-)?Fi|WLAN)[- ](Daten|Informationen|ID)"
            ],
            "WiFiStatus": ["(Wi(-)?Fi|WLAN)[- ]Status"],
            "WiFiHeatmap": ["(Wi(-)?Fi|WLAN)[- ]Heatmap"],
            "SSID": [
                "SSID",
                "(Wi(-)?Fi|WLAN)[- ]name",
                "(Wi(-)?Fi|WLAN)[- ]ID",
                "Netzwerkname"
            ],
            "SignalStrength": [
                "Signalstärke",
                "Verbindungsstabilität"
            ],
            "InternetSpeed": [
                "Internetgeschwindigkeit",
                "Netzwerkgeschwindigkeit"
            ],
            "KeypadInformation": [
                "(Geräte)?tastatur(-.{0,27})?informationen",
                "Informationen.{0,20}Tastatur",
            ],
            "UsageData": [
                "Nutzungs(-.{0,27})?(daten|informationen|verhalten|details|statistik|verlauf|gewohnheiten)",
                "(?=(Messung|Auswertung|Analyse|Information|Daten|Ihr|Häufigkeit)).{0,32}Nutzung.{0,20}(Dienste|Geräte|Produkte|Funktionen|Webs(ite|eite))",
                "Verhalten.{0,24}(Webseite|Website|Dienst|Service|Produkt|Gerät)",
                "bei der Nutzung von",
                "Sie zuvor genutzt haben",
                "Nutzerverhalten",
                "(Informationen|Häufigkeit|Daten|Details)(?=.*(Ihr)).{0,50}(Nutzung)",
                "(Daten|Information|Details)(?=.*(generiert|erzeugt|anfallen))(?=.*(Dienst|Produkt|Gerät|Service).{0,5}nutzen)",
                "^(?!.*(persönliche[rn]?|personenbezogene[rn]?)).* (Daten|Information|Details) zur Nutzung",
                "wie Sie.{0,50}nutzen"

            ],
            "UsageDuration": [
                "(Zugriffs|Sitzungs|Verweil)(dauer|zeitraum)",
                "(Dauer|Zeitraum).{0,20}(App|Dienst|Funktion|Zugriff|Besuch[es])",
                "Nutzungsdauer"
            ],
            "DeviceInteractions": [
                "(Geräte|Produkt)(-.{0,27})?interaktionen",
                "(Gerät|Produkt).{0,20}mit.{0,30}interagiert",
                "Interaktionen mit (Produkten|Geräten)",
                "^(?!.*(Wenn Sie|Wie Sie)).*(Gerät|Produkt)e?.{0,30}interagieren"
            ],
            "AppInteraction": [
                "App[- ]Interaktionen",
                "Interaktionen.{0,10}Apps?",
                "(Daten|Informationen)(?=.{0,100}\\bInteraktion)(?=.*App)",
                "App.{0,20}(daten|information)(?=.{0,60}Interaktion)"
            ],
            "DownloadHistory": ["Download(-.{0,15})?verlauf"],
            "EngagementMetrics": ["Engagement[- ](Daten|Informationen|Metriken|Statistiken|Kennzahlen)"],
            "TelemetryData": ["Telemetrie(informationen|daten)?"],
            "PerformanceData": [
                "Leistungs(-.{0,27})?(daten|informationen|Kennzahl|Details)",
                "(daten|informationen|Kennzahl|Details).{0,30}(App|Gerät|Produkt|Service|Dienstleistung|Website)-Performance"
                "(?<!Verbesserung (von|der) )(?<!Optimierung (von|der) )(?<!Dienst)Leistung\\b.{0,30}(Person|App|Gerät|Produkt|Service|Dienstleistung)",
                "Leistung(en)?.{0,30}(ein(zu)?holen|bewerten)",
                "Kennzahlen zur Leistung",
                "^(?!.*Optimierung).*\\bLeistung\\b.{0,30}(App|Gerät|Produkt)"
            ],
            "DiagnosticData": ["Diagnose(-.{0,27})?(daten|informationen|bericht)"],
            "StatisticalData": [
                "statistische[rn]? (Daten|Informationen|Angaben|Details)",
                "Statistiken"
            ],
            "DeviceStatistics": [
                "(Geräte|Produkt)statistik",
                "Statistik.{0,10}(Gerät|Produkt)"
            ],
            "SettingsData": [
                "(Browser|Energie|Anzeige|Präferenz|Kommunikations|Seiten|Präferenz)(-.{0,27})?Einstellungen",
                "Cookie-(Präferenzen|Einstellungen)"
            ],
            "ConfigurationData": [
                "Konfigurations(-.{0,27})?(daten|informationen)",
                "Konfiguration"
            ],
            "UserPreferences": [
                "(Deine[rn]?|Ihre[rn]?|persönliche[rn]?) (Präferenzen|Vorlieben)",
                "(Nutzer)?Präferenzen",
                "(Nutzer)?Vorlieben",
                "Veranlagungen"
            ],
            "FontSize": [
                "font size",
                "Schriftgröße"
            ],
            "DeviceState": [
                "Gerätestatus",
                "Status des Geräte?s",
                "Statusinformationen über.{0,15}Gerät(e|e?s)",
                "an/aus (Status|Einstellung)"
            ],
            "OnlineStatus": [
                "Onlinestatus",
                "ob Sie online sind"
            ],
            "BatteryData": ["(Batterie|Akku)(daten|informationen|status|verbrauch)"],
            "MemoryUsage": [
                "Speichernutzung",
                "RAM[- ]Auslastung",
                "Nutzungsinformationen.{0,20}Speicher"
            ],
            "StorageUsage": [
                "Festplatten(nutzung|auslastung)",
                "verwendete Speicherkapazität"
            ],
            "CpuUsage": [
                "(CPU|Prozessor)[- ](nutzung|auslastung)",
                "Nutzungsinformationen.{0,20}CPU"
            ],
            "ScreenUnlocks": [
                "^(?!.*verhindern).*(Bildschirm|Gerät).{0,20}entsperr(en|ung)",
                "Anzahl der Entsperrungen",
                "Bildschirmaktivierung(en)?"
            ],
            "UsageFrequency": [
                "Nutzungshäufigkeit",
                "wie oft Sie.{0,20}(nutzen|verwenden)",
                "Häufigkeit.{0,30}Nutzung",
            ],
            "BrowsingActivity": [
                "Browser(aktivität|verlauf|historie)",
                "(Browsing|Online)[- ](aktivität|verlauf|historie)",
                "Surfverhalten",
                "\\bbrowsen\\b"
            ],
            "ViewedContent": [
                "angesehene (Inhalte|Elemente)",
                "(Inhalt|Angebot|Anzeige).{0,20}(an(ge)?sehen|auf(ge)?rufen|angeklickt|anklicken)",
                "Bildaufrufe",
            ],
            "VisitedPages": [
                "(?<!bei )(Seiten|Website)aufruf",
                "(aufgerufene|angesehene|besuchte)n? ((Unter)?Seite|Website|URL)",
                "^(?!.*(Video|Inhalt)).*(Website|Seite)(?!.*(Video|Inhalt)).{0,60}(auf(ge)?rufen|an(ge)?sehen|besucht|besuchen)",
                "Besuchte.{0,20}(Website|Seite)",
                "Besucherverkehr",
            ],
            "ClickedLinks": [
                "angeklickte[rn]? Links",
                "Links.{0,20}geklickt haben",
                "Links.{0,20}klicken"
            ],
            "MouseMovements": [
                "Mausbewegung(en)?",
                "Mausaktivität(en)?",
                "(Maus|mouse)[- ]Tracking",
                "mouse-over",
            ],
            "Keystrokes": [
                "Tastenanschläge",
                "Tastatureingabe"
            ],
            "SearchHistory": [
                "Such(verlauf|historie|begriffe)",
                "Suchanfrage"
            ],
            "PageInteractions": [
                "Seiten?[- ]?Interaktion",
                "Interaktion.{0,30}(Seite|Webseite|Website)",
                "(Seiten|Webseiten?|Website)-Interaktion",
                "wie Sie.{0,20}(Seite|Webseite|Website).{0,48} interagieren"
            ],
            "LogData": [
                "(?<!Geräte)(?<!Zugriffs)(?<!Zugangs)(?<!Chat)(?<!Aktivitäts)-?protokolle?\\b",
                "\\bProtokoll(e|daten|informationen)\\b",
                "Sitzungsereignisse",
                "Log-Identifikation"
            ],
            "LogFiles": ["(Log|Protokoll)[- ]?(Datei|files?)"],
            "DeviceLogs": ["Geräteprotokoll(daten)?"],
            "DeviceHistory": ["Geräte(verlauf|historie)"],
            "Errors": [
                "(Fehler|Error)(-.{0,27})?(melde)?(daten|informationen|berichten?|ereignissen?|nachrichten|protokollen?|details|abfragen)",
                "\\b-Fehler\\b",
            ],
            "AccessLogs": [
                "Zu(gang|griff)s(-.{0,27})?protokolle?",
                "Protokollierung.{0,20}(Zugriff|Zugang)"
            ],
            "ActivityLogs": [
                "(?<!Browsing-)(?<!Online-)Aktivitäts-?(log|verlauf|historie|protokoll|daten)",
                "Ihre(r|en)?.{0,60}(?<!Browsing-)(?<!Online-)\\bAktivität(?!.{0,32}Netzwerk)"
            ],
            "ActivityStatus": [
                "Aktivität(s|en)status",
            ],
            "NotificationLogs": ["Benachrichtigungsprotokoll"],
            "MaintenanceLogs": ["Wartungs(prokoll|aufzeichnung)"],
            "DrivingEvents": ["(Fahr|Renn)veranstaltung"],
            "AppEvents": ["App-(Event|Ereignis)"],
            "DeviceEvents": [
                "Geräte?-(Event|Ereignis)",
                "ausgelöste Aktivitäten"
            ],
            "DeviceAlerts": [
                "Geräte(benachrichtigung|alarm)",
                "Benachrichtigungen.{0,10}Geräte?s",
                "Alarmmeldung"
            ],
            "DateTime": [
                "Uhrzeit",
                "\\bdatum\\b",
                "A[bn]fragezeit",
                "wann sie .{0,20}(öffnen|interagieren)",
                "über die zeit hinweg",
                "Zeitpunkt des (Aufrufe?s|Zugriffe?s)"
            ],
            "MACAddress": ["MAC[- ]Adresse"],
            "IPAddress": ["IP[- ]Adressen?", "\\bIP\\b"],
            "SerialNumber": ["Seriennummer"],
            "DeviceTemperature": [
                "(Geräte|Produkt)temperatur",
                "Temperatur des (Geräte?s|Produkte?s)",
            ],
            "ScheduleTimes": [
                "Zeitplan(ung)?"
            ],
            "Identifier": [
                "\\b(?<!nationale )(Identifikations|Kenn(ungs)?|ID|Kunden)(-.{0,27})?nummern?",
                "persönliche Identifizierer",
                "(?<!Geräte-)Identifikator"
            ],
            "AccountID": ["Konto[- ]ID"],
            "DeviceID": [
                "(Geräte|Produkt)(-.{0,27}| )?(nummer|U?ID\\b|Kennung)",
                "(Daten|Information|Details).{0,40}(Gerät identifiziert|Identifikation.{0,20}Gerät)"
            ],
            "RandomID": [
                "zufällige ID",
                "Zufalls-ID"
            ],
            "AdvertisingID": [
                "Werbe[- ]ID",
                "IDFA"
            ],
            "SessionID": ["Sitzungs[- ](ID|Kennung)"],
            "UserID": ["(Be)?Nutzer[- ]?(IDs?\\b|Kennung)"],
            "OpenID": [
                "open( |-)ID",
                "open identifier",
                "\\bO(A)?ID\\b"
            ],
            "GoogleAdID": [
                "Google (ad|advertising) ID",
                "GAID"
            ],
            "WindowsAdID": ["Windows (ad|advertising) ID"],
            "AndroidID": [
                "Android[- ]ID",
                "\\bAAID\\b"
                ],
            "FCMToken": [
                "FCM[- ]token",
                "Firebase Cloud Messaging token"
            ],
            "SpaceID": ["Space( |-)ID"],
            "ClickID": ["click[- ]ID"],
            "ICCID": [
                "ICCID",
                "Integrated Circuit Card Identifier"
            ],
            "IMEI": [
                "IMEI",
                "International Mobile Equipment Identity"
            ],
            "IMSI": [
                "IMSI",
                "International Mobile Subscriber Identity"
            ],
            "SIMInformation": ["SIM(-.{0,27})?(daten|informationen|fehler|karte)"],
            "WebsiteInformation": [
                "Website[- ](informationen|daten)",
                "Webseiten(informationen|daten)"
            ],
            "Referrer": [
                "referrer",
                "(verweisende|weiterleitende).{0,20}(URL|website|Webseite)",
                "Herkunfts-URL"
            ],
            "HostName": ["Host[- ]?Name"],
            "URL": [
                "URL",
                "uniform resource locator",
                "hyperlink",
                "adresse[^\\)]{0,20}von[^\\)]{0,20}(Seite|Webseite|Wesite)"
            ],
            "DomainName": ["(Domain|Webseiten|Seiten|Website)-?Name"],
            "Clicks": [
                "Klicks", 
                "(Seiten|Schaltflächen)klicks"
            ],
            "ScrollData": [
                "Scroll-?daten",
                "scrollen"
            ],
            "Clickstream": [
                "click( )?stream",
                "Klickverhalten",
                "Klicktracking"
            ],
            "PageResponseTime": ["Seiten?[- ]?Reaktionszeit", "Reaktionszeit.{0,20}(Seite|Website|Webseite)"],
            "ScreenResolution": ["(Bildschirm|Anzeige)auflösung"],
            "LocationData": [
                "Standort(-.{0,27})?(daten|information|bereich|berechtigung)",
                "Standort.{0,20}(?<!Meta)(Informationen|Daten|Diensten?)",
                "(Ihre[nm]|der).{0,15}Standort\\b",
                "Standort Ihre[sr]",
                "geogra(ph|f)ische[rn]? (Standort|Lage)",
                "Geolokalisierung"
            ],
            "LocationHistory": ["Standort(-.{0,27})?(verlauf|historie)"],
            "GPSData": [
                "GPS.{0,20}(daten|informationen|koordinaten)",
                "(daten|informationen|koordinaten).{0,20}GPS"
            ],
            "Coordinates": [
                "Koordinaten",
                "Längengrad",
                "Breitengrad"
            ],
            "AltitudeData": [
                "Höhendaten",
                "Erhöhungsdaten"
            ],
            "Timezone": ["Zeitzonen?"],
            "Address": [
                "(?<!Kontakt)(?<!angegebenen )(?<!untenstehende )(?<!genannten )(?<!mail[ -])(?<!E-mail[ -])(?<!mail)(?<!IP[ -])(?<!IP\"\\)-)(?<!IP-\\))(?<!MAC[ -])Adresse(?!.{0,30}besucht)",
                "Adressverarbeitung",
                "Adressdaten",
                "Ihre.{0,2}Postanschrift"
            ],
            "AreaCode": [
                "Ländercode",
                "PLZ",
                "Postleitzahl",
                "Standortbereichscode"
            ],
            "City": ["\\bStadt\\b"],
            "Region": [
                "^(?!.*(außerhalb|Regeln)).*Region(?!(speicher|ausgewählt|auswählen))\\b",
                "Bundesland",
                "Landkreis"
            ],
            "Country": [
                "\\bLand(es)?\\b"
            ], 
            "Language": [
                "Sprache",
                "Spracheinstellung(en)?",
                "Systemsprache"
            ],
            "Name": [
                "(?<!Paket)(?<!Geräte)(?<!Produkt)(?<!App)(?<!Vor)(?<!Nach)(?<!Nick)(?<!Spitz)(?<!Benutzer)(?<!Nutzer)(?<!Firmen)(?<!Halter)(?<!Kopplungs)(?<!Modell)(?<!im )(?<! dessen )(?<!Anzeige)(?<!Account)(?<!(unserem|eigenem) )(?<!in ihrem )namen?s?(angabe)?\\b(?!:)"
            ],
            "FirstName": ["Vor(-.{0,27})?name"],
            "LastName": [
                "Nachname",
                "Familienname"
            ],
            "Nickname": [
                "Nickname",
                "Spitzname"
            ],
            "DemographicData": ["demogra(ph|f)ische.{0,48}?(Daten|Informationen)"],
            "LifestyleInformation": [
                "(Lifestyle|Lebensstil|Lebensweise)[- ]?(information|daten)",
                "(Informationen|Daten).{0,20}(Lifestyle|Lebensstil|Lebensweise)"
            ],
            "NumberOfChildren": [
                "Kinder(an)?zahl",
                "(Anz)?zahl (der|Ihrer) Kinder"
            ],
            "PetInformation": [
                "Hautsier(informationen|daten)",
                "(Informationen|Daten) über.{0,20}Haustiere?",
            ],
            "NumberOfPets": [
                "Haustier(an)?zahl",
                "(Anz)?zahl (der|Ihrer) Haustiere"
            ],
            "Age": ["\\bAlter\\b"],
            "DateOfBirth": [
                "Geburtsdatum",
                "Geburtstag"
            ],
            "PhysicalBodyMetrics": [
                "Körpermaß"
            ],
            "Height": [
                "\\bGröße\\b",
                "Körpergröße"
            ],
            "Weight": [
                "\\bGewicht\\b",
                "Körpergewicht"
            ],
            "Gender": ["\\bGeschlecht\\b"],
            "Nationality": [
                "\\bNationalität\\b",
                "\\bStaatsbürgerschaft\\b",
                "\\bStaatsangehörigkeit\\b"
            ],
            "SexualOrientation": ["sexuelle[rn]? Orientierung"],
            "SexualLife": ["\\bSexualleben\\b"],
            "BiographicInformation": ["biografische (Informationen|Daten)"],
            "EducationalBackground": [
                "Bildungshintergrund",
                "Bildungsgrad",
                "Bildungsstand",
                "Bildungsniveau,"
            ],
            "EmploymentBackground": [
                "Ihr(es|en|em) Hintergrunds?"
                "(Hintergrund|Referenzen).{0,20}Bewerber",
                "(beruflichen?|Ihrer?) Referenz",
                "berufliche[rn]? Hinter(grund|gründe)",
                "Referenzdaten",
                "\\bBeruf\\b",
                "Referenzen.{0,20}Bewerber"
            ],
            "Employer": [
                "Arbeitgeber-(Daten|Details|Information)",
                "(Daten|Details|Information).{0,20}Arbeitgeber",
                "(Unternehmen|Firma).{0,20}sie arbeiten",
                "Ihr.{0,3}Arbeitgeber"
            ],
            "Ethnicity": [
                "Ethnien?",
                "ethnische[rn]? Herkunft"
            ],
            "PoliticalAffiliations": [
                "politische (Meinungen|Ansichten|Überzeugungen|Partei)\\b"
            ],
            "ReligiousBeliefs": ["religiöse[rn]?.{0,30}(Glaube|Ansichten|Überzeugung)"],
            "CriminalOffenses": [
                "(kriminelle|strafbare)[rn]? Handlungen",
                "kriminelle Vergangenheit",
            ],
            "CurriculumVitae": ["\\bLebenslauf\\b"],
            "CandidateInformation": ["Bewerber(-.{0,27})?(daten|information|pool)"],
            "TradeUnionMembership": ["\\bGewerkschaftsmitgliedschaft(en)?\\b"],
            "SocialAssistanceData": ["\\bsoziale[rn]? Hilfe"],
            "ContactInformation": [
                "(?<!weitere )(?<!die )(?<!aufgeführten )(?<!genannten )(?<!folgenden )(?<!angegebenen )(?<!entsprechenden )(?<!unter den )Kontakt(-.{0,27})?(informationen|info|daten|details)(?!.{0,30}(Verantwortlich|Referenzgeber|:))",
                "Kontaktdaten.{0,10}(Eltern|Erziehungsberechtigte)"
            ],
            "EmailAddress": [
                "E-Mail-?Adresse",
            ],
            "PhoneNumber": [
                "Telefonnummer",
                "Mobilfunknummer",
                "Mobiltelefonnummer",
                "Festnetznummer",
                "SMS(?!-Gateway)"
            ],
            "EmergencyData": ["Notfall(-.{0,27})?(Kontakt|Informationen|Daten)"],
            "FamilyInformation": [
                "Familien(-.{0,27})?(informationen|daten|details)",
                "information.{0,20}Familie",
                "Familienangehörige"
            ],
            "FriendsInformation": [
                "information.{0,30}Freunde",
            ],
            "IdentityInformation": [
                "Identitäts(-.{0,27})?(informationen|daten|details)",
                "Informationen über(.){0,20}Ihre Identität",
                "(physisch|physiologisch|genetisch|psychisch|wirtschaftlich|kulturell|sozial)en Identität"
            ],
            "GovernmentID": [
                "nationale Identifikationsnummer",
                "staatliche Ausweisnummer",
                "Regierungs-ID",
                "ausgestellte Identifikation"
            ],
            "Passport": ["\\b(Personal)?Ausweis(es)?\\b"],
            "DriverLicense": [
                "Führerschein"
            ],
            "TaxID": [
                "Steuernummer",
                "Steueridentifikationsnummer",
                "Steuer-ID"
            ],
            "SocialSecurityNumber": [
                "Sozialversicherungsnummer",
                "\\bSV-Nummer\\b"
            ],
            "UserInformation": [
                "((Be)?Nutzer|Besucher)(-.{0,27})?(information(en)?|daten|details)",
                "(Informationen|Daten|Details) des (Be)?Nutzers",
                "Informationen (über|des).{0,30}(Nutzer|Verbraucher)"
                ],
            "AccountData": [
                "\\b((Be)?nutzer)?Konto(-.{0,27})?(daten|informationen|details)",
                "(Daten|Informationen|Details) (des|Ihres|über Ihr|in Ihrem).{0,15} Kontos?\\b"
            ],
            "AccountAge": [
                "Kontoalter",
                "(Dauer des Bestehens|Bestehensdauer) des Kontos"
            ],
            "AccountNumber": [
                "\\b(?!(Kredit|Debit).*)Konto(?!.{0,27}(Kredit|Debit))nummer(?!.*(Kredit|Debit))"
            ],
            "AccountSettings": ["Kontoeinstellungen"],
            "SubscriptionData": ["^(?!.*(Beendigung|inaktive)).*(?<!-)\\bAbonnements"],
            "ProfileData": [
                "Profil(-.{0,27})?(daten|information|detail)",
                "(daten|information|detail) von Ihrem.{0,20}Profil",
                "sehen wir.{0,40}Profil ein"
            ],
            "ProfilePicture": ["Profilbild", "Profilfoto", "Avatar"],
            "Username": [
                "((Be)?nutzer|Konto|Profil|Anzeige)(?!(-ID|,))(-(?!.*,).{0,27})?name",
                "\\bPseudonym\\b"
            ],
            "SocialMediaDetails": [
                "(Details|Informationen)[^\\:]{0,40}soziale[rn]? (Medien|Netzwerke)"
            ],
            "ThirdPartyHandle": [
                "Drittanbieterkennung",
                "Kennung eines Dritt(en|anbieters)",
                "Social-Media-Kennung"
            ],
            "PermissionsData": [
                "\\bZugriffsrechte"
            ],
            "CameraPermissions": ["\\bKamera(zugriffsrechte|berechtigung)\\b"],
            "MicrophonePermissions": ["\\bMikrofon(zugriffsrechte|berechtigung)\\b"],
            "LocationPermissions": ["\\bStandort(zugriffsrechte|berechtigung)\\b"],
            "ContactsPermissions": ["\\bKontakt(zugriffsrechte|berechtigung)\\b"],
            "StoragePermissions": ["\\bSpeicher(zugriffsrechte|berechtigung)\\b"],
            "NotificationPermissions": ["\\bBenachrichtigungs(zugriffsrechte|berechtigung)\\b"],
            "Lighting": [
                "\\bBeleuchtung\\b",
                "\\bBelichtung\\b"
            ],
            "SensorData": ["Sensor(-.{0,27})?(daten|informationen)"],
            "EnvironmentalData": [
                "(Umwelt|Umgebungs)(-.{0,27})?(daten|informationen|details)",
                "Umwelteigenschaftenwert",
                "\\bECV\\b",
            ],
            "MotionData": [
                "(?<!Maus)Bewegungen",
                "\\bBewegungs(-.{0,27})?(daten|erkennung)\\b"
            ],
            "PresenceData": ["\\bPräsenz\\b"],
            "AmbientLightData": [
                "Umgebungslicht",
                "Lichtmesswert"
            ],
            "TemperatureData": ["\\bTemperatur"],
            "HumidityData": ["Luftfeuchtigkeit"],
            "MoistureData": ["\\bFeuchtigkeit"],
            "NoiseLevel": ["(Lärm|Geräusch)(level|niveau|pegel)"],
            "PrecipitationData": ["Niederschlag"],
            "WindData": ["\\bWind\\b"],
            "AirQualityData": ["Luftqualität"],
            "WaterReadings": ["Wasser(wert|stand|pegel)"],
            "CarbonMonoxideData": [
                "Kohlenstoffmonoxid",
                "\\bCO(?!-)\\b"
            ],
            "CarbonDioxideData": [
                "Kohlenstoffdioxid",
                "CO2"
            ],
            "SmokeData": ["\\bRauch"],
            "OutdoorData": ["outdoor-(Informationen|Daten|Details)", "Außen-?(Informationen|Daten|Details)"],
            "WeatherData": ["Wetter(daten|informationen|details)"],
            "WaterConsumptionData": ["Wasserverbrauch"],
            "WateringSchedule": ["Bewässerungsplan"],
            "GasConsumptionData": ["Gasverbrauch"],
            "DirtLevel": ["Verschmutzungsgrad"],
            "PresenceOfPeople": [
                "Anwesenheit.{0,20}(Leuten|Menschen|Personen)",
                "(erfasste|erkannte) (Leuten|Menschen|Personen)"
            ],
            "PresenceOfPets": ["Anwesentheit.{0,20}Haustier"],
            "CleaningHistory": ["Clean(er|ing)-(Verlauf|Historie)", "Reinigungs(verlauf|historie)"],
            "HeatingSchedule": ["Heiz(ungs)?plan"],
            "AppName": [
                "App(-(?!.*(Konto|ID)).{0,27})?name",
                "App(-(?!.*(Konto|ID)).{0,27})?Bezeichnung"
            ],
            "HomeName": ["Name.{0,20}(Zuhause|Heim(at)?)"],
            "FloorplanData": ["Grundriss"],
            "FloorType": ["Boden(-.{0,27})?(art|typ|belag)", "(Art|Typ|Belag).{0,20}Boden"],
            "ObjectData": [
                "Objekt(daten|information|detail)",
                "Art des Objekte?s",
                "Hindernis",
            ],
            "RoomName": ["Raum(name|bezeichnung)", "(Name|Bezeichnung).{0,20}Raum"],
            "OperatingPowerData": ["Betriebsleistung"],
            "EnergyConsumptionData": [
                "Energieverbrauch"
            ],
            "VoltageData": ["Spannungs(-.{0,27})?daten"],
            "EnergyProductivityData": ["Energieproduktivität"],
            "HealthData": [
                "(?<!öffentliche )(?<!öffentlichen )(Gesundheit)(?!status)"
            ],
            "HealthStatus": ["Gesundheits(.{0,27})?status"],
            "SleepData": [
                "Schlaf(daten|information)"
            ],
            "CoughingData": ["Husten"],
            "SnoringData": ["Schnarch(en)?"],
            "HeartRateData": [
                "Herzrate",
                "Puls"
            ],
            "StepCountData": [
                "Schrittzähler",
                "Schrittzahl",
            ],
            "BodyWaterData": ["Körperwasserdaten", "Körperflüssigkeit"],
            "FitnessGoals": ["(Fitness|Trainings|Übungs|Aktivitäts)ziel"],
            "FitnessChallengeResults": [
                "Fitness-Challenge Ergebnis",
                "persönlicher? Bestleistung"
            ],
            "PhysicalActivity": [
                "(physische|körperliche) (Aktivität|Bewegung)",
                "Workout-Aktivität",
            ],
            "WorkoutSummaries": ["\\bworkout Zusammenfassung"],
            "BloodPressure": ["Blutdruck"],
            "BloodSugar": ["Blutzucker(spiegel)?"],
            "BloodOxygenLevel": ["Blutsauerstoff", "SpO2"],
            "BMI": ["\\bBMI\\b", "body mass index"],
            "BodyFat": ["Körperfett"],
            "MuscleMass": ["Muskelmasse"],
            "ProteinContent": ["Proteingehalt"],
            "MetabolicInformation": ["metabolische (informationen|daten)"],
            "MenstrualCycleData": [
                "Menstruationszyklus",
                "(Perioden|Menstruations)(-.{0,27})?(daten|informationen)",
                "(Daten|Informationen|Details).{0,20}(Periode|Menstruation)"
            ],
            "BoneDensity": ["Knochendichte"],
            "DesignFiles": ["design(-.{0,27})?(dateien|dokument)"],
            "FinancialData": [
                "Finanz(-.{0,27})?daten",
                "persönliche[rn]? Finanzen"
            ],
            "IncomeData": ["Einkommen"],
            "FinancialStatus": [
                "Finanz(-.{0,27})?status",
                "wirtschaftliche[rn]? Situation"
            ],
            "CreditScore": ["Kreditwürdigkeit", "\\bBonität\\b"],
            "MembershipData": [
                "Mitglied(s|er)(daten|informationen|details|status)"
            ],
            "Maps": [
                "(?<!Kredit)(?<!SIM-)Karten\\b",
            ],
            "MapAreaNames": [
                "Kartenbereichsnamen",
                "Namen von Karten(bereiche|areale)"
            ],
            "MediaData": [
                "(Medien|Multimedia)(-.{0,27})?(daten|informationen)",
                "(Multi)?mediale (Daten|Dateien|Informationen|Details)"
            ],
            "AudioData": [
                "(Audio|Geräusch|Klang)(-.{0,27})?(daten|signale?|aufnahmen?|informationen|wiedergabe|dateien)"
            ],
            "VideoData": [
                "(video|film)(-.{0,27})?(daten|signal|aufnahme|datei|information|aufzeichnung)",
                "Aufnahmen.{0,20}Video",
                "Kamera(?=.*erfassen)",
                "(?<!Youtube-)(?<!diese )(?<!dieser )(?<!der )(?<!bestimmte )(?<!sich )Videos(?!.{0,40}Youtube)(?! bereit(zu)?stellen)"
            ],
            "ImageData": [
                "(Bild|Foto|Photo)(-.{0,27})?(daten|aufruf|aufnahme)",
                "Bilde(r|aufnahmen?)\\b",
                "(F|Ph)otos?\\b",
                "(F|Ph)otografien\\b",
                "Bildnisnutzung"
            ],
            "Screenshots": [
                "Screenshot",
                "Bildschirmfoto"
            ],
            "TouchData": ["\\bTouch(screen)?(-.{0,27})?(daten|informationen|interaktionen|signale)"],
            "VoiceCommands": ["Sprachbefehle?"],
            "VoiceCharacteristics": ["Stimm(en)?(merkmale|eigenschaften|charakteristik(en|a))"],
            "TextData": ["\\bText(-.{0,27})?(daten|information|inhalt|eingabe)"],
            "Drawings": [
                "(?<!Auf)Zeichnung(en)?",
                "Skizzen?",
                "Illustration(en)?",
            ],
            "Music": [
                "\\bMusic\\b",
                "Musik(-.{0,27})?(daten|informationen|dienst(e|en)?|dateien)"
            ],
            "OtherFileData": ["(andere|sonstige) (Dateien|Dateidaten)"],
            "TemporaryData": ["temporäre (daten|informationen)"],
            "TemporaryFiles": ["\\btemporäre datei(en)?\\b"],
            "Files": ["(?<!log-)(?<!text-)(?<!temporäre )\\bDateien\\b"],
            "GardenDesign": [
                "Garten(design|gestaltung)",
                "(Design|Gestaltung).{0,20}Garten"
            ],
            "PersonalBehaviorData": [
                "(Ihr(em)?|,) Verhalten\\b(?!.{0,40}(Webs|Gerät))",
                "Verhaltens(-.{0,27})?(daten|informationen|weise|muster)",
                "verhaltensbasiert",
                "Ihres (bisherigen )?Verhaltens",
                "Konsumverhalten"
            ],
            "HabitData": ["\\bGewohnheiten\\b"],
            "InterestData": [
                "(individuelle[sn]?|,) Interessen?\\b",
                "interessenbezogene (Daten|Informationen|Details)",
                "an denen Sie interessiert sind",
                "Interessenprofil"
            ],
            "HobbyData": [
                "\\bHobby\\b",
                "\\bHobbies\\b"
            ],
            "PurchaseMotivation": [
                "Kauf(motivation|grund|gründe)",
                "(Motivation|Grund|Gründe) für einen Kauf"
            ],
            "BiometricData": [
                "biometrische (Daten|informationen|details|Authentifizierung)"
            ],
            "FacialData": [
                "Gesichts(-.{0,27})?(daten|informationen|details)",
                "Gesichts(erkennung|scan)",
            ],
            "VoiceData": [
                "Sprach(-.{0,27})?(aufnahmen?|aufzeichnung(en)?|eingaben?|daten|informationen|details)"
            ],
            "FingerprintData": ["Fingerab(druck|drücke)"],
            "PersonDetectionInformation": [
                "Personenerkennungs(-.{0,27})?(daten|informationen)",
                "(Daten|Informationen) zur Personenerkennung"
            ],
            "Submissions": [
                "Ihre[rn]? Einreichung(en)?",
                "Einsendungen"
            ],
            "Feedback": [
                "((Be)?nutzer)?Feedback",
                "Rückmeldungen",
                "Vorschläge"
            ],
            "Comments": [
                "Kommentare?",
                "Kommentarfeld"
            ],
            "Opinions": [
                "(?<!politische )(?<!religiöse )(?<!philosophische )\\bMeinungen\\b",
                "(?<!politische )(?<!religiöse )(?<!philosophische )Ansichten",
                "Verhalten.{0,30}Einstellung"
            ],
            "Reviews": [
                "(Ihren?|Ihnen).{0,40}Bewertung(en)?(?!serinnerung)",
                "Rezension",
                "Produktbewertung"
            ],
            "ServicesData": [
                "(Informationen|Daten).{0,40}(Services|Dienste|Dienstleistungen).{0,30}Sie.{0,30}(genutzt|verwendet)",
                "(Daten|Informationen).{0,20}zur Nutzung.{0,40}(Dienste|Dienstleistungen|Service)",
                "Service(-.{0,27})?(daten|informationen)",
                "(Support|Kunden(service|dienst))-Tickets"
            ],
            "ServiceType": [
                "\\b(Dienst(leistungs)?|Service)(-.{0,27})?art\\b",
                "Art (der|des) (Dienstleistung|Dienstes|Service)"
            ],
            "CallRecords": [
                "Anrufaufzeichnungen",
                "Telefonanrufe",
                "\\b(Aufnahme|Aufzeichnung|aufgezeichnete).{0,30}(Anruf|Gespräch)"
            ],
            "Messages": [
                "(Chat-?|Gesprächs|SMS-|Ihre[rn]? |Direkt)Nachricht(en)?(?!verlauf)(?!empfänger)(?!dienst)(?!berichten)",
                "\\b(Details|Informationen).{0,20}(Nachrichten|Messenger|Messaging)(?!(verlauf|historie))",
                "Chat-Eingaben",
                
            ],
            "ChatHistory": [
                "Chat(-.{0,27})?(verlauf|historie|transkript|interaktion|protokoll|log)"
            ],
            "MessageDrafts": [
                "Nachrichtenentwürfe",
                "un(ge|ver)sendete Nachrichten",
                "Entwürfe von Nachrichten",
                "Entwurf einer Nachricht"
            ],
            "CommunicationRecords": [
                "Kommunikations(-.{0,27})?(Daten|Informationen|Details)",
                "Kommunikations(verlauf|historie)",
                "Aufzeichnungen.{0,20}Kunden(service|dienst)",
                "durchgeführte .{0,20}Kommunikation",
                "Kommunikation (speichern|gespeichert)",
                "Webinar.{0,20}Fragen"
            ],
            "RegistrationData": [
                "Registrierungs ?(-.{0,27})?(daten|information|detail)",
                "für die .{0,15}Registrierung",
                "Dienstregistrierungen"
            ],
            "ParticipationData": [
                "Teilnehmer(-.{0,27})?(daten|information|detail|liste)",
                "Teilnahme(-.{0,27})?(daten|information|detail|liste)",
                "(Daten|Informationen|Details).{0,10}Teilnehmer"
            ],
            "NumberOfParticipations": [
                "Anzahl.{0,10}(Teilnahmen|Teilnehmer)"
            ],
            "RewardHistory": [
                "(Belohnungs|Vergütungs)(verlauf|historie)",
                "Belohnung(.){0,20}(bekommen|überreicht|erhalten)",
            ],
            "FilmingEquipment": [
                "Filmausrüstung",
            ],
            "SecurityInformation": [
                "sicherheitsrelevante Informationen",
                "Sicherheits(-.{0,27})?(daten|informationen|details)\\b",
                "Sicherheitsanmeldedaten",
                "Sicherheitsstatus"
            ],
            "TamperStatus": [
                "Manipulationsstatus",
                "Manipulations (daten|information)"
            ],
            "SecurityQuestion": [
                "Sicherheitsfragen?",
            ],
            "CredentialData": [
                "(?<!Sicherheits)(Login|Anmelde|Authentifikations)(daten|informationen)",
            ],
            "SecurityPin": [
                "Sicherheits-PIN",
                "PIN-Code",
                "\\bPIN\\b"
            ],
            "Password": ["Passwort"],
            "AuthToken": [
                "Authentifizierungs-?token",
                "Auth Tokens?"
            ],
            "WrittenPermissions": [
                "Nachweis.{0,48}Erlaubnis",
                "unter(schrieben|zeichnet)(e|es|en|er)? Dokument",
                "(ausgefüllt|unterschrieben|unterzeichnet).{0,30}Ernennung zum bevollmächtigten",
                "schriftliche[rn]? (Vertretungsbefugnis|Berechtigung|Nachweis|Ermächtigung|Erlaubnis|Vollmacht)",
                "(Vertretungsbefugnis|Berechtigung|Erlaubnis|Ermächtigung|Vollmacht) (nachweisen|nachgewiesen)"
            ],
            "ProofOfIdentity": [
                "(Nachweis|Verifikation|Überprüfung|Beweis).{0,10}Identität",
                "Identitäts(nachweis|verifizierung|beleg|überprüfung|prüfung)",
                "\\bIdentität.{0,64}(nach(zu)?weisen|verifizieren|überprüfen|belegt)",
                "dass Sie der Verbraucher sind"
            ],
            "ConsentStatus": [
                "(Aufzeichnungen|Datensätze).{0,15}(Zustimmungen|Einwilligungen)",
                "Einwilligungserklärung",
                "Nutzer.{0,40}Einwilligung.{0,60}erteil(t|en)",
                "Einwilligung.{0,64}erteilen lassen",
                "(im Fall|falls).{0,30}erteilte[rn]? Einwilligung",
                "Einholung.{0,30}Einwilligung",
                "festlegen, welchen Verarbeitungen Sie zustimmen möchten",
                "per Häkchen"
            ],
            "EmployeeRecord": ["(Mitarbeiter|Personal|Angestellten)-?(akte|aufzeichnungen)"],
            "OrderData": [
                "Einkaufs(-.{0,27})?(details|informationen|daten)",
                "Bestell(-.{0,27})?(details|informationen|daten)",
                "^(?!.*(Verarbeiten|Bearbeitung|Lieferung|Verwaltung)).*(?<!in Ihrem Namen )(?<!B2B-)\\bBestellungen(?!.*aus(zu)?führen)(?!.*Support)",
                "(Daten|Information|Details|Dokumente).{0,40}(Bestellung|Einkäufe)"
                "Werten.{0,30}Bestellungen aus",
            ],
            "OrderHistory": [
                "(Einkaufs|kauf)(-.{0,27})?historie",
                "(Einkaufs|kauf)(-.{0,27})?verlauf",
                "Ihre bisherigen Bestellungen"
            ],
            "OrderNumber": ["Bestellnummer"],
            "InvoiceData": [
                "(?<!Ab)Rechnungs(-.{0,27})?(daten|informationen|details|datensätze)", # Abrechnungs.. -> BillingData
                "Buchungs(-.{0,27})?beleg"
            ],
            "PurchaseDate": [
                "Kauf(-.{0,27})?datum",
                "Datum.{0,30}Kauf"
            ],
            "PaymentData": ["Zahlungs(-.{0,27})?(daten|informationen|details|aufzeichnungen|datensätze)"],
            "PaymentAmount": [
                "(Zahlungs|Kaufs?|Transaktions)(-.{0,27})?(betrag|preis)",
                "Kaufs?(details|daten|information).{0,40}Preis"
            ],
            "PaymentMethod": ["Zahlungs(-.{0,27})?(methode|art)"],
            "BillingData": ["Abrechnungs(-.{0,27})?(daten|informationen|details|datensätze)"],
            "BillingReceipts": [
                "(Rechnungs|Abrechnungs|Zahlungs|Kauf)beleg"
            ],
            "TransactionData": [
                "Transaktions(-.{0,27})?(daten|informationen|details)"
            ],
            "TransactionHistory": ["Transaktions(-.{0,27})?(historie|verlauf)"],
            "InAppTransactions": ["in(-| )app-(Transaktionen|Käufe)"],
            "ShippingInformation": ["(Liefer(ungs|anten)?|Versand)(-.{0,27})?(information|daten)"],
            "CommercialInformation": ["kommerzielle(.){0,20}(informationen|daten|details)"],
            "CreditCardInformation": [
                "Kreditkarten(-.{0,27}| )?(informationen|daten|details)"
            ],
            "CreditCardNumber": [
                "Kredit(karten)?(-.{0,27})?nummer"
            ],
            "DebitCardInformation": [
                "debit(-.{0,27})?Karten(information|daten|details|nummer)"
            ],
            "BankAccountInformation": [
                "Bankkonto(informationen|daten|details)"
            ],
            "BankAccountNumber": [
                "(?<!-)(Konto|Bank)(-.{0,27})?nummer",
                "IBAN"
            ],
            "BankHolderName": [
                "Namen?.{0,10}Kontoinhabers",
                "Konto(-.{0,27})?inhabername"
            ],
            "PaymentCardInformation": [
                "Zahlungs(-.{0,27})?Karten(information|daten|details|nummer)",
                "Kartendaten während der Übertragung"
            ],
            "PaymentCardNumber": ["(Bezahl|Zahlungs)kartennummer"],
            "CardholderData": [
                "Karteninhaber(daten|informationen|details)",
                "Name.{0,20}Karteninhaber"
            ],
            "CardExpiryDate": [
                "Ablaufdatum der Karte",
                "Karten[- ]?(-.{0,27})?ablaufdatum"
            ],
            "CustomerList": ["Kundenliste"],
            "CustomerRecords": [
                "Kunden(-.{0,27})?(aufzeichnungen|aufnahmen|daten|informationen|details|datenbank)"
            ],
            "ApplicationDocuments": [
                "Bewerbungs(-.{0,27})?(daten|informationen|dokumente|unterlagen|formular)",
                "Unterlagen.{0,40}Bewerbung",
                "(?<!Status )(?<!rund um )(?<!auf )(Ihre[rn]?|eine|die|erfolgreiche).{0,5} Bewerbung(en)?\\b",
                "(?<!personenbezogene) Daten für (einen?|Ihren?|den|das) (Bewerbung(sprozess)|Beschäftigungsverhältnisses)"
            ],
            "AppInformation": [
                "App[ -]?(?<!Nutzungs)(Daten|Informationen|Details|Herkunft)",
                "(Daten|Informationen|Details) (von|über).{0,20}App(?!-)"
            ],
            "AppConfiguration": [
                "App-(Konfiguration|Einstellung)"
            ],
            "Qualifications": ["Qualifikationen"],
            "CallStatus": ["Anrufstatus"],
            "AmbientSound": ["Hintergrundgeräusche?"],
            "UserGeneratedContent": [
                "(Be)?Nutzerinhalte",
                "Beiträge für die Community",
                "^(?!.*(Forum|Foren|Gefällt[- ]mir)).*(Ihr|Ihre|Ihren|Ihnen)(?<!in einem Forum) (Beitrag|Beiträge)(?!.*(Forum|Foren))(?!.*(Gefällt[- ]mir))",
                "Beitrag öffentlich (posten|machen)",
                "^(?!.*(Forum|Foren)).*(gepostete|veröffentlichte|öffentliche).{0,5} (Inhalte|Beiträge)(?!.*(Forum|Foren))",
                ", Beiträge"
            ],
            "HistoricalDataRecord": [
                "(historische|geschichtliche)[rn]? (Daten|Informationen|Details|Aufzeichnungen)",
                "Geschichts(-.{0,27})?(daten|information|details)"
            ],
            "ForumPosts": [
                "(?<!per) Posts?\\b",
                "(Beitrag|Beiträge).{0,48}(Forum|Foren)",
                "(Forum|Foren).{0,48}(Beitrag|Beiträge)"
            ],
            "Testimonial": [
                "\\btestimonial\\b",
            ],
            "Ratings": ["\\b(Sterne|Punkte)bewertung\\b", "Rating"], 
            "SharedContent": [
                "(geteilte|freigegebene)[rn]? (Inhalt|Dokument)",
                "Freigaben",
                "(Inhalte|Dokumente).{0,30}teilen"
            ],
            "ListedItems": ["(gelisteter?|aufgeführter?) (Artikel|Sachen|Waren|Produkte)"],
            "Likes": [
                "\\blikes\\b",
                "Gefällt[- ]mir"
            ],
            "Follows": ["Follower"],
            "Contacts": ["\\bKontakte\\b"],
            "ContentUseHistory": [
                "Nutzungs(-.{0,27})?(verlauf|historie)",
                "Nutzungs(-.{0,27})?protokoll",
                "Inhaltsnutzung"
            ],
            "VirusDefinitions": [
                "Virendefinitionslisten",
                "Virusdefinition"
            ],
            "DeviceAutomations": ["Geräte(-.{0,27})?automatisierung"],
            "ContestData": ["Wettbewerbs(-.{0,27})?(daten|informationen|details|hinweise|einträge)"],
            "BusinessInformation": [
                "\\bGeschäfts(-.{0,27})?(informationen|daten|details)\\b",
                "geschäftlichen? (Daten|Informationen|Details)"
            ],
            "CompanyInformation": [
                "\\bUnternehmens(-.{0,27})?(informationen|daten|details)\\b",
                "(?<!Name )(?<!Namen )Ihr.{0,2} Unternehmens?\\b",
            ],
            "CompanyName": [
                "(Unternehmens|Firmen)(-.{0,27})?name",
                "Name (des|Ihres) Unternehmens"
            ],
            "NumberOfEmployees": ["\\bAnzahl.{0,10}Mitarbeiter\\b", "\\bMitarbeiter(an)?zahl\\b"],
            "BusinessModel": ["Ihr.{0,2} \\bGeschäfts(-.{0,27})?modell\\b"],
            "IndividualDeviceUsage": [
                "\\b(Wie viele|welche|wann|wie).{0,32}(Gerät|Produkt).{0,32}(verbunden|verbinden|verwendet|verwenden)"
            ],
            "CurrentData": [
                "Strom(stärke)?(-.{0,27})?daten",
                "Stärke des (elektrischen )?Stroms"
            ],
            "PlatformType": [
                "verwendete Plattform",
                "Plattform(-.{0,27})?art",
                "und Plattform"
            ],
            "InteractionData": [
                "Interaktion.{0,64}(social-media|Plug-?in|Service|Dienst)",
                "Interaktions(-.{0,27})?(protokoll|daten|information|details)",
                "(Mitteilung|Nachricht|Plug-?in|Dienst(?!(leister|anbieter))|Mail).{0,64}(interagieren|interagiert|(?<!zu )(?<!beim )öffnen)",
                "Interaktionen mit uns\\b",
                "ob (Sie|Einzelpersonen).{0,24}(Nachrichten|E-Mails|Mitteilungen)(öffnen|lesen|anklicken)",
                "Softwareinteraktion",
                "durchgeführte Interaktion"
            ],
            "Title": [
                "Titel",
                "akademische[rnm]? Grad"
            ],
            "FaxNumber": ["Fax(-.{0,27})?nummer"],
            "PersonalAssistants": [
                "persönliche[nrm]? Assistenten"
            ],
            "FontType": [
                "(Font|Schrift)(-.{0,27})?art",
                "Fonts?"
            ],
            "Badges": ["Badges"],
            "Favorites": ["Favoriten"],
            "BirthCertificate": ["Geburtsurkunde"],
            "BrowserExtensions": [
                "^(?!.*Signale).*Browsererweiterung",
                "Browser-Plug-?Ins?(?! herunterladen)",
                "Browser-Add-On"
            ],
            "ContentInteractions": [
                "((?<!Seiten)Inhalt|Content|Video|Werbung|Werbeanzeigen|Anzeige).{0,64}(interagieren|an(ge)?sehen|angeklickt|abgespielt|abspielen)",
                "(Interaktion|interagieren|Abspielen).{0,32}((?<!Seiten)Inhalt|Content|Video|Werbung|Werbeanzeigen|Anzeige)"
            ],
            "AccessData": [
                "(Zugriff|Zugang)s(-.{0,27})?daten",
                "(Zugriff|Zu(gang|gänge))(?=.*(auswerten|erheben|analysiere))"
            ],
            "PersonalID": ["persönliche (ID|Kennung)"],
            "OnlineID": ["online[ -](ID\\b|Kennung)"],
            "BankData": ["Bank(?!.*Karte).{0,27}(daten|informationen|details)"],
            "PurchaseData": [
                "Kauf(-.{0,27})?(daten|informationen|details|verhalten)",
                "\\bKauf.{0,48}(tätigen|abschließen|abgeschlossen)",
                "\\b(Daten|Information|Details).{0,64}(für|über).{0,32}(?<!Ver|Ein)(Kauf|Käufe|gekauft)",
                "(Daten|Information|Details).{0,20}(gekauftes|erworbene)s?(Produkt|Gerät|Hardware|Software)"
            ],
            "InternetData": ["(Internet|Online)(-.{0,27})?(daten|information|details)"],
            "DisabilityData": ["Daten.{0,20}Behinderung"],
            "GeneticData": [
                "genetische (Daten|Informationen|Details|Merkmale|Marker)"
            ],
            "PhilosophicalBeliefs": ["philosophische.{0,24}(Überzeugungen|Ansichten)"],
            "MetaData": ["Meta(-.{0,27})?daten", "Meta Data"],
            "CrashData": [
                "Crash-Bericht",
                "Absturz(-.{0,27})?(daten|informationen|details|Bericht)",
                "\\b(Absturz|Abstürze)\\b",
            ],
            "InferenceData": ["(Schluss|Inferenz)(-.{0,27})?daten"],
            "MartialStatus": ["Familienstand"]
        }
    ),
    track_conv=AttributePattern.from_dict(
        {
            "Cookies": ["\\bCookie(s)?\\b"],
            "WebBeacons": [
                "\\bbeacon(s)?\\b", "Web[- ]?Beacons"],
            "TrackingPixel": [
                "\\btracking pixel(s)?\\b",
                "\\bPixel\\b",
                "\\bZählpixel\\b"
            ],
            "ClearGIF": [
                "\\bClear[- ]GIFs?\\b",
                "\\bone-pixel gifs\\b"
            ],
            "SDK": ["\\bSDKs?(?!-Version)\\b"],
            "SimilarTechnologies": [
                "\\b(ähnliche|verwandte|vergleichbare)n? Technologien?\\b",
                "\\banderen? Identifizierungstechnologien\\b",
                "\\b(anderen?|verwandten?) Tracking-Technologien\\b"
            ],
        }
    ),
    method_source=AttributePattern.from_dict(
        {
            "UserProvided": [
                "(?<!über )(?<!ob )Sie(?!.*(nicht|freiwillig|entscheiden)).{0,80}zur Verfügung (gestellt (haben|werden)|(zu )?stellen)\\b",
                "stellen Sie(?!.*(nicht|freiwillig|entscheiden)).{0,80}zur Verfügung",
                "\\bnach eigenem Ermessen\\b",
                "\\bAngabe(?=.{0,40}ihre[rsn] .{0,20}(Daten|Informationen|Anliegen|Namen))\\b",
                "\\b(müssen|können|sollten) Sie (?=.*(angeben|einreichen|übermitteln|bereitstellen|mitteilen))\\b",
                "\\bSie (müssen|können|sollten)(?=.*(angeben|einreichen|übermitteln|bereitstellen|mitteilen|ausfüllen|nachweisen))\\b",
                "\\bSie (?=.*(angeben|einreichen|übermitteln|bereitstellen|bereitgestellt|mitteilen|geteilt|uns geben))\\b",
                "\\b^(?=.*(geben|reichen|übermitteln)).*Sie\\b",
                "\\bvon Ihnen(?=.*(angegeben(e|en|er)?|eingereicht(e|en|er)?|übermittelt(e|en|er)?|bereitgestellt(e|en|er)?|stammen|weitergegeben|mitgeteilt))\\b",
                "(wenn|vom).{0,20}Nutzer.{0,50}(übergeben|weitergegeben)",
                "direkt von Ihnen"
            ],
            "AutomaticallyCollected": [
                "(automatisiert|automatisch).{0,80}(verarbeitet|erhoben|erfass(t|te|en)|sammeln)",
                "(übermittelt|erhalten|erfassen).{0,120}automatisch (?!(gelöscht|gespeichert))"
            ],
            "ThirdPartyProvided": [
                "(Daten|Informationen|Details).{0,48}(von|aus|über) (diese.{0,2} )?(Drittpartei(en)?|Dritte[rn]?|Drittanbietern?|Drittpartnern?|Werbetreibenden|anderer Nutzer|Anbieter|Veranstaltern|(anderen?|externen?) Quellen).{0,80}(?<!nicht )(erhalten|bekommen|erwerben|erfassen|mitteilt|zur Verfügung)",
                "((erhalten|bekommen|erwerben|erfassen))(?=.*(Daten|Informationen|Details)).*(Drittpartei(en)?|Dritte[rn]?|Drittanbietern?|Veranstaltern|(anderen?|externen?) Quellen)",
                "aus Quellen von Drittanbietern",
                "Informationen.{0,20}(anderen|externen) Quellen",
                "(Daten|Informationen) über (?=.*einholen)",
                "wir.{0,30}(Daten|Informationen|Details).{0,60}(von|durch|über).{0,40}erhalten",
                "(von|vom).{0,20}(Anbieter|Werbetreibenden|Dienstleister|Dritten).{0,30}(erhalten|bekommen)",
                "die uns (andere|dritte) zur Verfügung stellen"
            ],
            "DataCombination": [
                "\\bkombinier(te?|en)\\b",
                "Kreier(ung|en)",
                "\\bleiten.{0,70}ab\\b",
                "abgeleitet",
                "ab(zu)?leiten",
                "verbinden.{0,30}(Daten|Informationen)",
                "(Daten|Informationen).{0,30}Schlussfolgerungen",
                "Erschlossene Daten"
            ],
            "AIAnalysis": [
                "(durch|mithilfe|auf Basis von)(?=.{0,30}\\b(Künstlicher Intelligenz|KI|AI|machine learning|ML)\\b(?!-Chat))"
            ],
            "SocialMedia": [
                "social media(?!(- )Anbieter)",
                "(?<!Anbieter von )(?<!Anbietern von )soziale[rn]? Medien\\b",
                "\\bsoziales Medium\\b",
                "(?<!Anbieter von )(?<!Anbietern von )soziale[rnms]? Netzwerk(e|en)?\\b",
                "Fan(seite|page)"
            ],
            "IndirectCollection": [
                "\\bindirekt(?=.*(gesammelt|erhalten|bekommen|erfasst))",
                "(Informationen|Daten|Details).{0,90}nicht.{0,20}(angefordert|gesammelt)"
            ],
            "Public": [
                "(Daten|Informationen|Details)(?=.*veröffentlichen)",
                "öffentlich (?=.*(posten|gepostet|bereitstellen|bereitgestellt|machen|gemacht|teilen|geteilten|veröffentlicht|bekannt (geben|gegeben)))",
                "öffentlich(e|er|en)?.{0,20}(Quellen|Bekanntmachungen)"
            ],
            "Interaction": [
                "\\bInteraktion(en)?\\b",
                "(wenn|während).{0,80}(Webseite|Website|Seite).{0,80}(besuchen)",
                "wenn Sie (?=.*interagieren)",
                "(bei der|durch) Nutzung.{0,50}(erhoben|gesammelt|erhalten|entstanden)"
            ],
            "VoluntaryProvided": [
                "\\bfreiwillig\\b",
                "Sie (können|endscheiden)(?=.*(Angaben|Daten|Informationen|Details))"
                "\\bvoluntary\\b",
                "\\byou (choose|elect|opt) to\\b",
                "\\boptional\\b",
                "(?=.*\\b(right to choose|not obliged))(?=.*(provide|share|submit|give|upload))",
            ],
            "Buying": [
                "durch.{0,30}Kauf"
                "\\bwir\\b(?=.*\\b(kaufen|erwerben)\\b)(?=.*\\b(daten|information)\\b)"
            ],
            "Feedback": [
                "\\bFeedback\\b",
                "Befragung",
                "Frage(bogen|bögen)"
            ],
            "Tracking": [
                "\\bVerfolgung",
                "Cookie",
                "Tracking"
            ],
        }
    ),
    descriptive=AttributePattern.from_dict(
        {
            "ServiceProvider": [
                "(?<!Cloud)(?<!(KI|AI))(?<!Analyse)(?<!Internet)(?<!Werbe)(?<!Newsletter)(?<!Backend)(?<!Inhalts)(?<!-)\\b(Online-?|Offline-?)?Dienst.{0,50}Anbieter",
                "(?<!Cloud)(?<!(KI|AI))(?<!Analyse)(?<!Internet)(?<!Werbe)(?<!Newsletter)(?<!Backend)(?<!Inhalts)(?<!-)\\bDienstleister",
                "^(?!.*(cloud|web|so[cz]ial|analyse).*(Anbieter|Datenverarbeiter)[sn]?).*(Anbieter|Datenverarbeiter)[sn]?(?!:)\\b",
                "(?<!-)\\bDienste.{0,20}Dritte[rn]",
                "\\bAuftragnehmern?\\b",
                "Drittanbieterplattform",
                "(?<!-)Server.{0,30}Anbieter"
            ],
            "InsuranceCompany": ["Versicherungsunternehmen"],
            "Employer": ["Arbeitgeber"],
            "Manufacturer": ["\\bHersteller"],
            "PaymentServiceProvider": [
                "Zahlungs(-.{0,27})?dienst(leister[sn]?)?",
                "Zahlungsinstitut",
                "Zahlungsabwickl(er|ungsdienst)"
            ],
            "CreditInstitution": [
                "Kredit(auskunfteien|institut|anbieter|verlängerung)",
                "Kredit-Auskunfteien"
            ],
            "InternetServiceProvider": [
                "\\b(Internet)?Provider\\b",
                "\\bisp\\b",
            ],
            "TransportCompany": [
                "(shipping|delivery|logistic|freight)(.){0,64}(company|service|provider|partner)",
                "(Paket|Transport)(dienst|unternehmen|partner|zusteller)"
            ],
            "FulfillmentCenter": [
                "(Logistik|fulfillment)-?(Center|Zentrum|Service|Partner|Dienst)"
            ],
            "HostingProvider": [
                "Hostingdienstleist(er|ung)",
                "Dienste?.{0,10}Hosting",
                "Hosting.{0,20}(Network|Netzwerk)",
                "Web.{0,20}Hosting"
            ],
            "StorageServiceProvider": [
                "Speicherdienst(leist(er|ung)|anbieter)",
                "Daten(center|zentrum)"
            ],
            "SocialMediaProvider": [
                "Social-?Media-?(Plattformen?|Schaltflächen?|Anbietern?|Diensten?|Funktion(en)?|PlugIns|(Web)?seiten|Partner|Dienstleister|Netzwerk)",
                "soziale[rns]? (Netzwerk(e|en)?|Medien)",
                "\\bsoziales Netzwerkkonto\\b",
                "Social Plugins"
            ],
            "Vendor": [
                "(Einzel)?Händler",
                "Verkäufer"
            ],
            "Supplier": [
                "\\bLieferant(en)?\\b",
                "Versand(dienstleister|unternehmen)",
                "Liefer(partner|dienst)",
                "Zulieferer"
            ],
            "Customer": [
                "(?<!-)(?<!Kommunikation mit )(?<!an )(?<!unsere )(?<!unsere )\\bKunden?\\b(?!-)(?!.*Support)",
                "^(?!.*poten[tz]iell).*\\bKäufern?\\b(?!.*(Investor|Unternehmen))",
                "Konsument"
            ],
            "SubContractors": [
                "\\bUnterauftragnehmer\\b",
                "Subunternehmer"
            ],
            "Adviser": [
                "Beratern?\\b"
            ],
            "Buyer/Investor": [
                "(?=.*poten[tz]ielle).*Käufer",
                "(Investor|Erwerber|Nachfolgeunternehmen)",
                "(Fusion|Zusammenschluss|Übernahme|Eigentümerwechsel)",
                "(Käufer|(ver)?kauf)(?=.*Unternehmen)",
                "(Vermögen|Anteile?|Unternehmen|Geschäfte?)\\b(?=.*(veräußer|verkauf|übertragen))"
            ],
            "RatingPlatform": [
                "Bewertungsplattform"
            ],
            "RecruitmentPlatform": [
                "Rekrutierungs(plattform|portal)"
            ],
            "MarketingAffiliate": [
                "Marketing-?Partner"
            ],
            "AdvertisingAgency": [
                "\\bWerbe(agentur|treibende)",
                "Marketing-Drittanbieter",
                "(Drittanbieter|Dienstleister|Partei)(?=.*Werbung)",
            ],
            "AdvertisingNetwork": [
                "Werbenetzwerk"
            ],
            "AdvertisingPartner": [
                "\\bWerbepartnern?\\b",
                "\\bMarketing[- ]?Partnern?\\b",
            ],
            "SoftwareDeveloper": [
                "Softwareentwickler",
                "App-Entwickler"
            ],
            "CustomerServiceProvider": [
                "\\bKunden(dienst|support)(anbietern?|partnern?|service(es)?)\\b",
                "(Kundenservice|Support)-(Agent|Plattform)",
                "Kundenhotline",
                "Kundenservice-Agent"
            ],
            "BusinessPartner": ["Geschäftspartnern?"],
            "CloudService": [
                "Cloud-(service-)?(Anbieter|Dienstleister|Dienstanbieter|Dienst)",
                "cloudbasierte.{0,20}(Dienste|Anwendungen)",
                "Cloud[- ]Server.{0,24}Anbieter",
                "Cloud-Service"
            ],
            "AnalyticsService": [
                "Analyse-?(service|dienst|anbieter|dienstanbieter|plattform|tool)",
                "Analyse-.{0,20}(service|dienst|anbieter|dienstanbieter|plattform|tool)",
                "Anbieter von Analysen"
            ],
            "CompatibleApp": [
                "Drittanbieter-Apps",
                "App.{0,30}(von|eines) Drittanbieter",
                "kompatib(el|le).{0,30}App"
            ],
            "CompatibleDevice": [
                "Drittanbieter-(Gerät|Produkt)",
                "(Gerät|Produkt).{0,30}(von|eines) Drittanbieter",
                "kompatib(el|le).{0,30}(Gerät|Produkt)"
            ],
            "CompatibleService": [
                "(Dienst|Dienstleistung|Service).{0,30}(von|eines) Drittanbieter(?!.*betrieben)",
                "kompatib(el|le).{0,30}(Dienst|Dienstleistung|Service)"
            ],
            "PartnerIntegrations": [
                "Partnerintegration",
                "Integration.{0,30}(Geräte|Produkte|Dienst|Service)"
            ],
            "ExternalAccount": [
                "externes? (((Be)?nutzer)?Kont(o|en))",
                "(Affiliate|Affiliations|affiliierten|Partner)[- ]?((Be)?nutzer)?Kont(o|en)",
                "Konto.{0,30}Drittanbieter"
            ],
            "ThirdPartySite": [
                "Drittanbieter-(Site|Website|Seite|Webseite)",
                "Drittseite",
                "Web(seiten?|sites?) (anderer|externer) (Anbieter|Dienstleister)",
                "Web(seite|site).{0,50}Dritt.{0,30}betrieben"
            ],
            "ThirdPartyStore": [
                "externe[rnm]? (App|Software|Online)[- ](store|Markt|Laden)",
                "Markt(platz|plätze) Dritter"
            ],
            "DataPartner": ["Datenpartner"],
            "FraudPreventionService": [
                "Betrugs(prävention|erkennung|schutz)s?(service|dienst|partner|zweck|prüfung|erkennung)",
                "Dienst (prüft|erkennt|erfasst|untersucht)(?=.*(Schad(en)?|missbr(auch|äuchlich)|betrug))"
            ],
            "SmartAssistant": ["smart[- ]assistant"],
            "VoiceAssistant": ["Sprachassistent"],
            "AiServices": [
                "(KI|machine learning|ML|Modell)[- ]?(Dienst|Anbieter|Service|Assistent|Dritt)"
            ],
            "ContentProvider": [
                "Inhalt[se]?anbieter",
                "Anbieter von Inhalten",
            ],
            "Affiliates": [
                "verbundenen? (Unternehmen|Geschäftsbereiche|Gesellschaften|Partner)",
                "Affiliate(?!-)",
                "Schwestergesellschaft"
            ],
            "ParentCompany": ["Mutter(konzern|gesellschaft)"],
            "Subsidiaries": ["\\bTochter(konzern|unternehmen|gesellschaften)\\b"],
            "ContentDeliveryNetwork": [
                "\\bcdn\\b",
                "content[- ]delivery[- ]network",
            ],
            "NetworkOperator": [
                "Netzwerkbetreib(er|ende)"
            ],
            "EcosystemCompanies": [
                "(Öko(system)?|Umwelt)[- ]?(Unternehmen|Firm(a|en)|konzern|gesellschaft)"
            ],
            "Partners": [
                "(Vertrags|Kanal|Dritt)partnern",  
                "(?<!B2B-)\\bPartnern?\\b(?!-)",
                "Partnerbeziehung",
                "Partner(unternehmen|organisationen)"
            ],
            "Accountant": [
                "\\bWirtschaftsprüfern?",
                "\\bBuchhaltern?",
            ],
            "Auditors": ["\\bAuditor(en)?\\b"],
            "Lawyers": [
                "Rechtsanwalt",
                "Rechtsanwälten?",
                "Anwalt",
                "Anwälten?"
            ],
            "DataController": [
                "Datenverantwortliche[rn]?"
            ],
            "AttributionCompanies": [
                "(Attributions|Zurechnungs)unternehmen"
            ],
            "ThirdPartyEmployee": [
                "(Angestellter|Mitarbeiter) einer Drittpartei",
                "externer (Angestellter|Mitarbeiter)"
            ],
            "BackupService": ["\\bBackup[- ]?(Service|Dienstleister|Partner|Anbieter)"],
            "CustomerRelationshipManagement": [
                "\\bcrm\\b",
                "Kundenbeziehungsmanagement",
            ],
            "ECommercePlatform": [
                "E-Commerce-Plattform",
                "Handelsplattform"
            ],
            "EmailServiceProvider": ["E-Mail[- ](Anbieter|Dienst(leister|anbieter)|Provider)"],
            "SecurityServiceProvider": [
                "Sicherheits(-.{0,27})?(service|dienst|unternehmen)",
                "(Drittanbieter|Dienstleister).{0,30}Sicherheit"
            ],
            "IdentityVerificationService": [
                "Identitätsprüfungs(service|dienst)",
                "(Service|Dienst).{0,20}(Identitätsprüfung|Prüfung.{0,10}Identität)"
            ],
            "Insurer": [
                "Versicherungen",
                "Versicherer"
            ],
            "SmartHomePlatform": ["Smart-Home-(Plattform|Anbieter|Dienst)"],
            "DataProcessor": [
                "Datenmanagementplattformen",
                "Auftragsverarbeiter",
                "Datenaggregator"
            ],
            "Sponsor": ["Sponsor"],
            "Promoter": ["Promoter"],
            "EventOrganiser": [
                "Veranstalter",
                "Organisator(en|s)?\\b"
            ],
            "Successor": ["Nachfolger"],
            "Banks": ["\\bBank(en)?\\b(?!-)"],
        }
    ),
    official=AttributePattern.from_dict(
        {
            "SecurityAuthorities": [
                "Rettungs(dienst|käfte)",
                "Sicherheits(behörden|kräfte)",
                "(Militär|Bundeswehr)",
                "Polizei",
                "Feuerwehr"
                ],
            "Court": [
                "Gerichte?",
                "Gerichtsverfahren"
            ],
            "Tribunal": ["Tribunal(e|en)?"],
            "LawEnforcement": [
                "\\bStraf(verfolgung|vollzug)sbehörden\\b",
                "Strafverfolgung",
                "\\bStraftaten\\b(?!.*Ermittlungsbehörden)",
                "Verletzung(?=.*(Recht|Gesetz|Verordnung))",
                "Zollbehörden"
            ],
            "EmergencyServices": [
                "\\bNot(fall)?dienste?\\b",
                "Katastrophenschutz"
            ],
            "MunicipalAuthorities": [
                "Kommunalbehörde",
                "kommunale[rn]? (Amt|Ämter|Behörde|Stelle)"
            ],
            "RegulatoryAgencies": [
                "(?<!Finanz)(Aufsichts|Regulierungs)behörde",
                "Regulierungsbefugnisse",
                "Datenschutzaufsicht"
            ],
            "CertificationBody": [
                "Zertifizierungsstelle",
                "\\bTÜV\\b",
            ],
            "GovernmentAgencies": [
                "\\bRegierungs(-.{0,27})?(behörden|stellen)\\b",
                "\\bBehörden?\\b",
                "behördlich",
                "\\bRegierungen\\b",
                "staatliche (Einrichtungen|Stellen)",
                "nationale Verteidigung"
            ],
            "PublicHealthAuthorities": [
                "Gesundheits(behörde|amt)"
            ],
            "ChildProtectionServices": [
                "Kinderschutz(dienst|behörde)",
                "Kinder- und Jugend(amt|hilfe)",
            ],
            "ImmigrationAuthorities": [
                "Einwanderungsbehörde",
                "BAMF",
                "Bundesamt für Migrations und Flüchtlinge"
            ],
            "TaxAuthorities": ["\\b(Steuer|Finanz)(-.{0,27})?(amt|behörden?)"],
            "FinancialRegulators": [
                "Finanzaufsichtsbehörde"
            ],
            "InvestigationAuthorities":[
                "Ermittlungsbehörden?",
                "Staatsanwaltschaft",
                "Justizbehörden?"
            ]
        }
    ),
    country=AttributePattern.from_dict(
        {
            "North America": [
                "\\bNordamerika\\b",
                "\\bNord-.{0,20}amerika"
            ],
            "South America": [
                "\\bSüdamerika\\b",
                "\\bSüd-.{0,20}amerika"
            ],
            "Central America": [
                "\\b(Zentral|Mittel)amerika\\b",
                "(Zentral|Mittel)-.{0,20}amerika"
            ],
            "Europe": ["\\bEuropas?\\b"],
            "European Union": [
                "\\bEuropäischen? Union\\b",
                "\\bEU(-(Mitgliedstaat.{0,2})|DSGVO)?(?!-)\\b"
            ],
            "EEA": [
                "\\bEWR\\b",
                "\\bEuropäische[rn] Wirtschaftsraums?\\b"
            ],
            "Asia": ["\\bAsiens?\\b"],
            "Africa": ["\\bAfrikas?\\b"],
            "Oceania": ["\\bOzeaniens?\\b"],
            "Near East": ["Nahe[rn]? Osten"],
            "Middle East": ["\\bMittlere[rn] Ostens?\\b"],
            "International": [
                "\\binternational(es|en| übertragen)",
                "\\bweltweit",
                "\\bglobal",
                "\\bübersee\\b",
                "Alle Länder\\b"
            ],
            "ResidenceState": [
                "Ihr.{0,2} Wohnsitz",
                "in dem sie (sich befinden|wohnen|leben)",
                "\\bIhre[srnm] (Land|Stadt|Standort|Provinz|Territorium|Region|Gerichtsbarkeit)",
                "(an ausländische)|(ins Ausland)",
                "ausgewählt.{0,2} Land",
                "ansässigen Landes"
            ],
            "CountriesOutsideOf": [
                "\\banderen? (Ländern|Gebieten|Staaten)\\b",
                "\\baußerhalb (Ihrer|Ihres|des|der|von) \\b",
                "\\bnicht-EU\\b",
                "Landes abweichen",
                "(an ausländische)|(ins Ausland)"
            ],
            "AndOther": [
                "andere Länder",
                "andere[sn] Land"],
            "California": ["\\bKaliforniens?\\b", "\\bCCPA\\b"],
            "Washington": ["\\bWashingtons?\\b"],
            "Colorado": ["\\bColorados?\\b"],
            "Connecticut": ["\\bConnecticuts?\\b"],
            "Florida": ["\\bFloridas?\\b"],
            "Georgia": ["\\bgeorgiens?\\b"],
            "Texas": ["\\bTexas\\b"],
            "Virginia": ["\\bVirginias?\\b"],
            "New Jersey": ["\\bNew Jerseys?\\b"],
            "Delaware": ["\\bDelawares?\\b"],
            "Maryland": ["\\bMarylands?\\b"],
            "Oregon": ["\\bOregons?\\b"],
            "Nevada": ["\\bNevadas?\\b"],
            "Minnesota": ["\\bMinnesotas?\\b"],
            "New York": ["\\bNew Yorks?\\b"],
            "North Carolina": ["\\bNorth Carolinas?\\b"],
            "Utah": ["\\bUtahs?\\b"],
            "Nebraska": ["\\bNebraskas?\\b"],
            "United States": [
                "\\bVereinigten? Staaten\\b",
                "\\bUSA?s?\\b",
                "\\bu\\.s\\.a\\.\\b",
                "\\bu\\.s\\.\\b"
            ],
            "United Kingdom": [
                "\\bVereinigte[ns]? Königreichs?\\b",
                "\\buk\\b",
                "\\bu\\.k\\.\\b",
                "\\bGroßbritannien\\b",
                "\\bBritannien\\b",
            ],
            "Canada": ["\\bKanadas?\\b"],
            "Québec": ["\\bQu[eé]becs?\\b"],
            "Australia": ["\\bAustraliens?\\b", "\\bANZ\\b"],
            "New Zealand": ["\\bNeuseelands?\\b", "\\bANZ\\b"],
            "Germany": ["\\bDeutschlands?\\b"],
            "France": ["\\bFrankreichs?\\b"],
            "Italy": ["\\bItaliens?\\b", "\\bitaly\\b", "italienisch"],
            "Spain": ["\\bSpaniens?\\b"],
            "Portugal": ["\\bPortugals?\\b"],
            "Netherlands": ["\\bNiederlandes?\\b", "\\bHollands?\\b", "\\bnetherlands\\b", "niederländisch"],
            "Belgium": ["\\bBelgiens?\\b"],
            "Switzerland": ["\\bSchweiz(er)?\\b", "(?<!-)\\bch\\b(?!-)"],
            "Austria": ["\\bÖsterreichs?\\b"],
            "Sweden": ["\\bSchwedens?\\b"],
            "Norway": ["\\bNorwegens?\\b"],
            "Denmark": ["\\bDänemarks?\\b"],
            "Finland": ["\\bFinnlands?\\b"],
            "Iceland": ["\\bIslands?\\b"],
            "Ireland": ["\\bIrlands?\\b"],
            "Poland": ["\\bPolens?\\b"],
            "Czech Republic": ["\\bTschechischen? Republik\\b", "\\bTschechiens?\\b"],
            "Slovakia": ["\\bSlowakeis?\\b"],
            "Hungary": ["\\bUngarns?\\b"],
            "Romania": ["\\bRumäniens?\\b"],
            "Bulgaria": ["\\bBulgariens?\\b"],
            "Greece": ["\\bGriechenlands?\\b"],
            "Croatia": ["\\bKroatiens?\\b"],
            "Slovenia": ["\\bSloweniens?\\b"],
            "Estonia": ["\\bEstlands?\\b"],
            "Latvia": ["\\bLettlands?\\b"],
            "Lithuania": ["\\bLitauens?\\b"],
            "Luxembourg": ["\\bLuxemburgs?\\b"],
            "Malta": ["\\bMaltas?\\b"],
            "Cyprus": ["\\bZyperns?\\b"],
            "Russia": ["\\bRusslands?\\b", "\\brussischen? Föderation\\b"],
            "Ukraine": ["\\bUkraines?\\b"],
            "Belarus": ["\\bBelarus\\b", "\\bWeißrusslands?\\b"],
            "Moldova": ["\\bMoldaus?\\b"],
            "Serbia": ["\\bSerbiens?\\b"],
            "Bosnia and Herzegovina": ["\\bBosniens?\\b", "\\bBosnien und Herzegowina\\b"],
            "Albania": ["\\bAlbaniens?\\b"],
            "North Macedonia": ["\\bNordmazedoniens?\\b", "\\bMazedoniens?\\b"],
            "Montenegro": ["\\bMontenegros?\\b"],
            "Kosovo": ["\\bKosovos?\\b"],
            "Turkey": ["\\bTürkeis?\\b"],
            "China": [
                "\\bChinas?\\b",
                "\\bchinesischen? Festlands?\\b",
            ],
            "Japan": ["\\bJapans?\\b"],
            "South Korea": ["\\bSüdkoreas?\\b"],
            "North Korea": [
                "\\bNordkoreas?\\b",
                "\\bDemokratischen? Volksrepublik Korea\\b"
                "\\bDVRK\\b"
            ],
            "Taiwan": ["\\bTaiwans?\\b"],
            "Hong Kong": ["\\bHongkongs?\\b"],
            "Macau": ["\\bMacaus?\\b"],
            "Singapore": ["\\bSingapurs?\\b", "\\bSingapore?\\b"],
            "Malaysia": ["\\bMalaysias?\\b"],
            "Indonesia": ["\\bIndonesiens?\\b"],
            "Thailand": ["\\bThailands?\\b"],
            "Vietnam": ["\\bVietnams?\\b"],
            "Philippines": ["\\bPhilippinens?\\b"],
            "Myanmar": ["\\bMyanmars?\\b", "\\bB[ui]rmas?\\b"],
            "Cambodia": ["\\bCambodias?\\b", "\\bKambodschas?\\b"],
            "Laos": ["\\bLaos\\b"],
            "Brunei": ["\\bBruneis?\\b"],
            "India": ["\\bIndiens?\\b", "\\bindia\\b"],
            "Pakistan": ["\\bPakistans?\\b"],
            "Bangladesh": ["\\bBangladeschs?\\b"],
            "Sri Lanka": ["\\bSri Lankas?\\b"],
            "Nepal": ["\\bNepals?\\b"],
            "Bhutan": ["\\bBhutans?\\b"],
            "Maldives": ["\\bMaledivens?\\b"],
            "Afghanistan": ["\\bAfghanistans?\\b"],
            "Iran": ["\\bIrans?\\b"],
            "Iraq": ["\\bIraks?\\b"],
            "Saudi Arabia": ["\\bSaudi Arabiens?\\b"],
            "United Arab Emirates": [
                "\\bVereinigten? Arabischen? Emirate\\b",
                "\\bvae\\b",
                "\\bu\\.a\\.e\\.\\b",
            ],
            "Qatar": ["\\bKatars?\\b"],
            "Kuwait": ["\\bKuwaits?\\b"],
            "Bahrain": ["\\bBahrains?\\b"],
            "Oman": ["\\bOmans?\\b"],
            "Yemen": ["\\bJemens?\\b"],
            "Jordan": ["\\bJordans?\\b"],
            "Lebanon": ["\\bLibanons?\\b"],
            "Syria": ["\\bSyriens?\\b"],
            "Israel": ["\\bIsraels?\\b"],
            "Palestine": ["\\bPalästinas?\\b"],
            "Egypt": ["\\bÄgytpens?\\b"],
            "Libya": ["\\bLibyens?\\b"],
            "Tunisia": ["\\bTunesiens?\\b"],
            "Algeria": ["\\bAlgeriens?\\b"],
            "Morocco": ["\\bMarokkos?\\b"],
            "Sudan": ["\\bSudans?\\b"],
            "South Sudan": ["\\bSüdsudans?\\b"],
            "Ethiopia": ["\\bÄthopiens?\\b"],
            "Kenya": ["\\bKenias?\\b"],
            "Tanzania": ["\\bTansanias?\\b"],
            "Uganda": ["\\bUgandas?\\b"],
            "Rwanda": ["\\bRuandas?\\b"],
            "Burundi": ["\\bBurundis?\\b"],
            "Somalia": ["\\bSomaliens?\\b"],
            "Djibouti": ["\\bDschibutis?\\b"],
            "Eritrea": ["\\bEritreas?\\b"],
            "Nigeria": ["\\bNigerias?\\b"],
            "Ghana": ["\\bGhanas?\\b"],
            "Ivory Coast": ["\\bElfenbeinküstes?\\b"],
            "Senegal": ["\\bSenegals?\\b"],
            "Mali": ["\\bMalis?\\b"],
            "Burkina Faso": ["\\bBurkina Fasos?\\b"],
            "Niger": ["\\bNigers?\\b"],
            "Chad": ["\\bTschads?\\b"],
            "Cameroon": ["\\bKameruns?\\b"],
            "Central African Republic": ["\\bZentralafrikanischen? Republik?\\b"],
            "Gabon": ["\\bGabuns?\\b"],
            "Congo": ["\\bKongos?\\b"],
            "Democratic Republic of Congo": [
                "\\bDemokratischen? Republik Kongos?\\b",
                "\\bDRK\\b"
            ],
            "Angola": ["\\bAngolas?\\b"],
            "Zambia": ["\\bSambias?\\b"],
            "Zimbabwe": ["\\bSimbabwes?\\b"],
            "Mozambique": ["\\bMosambiks?\\b"],
            "Malawi": ["\\bMalawis?\\b"],
            "Botswana": ["\\bBotswanas?\\b"],
            "Namibia": ["\\bNamibias?\\b"],
            "South Africa": ["\\bSüdafrikas?\\b"],
            "Lesotho": ["\\bLesothos?\\b"],
            "Eswatini": ["\\bEswatinis?\\b", "\\bswasilands?\\b"],
            "Madagascar": ["\\bMadagaskars?\\b"],
            "Mauritius": ["\\bMauritius\\b"],
            "Seychelles": ["\\bSeychellens?\\b"],
            "Comoros": ["\\bKomorens?\\b"],
            "Cape Verde": ["\\bKap Verdes?\\b"],
            "Sao Tome and Principe": ["\\bS[ãa]o Tom[ée]s?\\b"],
            "Equatorial Guinea": ["\\beÄquatorialguineas?\\b"],
            "Guinea": ["\\bGuineas?\\b"],
            "Guinea-Bissau": ["\\bGuinea-Bissaus?\\b"],
            "Sierra Leone": ["\\bSierra Leones?\\b"],
            "Liberia": ["\\bLiberias?\\b", "\\bLiberiens?\\b"],
            "Togo": ["\\bTogos?\\b"],
            "Benin": ["\\bBenins?\\b"],
            "Mauritania": ["\\bMauretaniens?\\b"],
            "Gambia": ["\\bGambias?\\b"],
            "Mexico": ["\\bMexikos?\\b"],
            "Guatemala": ["\\bGuatemalas?\\b"],
            "Belize": ["\\bBelizes?\\b"],
            "Honduras": ["\\bHonduras\\b"],
            "El Salvador": ["\\bEl Salvadors?\\b"],
            "Nicaragua": ["\\bNicaraguas?\\b"],
            "Costa Rica": ["\\bCosta Ricas?\\b"],
            "Panama": ["\\bPanamas?\\b"],
            "Cuba": ["\\bKubas?\\b"],
            "Jamaica": ["\\bJamaikas?\\b"],
            "Haiti": ["\\bHaitis?\\b"],
            "Dominican Republic": ["\\bDominikanischen? Republik\\b"],
            "Bahamas": ["\\bBahamas\\b"],
            "Trinidad and Tobago": ["\\bTrinidads? und Tobagos?\\b", "\\btrinidads?\\b"],
            "Barbados": ["\\bbarbados\\b"],
            "Saint Lucia": ["\\bSaint Lucias?\\b", "\\bSt\\.? Lucias?\\b"],
            "Grenada": ["\\bgrenadas?\\b"],
            "Saint Vincent": ["\\bSt. Vincent und die Grenadinens?\\b"],
            "Antigua and Barbuda": ["\\bAntigua und Barbudas?\\b"],
            "Dominica": ["\\bdominicas?\\b"],
            "Saint Kitts": ["\\bSaint Kitts\\b", "\\bSt\\.? Kitts\\b"],
            "Brazil": ["\\bBrasiliens?\\b"],
            "Argentina": ["\\bArgentiniens?\\b"],
            "Chile": ["\\bChiles?\\b"],
            "Colombia": ["\\bKolumbiens?\\b"],
            "Peru": ["\\bPerus?\\b"],
            "Venezuela": ["\\bVenezuelas?\\b"],
            "Ecuador": ["\\bEcuadors?\\b"],
            "Bolivia": ["\\bBoliviens?\\b"],
            "Paraguay": ["\\bParaguays?\\b"],
            "Uruguay": ["\\bUruguays?\\b"],
            "Guyana": ["\\bGuyanas?\\b"],
            "Suriname": ["\\bSurinames?\\b"],
            "French Guiana": ["\\bFranzösisch Guayanas?\\b"],
            "Fiji": ["\\bFijis?\\b"],
            "Papua New Guinea": ["\\bPapua-Neuguineas?\\b"],
            "Solomon Islands": ["\\bSolomon-Inseln\\b", "\\bSalomonens?\\b"],
            "Vanuatu": ["\\bVanuatus?\\b"],
            "Samoa": ["\\bSamoas?\\b"],
            "Tonga": ["\\bTongas?\\b"],
            "Kiribati": ["\\bKiribatis?\\b"],
            "Micronesia": ["\\bMikronesiens?\\b"],
            "Marshall Islands": ["\\bMarshallinseln\\b"],
            "Palau": ["\\bPalaus?\\b"],
            "Nauru": ["\\bNaurus?\\b"],
            "Tuvalu": ["\\bTuvalus?\\b"],
            "Cook Islands": ["\\bCookinseln\\b"],
            "Niue": ["\\bNiues?\\b"],
            "Kazakhstan": ["\\bKasachstans?\\b"],
            "Uzbekistan": ["\\bUsbekistans?\\b"],
            "Turkmenistan": ["\\bTurkmenistans?\\b"],
            "Kyrgyzstan": ["\\bKirgisistans?\\b"],
            "Tajikistan": ["\\bTadschikistans?\\b"],
            "Mongolia": ["\\bMongoleis?\\b"],
            "Armenia": ["\\bArmeniens?\\b"],
            "Azerbaijan": ["\\bAserbaidschans?\\b"],
        }
    ),
    company=AttributePattern.from_dict(
        {
            "Amazon": ["\\bamazon(s)?\\b", "\\baws\\b"],
            "Microsoft": [
                "\\bmicrosoft\\b",
                "\\bazure\\b",
                "\\bbing\\b",
                "\\boffice 365\\b",
                "\\bskype\\b",
                "\\bonedrive\\b",
            ],
            "Apple": ["\\bapple(s)?\\b", "\\bicloud\\b", "\\bios\\b", "\\bmac(os)?\\b"],
            "Google": [
                "\\bgoogle(s)?\\b",
                "\\bgcp\\b",
                "\\bandroid\\b",
                "\\bgmail\\b",
                "\\bchromecast\\b",
                "\\bgoogle analytics\\b",
                "\\bgoogle ads\\b",
                "\\bgoogle tag manager\\b",
                "\\bgoogle maps\\b",
                "\\bgoogle cloud\\b",
                "\\bdoubleclick\\b",
                "\\badmob\\b",
            ],
            "Facebook": [
                "\\bfacebook(s)?\\b",
                "\\binstagram\\b",
                "\\bwhatsapp\\b",
                "\\bfacebook pixel\\b",
            ],
            "SmartThings": ["\\bsmartthing(s)?\\b"],
            "Avast": ["\\bavast\\b"],
            "Antiy": ["\\bantiy\\b"],
            "Tencent": ["\\btencent\\b", "\\bwechat\\b", "\\bqq\\b"],
            "Unity": ["\\bunity\\b"],
            "Vungle": ["\\bvungle\\b"],
            "IronSource": ["\\bironsource\\b"],
            "AppLovin": ["\\bapplovin\\b"],
            "Chartboost": ["\\bchartboost\\b"],
            "Mopub": ["\\bmopub\\b"],
            "Mytarget": ["\\bmytarget\\b"],
            "Yandex": ["\\byandex\\b"],
            "Tapjoy": ["\\btapjoy\\b"],
            "AdColony": ["\\badcolony\\b"],
            "Indus Appstore": ["\\bindusappstore\\b"],
            "Adjust": ["\\badjust\\b"],
            "Appsflyer": ["\\bappsflyer\\b"],
            "Affise": ["\\baffise\\b"],
            "Miaozhen": ["\\bmiaozhen\\b"],
            "Nielsen": ["\\bnielsen\\b"],
            "PayPal": ["\\bpaypal\\b", "\\braintree\\b"],
            "Twitter": ["\\btwitter\\b", "\\bx\\.com\\b"],
            "Instagram": ["\\binstagram\\b"],
            "Pinterest": ["\\bpinterest\\b"],
            "YouTube": ["\\byoutube\\b"],
            "LinkedIn": ["\\blinkedin\\b"],
            "Xing": ["\\bxing\\b"],
            "Kununu": ["\\bkununu\\b"],
            "RISKIFIED": ["\\briskified\\b"],
            "Stripe": ["\\bstripe\\b"],
            "Firebase": ["\\bfirebase\\b"],
            "Mailchimp": ["\\bmailchimp\\b", "\\bmandrill\\b"],
            "Spotify": ["\\bspotify\\b"],
            "Pandora": ["\\bpandora\\b"],
            "Salesforce": ["\\bsalesforce\\b", "\\btableau\\b", "\\bslack\\b"],
            "UnionPay": ["\\bunionpay\\b"],
            "WeChat": ["\\bwechat\\b", "\\bweixin\\b"],
            "Alibaba": ["\\balibaba\\b", "\\balipay\\b"],
            "Alipay": ["\\balipay\\b"],
            "Visa": ["\\bvisa\\b"],
            "Mastercard": ["\\bmastercard\\b"],
            "Garmin Pay": ["\\bgarmin( )?pay\\b"],
            "Venmo": ["\\bvenmo\\b"],
            "6Sense": ["\\b6sense\\b"],
            "TransUnion": ["\\btransunion\\b", "\\bsontiq\\b"],
            "PIPL": ["\\bpipl\\b"],
            "Adyen": ["\\badyen\\b"],
            "Matomo": ["\\bmatomo\\b", "\\bpiwik\\b"],
            "Shopify": ["\\bshopify\\b", "\\bshop( )?pay\\b"],
            "OpenAI": ["\\bopenai\\b", "\\bchatgpt\\b"],
            "Hotjar": ["\\bhotjar\\b"],
            "Hubspot": ["\\bhubspot\\b"],
            "Wyng": ["\\bwyng\\b"],
            "Reddit": ["\\breddit\\b"],
            "Mouseflow": ["\\bmouseflow\\b"],
            "Yahoo": ["\\byahoo\\b"],
            "Zoom": ["\\bzoom\\b"],
            "Adobe": ["\\badobe\\b", "\\badobe analytics\\b", "\\bomniture\\b"],
            "Klarna": ["\\bklarna\\b"],
            "Cloudflare": ["\\bcloudflare\\b"],
            "Akamai": ["\\bakamai\\b"],
            "Fastly": ["\\bfastly\\b"],
            "Snowflake": ["\\bsnowflake\\b"],
            "DigitalOcean": ["\\bdigitalocean\\b"],
            "TikTok": ["\\btiktok\\b", "\\bbytedance\\b"],
            "Zendesk": ["\\bzendesk\\b"],
            "Freshdesk": ["\\bfreshdesk\\b", "\\bfreshworks\\b"],
            "Datadog": ["\\bdatadog\\b"],
            "Bazaarvoice": ["\\bbazaarvoice\\b"],
            "StampedIO": ["\\bstamped\\.io\\b"],
            "Rapid Response Monitoring Services": [
                "\\brapid response monitoring services\\b"
            ],
            "Jaggaer": ["\\bjaggaer\\b"],
            "SAP": ["\\bsap\\b"],
            "Webhelp": ["\\bwebhelp\\b"],
            "GEP": ["\\bgep\\b"],
            "Cloud Security Alliance": ["\\bcloud security alliance\\b"],
            "Team Internet AG": ["\\bteam internet ag\\b"],
            "Meta": ["\\bMeta\\b"],
            "Clarity": ["\\bClarity\\b"],
            "Mozilla": ["\\bMozilla\\b", "\\bFirefox\\b"],
            "Opera": ["\\bOpera\\b"],
            "Trojan": ["\\bTrojan\\b"],
            "TrustedShops": ["\\bTrusted Shops\\b", "\\bTrustbadges?\\b"],
            "Qualtrics": ["\\bQualtrics\\b"],
            "Square": ["\\b(?<!Canal )Square\\b"],
            "ElevenLabs": ["\\bElevenLabs?\\b"],
            "TrustPilot": ["\\bTrustPilot\\b"],
            "CleverReach": ["\\bCleverReach\\b"],
            "Mavenoid": ["\\bMavenoid\\b"],
        }
    ),
    provide_service=AttributePattern.from_dict(
        {
            "OrderProcessing": [
                "^(?!.*(Versand|Status|Lieferung)).*(?<!nach einer )(?<!bisherigen )\\bBestellung",
                "\\bBestell(prozess|vorgang)",
                "\\bKäufe\\b",
                "^(?!.*(Werbe|Marketing|Garantie)).*\\bKaufs?\\b(?!-)",
                "^(?!.*(Garantie|Abschnitt)).*(?<!bei einem )\bKaufs?\b(?!-)",
                "\\bWarenkorb\\b",
                "Auftragsabwicklung",
                "Abwicklung.{0,24}(Bestellungen|Aufträge|Auftrag)"
            ],
            "PaymentProcessing": [
                "Zahlung(en|sabwicklung(en)?)?\\b",
                "Transaktion(en)?\\b",
                "Verarbeitung Ihrer Zahlungsangaben"
            ],
            "Shipping": [
                "(?<!Newsletter)Versands?\\b",
                "Zustellung",
                "(?<!Nach)Liefer(ung|zweck)(?!.*Preis)",
                "(?<!Informationen)(?<!Werbung)(?<!Dienstleistungen) zu liefern",
                "für die Logistik"
            ],
            "ReturnOrder": [
                "\\bzurück(zu)?(geben|schicken|senden)\\b",
                "Rück(sendung|gabe|erstattung)",
                "Reklamation"
            ],
            "OrderTracking": [
                "(Paket|Sende)verfolgung",
                "Status (Deiner|Ihrer|der) Bestellung"
            ],
            "WarrantyService": ["Garantie(?!zeit)(?!rt)(?!ren)"],
            "AfterSalesService": [
                "Nachlieferung",
                "nach einer Bestellung"
            ],
            "PresentWebsite": [
                "^(?!(Verbesserung|Optimierung)).*(Darstellung|Gestaltung|Bereitstellung|Betrieb|Zurverfügungstellung|Funktionalität).{0,40}(Web?(seite|site)|Internetauftritt)",
                "((Web)?(seite|site)|Internetauftritt).{0,48}(gestalten|ermöglichen|an(zu)?passen|aus(zu)?liefern|aufzurufen|betreiben)",
                "einheitliche[rn]? Darstellung",
                "um.{0,20}(Text|Schrift).{0,30}(an(zu)?zeigen|dar(zu)?stellen)",
                "Browser.*schrift",
                "optische Gestaltung",
                "für.{0,30}(Aufruf|Nutzung|Verwendung).{0,30}(Web)?(seite|site).{0,30}(notwendig|erforderlich)"
            ],
            "ProvideApp": [
                "(Bereitstellung|Schaffung|Funktionalität|Betrieb).{0,48}(App|Anwendung)",
                "Apps? zur Verfügung (zu )?stellen"
            ],
            "ProvideDevice": [
                "(Bereitstellung|Schaffung|Funktionalität|Betrieb)\\b.{0,48}(Gerät|Produkt)",
                "(Gerät|Produkt).{0,2}\\b.{0,20}bereit(zu)?stellen"
            ],
            "PreContractualMeasures": ["\\bvorvertraglicher Maßnahmen\\b"],
            "Loaning": [
                "Verleih",
                "Ausleih(ung|en)?"
            ],
            "RiskAssessment": [
                "\\bRisiko(bewertung|berücksichtigung|management)",
                "(berücksichtigen|bewerten).{0,110}Risik(o|en)"
            ],
            "Insurance": [
                "\\bVersicherung(en)?\\b",
                "Versicherungs(antrag|anträgen)"
            ],
            "FacialRecognition": [
                "Gesichtserkennung"
            ],
            "AccountCreation": [
                "\\bKonto(erstellung|registrierung)\\b",
                "(Erstellung|Registrierung|Eröffnung|registrieren|einrichten|verwalten|erstellen)(.){0,32}(Konto|\\bProfil)",
                "(Konto|Profil|Web(seiten?|sites?)).{0,32}(erstellen|ein(zu)?richten|eröffnen|registrieren|verwalten|anlegen|angelegt)",
                "Registrierung als Kunde",
                "als Kunde.{0,20} registrieren"
            ],
            "ProductActivation": [
                "(Produkt|Geräte)aktivierung",
                "(?<!de)(Aktivierung|aktivieren)(?!.*:).{0,48}(Produkt|Gerät)",
                "(?<!auf ihrem )(Produkt|Gerät).{0,49}\\b(Aktivierung|aktivieren)"
            ],
            "ServiceActivation": [
                "(Service|Dienst)[- ]?aktivierung",
                "\\b(Aktivierung|aktivieren).{0,60}(Service|Dienst)",
                "(Services?|Dienste?).{0,48}\\b(Aktivierung|aktivieren|gewähren)",
                "\\bAktivierungslinks?\\b",
                "Registrierung.{0,24}Services?",

            ],
            "DeviceRegistration": [
                "(Produkt|Geräte?)(registrierung|einrichtung)",
                "(Registrierung|registrieren)[^,\\.]{0,48}(Produkt|Gerät)",
                "(Produkt|Gerät).{0,48}(Registrieren|registrieren|verknüpfen)"
            ],
            "OfflineAvailability": [
                "offline-Verfügbarkeit",
                "wenn Sie offline sind",
                "Offline-Modus"
            ],
            "Authentication": [
                "\\bAuthentifi(kation|zieren)\\b",
                "\\bVerifizier(ung|en|ungsschritte)\\b",
                "Identität.{0,64}(verifizieren|überprüfen)\\b"
            ],
            "UserIdentification": [
                "Identifizierung (von|des|der) (Be)?Nutzer",
                "^(?!.*Bedrohung).*\\bidentifizieren\\b(?!.*(keine|nicht))",
                "Wiedererkennung",
                "wiedererk(ennen|annt)",
                "(um|und) Sie.{0,64} zu identifizieren",
                "um sich.{0,40}anzumelden"
            ],
            "SocialLogin": [
                "\\bsocial (log(-| )?in|sign(-| )?in)\\b",
                "(über|mithilfe|durch|mit).{0,32}(social media|soziale Medien|soziales Netzwerk).{0,32}(an(zu)?melden|ein(zu)?loggen)"
            ],
            "Monitoring": [
                "^(?!.*Gesundheit).*\\b(überwachen|Überwachung|Monitoring)\\b(?!.*Gesundheit)",
                "^(?!.*Dritt).*Tracking(?!-)(?!.*Dritt)"
            ],
            "HealthMonitoring": [
                "(Zustands|Gesundheits)(überwachung|verfolgung)",
                "(Überwach(en|ung)|Verfolg(en|ung)).{0,32}(Gesundheit|Fitness)",
            ],
            "WebHosting": [
                "\\bHosting\\b"
            ],
            "Recruiting": [
                "sich.{0,30} bewerben",
                "Bewerbung",
                "(Rekrutierung|Recruiting)",
                "Stellenausschreibung",
                "(Einstellungs|Bewerbungs)(prozess|entscheidung|verfahren)",
                "berufliche Referenzen",
                "(Beschäftigungs(verhältnis|verlauf))",
                "Stelle.{0,24} (zu finden|bewerben|beworben)",
                "Bewerberprofil",
                "Eignung.{0,40}(Bewerber|Bewerbung)",
                "Personal(auswahl|gewinnung)"
            ],
            "CreditWorthiness": [
                "\\b(Steuer|Einkommen).{0,24} (erfassen|einsehen|zugang)",
                "Kredit.{0,20}gewähren",
                "Bonität",
                "\\bKreditwürdigkeit"
            ],
            "FraudRiskScoring": [
                "Betrugserkennung",
                "Betrugsrisikobewertung"
            ],
            "Comfort": [
                "bequem",
                "(Surf|(Be)?Nutzer)(erlebnis|erfahrung).{0,24}(verbessern|optimieren)",
                "(bessere|verbesserte|optimierte)[mnrs]? (Surf|(Be)?Nutzer)(erlebnis|erfahrung)",
                "(be)?nutzerfreundlich(keit)?",
                "Kundenzufriedenheit",
                "Komfort"
            ],
            "PersonalizeContent": [
                "(nützlicheren?|maßgeschneiderten?|zugeschnittener?|gezielter?|Individueller?|relevantere) (Information|Info|Inhalt|(Online-)?Werbung|Werbezwecke|Gestaltung|Produkte)",
                "personalisier(t|te|ten|tem|tes|ter|e|er|en|ung|ungen)",
                "(Interessen).{0,24}(an(zu)?passen|entsprechen)"
                "individuell.{0,12}gestalten",
                "(auf sie|Kunden) zugeschnitten",
                "persönlichen Präferenzen (angepasst|anpassen)"
            ],
            "Updates": [
                "(Software|Service|System|Produkte).{0,24} (aktualisiert|optimiert)",
                "Bereitstellung.{0,50}(Update|Optimierung|Aktualisierung|Verbesserung)",
                "automatische Aktualisierung",
                "^(?!.*(Information|Nachricht)).*\\b(Aktualisierungen(en)?|Updates?)\\b(?!.*(Erklärung|Datenschutz|senden|Kontakt))",
                "Software-?Updates",
            ],
            "Upload/Download": [
                "^(?!.*(Dritt|keine|nicht|Plugin|Addon).*(herunterladen|hochladen)).*(herunterladen|hochladen)",
                "\\b(Download|Upload)\\b(?!-)"
            ],
            "SyncContent": [
                "(Synchronisation|synchronisieren)"
            ],
            "LocalizeContent": [
                "\\bgeo(-)?targeting\\b",
                "regionale Adresse",
                "(Produkte|Dienstleistungen|Anpassungen|Inhalt|Content).{0,32}(in|für).{0,32}Ihr.{0,30}(Region|Land|Sprache)"
            ],
            "EstimateBodyMetrics": [
                "Körpermaße.{0,30}schätzen",
                "schätzen.{0,30}Körpermaße"
            ],
            "VideoAnalysis": [
                "Videoanalyse",
                "analysiere.{0,32}video",
                "video.{0,32}analysieren"
            ],
            "PersonDetection": [
                "Personenerkennung",
                "(?<!von )(Person(en)?\\b|Leute|Menschen|Individuen|Besucher|Passanten).{0,32}(erkennen|wahrnehmen|entdecken|bemerken|erfassen)",
                "(erkennen|wahrnehmen|entdecken|bemerken|erfassen).{0,32}(Person(en)?\\b|Leute|Menschen|Individuen|Besucher(?!.{0,32}Webseite)|Passanten)"
            ],
            "ActivityDescription": [
                "Aktivitätsbeschreibung",
                "(beschreiben|Beschreibung|Zusammenfassung|zusammenfassen).{0,32}(Aktivität|Bewegung|Betätigung|Tätigkeit)",
            ],
            "SignalingActiveEngagement": [
                "(Zeichen|Signal|an(zu)?zeigen).{0,20}dass Sie(.){0,32}aktiv"
            ],
            "CountVisits": [
                "Besucher(an)?zahl",
                "Besucher(.){0,32}zählen"
            ],
            "RecommendSettings": [
                "(empfohlene|vorgeschlagene).{0,32}(Einstellung|Konfiguration)",
            ],
            "ProvideUsageInsights": [
                "Nutzungseinblicke",
                "Einblicke? in die Nutzung"
            ],
            "Logging": [
                "\\blogging\\b",
                "(Verhalten|Nutzung|Sicherheitszwecken).{0,64}(protokollieren|auf(zu)?zeichnen)",
                "(Protokolle?|Logs?|Log-Datei).{0,64}(erstellen|erzeugen)",
                "(erstellen|erzeugen).{0,64}(Protokollen?|Logs|Log-Datei)\\b"
            ],
            "CloudBasedControl": ["Cloud-basierte (Steuerung|Kontrolle)\\b"],
            "NightVision": ["\\bNachtsicht\\b"],
            "MotionDetection": [
                "Bewegungs(erkennung|erfassung|detektion)",
                "(erkennen|erfassen|detektieren).{0,32}Bewegung",
                "\\b(wenn|falls)(.){0,48}(Tür|Fenster)\\b",
                "\\bBewegung(.){0,20}(erkennen|erfassen|detektieren)\\b"
            ],
            "ThirdPartyCompatibility": [
                "(Produkte|Dienste|Dienstleistungen|Geräte|Apps)(?=.*(Dritten|Drittanbietern|Dienstleister))(?=.*(verbinden|verknüpfen|koppeln|verlinken))",
                "(verbinden|verknüpfen|koppeln|verlinken)(?=.*(Produkte|Dienste|Dienstleistungen|Geräte|Apps))(?=.*(Dritten|Drittanbietern|Dienstleister))",
                "(verbinden|verknüpfen|koppeln|verlinken)(?=.*(Dritten|Drittanbietern|Dienstleister))(?=.*(Produkte|Dienste|Dienstleistungen|Geräte|Apps))",
                "Interoperabilität",
            ],
            "StorePreferences": [
                "(speichern|erinnern).{0,32}(Präferenzen|Einstellungen|Konfigurationen)",
                "(Präferenzen|Einstellungen|Konfigurationen).{0,32}((ge)?speicher|erinner)[nt]"
            ],
            "MembershipManagement": [
                "Mitglieder(verwaltung|management)",
                "(managen|verwalten|Verwaltung|beenden|Beendigung|Änderung|ändern).{0,48}(Mitgliedschaft|Teilnahme)",
                "Mitgliedschaft.{0,48}(verwalten|managen|beenden|ändern)"
            ],
            "SpeedUp": [
                "(erhöhen|verbessern|beschleunigen|optimieren|schneller|verkürzen).{0,32}(Geschwindigkeit|Zeit|\\bLade)",
                "(Geschwindigkeit|Zeit|\\bLade).{0,32}(erhöhen|verbessern|beschleunigen|optimieren|schneller|verkürzen)"
            ],
            "PromotionalActivities": [
                "(Werbe|Marketing)-?(Aktivität|Aktion|Kampagne|Wettbewerb|Anzeige|Veranstaltung).{0,64}(teil(zu)?nehmen|teilnimmst|durch(zu)?führen|an(zu)?melden)",
                "(Gewinnspiel|Promotion|Preisausschreiben|Rabattaktion)",
                "(Durchführung|Teilnahme|teilnehmen|durchführen).{0,64}(Werbe|Marketing)-?(aktivitäten|aktionen|kampagen|veranstaltung|kamgagne)"
            ],
            "RecommendPurchases": [
                "(Produkt|service|Dienst(leistung)?|Kauf|Gerät).{0,64}(zu empfehlen|vorzuschlagen)",
                "Kaufempfehlung"
            ],
            "AutomaticPurchases": [
                "automatischer?.{0,32}(Lieferung|Kauf|Abwicklung)"
            ],
            "SubscriptionManagement": [
                "Dienste? abonnieren",
                "(Abo|Abonnement)-?(verwaltung|management)",
                "(managen|verwalten|handhaben).{0,32}(Abonnement|Abos)"
            ],
            "CloudService": [
                "Cloud[ -]?(Dienst|Service|Speicher|Infrastruktur)(?!anbieter)(?!-anbieter)",
                "cloudbasierte (Dienste|Services|Anwendungen)"
            ],
            "StorageService": [
                "Speicher(dienst|service)",
                "Cloud-(basierter?)(Speicher|Speicherung)"
            ],
            "BackupService": [
                "Backup-?(dienst|service)",
                "^(?!.*lösch).*Backups"],
            "MusicService": ["Musik-?(dienst|service)"],
            "ThemeService": ["Themen?-?(dienst|service|empfehlung)"],
            "WallpaperService": ["Wallpaper"],
            "LocationService": [
                "standortbezogene[rn]? (service|Dienst)",
                "(Standort|Ortungs)(service|dienst)",
                "(Geo)?lokalisierung", 
                "Anzeige (der|von) Kartendaten",
            ],
            "WeatherService": [
                "Wetter(dienst|bericht)",
                "(Dienst|Service).{0,64}Wetter"
            ],
            "SecurityService": [
                "Sicherheits-?(?!scan).{0,32}(dienst(?!leister)|service|funktion|system)(?!anbieter)"
            ],
            "CommunicationService": ["Kommunikations-?(dienst|service)"],
            "HeatingSystem": [
                "Heizungssystem",
                "Temperaturregler",
                "(regeln|regulieren|einstellen).{0,24}(Temperatur|Thermostat)",
                "(Temperatur|Thermostat).{0,24}(regeln|regulieren|einstellen)"
            ],
            "CoolingSystem": [
                "Klimaanlage",
            ],
            "Navigation": [
                "(?<!Website-)(?<!Web-)(?<!Nutzer)navigation\\b",
                "Steuerung des Mähers"
            ],
            "FindDevice": [
                "Gerätesuche",
                "Gerät.{0,64}((?<!be)suchen|finden|lokalisieren)(?!.{0,12}verbinden)"
            ],
            "ConserveResources": [
                "Ressourcen.{0,20}schonen",
                "(Schonen|Einsparen).{0,20}Ressourcen"
            ],
            "SaveWater": ["Wasser.{0,20}sparen"],
            "SaveEnergy": [
                "Energie.{0,20}sparen",
                "Energieeffizien[tz]",
                "(Akku|Energie)sparmodus"
            ],
            "OptimizeWifFi": ["(wi-?fi|Wlan|Internetverbindung) zu (optimieren|verbessern)"],
            "SwitchLight": [
                "Licht (ein|aus)(zu)?schalten"
            ],
            "Invoice": [
                "((aus)?drucken|bereitstellen|senden|ausstellen)(.){0,32}Rechnung",
                "Rechnung.{0,32}((aus)?ducken|bereitstellen|senden|ausstellen)",
                "Rechnungs(aus)?stellung"
            ],
            "SocialSharing": [
                "\\bsocial sharing\\b",
                "Social[- ](Media[- ])?Plug[- ]?in",
                "Plug[- ]?ins?.{0,64}(Facebook|X|Twitter|Instagram|Pinterest|LinkedIn|XING|WhatsApp|Telegram)",
                "(Buttons|Plug-?In).{0,48}soziale[rn]? Netzwerk",
                "sharing[- ]Funktion"
            ],
            "ErrorDiagnosis": [
                "(Diagnose|Analyse|beheben|finden|identifizieren|handhaben).{0,32}(Fehler|Bug|Problem)",
                "Fehler(analyse|diagnose|diagnostik|behebung)",
                "(Fehler|Bug|Problem).{0,32}(identifizieren|beheben|finden|handhaben|analysieren)"
            ],
            "PhotoMetadata": [
                "Metadaten.{0,20}Foto",
                "beim (Fotografieren|Aufnehmen eines Fotos).{0,32}(aufzeichnen|aufgezeichnet|speichern|gespeichert)",
                "aufzeichnen.{0,32}(beim|während).{0,32}(Foto|fotografieren)"
            ],
            "SecurityScan": ["Sicherheitsscan(funktion)?"],
            "VoiceSupport": [
                "sprachfähiger (Geräte|Produkte|Funktionen|Dienste)",
                "voice-?(support|service)"
            ],
            "TaxFreePurchase": [
                "(Bestellung|Kauf).{0,32}steuerfrei",
                "steuerfrei.{0,32}(Bestellung|Kauf)"
            ],
            "ScanQRCode": ["QR-Code.{0,48}(scannen|ein(zu)?lesen)"],
            "SaveToAlbum": [
                "(speichern|ablegen)(.){0,32}album",
                "album.{0,32}speichern"
            ],
            "DeliverPrize": [
                "(liefern|(zu)?senden|Lieferung|Zusendung|zustellen|Zustellung).{0,64}(Preis|Gewinn)",
                "(Preis|Gewinn).{0,64}(liefern|zustellen|(zu)?senden)",
                "Gewinnübergabe",
                "Preis gewinnen"
            ],
            "EnablingConnectivity": [
                "(Gerät|Dienst|Service|Produkt|Kont(o|en)|App).{0,32}(verbinden|vernetzen)",
                "(Konnektivität|vernetzt|(?<!in )Verbindung|verbinde|Vernetzung).{0,24}(Gerät|Dienst|Service|Produkt|Konto|App)",
                "(zur|für).{0,10}Verbindungsherstellung"
            ],
            "ParkDevice": ["(Gerät|Produkt|Mäher|Roboter).{0,32}parken"],
            "DataInfrastructure": [
                "Infrastruktur.{0,32}(bereit(zu)?stellen|gewährleisten)",
                "(Bereitstellen|Bereitstellung).{0,32}Infrastruktur"
            ],
            "GoogleAssistance": ["Google (Sprach)?assistenten"],
            "AmazonAlexa": ["Alexa Voice Service", "Amazon Alexa"],
            "AppleSiri": ["\\bapple siri\\b"],
            "RemoteControl": [
                "Fern(steuerung|verwaltung|zugriff)",
                "Remote.{0,32}(Zugriff|zu(zu)?greifen|nutzen|verwenden|Funktion)"
            ],
            "SmartHomeFunctions": [
                "Smart-Home(?!-Plattform)"
            ],
            "ObjectDetection": [
                "Objekterkennung",
                "(Objekte|Gegenstände|Umgebung).{0,32}(erkennen|wahrnehmen|entdecken|bemerken)",
                "(erkennen|wahrnehmen|entdecken|bemerken).{0,32}(Objekte|Gegenstände|Umgebung)"
            ],
            "RepairService": [
                "Reparatur",
                "reparieren"
            ],
            "ConsentManagement": [
                "(Consent|Einwilligungs)-(Tool|Manager)",
                "(Tool|Manager).{0,64}Einwilligung",
                "Einwilligungs(verwaltung|administration|management)"
            ],
            "BuyerProtection": ["Käuferschutz"],
            "BetaProgram": [
                "Beta-?(Programm|Test|Version)",
                "(Test(er)?|Vorab|Early-Access)-?programm",
                "geschlossener Test"
            ],
            "SelfService": [
                "Self-Service",
                "Kundenportal"
            ],
            "LoyaltyProgram": ["(Treue|Bonus)programm"],
        }
    ),
    communication=AttributePattern.from_dict(
        { 
            "InformationalUpdates": [
                "\\b(übermitteln|(zu)?senden).{0,84}(?<!System-)(?<!Produkt-)(?<!Software-)(Aktualisierungen|Updates|Nachrichten|Mitteilungen)",
                "(Aktualisierungen|Änderungen|Neuerungen|Empfehlungen)(?!.{0,48}Richtlinien).{0,120}(zusenden|zu informieren|bereit(zu)?stellen|zu unterrichten|zu übermitteln)",
                "(Service|Produkt)-?Aktualisierungen",
                "(?<!Werbe)(?<!Marketing)(Mitteilungen|Nachrichten|Benachrichtigungen|Bereitstellung).{0,20}(Änderungen|Aktualisierungen|(?<!Software-)(?<!Geräte-)(?<!Produkt-)Updates)",
                "(?<!Werbe)(?<!Marketing)(Mitteilungen|Nachrichten|Benachrichtigungen).{0,20}(Websites|Webseiten|Dienstleistungen|Services|Apps|Produkte|Geräte)(?!.{0,30}Update)"
            ],
            "UpdateNotifications": [
                "(Benachrichtigungen|Mitteilungen).{0,20}(Software|Geräte|Produkt)-(Updates|Aktualisierungen|Neuerungen)",
                "(Benachrichtigungen|Mitteilungen).{0,32}Upgrades",
                "(Update|Upgrade).{0,20}(Benachrichtigungen|Mitteilungen)",
                "Aktualisierungs.{0,24}informationen",
                "(Updates|Aktualisierungen|Neuerungen|Version).{0,20}(Mitteilung|mitteilen|benachrichtigen|nachricht)"
            ],
            "Notifications": [
                "(?<!werbliche )(?<!werblichen )(?<!Liefer)(?<!Zahlungs)benachrichtigung(?!.*(Änderung|Aktualisierung|Update|Einstellung|berechtigung))",
                "(Push|Benachrichtigungs)-?Dienst",
                "Push-Nachrichten",
                "\\bMitteilung(?!.*(Änderung|Aktualisierung|Update))",
                "^(?!.*Richtlinie).*(unterrichten|benachrichtigen) wir Sie(?!.*Richtlinie)",
                "bereitstellung.{0,32}relevanter.{0,32}Informationen",
                "benutzer.{0,20}(nformieren|benachrichtigen)"
            ],
            "DowntimeNotifications": [
                "Ausfallinformationen",
                "(Informationen).{0,32}(Ausfall|Ausfälle)",
                "Ausfall.{0,32}(benachrichtigen|informieren)"
            ],
            "MandatorySystemNotifications": [
                "(obligatorische|verpflichtende|notwendige|gesetzlich vorgeschriebe|sicherheitsrelevante).{0,20}(System|Service)-?(Mitteilungen|Nachrichten|Meldungen|Hinweise|Benachrichtigungen)"
            ],
            "Reminders": [
                "reminder",
                "Erinnerung",
                "Sie.{0,24}zu erinnern"
            ],
            "Feedback": [
                "Feedback",
                "Rückmeldung(en)?",
                "Vorschläge"
            ],
            "Review": [
                "\\breview(s)?\\b",
                "(?<!Risiko)Bewertung(en)?(?!.{0,20}(Erfolg|Sicherheit|Leistung|erinnerung))",
                "(Umfrage.{0,50}|(?<!externe)(?<!externer) Kunden|Produkt|Ihre[rn]? |, )Bewertung(?!.{0,50}(Erfolg|Sicherheit|Schutz|Leistung|erinnerung))"
            ],
            "Newsletter": ["newsletter(s)?"],
            "Survey": [
                "\\bsurvey(s)?\\b",
                "(Zufriedenheits|Kunden)?Umfragen?",
                "Befragungen",
                "Fragebögen"
            ],
            "CustomerService": [
                "Kunden(-.{0,27})?(dienst|service|betreuung|support|betreuer(funktion)?)",
                "Beantwortung von Kundenfragen",
                "(Beantwortung|Bearbeitung|Verarbeitung).{0,24}(Anfragen|Anliegen)",
                "(?<!technische )(?<!technische[rn] )(Problem|Anfragen).{0,32}(melden|lösen|beheben)",
                "(?<!technischer )(?<!technischen )(?<!/)Support-?(leistungen|anfrage|plattform|Ticket)?",
                "Anfragen nachzukommen",
                "persönliche Beratung",
                "(?<!Ihre )(?<!Ihrer )(?<!technische )(?<!technische[rn] )Unterstützung(?!.{0,32}(Verbesserung|Fehlerbehebung))",
                "Bei Fragen (zur|zu|zum) (?!.{0,32}Recht)(?!.{0,32}Schutz)(?!.{0,32}Verarbeitung)(?!.{0,32}Bestellung)(?!.{Fehlerbehebung})(?!Verbesserung)"
            ],
            "TechnicalSupport": [
                "\\btechnical support\\b",
                "\\btech support\\b",
                "technische[rnm]? (-.{0,27})?(Support|Unterstützung|Probleme|Anfrage|Rückfrage|Administration)",
                "Bereitstellung.{0,32}(Unterstützung|Fehlerbehebung).{0,32}(Produkt|Gerät|System|App)"
            ],
            "FanPage": [
                "Fan(page|seite)",
            ],
            "ChatBot": [
                "\\bchat(-)?bot\\b",
                "\\bVirtueller Assistent\\b"
            ],
            "LiveChat": [
                "\\bLive[- ]Chat\\b",
                "\\bEchtzeit[- ]Chat\\b"
            ],
            "AccountVerification": [
                "\\bKontoverifizierung\\b",
                "Konto.{0,20}verifizieren",
                "Verifizierung.{0,20}(Konto/Account)"
            ],
            "OrderCommunication": [
                "(Bestell|Liefer)bestätigung(en)?",
                "(detail|information|message|notification|alert|notice)(s)?(.){0,20}about( your)? order",
                "(Nachrichten|Benachrichtigungen|Mitteilungen).{0,64}((Produkte)?Bestellung(en)?|Lieferung(en)?|Käufen?)",
                "(Beschwerden?|Fragen?|Hotline|Support).{0,40}((Produkte)?Bestellung(en)?|Lieferung(en)?|Käufen?)",
                "Shop-(Support|Hotline|Team)"
            ],
            "BillingInquiries": [
                "((Ab)?Rechnungs|Zahlungs)(Fragen|Probleme)",
                "(Frage|Probleme?)n?.{0,20}((Ab)?Rechnung|Zahlung|Überweisung)"
            ],
            "PricingInquiries": [
                "(Preis|Kosten)((An)?frage|problem)",
                "((An)?fragen?|Probleme?).{0,20}(Preis(gestaltung|bildung)?|Kosten)\\b"
            ],
            "LegalChanges": [
                "(Änderungen|Aktualisierungen).{0,40}((Geschäfts)?Bedingungen|Richtlinien|Datenschutz(erklärung|richtlinie))",
                "((Geschäfts)Bedingungen|Richtlinien|Datenschutz(erklärung|richtlinie)).{0,20}((ab)?ändern|aktualisieren)",
                "rechtliche Änderungen"
            ],
            "WinnerNotification": [
                "Gewinner.{0,16}benachrichtigen",
                "benachrichtigen.{0,32}(Gewinner|gewonnen)"
            ],
            "MarketingMessage": [
                "(Direkt)?Marketing[- ]?(E-Mail|materialien|informationen|hinweise|kommunikation|mitteilungen)",
                "E-Mail[- ]Marketing",
                "(Angebote|Katalog|Kaufempfehlungen)(?=.* zu senden)",
                "Werbe(kommunikation|hinweise)",
                "werbliche[rn] (E-Mail|Kommunikation|Mitteilungen|Nachrichten|Benachrichtigung)",
                "(Marketing|Produkte|Dienstleistungen|Apps)(?=.*von Interesse)"
            ],
            "SocialMedia": [
                "Social[- ]Media[- ](Auftritte|Funktionen|Seite|(Werbe)?Kampagnen)",
                "(auf|über|per).{0,35}Social Media",
                "(\\bin\\b|über|für|per).{0,35} soziale[rns]? (Medien|Medium|Netzwerke?)"
            ],
            "ProductSafety": [
                "(Sicherheits|Leistungs)(-.{0,32})?Probleme",
                "Produktsicherheitsmitteilungen"
            ],
            "EmergencyContact": ["Notfall-?(Warnung|Hinweis|Meldung|Nachricht|kontakt)"],
            "ErrorReporting": [
                "Fehler.{0,24}(benachrichtigen|melden|senden)",
                "(benachrichtigen|melden|senden).{0,24}Fehler",
                "Crash-Bericht"
            ],
            "TransactionCommunication": [
                "(?=.*(transaction|receipt|purchase))(?=.*(communication|message|notification|e(-)?mail|alert|detail|notice))",
                "(Transaktionen|Überweisung).{0,24}(kommunizieren|Kommunikation|kontaktieren|Kontakt|Nachricht|Meldung|e-?mail)",
                "(Benachrichtigung|Mitteilungen|Nachricht|Meldung|e-?mail).{0,24}(Transaktionen|Überweisung)",
                "Transaktions-Servicemitteilungen"
            ],
            "BirthdayGreeting": ["Geburtstags(gruß|grüße)"],
            "Membership": [
                "(Mitgliedschaft|Abo(nnement)?).{0,64}(Kontakt|kontaktieren|Kommunikation|kommunizieren|Nachricht|Mitteilung|Detail)",
                "(kontaktieren|Kommunikation|kommunizieren|Nachricht|Mitteilung|Detail).{0,64}(Mitgliedschaft|Abo(nement)?)"
            ],
            "LoyaltyProgram": [
                "(Fragen|Benachrichtigungen|Mitteilungen|Kontakt|Informationen).{0,32}(Treue|Bonus)programm",
                "(Treue|Bonus)programm.{0,32}(kommunizieren|mitteilen|benachrichtigen|informieren|senden|bereit(zu)?stellen)"
            ],
            "ChatRoom": ["Chat-?room"],
            "CommercialCommunication": [
                "Kommerzieller? Kommunikation",
                "Kaufgespräch",
                "Werbekommunikation"
            ],
            "AIChat": [
                "(KI|AI).{0,20}Chat"
            ],
        }
    ),
    tech_priv=AttributePattern.from_dict(
        {
            "Anonymization": [
                "Anonymisier(en|t|ung)",
                "de-identifizier(en|t|ung)",
            ],
            "Pseudonymization": ["Pseudonymisier(en|t|ung)"],
            "Aggregation": [
                "Aggregier(en|t|ung)",
                "zusammengefasste.{0,30}(Daten)",
                "(Daten|Informationen)\\b.{0,120}(gemischt|zusammengefasst)"
            ],
            "Shortened": ["(ge|ver)kürz(t|en)", "trunktier(t|en)", "reduzier(t|en)"],
            "DataSeperation": [
                "Trennung.{0,84}Daten",
                "(Daten|Informationen).{0,84}(trennen|trennung)",
                "(Daten|Informationen).*nicht.*(zusammenführen|zusammengeführt|verknüpf(t|en)|kombinier(t|en))",
                "(Zusammenführ|verknüpf)(en|ung).*Daten.*nicht",
            ],
            "Desensitization": ["desensibilisier(en|t|ung)", "schwärzen", "geschwärzt"],
        }
    ),
    tech_sec=AttributePattern.from_dict(
        {
            "Encryption": [
                "^(?!.*https).*(?<!un)Verschlüssel(n|t|ung)",
            ],
            "Monitoring": [
                "monitoring",
                "^(?!.*Datenschutzbeauftragte).*(?<!video)überwach(t|ung)",
            ],
            "TwoFactorAuth": [
                "zweistufiges? (Verifizierung(sprogramm)?)",
                "(Zwei|2|Mehr|Multi)-Faktor-Authentifizierung"
            ],
            "HashedPassword": ["Hash-Passwor[dt]", "gehashtes Passwort"],
            "MutualAuthentication": ["gegenseitige Authentifizierung"],
            "ProhibitedDefaultPassword": [
                "(unzulässige|verbotene|nicht erlaubte|unerlaubte)s?.{0,32}Standardpass(wort|wörter)"
            ],
        }
    ),
    cont_sec=AttributePattern.from_dict(
        {
            "DataProcessingAgreement": [
                "(Auftrags|Daten)verarbeitungs(vereinbarung|vertrag)",
                "Vertrag.{0,24}gemeinsame Verantwortlichkeit",
                "Vereinbarung zum Datentransfer",
                "Data Transfer Agreement"
            ],
            "StandardContractualClauses": [
                "Standard(vertrags)?klauseln", 
                "Standardvertrag"
            ],
            "AdequacyDecision": [
                "angemessenes Datenschutzniveau",
                "Angemessenheits(mechanism(us|en)|beschluss)",
            ],
            "Audits": [
                "audits",
                "Sicherheitsprüfung",
                "überprüf(t|en).{0,48}Sicherheitsstandards",
                "Sicherheitsstandards.{0,48}überprüf(t|en)"
            ],
            "Confidentiality": [
                "\\bvertraulich(keit)?",         
                "Geheimhaltungs(pflicht|verpflichtung)"
            ],
            "BindingContractualRules": [
                "Datenschutzgrund(sätze|linien).{0,32}verpflichten",
                "verbindliche[rn]? vertragliche[rn]? Verpflichtungen",
                "verbindliche[rn]?.{0,20}Datenschutzvorschriften",
            ],
        }
    ),
    chosen=AttributePattern.from_dict(
        {
            "AuthorizedAgent": [
                "bevollmächtigte[rn]? Vertreter",
                "Ihr Vertreter",
                "(?<!von Ihnen) (autorisiert|bevollmächtigt).{0,48}(Person|Vertreter|Partei|Bevollmächtigter?)" # von Ihnen... -> DesignatedPerson
            ],
            "DesignatedPerson": [
                "(?<=von Ihnen) (autorisiert|bevollmächtigt).{0,48}(Person|Vertreter|Partei|Bevollmächtigter?)",
                "(benannte|festgelegte) (person|(Nachlass)?kontakt)",
                "Vertrauensperson",
                "(Person|Nachfolger) ((zu )?benennen|bestimmen|festlegen)"
            ],
            "AppointedRepresentatives": [
                "(bestellte|benannte)[rnm]? Vertreter"
            ],
            "LegalRepresentative": [
                "gesetzliche[rn]? Vertreter",
                "gesetzlich vorgeschriebener?.{0,48}(Partei(en)?|Person(en)?|Vertretern?)\\b"
            ],
            "Caregiver": [
                "Pflege(r|rin|kraft)",
                "(?<!Kunden)Betreu(er|rin|ungskraft)"
            ],
            "Invitee": [
                "eingeladene (Person|Mitglieder|Nutzer)",
                "Eingeladene[rn]?"
            ],
            "Proxy": ["Proxy", "Stellvertret(er(in)?|ender?)"],
            "LegalGuardian": [
                "Erziehungsberechtigte[rns]?",
                "gesetzliche[rn] Vormund"
            ],
            "AuthorizedUser": ["(berechtigte|autorisierte)[rn]? (Be)?Nutzer"],
            "TrustedIndividual": [
                "vertrau(ten|enwürdige[rn]?) (Person|Kontakt)"
            ],
            "DesignatedAdministrator": ["(bestellte|beauftrage)[rn]? (Verwalter|Administrator)"],
            "FamilyMember": ["Familienmitglied", "\\bVerwandte", "Angehörige"],
        }
    ),
    profiling=AttributePattern.from_dict(
        {
            "NotProfiling": [
                "(nicht|kein(?!e Auswirkung)).{0,84}(Profil(erstellung|bildung|e)|profiling)",
                "Profil(erstellung|bildung).{0,96}nicht (statt|vor|ein)"
            ]
        }
    ),
    automated_decision=AttributePattern.from_dict(
        {
            "NotAutomatedDecisionMaking": [
                "(nicht|keine|verzichten).{0,64}(voll)?(automatische|automatisierte|maschinelle?)[rn]?.{0,32}(Entscheidung(sfindung)?|Bewertung)",
                "(nicht|keine|verzichten).{0,32}Entscheidungen.{0,96}automatisierten (Verarbeitung|Verfahren)",
                "(voll)?(automatisierte|automatische) (Entscheidungsfindung|Bewertung|Entscheidung).{0,96}nicht (statt|vor|ein)",
                "erfolgt nicht (automatisch|automatisiert)"
            ]
        }
    ),
    certifications=AttributePattern.from_dict(
        {
            "ISO/IEC 27001:2013": ["ISO/IEC 27001:2013"],
            "ISO/IEC 27701:2019": ["ISO/IEC 27701:2019"],
            "ISO/IEC 27018:2019": ["ISO/IEC 27018:2019"],
            "SOC 2 Type II": ["SOC 2 Type? II"],
            "PCI DSS": ["PCI DSS"],
            "ETSI EN 303 645": ["ETSI EN 303 645"],
            "CSA STAR": ["CSA STAR"],
        }
    ),
    user_responsibility=AttributePattern.from_dict(
        {
            "BystanderNotice": [
                "\\bbystander notice\\b",
                "notice to bystanders",
                "inform people around you",
                "they are also aware",
                "(?=.*(inform|notify|make aware))(?=.*(people around you|bystanders|others|those around you|anyone))",
                "(display|post)(.){0,32}(signage|notice|warning)",
                "\\bprovide(.){0,20}notice\\b",
                "responsible for (notifying|inform) other(s)?",
            ],
            "ParentalResponsibility": [
                "Verantwortung de[rs] Eltern(teils?)?(?=.*(Kinder|Minderjährige))",
                "Eltern(?=.*(Verantwortung|verantwortlich|Haftung|haften))(?=.*(Kinder|Minderjährige))"
            ],
            "ThirdPartyData": [
                "Daten Dritter",
                "Daten, die Dritt(en|anbieter) gehören"
            ],
        }
    ),
)
""" German language attribute patterns. """

#------------------------------------------------------------------------------------------

DE_DURATION_PATTERN_CONFIG: DurationPattern = DurationPattern(
    unit=AttributePattern.from_dict(
        {
            "Days": ["\\btag(e|en)?\\b"],
            "Weeks": ["\\bwochen?\\b"],
            "Months": ["\\bmonat(e|en)?\\b"],
            "Years": ["\\bjahr(e|en)?\\b"],
            "Hours": ["\\bstunden?\\b"],
            "Minutes": ["\\bminuten?\\b"],
            "Seconds": ["\\bsekunden?\\b"],
        }
    ),
    length=AttributePattern.from_dict(
        {
            "1": ["\\b1\\b", "\\beins\\b", "\\beine[rnms]?\\b"],
            "2": ["\\b2\\b", "\\bzwei\\b"],
            "3": ["\\b3\\b", "\\bdrei\\b"],
            "4": ["\\b4\\b", "\\bvier\\b"],
            "5": ["\\b5\\b", "\\bfünf\\b"],
            "6": ["\\b6\\b", "\\bsechs\\b"],
            "7": ["\\b7\\b", "\\bsieben\\b"],
            "8": ["\\b8\\b", "\\bacht\\b"],
            "9": ["\\b9\\b", "\\bneun\\b"],
            "10": ["\\b10\\b", "\\bzehn\\b"],
            "14": ["\\b14\\b", "\\bvierzehn\\b"],
            "15": ["\\b15\\b", "\\bfünfzehn\\b"],
            "20": ["\\b20\\b", "\\bzwanzig\\b"],
            "24": ["\\b24\\b", "\\bvierundzwanzig\\b"],
            "30": ["\\b30\\b", "\\bdrei(ß|ss)ig\\b"],
            "48": ["\\b48\\b", "\\bachtundvierzig\\b"],
            "60": ["\\b60\\b", "\\bsechzig\\b"],
            "90": ["\\b90\\b", "\\bneunzig\\b"],
            "180": [
                "\\b180\\b",
                "\\bein[- ]?hundert (und )?achtzig\\b",
                "einhundertachzig"
            ],
            "365": [
                "\\b365\\b",
                "\\bein[- ]?hundert (und )?fünf[- ]? (und )?sechzig\\b",
                "dreihundertfünfundsechzig"
            ],
        }
    ),
)
""" German language duration patterns. """

#------------------------------------------------------------------------------------------

DE_DATE_PATTERN_CONFIG: DatePattern = DatePattern(
    {
        "%Y-%m-%d": "\\b(\\d{4})-(\\d{1,2})-(\\d{1,2})\\b",
        "%Y/%m/%d": "\\b(\\d{4})/(\\d{1,2})/(\\d{1,2})\\b",
        "%m/%d/%Y": "\\b(\\d{1,2})/(\\d{1,2})/(\\d{4})\\b",
        "%m-%d-%Y": "\\b(\\d{1,2})-(\\d{1,2})-(\\d{4})\\b",
        "%d.%m.%Y": "\\b(\\d{1,2})\\.(\\d{1,2})\\.(\\d{4})\\b",
        "%d/%m/%Y": "\\b(\\d{1,2})/(\\d{1,2})/(\\d{4})\\b",
        "%d-%m-%Y": "\\b(\\d{1,2})-(\\d{1,2})-(\\d{4})\\b",
        "%B %d, %Y": "\\b(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\\s+(\\d{1,2}),?\\s+(\\d{4})\\b",
        "%d %B %Y": "\\b(\\d{1,2})\\s+(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\\s+(\\d{4})\\b",
        "%b %d, %Y": "\\b(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)[a-z]*\\.?\\s+(\\d{1,2}),?\\s+(\\d{4})\\b",
        "%d %b %Y": "\\b(\\d{1,2})\\s+(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)[a-z]*\\.?\\s+(\\d{4})\\b",
        "%m/%d/%y": "\\b(\\d{1,2})/(\\d{1,2})/(\\d{2})\\b",
        "%d.%m.%y": "\\b(\\d{1,2})\\.(\\d{1,2})\\.(\\d{2})\\b",
        "%Y%m%d": "\\b(\\d{4})(\\d{2})(\\d{2})\\b",
        "%B %Y": "\\b(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember),?\\s+(\\d{4})\\b",
        "%b %Y": "\\b(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)[a-z]*\\.?\\s*,?\\s+(\\d{4})\\b",
    }
)
""" German language date patterns. """