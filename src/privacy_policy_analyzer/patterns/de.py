###=========================================================================
### script in progress

# new attributes will be added once the labeling is done

##U: incomplete -- need more data
##X: no examples in the data yet
###: last position

###=========================================================================


from privacy_policy_analyzer.analysis.attributes import (
    AttributePattern,
    AttributePatterns,
    DatePattern,
    DurationPattern,
)
from privacy_policy_analyzer.crawl.splitter import SplitterPattern

# ------------------------------------------------------------------------------------------

DE_SPLITTER_CONFIG: SplitterPattern = SplitterPattern.from_parts(
    replace_words=[
        ("„", "\"" ),
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
        "Art\\. [0-9] para\\. s\\.$"
    ],
)
""" German language splitter configuration. """

#------------------------------------------

EN_PATTERN_CONFIG: AttributePatterns = AttributePatterns(
    data_type=AttributePattern.from_dict(
        {
            "PersonalData": [
                "(?<!nicht[- ])(?<!sensitive)(?<!sensitive[rn])(?<!sensible)(?<!sensible[rn]).{0,20}(Daten|Informationen|Details)",
                "(?<!Spezialkategorien von )(persönliche[rn]?|personenbezogene[rn]?).{0,20}(Daten|Informationen|Details)",
                "Ihren?.{0,20}(Daten|Informationen|Details)",
                "(Daten|Informationen|Details) über Sie"
            ],
            "SensitiveData": [
                "sentitive[rn]?.{0,20}(Daten|Informationen|Details)"
            ],
            "SpecialCategoryData": [
                "Spezialkategorie von (persönlichen|personenbezogenen) Daten",
                "Spezialkategorie (persönlicher|personenbezogener) Daten"
            ],
            "GeneralInformation": [
                "allgemeine[rn]?.{0,20}(Daten|Informationen)"
            ],
            "PII": [
                "PII",
                "(?<!nicht[- ])persönlich identifizierbare[rn]? Informationen",
                "(Daten|Informationen)(.){0,30}(?!die sie nicht) identifizieren",
                "Identifizierung (.){0,20} natürlichen Person",
                "natürliche Person zu identifizieren" ##U
            ],
            "NPII": [
                "NPII",
                "non-personally identifiable information",
                "nicht[- ]personenbezogene Informationen"
            ],
            "SetupInformation": [
                "Setup[- ]?information",
            ],
            "DeviceInformation": [
                "Geräte?(information|daten)",
                "(Informationen|Daten).{0,20}(ü|ue)ber.{0,20}(Gerät|Produkt)"
            ],
            "DeviceName": [
                "(Geräte|Produkt|Modell)name",
                "Name des (Geräte?s|Produkte?s)",
                "Kameraname"
            ],
            "DeviceType": [
                "(Geräte|Produkt)(typ|modell|art)",
                "(Typ|Modell|Art) des (Geräte?s|Produkte?s)",
                "Tele(f|ph)onmodel",
                "Hardware(modell|typ|art)"
            ],
            "ProductInfo": [
                "Produkt(information|daten|detail)",
                "(Information(en)?|Details?) über .{0,20}Produkt"
            ],
            "ManufacturerInformation": [
                "(Geräte)?[Hh]ersteller(informationen|details)",
                "(Informationen|Details).{0,20}Herstellers?",
            ],
            "TechnicalInformation": ["technische (Informationen|Daten)"],
            "OperatingSystem": [
                "Betriebssystem",
                "operatives System"
                ],
            "FirmwareVersion": ["Firmware[- ]?version"],
            "SoftwareVersion": ["Software[- ]?version"],
            "HardwareInformation": [
                "Hardware(informationen|daten|details)",
                "(Informationen|Details).{0,20}hardware"
            ],
            "HardwareVersion": ["Hardware[- ]?version"],
            "BrowserInformation": [
                "Browser(informationen|daten)",
                "Informationen.{0,20}Browser"
            ],
            "BrowserType": [
                "Browsertyp",
                "verwendente[rn]? Browsers?",
                "(Typ|Art) des Browsers?"
            ],
            "BrowserVersion": [
                "Browserversion",
                "Version des.{0,20}Browsers"
            ],
            "AppVersion": [
                "Appversion",
                "Version der.{0,20}Apps?"
            ],
            "AppStatus": ["Appstatus"],
            "AppID": [
                "App[- ]ID",
                "App identifier",
                "App[- ]Identifizierer"
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
                "Internet(dienst)?anbieter",
                "Internetdienstleister",
                "Internetprovider",
                "\\bISP\\b"
            ],
            "NetworkData": [
                "(?<!media )network(.){0,20}(data|information)",
                "network activity",
                "(?<!soziale )(?<!sozialen )Netzwerk(daten|dateien|information(en)?)",
                "Netzwerkanfrageinformation(en)?"
            ],
            "NetworkStatus": ["Netzwerkstatus"],
            "NetworkOperator": ["Neth(werk)?betreiber"],
            "CustomerProprietaryNetworkInformation": [
                "customer proprietary network information",
                "kunden(eigene|bezogene) Netzwerk(informationen|daten)",
                "\\bCPNI\\b",
            ],
            "OtherElectronicNetworkActivityInformation": [
                "other electronic network activity information",
                "(sonstige|andere) elektronische Netzwerkaktivitäteninformationen",
                "\\bOENAI\\b",
            ],
            "SMSStorage": ["SMS-Speicher"],
            "MobileNetworkData": ["mobilen? Netzwerk(-.{0,20})?(daten|informationen)"],
            "MobileNetworkCode": [
                "Mobilfunknetzcode",
                "mobilen? Netzwerk(-.{0,20})?code"
            ],
            "MobileCountryCode": [
                "Mobilfunk-Ländercode",
                "mobilen?.{0,20}Ländercode"
            ],
            "ConnectionData": ["Verbindungs(daten|informationen)"],
            "DataAmount": [
                "Datenmenge",
                "Menge.{0,10}Daten",
                "Netzwerkbandbreitennutzung"
            ],
            "NumberOfRequests": [
                "(An)?zahl der Abfragen",
                "getätigte Abfragen"
            ],
            "WiFiData": [
                "Wi(-)?Fi (Daten|Informationen)"
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
                "(Geräte)?tastaturinformationen",
                "Informationen.{0,20}Tastatur",
            ],
            "UsageData": [
                "(Nutzungs|Aktivitäts)(daten|informationen|verhalten|details|statistik|verlauf|gewohnheiten)",
                "(statistische) Daten",
                "(Informationen|Häufigkeit|Daten|Details).{0,20}Nutzung",
                "Nutzung.{0,20}(Dienste|Geräte|Produkte|Funktionen)",
            ],
            "UsageDuration": [
                "(Seiten)?verweils(dauer|zeitraum)",
                "Zugriffs(dauer|zeitraum)",
                "(Dauer|Zeitraum).{0,20}(App|Dienst|Funktion|(Web)?Seite(nzugriffs?))"
            ],
            "DeviceInteractions": [
                "Geräteinteraktionen",
                "Interaktionen mit (Produkten|Geräten)"
            ],
            "AppInteraction": [
                "App[- ]Interaktionen",
                "Interaktionen.{0,10}Apps?",
            ],
            "DownloadHistory": ["Download(-.{0,15})?verlauf"],
            "EngagementMetrics": ["engagement (data|information|metric|statistic)"], ##X
            "TelemetryData": ["Telemetrie(informationen|daten)"],
            "PerformanceData": [
                "(?<!conversion )performance(.){0,20}(data|information|metric|statistics)" ##X
            ],
            "DiagnosticData": ["Diagnose(daten|informationen)"],
            "StatisticalData": ["statistische[rn]? (Daten|Informationen)"],
            "DeviceStatistics": [
                "(Geräte|Produkt)statistik",
                "Statistik.{0,10}(Gerät|Produkt)"
            ],
            "SettingsData": ["Einstellungen"], ##U
            "ConfigurationData": ["Konfigurations(daten|informationen)"],
            "UserPreferences": [
                "(Deine[rn]?|Ihre[rn]?|persönliche[rn]?) (Präferenzen|Vorlieben)",
                "(Nutzer)?Präferenzen",
                "(Nutzer)?Vorlieben"
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
            "OnlineStatus": ["Onlinestatus"],
            "BatteryData": ["(Batterie|Akku)(daten|informationen|status|verbrauch)"],
            "MemoryUsage": ["Speichernutzung", "RAM[- ]Auslastung"],
            "StorageUsage": [
                "(Speicher|Festplatten)(nutzung|auslastung)",
                "verwendete Speicherkapazität",
                "Nutzungsinformationen.{0,20}Speicher"
            ],
            "CpuUsage": [
                "(CPU|Prozessor)[- ](nutzung|auslastung)",
                "Nutzungsinformationen.{0,20}CPU"
            ],
            "ScreenUnlocks": [
                "(Bildschirm|Gerät).{0,20}entsperr(en|ung)",
                "Anzahl der Entsperrungen",
                "Bildschirmaktivierung(en)?"
            ],
            "UsageFrequency": [
                "Nutzungshäufigkeit",
                "wie oft Sie.{0,20}(nutzen|verwenden)",
                "Häufigkeit(.){0,15}Nutzung",
            ],
            "BrowsingActivity": [
                "Browser(aktivität|verlauf|historie)",
                "Browsing[- ](aktivität|verlauf|historie)"
            ],
            "ViewedContent": [
                "angesehene Inhalte",
                "Inhalte.{0,20}(angesehen|aufgerufen|angeklickt) haben",
                "Bildaufrufe",
            ],
            "VisitedPages": [
                "(Seiten|Website)aufrufe",
                "(aufgerufene|angesehene|besuchte) (Seiten|Websites)"
                "(Websites|Seiten).{0,20}(aufgerufen|angesehen|besucht) haben",
            ],
            "ClickedLinks": [
                "angeklickte Links",
                "Links.{0,20}geklickt haben"
            ],
            "MouseMovements": [
                "Mausbewegung(en)?",
                "Mausaktivität(en)?",
                "(Maus|mouse)[- ]Tracking",
                "mouse-over",
            ],
            "Keystrokes": ["keystroke", "key press", "keyboard input"], ##X
            "SearchHistory": [
                "Such(verlauf|historie)",
                "Suchanfrage"
            ],
            "PageInteractions": [ ##X
                "page interaction",
                "website interaction",
                "site interaction",
            ],
            "LogData": [
                "((Standard-)?System|Netzwerk|Geräte|Absturz-)protokoll(e|daten)?",
                "Protokoll(e|daten|informationen)",
                "Sitzungsereignisse"
            ],
            "LogFiles": ["log file"],##X
            "DeviceLogs": ["Geräteprotokoll(daten)?"],
            "DeviceHistory": ["Geräte(verlauf|historie)"],
            "Errors": [
                "(Absturz|Fehler|Crash).{0,10}(daten|informationen|berichten?|ereignissen?|nachrichten|protokollen?|details|abfragen)",
                "\\b(Absturz|Abstürze)\\b",
                "\\bFehler\\b",
            ],
            "AccessLogs": [ ##X
                "Zugriffsprotokolle?",
                "access log",
                "access report",
                "access message",
                "security log",
            ],
            "ActivityLogs": [ ##X
                "activity (log|history)",
                "account activity",
                "timestamp of(.){0,32}activity",
                "\\bevent log(s)?\\b",
            ],
            "ActivityStatus": [
                "Aktivität(s|en)status",
            ],
            "NotificationLogs": ["notification log(s)?\\b"], ##X
            "MaintenanceLogs": ["maintenance log", "maintenance record"], ##X
            "DrivingEvents": ["driving event"], ##X
            "AppEvents": ["app event"], ##X
            "DeviceEvents": ["device event"], ##X
            "DeviceAlerts": [
                "Gerätebenachrichtigung(en)?",
                "Benachrichtigungen.{0,10}Geräte?s",
            ],
            "DateTime": [
                "(?<!jeder )(?<!echt)(?<!von )(?<!zur )(?<!irgendeiner )zeit\\b",
                "datum\\b"
            ],
            "MACAddress": ["MAC[- ]Adresse"],
            "IPAddress": ["IP[- ]Adressen?", "\\bIP\\b"],
            "SerialNumber": ["Seriennummer"],
            "DeviceTemperature": [
                "(Geräte|Produkt)temperatur",
                "Temperatur des (Geräte?s|Produkte?s)",
            ],
            "ScheduleTimes": [ ##X
                "schedule(.){0,20}time",
                "\\bschedules\\b",
                "scheduling (.){0,20}setup",
                "wakeup time setup",
            ],
            "Identifier": [
                "Identifikationsnummern?",
                "persönliche Identifizierer",
                "\\bIdentifizierer\\b",
                "ID-Nummer",
                "Kennnummer",
                "Kundennummer"
            ],
            "AccountID": ["Konto[- ]ID"],
            "DeviceID": [
                "(Geräte|Produkt)[- ]U?ID",
                "Gerätenummer",
                "Geräteidentifizierung"
            ],
            "RandomID": ["random ID", "random identifier"], ##X
            "AdvertisingID": [
                "Werbe[- ]ID",
                "IDFA"
            ],
            "SessionID": ["Sitzungs[- ]ID"],
            "UserID": ["(Be)?Nutzer[- ]ID"],
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
            "SIMInformation": ["SIM.{0,20}(daten|informationen|fehler)"],
            "WebsiteInformation": [
                "Website[- ](informationen|daten)",
                "Webseiten(informationen|daten)"
            ],
            "Referrer": ["referrer", "referring(.){0,20}(URL|website)", "referer"], ##X
            "HostName": ["host name", "hostname"], ##X
            "URL": ["URL", "uniform resource locator", "hyperlink"], ##X
            "DomainName": ["domain name", "website domain"], ##X
            "Clicks": [
                "Klicks", 
                "(Seiten|Schaltflächen)klicks"
            ],
            "ScrollData": ["scroll data", "\\bscroll(s)?\\b"], ##X
            "Clickstream": ["click( )?stream"],##X
            "PageResponseTime": ["page response time", "website response time"], ##X
            "ScreenResolution": ["(Bildschirm|Anzeige)auflösung"],
            "LocationData": [
                "Standort(daten|informationen|bereich|berechtigung)",
                "Standort.{0,20}(?<!Meta)(Informationen|Daten|Diensten?)",
                "Ihre[nm].{0,15}Standort"
            ],
            "LocationHistory": ["Standort(verlauf|historie)"],
            "GPSData": ["GPS[- ](daten|informationen|koordinaten)"],
            "Coordinates": [
                "Koordinaten",
                "Längengrad",
                "Breitengrad"
            ],
            "AltitudeData": ["Höhendaten", "Erhöhungsdaten"], ##U
            "Timezone": ["Zeitzonen?"],
            "Address": [
                "(?<!Email[ -])(?<!E-mail[ -])(?<!IP[ -])Address",
                "(Liefer|Kontakt|Empfänger|Sender)addresse"
            ],
            "AreaCode": [
                "Ländercode",
                "PLZ",
                "Postleitzahl",
                "Standortbereichscode"
            ],
            "City": ["\\bStadt\\b"], ##U
            "Region": ["Region", "Land", "Bundesland", "Landkreis"], ##U
            "Country": [ ##U
                "(?<!outside of your )(?<!to the )Land",
                "\\bLand\\b"
                ], 
            "Language": [
                "Sprache",
                "Spracheinstellung(en)?",
                "Systemsprache"
            ],
            "Name": [
                "(?<!Geräte)(?<!Produkt)(?<!App)(?<!Vor)(?<!Nach)(?<!Nick)(?<!Spitz)(?<!Benutzer)(?<!Nutzer)(?<!Firmen)(?<!Halter)name\\b(?!:)(?! (des|der))(?! (Ihrer|Ihres))(?! (von|vom))", ##U
                "vollständiger name",
            ],
            "FirstName": ["Vornamen?"],
            "LastName": [
                "Nachname",
                "Familienname"
            ],
            "Nickname": [
                "Nickname",
                "Spitzname"
            ],
            "DemographicData": ["demografische(.){0,20}(Daten|Informationen)"],
            "LifestyleInformation": ["lifestyle(.){0,20}(information|data)"],##X
            "NumberOfChildren": [
                "Kinder(an)?zahl",
                "(Anz)?zahl (der|Ihrer) Kinder"
            ],
            "PetInformation": [
                "Hautsier(informationen|daten)",
                "(Informationen|Daten) über(.){0,20}Haustiere?",
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
            "PhysicalBodyMetrics": [##X
                "physical body(.){0,20}(metric|measurement)",
                "body composition (data|information)",
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
            "SexualOrientation": ["sexuelle Orientierung"],##U
            "SexualLife": ["\\bSexualleben\\b"],
            "BiographicInformation": ["biografische (Informationen|Daten)"],
            "EducationalBackground": [
                "Bildungshintergrund",
                "Bildungsgrad",
                "Bildungsstand",
                "Bildungsniveau,"
            ],
            "EmploymentBackground": [ ##X
                "employment(.){0,20}background",
                "job title",
                "occupation",
                "work history",
            ],
            "Employer": [ ##U
                "\\bArbeitgeber\\b",
                "company you work for",
                "organization you work for",
                "your(.){0,20}company",
            ],
            "Ethnicity": ["Ethnien?"],
            "PoliticalAffiliations": [
                "politische (Meinungen|Ansichten|Überzeugungen|Partei)\\b"
            ],
            "ReligiousBeliefs": ["religiöser? (Glaube|Ansichten|Überzeugungen)\\b"],
            "CriminalOffenses": [
                "(kriminelle|strafbare) Handlungen",
                "Straftaten",
                "kriminelle Vergangenheit",
            ],
            "CurriculumVitae": ["\\bLebenslauf\\b"],
            "CandidateInformation": ["\\bcandidate (information|data)\\b"], ##X
            "TradeUnionMembership": ["\\bGewerkschaftsmitgliedschaft(en)?\\b"],
            "SocialAssistanceData": ["\\bsoziale Hilfen?\\b"],
            "ContactInformation": ["Kontakt(informationen|info|daten|details)"],
            "EmailAddress": [
                "E-Mail-Adresse",
                "E-Mail",
            ],
            "PhoneNumber": [
                "Telefonnummer",
                "Mobilfunknummer",
                "Mobiltelefonnummer",
                "Festnetznummer"
            ],
            "EmergencyData": ["emergency(.){0,20}(contact|information|data)"], ##X
            "FamilyInformation": [ ##X
                "family(.){0,20}(information|data|details)",
                "information about(.){0,20}family",
                "family member(s)?",
                "family relationship",
            ],
            "FriendsInformation": [ ##X
                "friend(s)?(.){0,20}(information|data)",
                "information about(.){0,20}friend",
            ],
            "IdentityInformation": [
                "Identitäts(informationen|daten|details)",
                "Informationen über(.){0,20}Ihre Identität",
                "(physisch|physiologisch|genetisch|psychisch|wirtschaftlich|kulturell|sozial)en Identität",
                "Informationen.{0,60}identifiziert werden (kann|können)" ##U
            ],
            "GovernmentID": [
                "nationale Identifikationsnummer"##U
            ],
            "Passport": ["\\b(Personal)Ausweis\\b"],
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
                "(Be)Nutzer(information(en)?|daten|details)",
                "(Informationen|Daten|Details) des (Be)?Nutzers"
                ],
            "AccountData": [
                "\\b((Be)?nutzer)?Konto(daten|informationen|details)",
                "(Daten|Informationen|Details).{0,20}Kontos?"
            ],
            "AccountAge": ["account age", "how long you have had an account"], ##X
            "AccountNumber": [
                "\\bKontonummer"
                "\\bKonto-.{0,20}nummer"
            ],
            "AccountSettings": ["Kontoeinstellungen"],
            "SubscriptionData": ["Abonnements"], ##U
            "ProfileData": ["Profil(daten|informationen|details)"],
            "ProfilePicture": ["Profilbild", "Profilfoto", "Avatar"],
            "Username": [
                "Benutzername",
                "Nutzername"
            ],
            "SocialMediaDetails": [
                "(Details|Informationen).{0,40}soziale[rn]? (Medien|Netzwerke)" ##U
            ],
            "ThirdPartyHandle": [ ##X
                "social media(.){0,64}handle\\b",
                "third(-| )party(.){0,64}handle\\b",
            ],
            "PermissionsData": [
                "\\bZugriffsrechte",
                "Berechtigungen"
            ],
            "CameraPermissions": ["\\bKamerazugriffsrechte?\\b"],
            "MicrophonePermissions": ["\\bMikrofonzugriffsrechte\\b"],
            "LocationPermissions": ["\\bStandortzugriffsrechte\\b"],
            "ContactsPermissions": ["\\bKontaktzugriffsrechte\\b"],
            "StoragePermissions": ["\\bSpeicherzugriffsrechte\\b"],
            "NotificationPermissions": ["\\bBenachrichtigungszugangsrechte\\b"],
            "Lighting": [
                "\\bBeleuchtung\\b",
                "\\bBelichtung\\b"
            ],
            "SensorData": ["Sensor(daten|informationen)"],
            "EnvironmentalData": [
                "(Umwelt|Umgebungs)(daten|informationen|details)",
                "Umwelteigenschaftenwert",
                "\\bECV\\b",
            ],
            "MotionData": [
                "\\bBewegungsdaten\\b" ##U
            ],
            "PresenceData": ["presence"], ##X
            "AmbientLightData": ["ambient light"], ##X
            "TemperatureData": ["Temperatur"],
            "HumidityData": ["Luftfeuchtigkeit"],
            "MoistureData": ["\\bFeuchtigkeit"],
            "NoiseLevel": ["Geräusch(level|niveua|pegel)"], ##U
            "PrecipitationData": ["precipitation", "\\brain\\b"], ##X
            "WindData": ["\\bWind\\b"],
            "AirQualityData": ["Luftqualität"],
            "WaterReadings": ["water reading(s)?", "water sensor reading(s)?"], ##X
            "CarbonMonoxideData": [
                "Kohlenstoffmonoxid",
                "\\bCO(?!-)\\b"
            ],
            "CarbonDioxideData": [
                "Kohlenstoffdioxid",
                "CO2"
            ],
            "SmokeData": ["\\bRauch"], ##U
            "OutdoorData": ["outdoor (data|information|detail)"], ##X
            "WeatherData": ["Wetter(daten|informationen|details)"],
            "WaterConsumptionData": ["Wasserverbrauch"],
            "WateringSchedule": ["watering schedule", "watering timetable"], ##X
            "GasConsumptionData": ["Gasverbrauch"],
            "DirtLevel": ["dirt level", "dust level", "level(s)? of dirt"], ##X
            "PresenceOfPeople": [ ##X
                "presence of(.){0,20}people",
                "people detected",
                "(humand|people|person)(s)? (detected|present|detection|presence)",
                "where (human|people|person)(s)? are (located|present)",
            ],
            "PresenceOfPets": ["presence of(.){0,20}pet", "pets detected"], ##X
            "CleaningHistory": ["cleaning history"], ##X
            "HeatingSchedule": ["heating schedule", "heating timetable"], ##X
            "AppName": [
                "App(.){0,16}name",
                "App-Bezeichnung"
            ],
            "HomeName": ["home(.){0,16}name", "name of home"], ##X
            "FloorplanData": ["floorplan"], ##X
            "FloorType": ["floor type", "type(s)? of floor"], ##X
            "ObjectData": [ ##X
                "object (data|information|detail)",
                "type(s)? of object",
                "obstacle",
            ],
            "RoomName": ["room name", "name of room"], ##X
            "OperatingPowerData": ["operating power"], ##X
            "EnergyConsumptionData": [
                "Energieverbrauch"
            ],
            "VoltageData": ["Spannung"], ##U
            "EnergyProductivityData": ["energy productivity", "energy production data"], ##X
            "HealthData": [
                "(?<!öffentliche )(?<!öffentlichen )(Gesundheit)" ##U
            ],
            "HealthStatus": ["health(.){0,20}status"], ##X
            "SleepData": [##X
                "sleep(.){0,20}(data|information)",
                "nap (data|information|pattern)",
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
            "BodyWaterData": ["body water", "hydration data"], ##X
            "FitnessGoals": ["fitness goal", "exercise goal", "activity goal"], ##X
            "FitnessChallengeResults": [ ##X
                "fitness challenge result",
                "exercise challenge result",
                "personal bests",
            ],
            "PhysicalActivity": [ ##X
                "physical activity",
                "exercise activity",
                "workout activity",
            ],
            "WorkoutSummaries": ["\\bworkout (summaries|summary)"], ##X
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
                "Periode(daten|informationen)" ##U
            ],
            "BoneDensity": ["Knochendichte"],
            "DesignFiles": ["design file", "design document", "design specification"], ##X
            "FinancialData": ["Finanzdaten"], ##U
            "IncomeData": ["Einkommen"], ##U
            "FinancialStatus": ["Finanzstatus"],
            "CreditScore": ["Kreditwürdigkeit", "Bonität"],
            "MembershipData": [ ##X
                "membership (data|information|details|level)",
                "membership status",
            ],
            "Maps": [ ##X
                "\\bmap(s)?\\b",
            ],
            "MapAreaNames": ["area names of map", "map area name(s)?"], ##X
            "MediaData": [
                "(Medien|Multimedia)(daten|informationen|dateien)",
                "(Multi)?mediale (Daten|Dateien|Informationen|Details)"
            ],
            "AudioData": [
                "(Audio|Geräusch|Klang)(daten|signale?|aufnahmen?|informationen|wiedergabe|dateien)"
            ],
            "VideoData": [
                "video(daten|signale?|aufnahmen?|dateien|informationen|aufzeichnungen)",
                "Videos"
            ],
            "ImageData": [
                "(Bild|Foto|Photo)(.){0,20}data",
                "Bilder\\b",
                "(F|Ph)otos?\\b",
                "(F|Ph)otografien?\\b",
            ],
            "Screenshots": [
                "Screenshot",
                "Bildschirmfoto"
            ],
            "TouchData": ["\\bTouch(.){0,20}(daten|informationen|interaktionen|signale)"],
            "VoiceCommands": ["Sprachbefehle?"], ##U
            "VoiceCharacteristics": ["voice characteristic", "voice feature"], ##X
            "TextData": ["\\btext(.){0,20}(data|information|content)"], ##X
            "Drawings": [
                "(?<!Auf)Zeichnung(en)?",
                "Skizzen?",
                "Illustration(en)?",
            ],
            "Music": [
                "\\bMusic\\b",
                "Musik(daten|informationen|dienst(e|en)?|dateien)"
            ],
            "OtherFileData": ["other file(s)?", "other document(s)?", "other content"], ##X
            "TemporaryData": ["temporäre (daten|informationen)"],
            "TemporaryFiles": ["\\btemporäre datei(en)?\\b"],
            "Files": ["\\bDatei(en)?\\b", "\\bDokumente?\\b"], ##X too general!
            "GardenDesign": [ ##X
                "(?=.*garden)(?=.*(data|information|detail|created|planned))"
            ],
            "PersonalBehaviorData": [
                "Verhalten", ## zu allgemein!
                "Verhaltens(daten|informationen)"
            ],
            "HabitData": ["Gewohnheiten\\b"], ##U
            "InterestData": [
                "\\bInteressen\\b", ##X zu allgemein!
                "interessensbezogene (Daten|Informationen|Details)",
            ],
            "HobbyData": [
                "\\bHobby\\b",
                "\\bHobbies\\b"
            ],
            "PurchaseMotivation": ["purchase motivation", "motivation for purchase"], ##X
            "BiometricData": [
                "biometrische (Daten|informationen)" ##U
            ],
            "FacialData": [ ##X
                "facial (data|information|feature)",
                "scan of(.){0,20}face",
                "(recognition|detect)(.){0,48}face",
                "facial recognition (data|information)",
                "facial (scan|image)",
                "face prints",
            ],
            "VoiceData": [ ##U
                "Sprach(aufnahmen?|aufzeichnung(en)?|eingaben?)"
            ],
            "FingerprintData": ["fingerprint (data|information)"], ##X
            "PersonDetectionInformation": [ ##X
                "person detection (data|information)",
            ],
            "Submissions": ["\\bsubmission(s)?\\b"], ##X
            "Feedback": [
                "((Be)?nutzer)Feedback",
                "Rückmeldungen",
                "Vorschläge"
            ],
            "Comments": ["\\bKommentare?\\b"],
            "Opinions": [ ##U
                "\\bMeinung(en)?\\b",
                "Kommentaren?\\b"
            ],
            "Reviews": ["Bewertung(en)?"], ## U --too general
            "ServicesData": [
                "Service(daten|informationen)",
                "(Daten|Informationen).{0,50}Diensten" ##U
            ],
            "ServiceType": ["service type", "type of service"], ##X
            "CallRecords": [
                "Anrufaufzeichnungen",
                "Telefonanrufe"
            ],
            "Messages": [
                "(Chat|Gesprächs|SMS-)?Nachrichten(?!verlauf)(?!empfänger)(?!dienst)(?!berichten)", ## too general?
                "(Details|Informationen).{0,20}(Nachrichten|Messenger|Messaging)",
                "Chat-Eingaben"
            ],
            "ChatHistory": [
                "Chat(verlauf|historie)",
                "Nachrichten(verlauf|historie)"
            ],
            "MessageDrafts": [ ##X
                "message draft(s)?\\b",
                "unsent message(s)?",
                "\\bdraft message(s)?",
                "\\bunsent form data\\b",
            ],
            "CommunicationRecords": [ ##U
                "Kommunikations(verlauf|historie)"
            ],
            "RegistrationData": ["Registrierungs(daten|informationen|details)"], ##U
            "ParticipationData": [
                "Teilnehmer(daten|informationen|details)",
                "Teilnahme(daten|informationen|details)",
                "(Daten|Informationen|Details).{0,10}Teilnehmer"
            ],
            "NumberOfParticipations": [
                "Anzahl.{0,10}(Teilnahmen|Teilnehmer)"
            ],
            "RewardHistory": [ ##X
                "reward history",
                "\\brewards(.){0,20}received",
            ],
            "FilmingEquipment": [ ##U
                "Filmausrüstung",
            ],
            "SecurityInformation": [
                "sicherheitsrelevante Informationen",
                "Sicherheits(daten|informationen|details)",
                "Sicherheitsanmeldedaten",
                "Sicherheitsstatus"
            ],
            "TamperStatus": ["tamper status", "tampering (data|information)"], ##U
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
            "AuthToken": [ ##X
                "\\bauth token(s)?\\b",
                "\\bauthentication token(s)?\\b",
                "\\bsession token(s)?\\b",
            ],
            "WrittenPermissions": [ ##X
                "\\bwritten permission\\b",
                "\\bwritten consent\\b",
                "signed declaration confirming your authorization",
                "probate documentation",
                "valid authori(s|z)ation",
            ],
            "ProofOfIdentity": [
                "(Nachweis|Verifikation|Überprüfung|Beweis).{0,10}Identität",
                "Identitätsnachweis",
                "Identität.{0,20}(nach(zu)?weisen|verifizieren|überprüfen)"
            ],
            "ConsentStatus": [
                "(Aufzeichnungen|Datensätze).{0,15}(Zustimmungen|Einwilligungen)",
                "Einwilligungserklärung(en)?",
            ],
            "EmployeeRecord": [ ##X
                "HR record(s)?",
                "human resource record(s)?",
                "personnel record(s)?",
                "employee record(s)?",
            ],
            "OrderData": [
                "Einkaufs(details|informationen|daten)",
                "Bestell(details|informationen|daten)",
                "Bestellungen",
                "Dokumente über Einkäufe",
                "gekaufte (Artikel|Produkte)"
            ],
            "OrderHistory": [
                "(Einkaufs|kauf)historie",
                "(Einkaufs|kauf)verlauf"
            ],
            "OrderNumber": ["Bestellnummer"],
            "InvoiceData": [
                "Rechnungs(daten|informationen|details|datensätze)"
            ],
            "PurchaseDate": ["Kaufdatum"], ##U
            "PaymentData": ["Zahlungs(daten|informationen|details|aufzeichnungen|datensätze)"],
            "PaymentAmount": [
                "(Zahlungs|Kauf|Transaktions)(betrag|preis)"
            ],
            "PaymentMethod": ["Zahlungsmethode"],
            "BillingData": ["billing(.){0,20}(data|information|detail)"], ##X -- InvoiceData?
            "BillingReceipts": [ ##X
                "billing receipt",
                "payment receipt",
                "purchase receipt",
            ],
            "TransactionData": [
                "Transaktions(daten|informationen|details)"
            ],
            "TransactionHistory": ["Transaktions(historie|verlauf)"],
            "InAppTransactions": ["in(-| )app transaction", "in(-| )app purchase"], ##X
            "ShippingInformation": ["(shipping|delivery)(.){0,20}(information|data)"], ##X
            "CommercialInformation": ["kommerzielle(.){0,20}(informationen|daten|details)"], ##U
            "CreditCardInformation": [
                "Kreditkarten(informationen|daten|details)"
            ],
            "CreditCardNumber": [
                "Kreditkartennummer",
                "Kredit(karten)?-.{0,20}nummer"
            ],
            "DebitCardInformation": [ ##X
                "debit(.){0,20}card(.){0,20}(information|data|detail)"
            ],
            "BankAccountInformation": [ ##U
                "Bankkonto(informationen|daten|details)"
            ],
            "BankAccountNumber": [
                "(Bank)?Kontonummer",
                "Konto-.{0,20}nummer",
                "Banknummer",
                "IBAN"
            ],
            "BankHolderName": [
                "Namen?.{0,10}Kontoinhabers",
                "Kontoinhabername"
            ],
            "PaymentCardInformation": [
                "payment(.){0,20}card(.){0,20}(information|data|detail)" ##X
            ],
            "PaymentCardNumber": ["Bezahlkartennummer"], ##?U
            "CardholderData": [
                "Karteninhaber(daten|informationen|details)",
                "Name.{0,20}Karteninhaber"
            ],
            "CardExpiryDate": [ ##U
                "Ablaufdatum der Karte"
            ],
            "CustomerList": ["Kundenliste"], ##U
            "CustomerRecords": [ ##U
                "Kunden(aufzeichnungen|aufnahmen|daten|informationen|details)"
            ],
            "ApplicationDocuments": [
                "Bewerbungs(daten|informationen|dokumente|unterlagen)",
                "Lebenslauf" ##U
            ],
            "AppInformation": [
                "App-(Daten|Informationen|Details|Herkunft)", ##U
                "(Daten|Informationen|Details).{0,20}App"
            ],
            "AppConfiguration": [
                "App-(Konfiguration|Einstellung)"
            ],
            "Qualifications": ["Qualifikationen"],
            "CallStatus": ["call status"], ##X
            "AmbientSound": ["Hintergrundgeräusche?"], ##U
            "UserGeneratedContent": [ ##X
                "user(-| )generated content",
                "\\bUGC\\b",
                "\\buser content\\b",
            ],
            "HistoricalDataRecord": [ ##X
                "historical data record",
                "historical (data|information|record|detail)",
                "historical records of your data",
            ],
            "ForumPosts": ["(question|answer)(.){0,48}(forum)"], ##X
            "Testimonial": [ ##X
                "\\btestimonial(s)?\\b",
            ],
            "Ratings": ["\\bBewertung\\b"], ##U
            "SharedContent": [
                "(geteile|freigegebene)[rn]? Inhalte?",
                "Freigaben"
            ],
            "ListedItems": ["listed item(s)?\\b", "\\bitems you have listed"], ##X
            "Likes": [
                "\\blikes\\b",
                "Gefällt-mir-(Informationen|Daten)"
            ],
            "Follows": ["\\bfollow(s)?\\b"], ##U
            "Contacts": ["Kontakte?\\b"],
            "ContentUseHistory": ["content use history", "content viewing history"], ##X
            "VirusDefinitions": [ ##X
                "virus definition(s)?",
                "malware definition(s)?",
                "virus definition list",
            ],
            "DeviceAutomations": ["device automations"], ##X
            "ContestData": ["contest (data|information|entry|detail|entries)"], ##X
            "BusinessInformation": ["\\bGeschäfts(informationen|daten|details)\\b"],
            "CompanyInformation": [
                "\\bUnternehmens(informationen|daten|details)\\b",
                "Unternehmens?",
            ],
            "CompanyName": ["\\bcompany(.){0,20}name\\b", "\\bname of company\\b"], ##X
            "NumberOfEmployees": ["\\bAnzahl.{0,10}Mitarbeiter\\b", "\\bMitarbeiter(an)?zahl\\b"],
            "BusinessModel": ["\\bGeschäftsmodell\\b"],
        }
    ),
    track_conv=AttributePattern.from_dict(
        {
            "Cookies": ["\\bCookie(s)?\\b"],
            "WebBeacons": ["\\bbeacon(s)?\\b", "Web[- ]Beacons"],
            "TrackingPixel": [
                "\\btracking pixel(s)?\\b",
                "\\bPixel\\b",
                "\\bZählpixel\\b"
                #"(?=.*pixel)(?=.*(html|email|cookie|tracking))",
            ],
            "ClearGIF": [
                "\\bClear-GIFs?\\b",
                "\\bone-pixel gifs\\b"
            ],
            "SDK": ["\\bSDKs?(?!-Version)\\b"],
            "SimilarTechnologies": [
                "\\b(ähnlichen?|verwandten?) Technologien?\\b",
                "\\banderen? Identifizierungstechnologien\\b",
                "\\b(anderen?|verwandten?) Tracking-Technologien\\b"
            ],
        }
    ),
    method_source=AttributePattern.from_dict(
        {
            "UserProvided": [ ##U
                "\\bzur Verfügung (zu)? (stellen|gestellt (haben|werden))\\b",
                "\\bnach eigenem Ermessen\\b"
                "\\bAngabe(?=.*(Daten|Informationen))\\b",
                "\\b(müssen|können|sollten) Sie (?=.*(angeben|einreichen|übermitteln|bereitstellen|mitteilen))\\b",
                "\\bSie (?=.*(angeben|einreichen|übermitteln|bereitstellen|mitteilen))\\b",
                "\\bvon Ihnen(?=.*(angegebenen?|eingereichen?|übermittelten?|bereitgestellten?|stammen|weitergegeben))\\b"
            ],
            "AutomaticallyCollected": [ ##U
                "(automatisierten|automatische) Verarbeitung",
                "(automatisiert|automatisch) verarbeitet"
            ],
            "ThirdPartyProvided": [ ##U
                "(?=.*(obtain|receive|collect from))(?=.*(third(-| )party|external source))",
                "\\breceive.*from.*(partner|vendor|affiliate|provider)\\b",
                "(Drittpartei(en)?|Dritte[rn]?|Drittanbietern?)(?=.*(erhalten|bekommen|erwerben|erfassen))",
                "((erhalten|bekommen|erwerben|erfassen))(?=.*(Drittpartei(en)?|Dritte[rn]?|Drittanbietern?))",
            ],
            "DataCombination": [
                "\\bkombinieren\\b",
                "\\bkombinierte?\\b",
            ],
            "AIAnalysis": [ ##X
                "(?=.*\\b(use|using|through)\\b)(?=.*\\b(artificial intelligence|AI|machine learning|ML)\\b)"
            ],
            "SocialMedia": [ ## Gardena 295?
                "\\bsocial media\\b",
                "\\bsoziale[rn]? Medien\\b",
                "\\bsoziales Medium\\b",
                "\\bsoziale[rnms]? Netzwerke?\\b",
                "Fan(seite|page)"
            ],
            "IndirectCollection": [
                "(?=.*\\bindirekt)(?=.*(gesammelt|erhalten|bekommen))",
                "(?=.*(Informationen|Daten|Details)(?=.*nicht).{0,20}(angefordert|gesammelt|))" ##U
            ],
            "Public": [
                "(Daten|Informationen|Details)(?=.*veröffentlichen)",
                "öffentlich (?=.*(posten|gepostet|bereitstellen|bereitgestellt|machen|gemacht|teilen|geteilten|veröffentlicht|bekannt (geben|gegeben)))",
                "öffentliche[rn]? (Quellen|Bekanntmachungen)"
            ],
            "Interaction": [ ## gardena 32?
                "\\bInteraktion(en)?\\b",
                "(?=.*(wenn|während))(?=.*(interagieren|nutzen|besuchen))",
                #"(Formular|Umfrage|Fragebogen)",
            ],
            "VoluntaryProvided": [
                "\\bfreiwillig\\b",
                "Sie können(?=.*(Angaben|Daten|Informationen|Details))"
                "\\bvoluntary\\b",
                "\\byou (choose|elect|opt) to\\b",
                "\\boptional\\b",
                "(?=.*\\b(right to choose|not obliged))(?=.*(provide|share|submit|give|upload))",
            ],
            "Buying": [##X
                "(?=.*\\bwe\\b)(?=.*\\b(purchase|buy|acquire)\\b)(?=.*\\b(data|information)\\b)"
            ],
            "Feedback": [ ##U
                "\\bFeedback\\b"
            ],
        }
    ),
    descriptive=AttributePattern.from_dict(
        {
            "ServiceProvider": [
                "\\bDienst(leister|anbieter)[sn]?",
                "Anbieter[sn]?\\b",
                "Drittanbieter[sn]?\\b",
                "Drittanbieterplattform",
                "Dienste.{0,20}Dritte[rn]"
            ],
            "InsuranceCompany": [
                "Versicherungsunternehmen",
            ],
            "Employer": [ ##X
                "\\bemployer\\b",
                "(company|organization) you work for",
                "your(.){0,20}company",
            ],
            "Manufacturer": ["manufacturer(s)?\\b", "company that made (the )?product"], ##X
            "PaymentServiceProvider": [
                "Zahlungsdienst(leister[sn]?)?",
                "Zahlungs-.{0,20}dienst(leister[sn]?)?",
                "Zahlungsinstitut[es]?",
                "Zahlungsabwicklungsdienste?"
            ],
            "CreditInstitution": [
                "Kredit(auskunfteien|institut|anbieter)",
                "Kredit-Auskunfteien"
            ],
            "InternetServiceProvider": [
                "(Internet)?-?Provider",
                "(Mobil(gerät|telefon)|Internet)(?=.*(Anbieter|Dienstleister))", ##U
                "\\bisp\\b",
            ],
            "TransportCompany": [
                "(shipping|delivery|logistic|freight)(.){0,64}(company|service|provider|partner)",
                "(Paket|Liefer|Versand|Logistik)(dienste|unternehmen|partner|zusteller|dienstleister)"
            ],
            "FulfillmentCenter": [ ##X
                "(fulfillment|fulfilment)(.){0,64}(center|centre|service|provider|partner)"
            ],
            "HostingProvider": [ ##U
                "Hostingdienstleistungen",
                "Dienste?.{0,10}Hosting"
            ],
            "StorageServiceProvider": [ ##X
                "(storage)(.){0,64}(provider|partner|service)",
                "data (center|centre)(s)?\\b",
                "database management provider",
            ],
            "SocialMediaProvider": [
                "Social-?Media-?(Plattformen?|Schaltflächen?|Anbietern?|Diensten?|Funktion(en)?|PlugIns|(Web)?seiten|Partner|Dienstleister|Netzwerk)"
                "soziale[rn] (Netzwerken?|Medien)",
                "\\bsoziales Netzwerkkonto\\b",
                "Social Plugins"
            ],
            "Vendor": [ ##U
                "Einzelhändlern"
            ],
            "Supplier": ["\\bLieferant(en)?\\b"],
            "Customer": [ ##X
                "\\bcustomer(s)?\\b",
                "client(s)?",
                "user(s)?",
                "consumer(s)?",
            ],
            "SubContractors": [
                "\\bUnterauftragnehmer\\b"
            ],
            "Adviser": [
                "Berater\\b"
            ],
            "Buyer/Investor": [ ##U
                "Nachfolgeunternehmen",
                "(Fusion|Zusammenschluss|Übernahme)", ##U
                "(Investor(s|en)?|Käufer[sn]?)(?=.*Unternehmens?)"
            ],
            "RatingPlatform": [ ##X
                "\\brating platform(s)?\\b",
                "\\breview platform(s)?\\b",
            ],
            "RecruitmentPlatform": [ ##X
                "\\brecruitment platform(s)?\\b",
                "\\bapplicant tracking system",
            ],
            "MarketingAffiliate": [ ##X
                "\\bmarketing affiliate(s)?\\b",
                "affiliate marketing (company|companies|entity|entities|partner|provider)",
            ],
            "AdvertisingAgency": [ ##U
                "\\bWerbeagentur(en)?\\b",
                "Drittanbietern(?=.*Werbung)"
            ],
            "AdvertisingNetwork": [ ##U
                "\\bWerbenetzwerke?\\b"
            ],
            "AdvertisingPartner": [
                "\\bWerbepartnern?\\b",
                "\\bMarketing[- ]?Partnern?\\b",
            ],
            "SoftwareDeveloper": [ ##U
                "Softwareentwicklern?",
                "App-Entwicklern?"
            ],
            "CustomerServiceProvider": [ ##U
                "\\bKunden(dienst|support)(anbieter|partner|service)\\b"
            ],
            "BusinessPartner": ["Geschäftspartnern?"],
            "CloudService": [
                "Cloud-service-(Anbieter|Dienstleister)",
                "cloudbasierte.{0,20}(Dienste|Anwendungen)"
            ],
            "AnalyticsService": [
                "Analyse-?(service|dienst|anbieter|dienstanbieter|plattform|tool)",
                "Analyse-.{0,20}(service|dienst|anbieter|dienstanbieter|plattform|tool)",
                "Anbieter von Analysen"
            ],
            "CompatibleApp": [ ##U
                "Drittanbieter-Apps",
                "App eines Drittanbieters"
            ],
            "CompatibleDevice": [ ##X
                "third(-| )party(.){0,20}(device|product)",
                "\\bdevice made by (third(-| )party|external)",
                "kompatible[rsnm] Geräte[ns]?",
            ],
            "CompatibleService": [ ##X
                "third(-| )party(.){0,20}service",
                "\\bservice made by (third(-| )party|external)",
                "(compatible|external) service",
            ],
            "PartnerIntegrations": [
                "Partnerintegration\\b",
                "Integration.{0,15}(Geräte|Produkte)", ##U
                "\\bintegrated service(s)?\\b",
                "\\bwho integrate with\\b",
            ],
            "ExternalAccount": [ ##U
                "externes ((Be)?nutzer?Konto)\\b",
                "Partner-Benutzerkonto"
            ],
            "ThirdPartySite": [
                "Drittanbieter-Site"
            ],
            "ThirdPartyStore": [ ##X
                "third(-| )party(.){0,20}(store|marketplace)",
                "external (app|software|online) store",
                "Marktplätze Dritter"
            ],
            "DataPartner": ["\\bDatenpartnern?\\b"], ##U
            "FraudPreventionService": [ ##X
                "fraud (prevention|detection) (service|provider|partner)"
            ],
            "SmartAssistant": ["\\bsmart assistant(s)?\\b"], ##X
            "VoiceAssistant": ["\\bSprachassistent(e|en)?\\b"], ##U
            "AiServices": [ ##X
                "(service|provider|partner|compan(y|ies))(.){0,64}(artificial intelligence|AI|machine learning|ML)",
                "\\bAI service(s)?\\b",
                "\\bartificial intelligence service(s)?\\b",
            ],
            "ContentProvider": [ ##X
                "\\bcontent provider(s)?\\b",
                "(provider|contributor)(s)? of content",
            ],
            "Affiliates": [
                "\\bPartnerunternehmen\\b",
                "verbundenen? (Unternehmen|Geschäftsbereiche|Gesellschaften|Partner)"
            ],
            "ParentCompany": ["\\bMutterkonzern"], ##U
            "Subsidiaries": ["\\bTochter(konzern|unternehmen|gesellschaften)\\b"],
            "ContentDeliveryNetwork": [ ##X
                "\\bcdn\\b",
                "\\bcontent delivery network(s)?\\b",
            ],
            "NetworkOperator": [ ##U
                "Netzwerkbetreiber"
            ],
            "EcosystemCompanies": [ ##X
                "companies forming(.){0,20}ecosystem",
                "ecosystem (companies|entities|partners)",
            ],
            "Partners": [ ##U
                "(Vertrags|Kanal)partnern",  
                " Partnern?[\\., ]"
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
            "DataController": [ ##X
                "\\bdata controller(s)?\\b",
                "\\bjoint controller(s)?\\b",
            ],
            "AttributionCompanies": [ ##X
                "\\battribution (company|companies|entity|entities)\\b"
            ],
            "ThirdPartyEmployee": [
                "(Angesteller|Mitarbeiter) einer Drittpartei",
                "externer (Angesteller|Mitarbeiter)"
            ],
            "BackupService": ["\\bbackup (service|provider|partner)\\b"], ##X
            "CustomerRelationshipManagement": [ ##X
                "\\bcrm\\b",
                "customer relationship manag(e|ement)",
            ],
            "ECommercePlatform": ["\\be-commerce platform(s)?\\b"], ##X
            "EmailServiceProvider": ["\\bemail (service|provider|partner)\\b"], ##X
            "SecurityServiceProvider": ["security (service provider|provider|partner)"], ##X
            "IdentityVerificationService": [ ##X
                "identity verification (service|provider|partner)"
            ],
            "Insurer": [ ##U
                "Versicherung(en)?",
                "\\binsurance (company|companies|provider)(s)?\\b",
            ],
        }
    ),
    official=AttributePattern.from_dict(
        {
            "SecurityAuthorities": ["\\b(security|safety) authority(ies)?\\b"], ##X
            "Court": [
                "Gerichte?",
                "Gerichtsverfahren"
            ],
            "Tribunal": ["Tribunal(e|en)?"],
            "LawEnforcement": [
                "\\bStraf(verfolgung|vollzug)sbehörden\\b",
                "Strafverfolgung",
                "\\bStraftaten\\b", # ein Fehler
                "Verletzung(?=.*(Recht|Gesetz|Verordnung))",
            ],
            "EmergencyServices": [ ##X
                "\\bemergency (service|services)\\b",
                "\\bfirst responder(s)?\\b",
                "\\brelief organization(s)?\\b",
            ],
            "MunicipalAuthorities": [ ##U
                "\\bKommunalbehörden\\b"
            ],
            "RegulatoryAgencies": [
                "\\b(Aufsichts|Regulierungs)behörden\\b",
                "\\bRegulierungsbefugnissen\\b",
            ],
            "CertificationBody": [ ##X
                "\\bcertification (body|bodies)\\b",
                "\\bcertifying (body|authority)\\b",
            ],
            "GovernmentAgencies": [ ##U
                "\\bRegierungs(behörden|agencies|authority|authorities|body)\\b",
                "\\bBehörden\\b",
                "\\bRegierungen\\b",
                "staatliche Einrichtungen",
                "nationale Verteidigung"
            ],
            "PublicHealthAuthorities": [ ##X
                "\\bpublic health (authority|authorities)\\b",
                "\\bhealth department(s)?\\b",
            ],
            "ChildProtectionServices": [ ##X
                "\\bchild protection (service|agency|authority|authorities)\\b",
                "\\bchild welfare (service|agency|authority)\\b",
            ],
            "ImmigrationAuthorities": [ ##X
                "\\bimmigration (authority|authorities)\\b",
                "\\border control\\b",
            ],
            "TaxAuthorities": ["\\btax (authority|authorities)\\b"], ##X
            "FinancialRegulators": [ ##U
                "\\bFinanzamt\\b"
            ],
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
            "Europe": ["\\bEuropa\\b"],
            "European Union": [
                "\\bEuropäische Union\\b",
                "\\bEU\\b"
            ],
            "EEA": [
                "\\bEWR\\b",
                "\\bEuropäischer Wirtschaftsraum\\b"
            ],
            "Asia": ["\\bAsien\\b"],
            "Africa": ["\\bAfrika\\b"],
            "Oceania": ["\\bOzeanien\\b"],
            "Middle East": ["\\bMittlerer Osten\\b"],
            "International": [
                "\\binternational\\b",
                "\\bweltweit\\b",
                "\\bglobal\\b",
                "\\bübersee\\b",
            ],
            "ResidenceState": [
                "Wohnsitz",
                "in dem sie (sich befinden|wohnen|leben)",
                "\\b Ihre[srnm] (Landes|Stadt|Standort|Provinz|Territorium|Region|Gerichtsbarkeit)"
            ],
            "CountriesOutsideOf": [
                "\\banderen? (Ländern|Gebieten|Staaten)\\b",
                "\\baußerhalb (Ihrer|Ihres|des|der|von) \\b",
                "\\bnicht-EU\\b",
                "Landes abweichen"
            ],
            "AndOther": ["\\bandere Länder\\b"], ##U
            "California": ["\\bKalifornien\\b", "\\bCCPA\\b"],
            "Washington": ["\\bWashington\\b"],
            "Colorado": ["\\bColorado\\b"],
            "Connecticut": ["\\bConnecticut\\b"],
            "Florida": ["\\bFlorida\\b"],
            "Georgia": ["\\bgeorgiG\\b"],
            "Texas": ["\\bTexas\\b"],
            "Virginia": ["\\bVirginia\\b"],
            "New Jersey": ["\\bNew Jersey\\b"],
            "Delaware": ["\\bDelaware\\b"],
            "Maryland": ["\\bMaryland\\b"],
            "Oregon": ["\\bOregon\\b"],
            "Nevada": ["\\bNevada\\b"],
            "Minnesota": ["\\bMinnesota\\b"],
            "New York": ["\\bNew York\\b"],
            "North Carolina": ["\\bNorth Carolina\\b"],
            "Utah": ["\\bUtah\\b"],
            "Nebraska": ["\\bNebraska\\b"],
            "United States": [
                "\\bVereinigte Staaten\\b",
                "\\bUSA?\\b",
                "\\bu\\.s\\.a\\.\\b",
                "\\bu\\.s\\.\\b"
            ],
            "United Kingdom": [
                "\\bVereinigtes Königreich\\b",
                "\\buk\\b",
                "\\bu\\.k\\.\\b",
                "\\bGroßbritannien\\b",
                "\\bBritannien\\b",
            ],
            "Canada": ["\\bKanada\\b"],
            "Québec": ["\\bQu[eé]bec\\b"],
            "Australia": ["\\bAustralien\\b", "ANZ"],
            "New Zealand": ["\\bNeuseeland\\b", "ANZ"],
            "Germany": ["\\bDeutschland\\b"],
            "France": ["\\bFrankreich\\b"],
            "Italy": ["\\bItalien\\b"],
            "Spain": ["\\bSpanien\\b"],
            "Portugal": ["\\bPortugal\\b"],
            "Netherlands": ["\\bNiederlande\\b", "\\bHolland\\b"],
            "Belgium": ["\\bBelgien\\b"],
            "Switzerland": ["\\bSchweiz\\b"],
            "Austria": ["\\bÖsterreich\\b"],
            "Sweden": ["\\bSchweden\\b"],
            "Norway": ["\\bNorwegen\\b"],
            "Denmark": ["\\bDänemark\\b"],
            "Finland": ["\\bFinland\\b"],
            "Iceland": ["\\bIsland\\b"],
            "Ireland": ["\\bIrland\\b"],
            "Poland": ["\\bPolen\\b"],
            "Czech Republic": ["\\bTschechische Republik\\b", "\\bTschechien\\b"],
            "Slovakia": ["\\bSlowakai\\b"],
            "Hungary": ["\\bUngarn\\b"],
            "Romania": ["\\bRumänien\\b"],
            "Bulgaria": ["\\bBulgarien\\b"],
            "Greece": ["\\bGriechenland\\b"],
            "Croatia": ["\\bKroatien\\b"],
            "Slovenia": ["\\bSlowenien\\b"],
            "Estonia": ["\\bEstland\\b"],
            "Latvia": ["\\bLettland\\b"],
            "Lithuania": ["\\bLitauen\\b"],
            "Luxembourg": ["\\bLuxemburg\\b"],
            "Malta": ["\\bMalta\\b"],
            "Cyprus": ["\\bZypern\\b"],
            "Russia": ["\\bRussland\\b", "\\brussische Föderation\\b"],
            "Ukraine": ["\\bUkraine\\b"],
            "Belarus": ["\\bBelarus\\b", "\\bWeißrussland\\b"],
            "Moldova": ["\\bMoldau\\b"],
            "Serbia": ["\\bSerbien\\b"],
            "Bosnia and Herzegovina": ["\\bBosnien\\b", "\\bBosnien und Herzegowina\\b"],
            "Albania": ["\\bAlbanien\\b"],
            "North Macedonia": ["\\bNordmazedonien\\b", "\\bMazedonien\\b"],
            "Montenegro": ["\\bMontenegro\\b"],
            "Kosovo": ["\\bKosovo\\b"],
            "Turkey": ["\\bTürkei\\b"],
            "China": [
                "\\bChina\\b",
                "\\bchinesischen Festland\\b",
            ],
            "Japan": ["\\bJapan\\b"],
            "South Korea": ["\\bSüdkorea\\b"],
            "North Korea": [
                "\\bNordkorea\\b",
                "\\bDemokratische Volksrepublik Korea\\b"
                "\\bDVRK\\b"
            ],
            "Taiwan": ["\\bTaiwan\\b"],
            "Hong Kong": ["\\bHongkong\\b"],
            "Macau": ["\\bMacau\\b"],
            "Singapore": ["\\bSingapur\\b"],
            "Malaysia": ["\\bMalaysia\\b"],
            "Indonesia": ["\\bIndonesien\\b"],
            "Thailand": ["\\bThailand\\b"],
            "Vietnam": ["\\bVietnam\\b"],
            "Philippines": ["\\bPhilippinen\\b"],
            "Myanmar": ["\\bMyanmar\\b", "\\bB[ui]rma\\b"],
            "Cambodia": ["\\bCambodia\\b", "\\bKambodscha\\b"],
            "Laos": ["\\bLaos\\b"],
            "Brunei": ["\\bBrunei\\b"],
            "India": ["\\bIndien\\b"],
            "Pakistan": ["\\bPakistan\\b"],
            "Bangladesh": ["\\bBangladesch\\b"],
            "Sri Lanka": ["\\bSri Lanka\\b"],
            "Nepal": ["\\bNepal\\b"],
            "Bhutan": ["\\bBhutan\\b"],
            "Maldives": ["\\bMalediven\\b"],
            "Afghanistan": ["\\bAfghanistan\\b"],
            "Iran": ["\\bIran\\b"],
            "Iraq": ["\\bIrak\\b"],
            "Saudi Arabia": ["\\bSaudi Arabien\\b"],
            "United Arab Emirates": [
                "\\bVereinigte Arabische Emirate\\b",
                "\\bvae\\b",
                "\\bu\\.a\\.e\\.\\b",
            ],
            "Qatar": ["\\bKatar\\b"],
            "Kuwait": ["\\bKuwait\\b"],
            "Bahrain": ["\\bBahrain\\b"],
            "Oman": ["\\bOman\\b"],
            "Yemen": ["\\bJemen\\b"],
            "Jordan": ["\\bJordan\\b"],
            "Lebanon": ["\\bLibanon\\b"],
            "Syria": ["\\bSyrien\\b"],
            "Israel": ["\\bIsrael\\b"],
            "Palestine": ["\\bPalästina\\b"],
            "Egypt": ["\\bÄgytpen\\b"],
            "Libya": ["\\bLibyen\\b"],
            "Tunisia": ["\\bTunesien\\b"],
            "Algeria": ["\\bAlgerien\\b"],
            "Morocco": ["\\bMarokko\\b"],
            "Sudan": ["\\bSudan\\b"],
            "South Sudan": ["\\bSüdsudan\\b"],
            "Ethiopia": ["\\bÄthopien\\b"],
            "Kenya": ["\\bKenia\\b"],
            "Tanzania": ["\\bTansania\\b"],
            "Uganda": ["\\bUganda\\b"],
            "Rwanda": ["\\bRuanda\\b"],
            "Burundi": ["\\bBurundi\\b"],
            "Somalia": ["\\bSomalien\\b"],
            "Djibouti": ["\\bDschibuti\\b"],
            "Eritrea": ["\\bEritrea\\b"],
            "Nigeria": ["\\bNigeria\\b"],
            "Ghana": ["\\bGhana\\b"],
            "Ivory Coast": ["\\bElfenbeinküste\\b"],
            "Senegal": ["\\bSenegal\\b"],
            "Mali": ["\\bMali\\b"],
            "Burkina Faso": ["\\bBurkina Faso\\b"],
            "Niger": ["\\bNiger\\b"],
            "Chad": ["\\bTschad\\b"],
            "Cameroon": ["\\bKamerun\\b"],
            "Central African Republic": ["\\bZentralafrikanische Republik\\b"],
            "Gabon": ["\\bGabun\\b"],
            "Congo": ["\\bKongo\\b"],
            "Democratic Republic of Congo": [
                "\\bDemokratische Republik Kongo\\b",
                "\\bDRK\\b"
            ],
            "Angola": ["\\bAngola\\b"],
            "Zambia": ["\\bSambia\\b"],
            "Zimbabwe": ["\\bSimbabwe\\b"],
            "Mozambique": ["\\bMosambik\\b"],
            "Malawi": ["\\bMalawi\\b"],
            "Botswana": ["\\bBotswana\\b"],
            "Namibia": ["\\bNamibia\\b"],
            "South Africa": ["\\bSüdafrika\\b"],
            "Lesotho": ["\\bLesotho\\b"],
            "Eswatini": ["\\bEswatini\\b", "\\bswasiland\\b"],
            "Madagascar": ["\\bMadagaskar\\b"],
            "Mauritius": ["\\bMauritius\\b"],
            "Seychelles": ["\\bSeychellen\\b"],
            "Comoros": ["\\bKomoren\\b"],
            "Cape Verde": ["\\bKap Verde\\b"],
            "Sao Tome and Principe": ["\\bS[ãa]o Tom[ée]\\b"],
            "Equatorial Guinea": ["\\beÄquatorialguinea\\b"],
            "Guinea": ["\\bGuinea\\b"],
            "Guinea-Bissau": ["\\bGuinea-Bissau\\b"],
            "Sierra Leone": ["\\bSierra Leone\\b"],
            "Liberia": ["\\bLiberia\\b", "\\bLiberien\\b"],
            "Togo": ["\\bTogo\\b"],
            "Benin": ["\\bBenin\\b"],
            "Mauritania": ["\\bMauretanien\\b"],
            "Gambia": ["\\bGambia\\b"],
            "Mexico": ["\\bMexiko\\b"],
            "Guatemala": ["\\bGuatemala\\b"],
            "Belize": ["\\bBelize\\b"],
            "Honduras": ["\\bHonduras\\b"],
            "El Salvador": ["\\bEl Salvador\\b"],
            "Nicaragua": ["\\bNicaragua\\b"],
            "Costa Rica": ["\\bCosta Rica\\b"],
            "Panama": ["\\bPanama\\b"],
            "Cuba": ["\\bKuba\\b"],
            "Jamaica": ["\\bJamaika\\b"],
            "Haiti": ["\\bHaiti\\b"],
            "Dominican Republic": ["\\bDominikanische Republik\\b"],
            "Bahamas": ["\\bBahamas\\b"],
            "Trinidad and Tobago": ["\\bTrinidad und Tobago\\b", "\\btrinidad\\b"],
            "Barbados": ["\\bbarbados\\b"],
            "Saint Lucia": ["\\bSaint Lucia\\b", "\\bSt\\.? Lucia\\b"],
            "Grenada": ["\\bgrenada\\b"],
            "Saint Vincent": ["\\bSt. Vincent und die Grenadinen\\b"],
            "Antigua and Barbuda": ["\\bAntigua und Barbuda\\b"],
            "Dominica": ["\\bdominica\\b"],
            "Saint Kitts": ["\\bSaint Kitts\\b", "\\bSt\\.? Kitts\\b"],
            "Brazil": ["\\bBrasilien\\b"],
            "Argentina": ["\\bArgentinien\\b"],
            "Chile": ["\\bChile\\b"],
            "Colombia": ["\\bKolumbien\\b"],
            "Peru": ["\\bPeru\\b"],
            "Venezuela": ["\\bVenezuela\\b"],
            "Ecuador": ["\\bEcuador\\b"],
            "Bolivia": ["\\bBolivien\\b"],
            "Paraguay": ["\\bParaguay\\b"],
            "Uruguay": ["\\bUruguay\\b"],
            "Guyana": ["\\bGuyana\\b"],
            "Suriname": ["\\bSuriname\\b"],
            "French Guiana": ["\\bFranzösisch Guayana\\b"],
            "Fiji": ["\\bFiji\\b"],
            "Papua New Guinea": ["\\bPapua-Neuguinea\\b"],
            "Solomon Islands": ["\\bSolomon-Inseln\\b", "\\bSalomonen\\b"],
            "Vanuatu": ["\\bVanuatu\\b"],
            "Samoa": ["\\bSamoa\\b"],
            "Tonga": ["\\bTonga\\b"],
            "Kiribati": ["\\bKiribati\\b"],
            "Micronesia": ["\\bMikronesien\\b"],
            "Marshall Islands": ["\\bMarshallinseln\\b"],
            "Palau": ["\\bPalau\\b"],
            "Nauru": ["\\bNauru\\b"],
            "Tuvalu": ["\\bTuvalu\\b"],
            "Cook Islands": ["\\bCookinseln\\b"],
            "Niue": ["\\bNiue\\b"],
            "Kazakhstan": ["\\bKasachstan\\b"],
            "Uzbekistan": ["\\bUsbekistan\\b"],
            "Turkmenistan": ["\\bTurkmenistan\\b"],
            "Kyrgyzstan": ["\\bKirgisistan\\b"],
            "Tajikistan": ["\\bTadschikistan\\b"],
            "Mongolia": ["\\bMongolei\\b"],
            "Armenia": ["\\bArmenien\\b"],
            "Azerbaijan": ["\\bAserbaidschan\\b"],
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
                #"\\bmeta\\b", ## -> Meta attribute
                "\\binstagram\\b",
                "\\bwhatsapp\\b",
                #"\\bmeta pixel\\b",
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
        }
    ),
    provide_service=AttributePattern.from_dict(
        {
            "OrderProcessing": [
                "\\bBestellung",
                "\\bBestellprozesse?",
                "\\bKäufe",
                "\\bKauf\\b",
                "Einzelhandelsdienste",
            ],
            "PaymentProcessing": [
                "Einzelhandelsdienste", ##U
                "Zahlung(en|sabwicklung(en)?)?\\b",
                "Transaktion(en)?\\b",
                "Verarbeitung Ihrer Zahlungsangaben" ##U
            ],
            "Shipping": [
                "Versands?\\b",
                "Liefer(ung|zweck)",
                "liefern" ##U
            ],###
            "ReturnOrder": [
                "\\bzurück(zu)?(geben|schicken|senden)\\b",
                "Rück(sendung|gabe|erstattung)"
            ],
            "OrderTracking": ["(Paket|Sende)verfolgung"],
            "WarrantyService": ["Garantie(?!zeit)(?!rt)(?!ren)"],
            "AfterSalesService": ["after(-| )sales (service|support|care|assistance)"],
            "PresentWebsite": [
                "\\b(provid(e|ing)|display(ing)?|present(ing)?|offer(ing)?|maintain|host|provision)(.){0,32}site",
                "site functionality",
                "ensure(.){0,32}website (availability|functionality|performance|works)",
            ],
            "ProvideApp": ["\\b(provid(e|ing)|offer(ing)?|maintain)(.){0,32}app"],
            "ProvideDevice": [
                "\\b(provid(e|ing)|offer(ing)?)(.){0,32}(device|product)"
            ],
            "PreContractualMeasures": ["\\bpre(-| )contractual measure(s)?\\b"],
            "Loaning": [
                "\\bloan(ing)?\\b",
                "\\bcredit(ing)?\\b",
                "loan eligibility decision(s)?",
            ],
            "RiskAssessment": [
                "\\brisk assessment\\b",
                "\\bassess(ing)?(.){0,20}risk\\b",
                "\\bevaluate(ing)?(.){0,20}risk\\b",
            ],
            "Insurance": [
                "\\binsurance\\b",
                "\\binsure(ing)?\\b",
                "insurance premium calculation(s)?",
            ],
            "FacialRecognition": [
                "\\bfacial recognition\\b",
                "(facial|face)(.){0,20}recognition",
                "(facial|face)(.){0,20}authentication",
                "recognize(ing)?(.){0,20}(face|facial)",
            ],
            "AccountCreation": [
                "\\baccount creation\\b",
                "(create|register|maintain|set up|manage)(ing)?(.){0,32}(account|personal profile)",
                "\\bregistering\\b",
            ],
            "ProductActivation": [
                "\\bproduct activation\\b",
                "(activate|activating|activation)(.){0,32}(device|product)",
            ],
            "ServiceActivation": [
                "\\bservice activation\\b",
                "(activate|activating|activation)(.){0,32}(service|feature)",
            ],
            "DeviceRegistration": [
                "\\bdevice registration\\b",
                "\\b(register|registration|associate|bind|link)(.){0,32}(device|product)",
            ],
            "OfflineAvailability": [
                "\\boffline availability\\b",
                "when you are offline",
                "when you have no internet connection",
                "\\boffline mode\\b",
            ],
            "Authentication": [
                "\\bauthentication\\b",
                "\\b(log|sign)(ed)?(-| )?(in|into)\\b",
                "\\b(verify|authenticate)(.){0,32}(access|user|identity|credentials)",
                "\\bverification\\b",
                "account validation\\b",
                "\\bverification process\\b",
            ],
            "UserIdentification": [
                "\\bidentification\\b",
                "\\bidentifying\\b",
                "\\bidentify (you|your)\\b",
            ],
            "SocialLogin": [
                "\\bsocial (log(-| )?in|sign(-| )?in)\\b",
                "(log(-| )?in|sign(-| )?in)(.){0,32}(using|with)(.){0,32}(social media|social network)",
            ],
            "Monitoring": [
                "\\b(?!health )monitoring\\b",
                "\\b(monitor|analyze)(.){0,20}(usage|performance|traffic)",
            ],
            "HealthMonitoring": [
                "\\b(health|fitness)(.){0,20}monitoring\\b",
                "(monitor|track|measure)(.){0,32}(health|fitness)(.){0,32}(status|condition|metrics|data)",
            ],
            "WebHosting": ["\\bweb hosting\\b", "\\bhosting service"],
            "Recruiting": [
                "\\brecruiting\\b",
                "\\bjob application\\b",
                "\\bapply (to|for) (becoming|become)\\b",
            ],
            "CreditWorthiness": [
                "\\baccess(.){0,20}reliability",
                "\\bcredit evaluation purpos",
            ],
            "FraudRiskScoring": [
                "\\bfraud risk scoring\\b",
                "\\bassess(ing)?(.){0,20}fraud risk\\b",
                "\\bevaluate(ing)?(.){0,20}fraud risk\\b",
            ],
            "Comfort": [
                "\\bkeep(.){0,32}comfort",
                "(maintain|provide)(.){0,64}comfort",
                "\\bmore helpful\\b",
                "\\buser-friendly\\b",
                "\\b(optimize|improve|better|greater|enhance|best)(.){0,20}experience",
                "\\bhelpful experience\\b",
                "\\bmake it easier\\b",
                "\\bsatisfactory(.){0,20}(product|service|experience)\\b",
            ],
            "PersonalizeContent": [
                "\\b((personaliz|customiz)(e|ing|ation|ed))\\b",
                "\\btailor(ed|ing)?(.){0,32}(service|content|experience)",
                "\\b(which|what)(.){0,32}(relevant|interesting)",
                "previously been interested in",
                "more (relevant|interesting|engaging) to you",
                "you(.){0,20}interested in",
                "predict your (interests|preferences)",
                "(appropriate|relevant) to your (interests|preferences)",
                "based on(.){0,48}you(.){0,32}(use|installed|viewed|purchase|install|watched|accessed)",
            ],
            "Updates": [
                "(software|service|system) (update|optimization)",
                "\\bprovide(ing)?(.){0,32}(updates)",
            ],
            "Upload/Download": ["\\b(upload|download)(.){0,20}process\\b"],
            "SyncContent": [
                "\\b(synchronization|synchronize)",
                "(save|store|sync)(.){0,64}across",
                "(sync|synchroniz)(.){0,32}(content|data|information|files|settings)",
            ],
            "LocalizeContent": [
                "\\blocaliz(e|ing|ation)\\b",
                "\\bgeo(-)?targeting\\b",
                "(provide|offer|deliver)(.){0,32}(content|service)(.){0,32}(in|for)(.){0,32}(your|my)?(location|region|country|language)",
                "\\baddress regional\\b",
            ],
            "Troubleshoot": [
                "\\btroubleshoot(ing)?\\b",
                "(identify|resolve|fix|handle|manage|troubleshoot)(ing)?(.){0,32}(issue|problem|error|bug)",
            ],
            "EstimateBodyMetrics": [
                "\\bestimate(.){0,48}(body|health|fitness)(.){0,48}metrics"
            ],
            "VideoAnalysis": [
                "\\bvideo analysis\\b",
                "\\banalyze(ing)?(.){0,32}video",
                "camera processing",
                "(anaylze|process)(ing)?(.){0,48}(video|footage|images)",
            ],
            "PersonDetection": [
                "\\b(person|human) detection\\b",
                "(detect|infer)(ing)?(.){0,32}(person|human|individual)",
            ],
            "ActivityDescription": [
                "\\b(activity|action) description\\b",
                "(describe|description|summary|summarize|identify|recognize)(ing)?(.){0,32}(activity|action|movement)",
            ],
            "SignalingActiveEngagement": [
                "(indicate|signal)(.){0,20}you are(.){0,32}active"
            ],
            "CountVisits": ["count(ing)?(.){0,32}(visits)"],
            "RecommendSettings": [
                "(recommend|suggest)(ing)?(.){0,32}(settings|configurations)",
                "(setting|configuration) (recommendation|suggestion)",
            ],
            "ProvideUsageInsights": [
                "(provide|offer|deliver)(.){0,32}(usage|performance)(.){0,32}(insights|analytics|reports)"
            ],
            "Logging": ["\\blogging\\b", "\\bcreate(.){0,20}logs\\b"],
            "CloudBasedControl": ["cloud-based control\\b"],
            "NightVision": ["\\bnight(-| )vision\\b"],
            "MotionDetection": [
                "\\bmotion detection\\b",
                "(detect|detection|identify)(ing)?(.){0,32}motion",
                "\\b(when|if)(.){0,48}(door|window)\\b",
                "\\bmotion(.){0,20}(detected|detection|detecting)\\b",
            ],
            "ThirdPartyCompatibility": [
                "\\b(?=.*work with|connect|link)(?=.*(third(-| )party)|external|3rd(-| )party)(?=.*(device|product|service|feature|plugin))",
                "\\benable interoperability",
            ],
            "StorePreferences": [
                "(store|save|remember(.){0,32}(preference|setting|configuration)(s)?)"
            ],
            "MembershipManagement": [
                "\\bmembership management\\b",
                "(manage|handle|process|provide)(.){0,64}(membership)",
            ],
            "SpeedUp": [
                "\\b(increase|improve|optimize|faster)(.){0,32}(speed|time|load(s)?)\\b"
            ],
            "PromotionalActivities": [
                "(?=.*(event|promotion|competition|contest|activit(y|ies)))(?=.*(participation|attendance|registration|entry|sign(-| )up|take part|enter (into|a)|handling))",
                "(carry out|organize|run|manage|conduct)(.){0,32}(promotion|event|competition|contest|activit(y|ies))",
            ],
            "RecommendPurchases": [
                "(recommend|suggest)(ing)?(.){0,64}(product|service|item|purchase|buy)(s)?"
            ],
            "AutomaticPurchases": [
                "(automatic|auto)(.){0,32}(ship|purchase|buy)(s)?",
                "(make|process|handle|facilitate)(.){0,32}(automatic|auto)(.){0,32}(purchase|buy)(s)?",
            ],
            "SubscriptionManagement": [
                "\\bsubscription management\\b",
                "\\bsubscription service(s)?\\b",
                "(manage|handle|process|provide)(.){0,64}(subscription)",
                "\\brecurring payments\\b",
            ],
            "CloudService": ["cloud(.){0,20}service"],
            "StorageService": [
                "storage(.){0,20}service",
                "\\bcloud storage\\b",
                "\\bstore(.){0,20}data\\b",
            ],
            "BackupService": ["backup(.){0,20}service"],
            "MusicService": ["music(.){0,20}service"],
            "ThemeService": ["theme(.){0,20}service"],
            "WallpaperService": ["wallpaper(.){0,20}service"],
            "LocationService": ["location(.){0,20}service", "\\bmap navigation"],
            "WeatherService": [
                "weather(.){0,20}service",
                "(retrieve|retrieving) weather",
            ],
            "SecurityService": ["security(.){0,32}service"],
            "CommunicationService": ["communication(.){0,32}service"],
            "HeatingSystem": [
                "\\bheating(.){0,64}system",
                "(adjust)(.){0,20}(temperature|thermostat)",
            ],
            "CoolingSystem": [
                "\\bcooling(.){0,64}system",
                "\\bair(-| )condition(ing)?(.){0,20}system\\b",
            ],
            "Navigation": ["\\bmap navigation"],
            "FindDevice": ["\\bfind(ing)?(.){0,20}device\\b"],
            "ConserveResources": ["conserve resource"],
            "SaveWater": ["\\b(sav|conserv)(e|ing) water\\b"],
            "SaveEnergy": ["\\b(sav|conserv)(e|ing) energy\\b"],
            "OptimizeWifFi": ["(optimize|improve)(.){0,20}wi(-)?fi"],
            "SwitchLight": [
                "turn (off|on)(.){0,20}light",
                "\\bswitch(ing)?(.){0,32}light(s)?\\b",
            ],
            "Invoice": [
                "\\b(issue|provide|generate|send|deliver)(.){0,32}(invoice|bill)(s)?\\b"
            ],
            "SocialSharing": ["\\bsocial shar(e|ing)\\b"],
            "ErrorDiagnosis": [
                "(diagnose|diagnosis)(.){0,32}(error|problem|issue|fault|failure)"
            ],
            "PhotoMetadata": [
                "(store|embed|add|save|record)(.){0,32}(metadata|geotag|tag|information|detail)(.){0,32}(photo|image|picture)",
                "record(.){0,20}(while|when|during)(.){0,20}(tak|captur)(e|ing)(.){0,20}(photo|image|picture)",
            ],
            "SecurityScan": ["security scan function(s)?"],
            "VoiceSupport": [
                "voice enabled (device|product|service|feature)",
                "\\bvoice support",
            ],
            "TaxFreePurchase": [
                "(?=.*(provide|enable|allow|make possible))(?=.*tax-free)"
            ],
            "ScanQRCode": ["(scan)(.){0,64}qr(-| )code"],
            "SaveToAlbum": ["(save|store)(.){0,64}album"],
            "DeliverPrize": [
                "(provide|send|ship|deliver)(.){0,64}(winnings|prize|trophy)"
            ],
            "EnablingConnectivity": ["\\benabl(e|ing) connectivity", "work together"],
            "ParkDevice": ["\\b(park)(.){0,32}(device|product|mower|vacuum|robot)"],
            "DataInfrastructure": ["(provide|run|maintain)(.){0,32}infrastructure"],
            "GoogleAssistance": ["\\bgoogle assistant\\b"],
            "AmazonAlexa": ["\\bamazon alexa\\b"],
            "AppleSiri": ["\\bapple siri\\b"],
        }
    ),
    communication=AttributePattern.from_dict(
        {
            "InformationalUpdates": [
                "\\b(keep|send)(ing)? you (inform|update|posted)",
                "\\b(email|message)(s)?(.){0,32}contain(ing)? (the )?information\\b",
                "\\b(send(ing)?|provid(e|ing)|receiv(e|ing))(.){0,32}(news|information|details|notice)",
                "\\bnew(.){0,32}(information|update|detail)(s)?\\b",
                "\\b(change|update)(s)?(.){0,32}(service|feature|product)(s)?\\b",
                "\\binformation about (how|when|what|where|why)\\b",
            ],
            "UpdateNotifications": [
                "\\b(update|upgrade) notification(s)?\\b",
                "\\bnotify(ing)? you (about|of)(.){0,32}(update|upgrade)\\b",
            ],
            "Notifications": [
                "\\b(push-)?notification(s)?\\b",
                "\\balert(s)?\\b",
                "\\bnotify(ing)?\\b",
                "\\btell you (when|if)\\b",
                "\\bpush message(s)?\\b",
            ],
            "DowntimeNotifications": [
                "\\bdowntime (alert|notification)(s)?\\b",
                "\\bnotify(ing)? you (about|of)(.){0,32}downtime\\b",
            ],
            "MandatorySystemNotifications": [
                "mandatory (service|system) notification(s)?"
            ],
            "Reminders": ["\\breminder(s)?\\b", "\\bremind you\\b"],
            "Feedback": [
                "\\bfeedback\\b",
                "\\bsuggestion(s)?\\b",
                "(obtaining|gather)(.){0,20} (view|opinion)(s)?",
            ],
            "Review": ["\\breview(s)?\\b", "\\brat(ed|ing)?\\b"],
            "Newsletter": ["\\bnewsletter(s)?\\b", "\\bnews bulletin\\b"],
            "Survey": ["\\bsurvey(s)?\\b", "\\bquestionnaire(s)?\\b"],
            "CustomerService": [
                "\\bcustomer (service|support)\\b",
                "provid(e|ing)(.){0,32}(support|assistance|help|solution(s)?)\\b",
                "receiv(e|ing) advice\\b",
                "\\b(process(ing)?|verify) (your|the )?(request|issue|problem|query|queries)\\b",
                "\\bcontact form\\b",
                "\\b(solve|answer|respond|handl(e|ing)|deal(ing)?)(.){0,32}(enquirie|question|query|queries|issue|request)(s)?\\b",
                "support communication",
                "call(-| )?(centre|center)(s)?\\b",
                "\\bhelp desk\\b",
                "support (purpose|request|issue|question)(s)?\\b",
                "\\b(grant|deny)(.){0,20}request",
                "\\bproduct support\\b",
            ],
            "TechnicalSupport": [
                "\\btechnical support\\b",
                "\\btech support\\b",
                "\\btechnical help\\b",
                "\\btroubleshoot (any |your )?(problem|issue)(s)?\\b",
            ],
            "FanPage": [
                "\\bfan page(s)?\\b",
            ],
            "ChatBot": ["\\bchat(-)?bot\\b", "\\bvirtual assistant\\b"],
            "LiveChat": ["\\blive chat\\b", "\\breal[- ]time chat\\b"],
            "AccountVerification": [
                "\\baccount verif(y|ication)(s)?\\b",
                "\\bconfirm(.){0,20}creation(.){0,20}account",
            ],
            "OrderCommunication": [
                "\\b(order|shipping|delivery) (confirmation|notification)(s)?\\b",
                "\\bconfirm(ing)?(.){0,20}order(s)?\\b",
                "(detail|information|message|notification|alert|notice)(s)?(.){0,20}about( your)? order",
                "(informing|notify)(.){0,48}(order|shipping)\\b",
                "(?=.*\\breturn\\b)(?=.*(instruction|detail|information))",
                "communicati(ng|ion)(.){0,32}(order|shipping|delivery)",
                "\\bquestion(s)? about (your )?order(s)?\\b",
                "procurement-related communication",
            ],
            "BillingInquiries": [
                "\\b(billing|invoice|payment)( )?(inquiry|question|issue|problem)(s)?\\b",
                "\\b(question|issue|problem)(s)? about (your )?(bill|invoice|payment)\\b",
            ],
            "PricingInquiries": [
                "\\b(pricing|cost|price)( )?(inquiry|question|issue|problem)(s)?\\b",
                "\\b(question|issue|problem)(s)? about (your )?(pricing|cost|price)\\b",
            ],
            "LegalChanges": [
                "\\b(?=.*(change|update))(?=.*(terms|conditions|(privacy|security) (policy|notice)|legal|agreement))",
                "\\bprivacy update(s)?\\b",
            ],
            "WinnerNotification": [
                "\\b(notify|inform)(.){0,32}(winner|won|participant)\\b"
            ],
            "MarketingMessage": [
                "\\b(promotional|marketing) (text|message|offer|e(-)?mail|sms|communication)(s)?\\b",
                "(?=.*(contact|message|e(-)?mail))(?=.*interested in)",
                "(?=.*(send|receive))(?=.*(brochure|catalog|catalogue))",
                "(?=.*(e(-)?mail|sms))(?=.*campaign)",
            ],
            "SocialMedia": [
                "\\bfan page(s)?\\b",
                "(via|using) social media",
                "community (platform|page|site|forum)",
                "company representation page",
            ],
            "ProductSafety": ["\\b(security|safety) alert(s)?\\b"],
            "EmergencyContact": ["(?=.*emergency)(?=.*(notify|contact|alert|reach))"],
            "ErrorReporting": [
                "(notif(i|y)|alert|report)(.){0,32}(error|issue|problem)(s)?",
                "(error|issue|problem)(s)?(.){0,32}(report|notif(i|y)|alert)",
            ],
            "TransactionCommunication": [
                "(?=.*(transaction|receipt|purchase))(?=.*(communication|message|notification|e(-)?mail|alert|detail|notice))"
            ],
            "BirthdayGreeting": ["(?=.*birthday)(?=.*(greeting|message))"],
            "Membership": [
                "(?=.*(membership|subscription))(?=.*(contact|communication|message|notification|e(-)?mail|alert|detail|notice))"
            ],
            "LoyaltyProgram": [
                "(?=.*loyalty)(?=.*(contact|communication|message|notification|e(-)?mail|alert|detail|notice))"
            ],
        }
    ),
    tech_priv=AttributePattern.from_dict(
        {
            "Anonymization": [
                "anonymization",
                "anonymised",
                "anonymized",
                "de-identified",
            ],
            "Pseudonymization": ["pseudonymization", "pseudonymised", "pseudonymized"],
            "Aggregation": ["aggregation", "aggregated"],
            "Shortened": ["shortened", "truncated", "abbreviated"],
            "DataSeparation": [
                "(?=.*\\b(isolat|separat|segregat)\\w*)(?=.*\\b(personal(ly)?[\\s-]identifiable|pii|personal)\\s+(data|information))(?=.*\\b(non[\\s-]personal(ly)?[\\s-]identifiable|npii|non[\\s-]personal)\\s+(data|information))",
                "(?=.*\\b(keep|maintain|store|process)\\w*\\s+separate(ly|d)?)(?=.*\\b(personal|pii)\\b)(?=.*\\b(non-personal|npii)\\b)",
                "(?=.*\\b(not|never|cannot|will\\s+not|shall\\s+not)\\s+(merge|link|combine|connect|associate|join)\\w*)(?=.*\\b(personal|pii|pseudonymized|anonymized|de-identified))(?=.*\\b(data|information)\\b)",
                "(?=.*\\b(pseudonymized|pseudonymised|anonymized|anonymised|de-identified)\\s+(data|information))(?=.*\\b(not|never|cannot)\\s+(merge|link|re-identif))",
            ],
            "Desensitization": ["desensitization", "desensitized"],
        }
    ),
    tech_sec=AttributePattern.from_dict(
        {
            "Encryption": ["encrypt"],
            "Monitoring": ["monitoring", "monitored"],
            "TwoFactorAuth": [
                "(two|multi)(-| )factor authentication",
                "2fa",
                "two factor auth",
                "two-step verification",
                "two step verification",
            ],
            "HashedPassword": ["hashed password", "password hashing"],
            "MutualAuthentication": ["\\bmutual(.){0,20}authentication\\b"],
            "ProhibitedDefaultPassword": [
                "(?=.*\\b(prohibit|not allow|disallow|forbid)\\b)(?=.*\\b(default|standart)password\\b)"
            ],
        }
    ),
    cont_sec=AttributePattern.from_dict(
        {
            "DataProcessingAgreement": ["data processing agreement"],
            "StandardContractualClauses": ["standard contractual clauses", "\\bscc\\b"],
            "AdequacyDecision": ["adequacy decision"],
            "Audits": ["\\baudits\\b"],
            "Confidentiality": ["\\bconfidentiality\\b", "strictly confidential"],
            "BindingContractualRules": [
                "binding corporate rules",
                "binding contractual obligations",
            ],
        }
    ),
    chosen=AttributePattern.from_dict(
        {
            "AuthorizedAgent": [
                "(?=.*(authorized|authorization|designate))(?=.*\\b(agend)(s)?\\b)",
                "authorized to act on your behalf",
                "authorize someone to act on your behalf",
                "legally authorized person",
            ],
            "DesignatedPerson": ["\\bperson you designate", "designated person"],
            "AppointedRepresentatives": [
                "(appointed|designate|authorized) representative"
            ],
            "LegalRepresentative": ["legal representative"],
            "Caregiver": ["\\bcaregiver(s)?\\b", "\\bcarer(s)?\\b"],
            "Invitee": ["\\binvitee(s)?\\b"],
            "Proxy": ["proxy of the holder"],
            "LegalGuardian": ["\\blegal guardian(s)?\\b"],
            "AuthorizedUser": ["\\bauthorized user"],
            "TrustedIndividual": [
                "\\b(trusted|selected) (individual|person|contact)(s)?\\b"
            ],
            "DesignatedAdministrator": ["\\bdesignated administrator\\b"],
            "FamilyMember": ["\\bfamily member(s)?\\b", "\\brelative(s)?\\b"],
        }
    ),
    profiling=AttributePattern.from_dict(
        {
            "NotProfiling": [
                "not performed",
                "not engage",
                "(not|other then)(.){0,64}(infer characteristics|profiling)",
                "no profile(.){0,32}(generated|created)",
                "not subject(ed)?to",
            ]
        }
    ),
    automated_decision=AttributePattern.from_dict(
        {
            "NotAutomatedDecisionMaking": [
                "not performed",
                "not engage",
                "(not|other then)(.){0,64}automated decision(-| )making",
                "no automated decision(-| )making",
                "not subject(ed)?to",
            ]
        }
    ),
    certifications=AttributePattern.from_dict(
        {
            "ISO/IEC 27001:2013": ["ISO/IEC 27001:2013"],
            "ISO/IEC 27701:2019": ["ISO/IEC 27701:2019"],
            "ISO/IEC 27018:2019": ["ISO/IEC 27018:2019"],
            "SOC 2 Type II": ["SOC 2 Type II"],
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
                "responsible for supervising(.){0,20}minor\\b",
                "(?=.*(child|minor|under 18|under the age of majority))(?=.*(responsible|responsibility|liable|liability))\\b",
            ],
            "ThirdPartyData": [
                "data belonging to (third parties|other)",
                "(other|those) (individual|people|user|person)(.){0,20}(information|data|detail)",
            ],
        }
    ),
)
""" English language attribute patterns. """

#------------------------------------------

DE_DURATION_PATTERN_CONFIG: DurationPattern = DurationPattern(
    unit=AttributePattern.from_dict(
        {
            "Days": [r"\btage?\b"],
            "Weeks": [r"\bwochen?\b"],
            "Months": [r"\bmonate?\b"],
            "Years": [r"\bjahre?\b"],
            "Hours": [r"\bstunden?\b"],
            "Minutes": [r"\bminuten?\b"],
            "Seconds": [r"\bsekunden?\b"],
        }
    ),
    length=AttributePattern.from_dict(
        {
            "1": [r"\b1\b", r"\beins\b"],
            "2": [r"\b2\b", r"\bzwei\b"],
            "3": [r"\b3\b", r"\bdrei\b"],
            "4": [r"\b4\b", r"\bvier\b"],
            "5": [r"\b5\b", r"\bf(ü|ue)nf\b"],
            "6": [r"\b6\b", r"\bsechs\b"],
            "7": [r"\b7\b", r"\bsieben\b"],
            "8": [r"\b8\b", r"\bacht\b"],
            "9": [r"\b9\b", r"\bneun\b"],
            "10": [r"\b10\b", r"\bzehn\b"],
            "15": [r"\b15\b", r"\bf(ü|ue)nfzehn\b"],
            "20": [r"\b20\b", r"\bzwanzig\b"],
            "30": [r"\b30\b", r"\bdrei(ß|ss)ig\b"],
            "60": [r"\b60\b", r"\bsechzig\b"],
            "90": [r"\b90\b", r"\bneunzig\b"],
            "180": [r"\b180\b", r"\bein[- ]?hundert (und )?achtzig\b", "einhundertachzig"],
            "365": [r"\b365\b", r"\bein[- ]?hundert (und )?fünf[- ]? (und )?sechzig\b", "dreihundertfünfundsechzig"],
        }
    ),
)
""" German language duration patterns. """

EN_DATE_PATTERN_CONFIG: DatePattern = DatePattern(
    {
        "%Y-%m-%d": "\\b(\\d{4})-(\\d{1,2})-(\\d{1,2})\\b",
        "%Y/%m/%d": "\\b(\\d{4})/(\\d{1,2})/(\\d{1,2})\\b",
        "%m/%d/%Y": "\\b(\\d{1,2})/(\\d{1,2})/(\\d{4})\\b",
        "%m-%d-%Y": "\\b(\\d{1,2})-(\\d{1,2})-(\\d{4})\\b",
        "%d.%m.%Y": "\\b(\\d{1,2})\\.(\\d{1,2})\\.(\\d{4})\\b",
        "%d/%m/%Y": "\\b(\\d{1,2})/(\\d{1,2})/(\\d{4})\\b",
        "%d-%m-%Y": "\\b(\\d{1,2})-(\\d{1,2})-(\\d{4})\\b",
        "%B %d, %Y": "\\b(Januar|Februar|M(ä|ae)rz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\\s+(\\d{1,2}),?\\s+(\\d{4})\\b",
        "%d %B %Y": "\\b(\\d{1,2})\\s+(Januar|Februar|M(ä|ae)rz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\\s+(\\d{4})\\b",
        "%b %d, %Y": "\\b(Jan|Feb|M(ä|ae)r|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)[a-z]*\\.?\\s+(\\d{1,2}),?\\s+(\\d{4})\\b",
        "%d %b %Y": "\\b(\\d{1,2})\\s+(Jan|Feb|M(ä|ae)r|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)[a-z]*\\.?\\s+(\\d{4})\\b",
        "%m/%d/%y": "\\b(\\d{1,2})/(\\d{1,2})/(\\d{2})\\b",
        "%d.%m.%y": "\\b(\\d{1,2})\\.(\\d{1,2})\\.(\\d{2})\\b",
        "%Y%m%d": "\\b(\\d{4})(\\d{2})(\\d{2})\\b",
        "%B %Y": "\\b(Januar|Februar|M(ä|ae)rz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember),?\\s+(\\d{4})\\b",
        "%b %Y": "\\b(Jan|Feb|M(ä|ae)r|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)[a-z]*\\.?\\s*,?\\s+(\\d{4})\\b",
    }
)
""" German language date patterns. """