"""Schémas de configuration des téléphones Mitel.

Noms de paramètres, valeurs et défauts tirés du « Mitel 6800/6900/6900w Series SIP Phones
Administrator Guide », release 6.4 SP3 (annexe A). Les choix commencent par une option vide :
un paramètre laissé vide n'est pas écrit dans le .cfg et le téléphone garde sa valeur par défaut.
"""

SCHEMA_VERSION = 2


# --- Constructeurs de champs -------------------------------------------------

def _opts(options):
    out = [{"value": "", "label": "— not set —"}]
    for o in options:
        value, label = (o if isinstance(o, tuple) else (o, o))
        out.append({"value": str(value), "label": f"{value} — {label}" if str(value) != label else label})
    return out


def text(key, label, default=None, help=None, suggestions=None):
    s = {"key": key, "label": label, "type": "string"}
    if default is not None:
        s["default"] = str(default)
    if help:
        s["help"] = help
    if suggestions:
        s["suggestions"] = suggestions
    return s


def secret(key, label, default=None, help=None):
    s = text(key, label, default, help)
    s["type"] = "password"
    return s


def choice(key, label, options, default=None, help=None):
    s = {"key": key, "label": label, "type": "choice", "options": _opts(options)}
    if default is not None:
        s["default"] = str(default)
    if help:
        s["help"] = help
    return s


def boolean(key, label, default=None, help=None, on="Enabled", off="Disabled"):
    return choice(key, label, [(0, off), (1, on)], default, help)


def section(name, *settings):
    for s in settings:
        s["section"] = name
    return list(settings)


def _range(a, b):
    return [str(i) for i in range(a, b + 1)]


# --- Listes de valeurs -------------------------------------------------------

TIME_ZONES = [
    "FR-Paris", "BE-Brussels", "CH-Zurich", "LU-Luxembourg", "MC-Monaco", "DE-Berlin", "GB-London",
    "IE-Dublin", "ES-Madrid", "IT-Rome", "NL-Amsterdam", "PT-Lisbon", "AT-Vienna", "DK-Copenhagen",
    "SE-Stockholm", "NO-Oslo", "FI-Helsinki", "PL-Warsaw", "CZ-Prague", "GR-Athens", "RO-Bucharest",
    "MQ-Martinique", "GP-Guadeloupe", "GF-Cayenne", "MU-Mauritius", "CA-Eastern", "US-Eastern",
    "US-Central", "US-Mountain", "US-Pacific", "Custom", "DP-Dhcp",
]

LANGUAGE_PACKS = [
    "lang_fr.txt", "lang_fr_ca.txt", "lang_de.txt", "lang_es.txt", "lang_es_mx.txt", "lang_it.txt",
    "lang_nl.txt", "lang_nl_nl.txt", "lang_pt.txt", "lang_pt_br.txt", "lang_ca.txt", "lang_eu.txt",
    "lang_da.txt", "lang_sv.txt", "lang_no.txt", "lang_fi.txt", "lang_pl.txt", "lang_cs.txt",
    "lang_sk.txt", "lang_hu.txt", "lang_ro.txt", "lang_ru.txt", "lang_tr.txt", "lang_el.txt",
    "lang_ar.txt", "lang_ko.txt", "lang_zh_cn.txt", "lang_zh_tw.txt",
]

INPUT_LANGUAGES = ["English", "French", "German", "Italian", "Spanish", "Portuguese", "Russian", "Nordic"]

TONE_SETS = ["US", "Australia", "Brazil", "Canada", "Europe", "France", "Germany", "Italy", "Italy2",
             "Malaysia", "Mexico", "Russia", "Slovakia", "UK"]

RING_TONES = [(0, "Tone 1"), (1, "Tone 2"), (2, "Tone 3"), (3, "Tone 4"), (4, "Tone 5"), (5, "Silent"),
              (6, "Tone 7"), (7, "Tone 8"), (8, "Tone 9"), (9, "Tone 10"), (10, "Tone 11"), (11, "Tone 12"),
              (12, "Tone 13"), (13, "Tone 14"), (14, "Tone 15"), (15, "Tone 16"), (20, "Velocity"), (21, "Skyline")]

VOLUME = _range(0, 9)

LANG_INDEX = [(0, "English"), (1, "language 1"), (2, "language 2"), (3, "language 3"), (4, "language 4")]

CODEC_HELP = ("Comma-separated list, e.g. payload=8;ptime=20;silsupp=on,payload=0;ptime=20;silsupp=on. "
              "Payloads: 0 G711u, 8 G711a, 9 G722, 18 G729, 112/113 L16, 117 iLBC, 120 OPUS")

# Types de touches valides par famille (annexe A, « Softkey/Programmable Key/... Parameters »)
TOP_SOFTKEY_TYPES = ["none", "line", "speeddial", "dnd", "blf", "list", "acd", "xml", "flash", "spre",
                     "callforward", "park", "pickup", "blfxfer", "speeddialxfer", "speeddialconf",
                     "speeddialmwi", "lcr", "directory", "filter", "callers", "redial", "conf", "xfer",
                     "icom", "services", "phonelock", "paging", "hotdesklogin", "discreetringing",
                     "callhistory", "callcenter", "mystatus", "contacts", "favorite", "empty"]
BOTTOM_SOFTKEY_TYPES = ["none", "speeddial", "dnd", "xml", "flash", "spre", "park", "pickup", "lcr",
                        "callforward", "speeddialxfer", "speeddialconf", "directory", "filter", "callers",
                        "redial", "conf", "xfer", "icom", "phonelock", "paging", "hotdesklogin",
                        "discreetringing", "callhistory", "callcenter", "contacts", "empty"]
PRGKEY_TYPES = ["none", "line", "speeddial", "dnd", "blf", "list", "acd", "xml", "flash", "spre", "park",
                "pickup", "lcr", "callforward", "blfxfer", "speeddialxfer", "speeddialconf", "speeddialmwi",
                "directory", "filter", "callers", "redial", "conf", "xfer", "icom", "services", "phonelock",
                "paging", "save", "delete", "hotdesklogin", "discreetringing", "callcenter", "empty"]
EXPMOD_TYPES = ["none", "line", "speeddial", "dnd", "blf", "list", "acd", "xml", "flash", "spre", "park",
                "pickup", "lcr", "callforward", "blfxfer", "speeddialxfer", "speeddialconf", "speeddialmwi",
                "directory", "filter", "callers", "redial", "conf", "xfer", "icom", "services", "phonelock",
                "paging", "save", "delete", "hotdesklogin", "discreetringing", "callhistory", "callcenter",
                "empty"]
HARDKEY_TYPES = ["none", "line", "speeddial", "dnd", "blf", "list", "acd", "xml", "flash", "spre", "park",
                 "pickup", "lcr", "callforward", "blfxfer", "speeddialconf", "speeddialmwi", "directory",
                 "filter", "services", "callers", "redial", "conf", "xfer", "icom", "phonelock", "paging",
                 "hotdesklogin", "discreetringing", "callhistory", "callcenter"]

KEY_STATES = "idle connected incoming outgoing busy"


# --- Paramètres globaux (tous modèles) ---------------------------------------

def _global_settings():
    return [
        *section(
            "Network",
            boolean("dhcp", "DHCP", 1),
            text("ip", "Static IP address", help="Used when DHCP is disabled"),
            text("subnet mask", "Subnet mask"),
            text("default gateway", "Default gateway"),
            text("dns1", "Primary DNS"),
            text("dns2", "Secondary DNS"),
            choice("ethernet port 0", "LAN port speed/duplex",
                   [(0, "Auto negotiate"), (1, "Full 10Mbps"), (2, "Full 100Mbps"), (3, "Full 1000Mbps"),
                    (4, "Half 10Mbps"), (5, "Half 100Mbps"), (6, "Half 1000Mbps")], 0),
            choice("ethernet port 1", "PC port speed/duplex",
                   [(0, "Auto negotiate"), (1, "Full 10Mbps"), (2, "Full 100Mbps"), (3, "Full 1000Mbps"),
                    (4, "Half 10Mbps"), (5, "Half 100Mbps"), (6, "Half 1000Mbps")], 0),
            boolean("pc port passthru enabled", "PC port passthrough", 1),
            boolean("lldp", "LLDP-MED", 1),
            text("lldp interval", "LLDP interval (seconds, 0 = off)", 30),
            choice("use lldp elin", "Use LLDP ELIN as emergency caller ID",
                   [(0, "Disabled"), (1, "Enabled"), (2, "Enabled + elin= in From header")], 1),
        ),
        *section(
            "VLAN & QoS",
            boolean("tagging enabled", "VLAN tagging", 0, help="The phone reboots when this changes"),
            text("vlan id", "VLAN ID (LAN port)", help="1-4094, 4095 = untagged"),
            choice("priority non-ip", "VLAN priority for non-IP packets", _range(0, 7), 5),
            text("vlan id port 1", "VLAN ID (PC port)", help="1-4094, 4095 = untagged"),
            choice("qos eth port 1 priority", "VLAN priority for PC port", _range(0, 7), 0),
            text("tos sip", "DSCP for SIP", 26, help="0-63"),
            text("tos rtp", "DSCP for RTP", 46, help="0-63"),
            text("tos rtcp", "DSCP for RTCP", 46, help="0-63"),
        ),
        *section(
            "802.1x",
            choice("eap type", "EAP authentication", [(0, "Disabled"), (1, "MD5"), (2, "TLS")], 0),
            text("identity", "802.1x identity"),
            secret("md5 password", "802.1x MD5 password"),
        ),
        *section(
            "Configuration server",
            choice("download protocol", "Download protocol", ["TFTP", "FTP", "HTTP", "HTTPS"], "TFTP"),
            text("tftp server", "TFTP server"),
            text("tftp path", "TFTP path"),
            text("alternate tftp server", "Alternate TFTP server"),
            text("alternate tftp path", "Alternate TFTP path"),
            boolean("use alternate tftp", "Use alternate TFTP server", 0),
            text("ftp server", "FTP server"),
            text("ftp path", "FTP path"),
            text("ftp username", "FTP username"),
            secret("ftp password", "FTP password"),
            text("http server", "HTTP server"),
            text("http path", "HTTP path"),
            text("http port", "HTTP port", 80),
            text("https server", "HTTPS server"),
            text("https path", "HTTPS path"),
            text("https port", "HTTPS port", 443),
            text("firmware server", "Firmware server", help="e.g. http://10.0.0.1/firmware"),
            choice("auto resync mode", "Auto resync",
                   [(0, "None"), (1, "Configuration files"), (2, "Firmware"), (3, "Both")], 0),
            text("auto resync time", "Auto resync time (HH:MM)", "00:00"),
            text("auto resync max delay", "Auto resync max delay (minutes)", 15, help="0-1439"),
            text("auto resync days", "Days between resyncs", 0, help="0-364"),
        ),
        *section(
            "Passwords & web interface",
            secret("admin password", "Admin password", 22222, help="Up to 15 alphanumeric characters"),
            secret("user password", "User password"),
            boolean("options password enabled", "Require password for Options menu", 0),
            choice("web interface enabled", "Web interface",
                   [(0, "Disabled"), (1, "Admin and user"), (2, "Admin only")], 1),
            boolean("phone lock", "Allow phone lock", help="Enables/disables the phone lock feature"),
            boolean("speeddial edit", "Allow users to add/edit speeddial keys", 1),
        ),
        *section(
            "Time & date",
            choice("time server disabled", "Time server", [(0, "Use time servers"), (1, "Disabled")], 0),
            text("time server1", "Time server 1", suggestions=["fr.pool.ntp.org", "pool.ntp.org"]),
            text("time server2", "Time server 2"),
            text("time server3", "Time server 3"),
            text("time zone name", "Time zone", "US-Eastern", suggestions=TIME_ZONES),
            choice("dst config", "Daylight saving time",
                   [(0, "Off"), (1, "30 min summertime"), (2, "1 hr summertime"), (3, "Automatic")], 3),
            choice("time format", "Time format", [(0, "12h"), (1, "24h")], 0),
            choice("date format", "Date format",
                   [(0, "WWW MMM DD"), (1, "DD-MMM-YY"), (2, "YYYY-MM-DD"), (3, "DD/MM/YYYY"),
                    (4, "DD/MM/YY"), (5, "DD-MM-YY"), (6, "MM/DD/YY"), (7, "MMM DD"), (8, "DD MMM YYYY"),
                    (9, "WWW DD MMM"), (10, "DD MMM"), (11, "DD.MM.YYYY")], 0),
        ),
        *section(
            "Language",
            text("language 1", "Language pack 1", suggestions=LANGUAGE_PACKS),
            text("language 2", "Language pack 2", suggestions=LANGUAGE_PACKS),
            text("language 3", "Language pack 3", suggestions=LANGUAGE_PACKS),
            text("language 4", "Language pack 4", suggestions=LANGUAGE_PACKS),
            choice("language", "Phone UI language", LANG_INDEX, 0),
            choice("web language", "Web UI language", LANG_INDEX, 0),
            text("input language", "Keypad input language", "English", suggestions=INPUT_LANGUAGES),
        ),
        *section(
            "Tones & ringing",
            choice("tone set", "Tone set (country)", TONE_SETS, "US"),
            choice("ring tone", "Ring tone (global)", RING_TONES, 0),
            boolean("call waiting", "Call waiting", 1),
            boolean("call waiting tone", "Call waiting tone", 1),
            text("call waiting tone period", "Call waiting tone period (seconds)", 0),
            choice("stutter disabled", "Stuttered dial tone for MWI", [(0, "Enabled"), (1, "Disabled")], 0),
            choice("play a ring splash", "BLF ring splash",
                   [(0, "Off"), (1, "Normal"), (2, "Normal, also during active calls")]),
        ),
        *section(
            "Audio",
            choice("audio mode", "Handsfree key mode",
                   [(0, "Speaker"), (1, "Headset"), (2, "Speaker/Headset"), (3, "Headset/Speaker")], 0),
            choice("handset volume", "Handset volume", VOLUME, 4),
            choice("speaker volume", "Speaker volume", VOLUME, 4),
            choice("headset volume", "Headset volume", VOLUME, 4),
            choice("ringer volume", "Ringer volume", VOLUME, 5),
        ),
        *section(
            "SIP identity (global)",
            text("sip screen name", "Screen name"),
            text("sip screen name 2", "Screen name 2"),
            text("sip user name", "User name (phone number)"),
            text("sip display name", "Display name (caller ID)"),
            text("sip auth name", "Authentication name"),
            secret("sip password", "Password"),
            choice("sip mode", "Line mode", [(0, "Generic"), (1, "BroadSoft SCA"), (3, "BLA")], 0),
            text("sip vmail", "Voicemail number"),
        ),
        *section(
            "SIP servers (global)",
            text("sip proxy ip", "Proxy server"),
            text("sip proxy port", "Proxy port"),
            text("sip backup proxy ip", "Backup proxy server"),
            text("sip backup proxy port", "Backup proxy port"),
            text("sip outbound proxy", "Outbound proxy"),
            text("sip outbound proxy port", "Outbound proxy port"),
            text("sip backup outbound proxy", "Backup outbound proxy"),
            text("sip backup outbound proxy port", "Backup outbound proxy port"),
            text("sip registrar ip", "Registrar server"),
            text("sip registrar port", "Registrar port"),
            text("sip backup registrar ip", "Backup registrar server"),
            text("sip backup registrar port", "Backup registrar port"),
            text("sip registration period", "Registration period (seconds)", 0),
        ),
        *section(
            "SIP advanced",
            choice("sip transport protocol", "Transport protocol",
                   [(0, "UDP + TCP"), (1, "UDP"), (2, "TCP"), (4, "TLS")], 1),
            text("sip local port", "Local SIP port (UDP/TCP)", 5060),
            text("sip local tls port", "Local SIP TLS port", 5061),
            boolean("sip rport", "Rport (RFC 3581)", 0),
            text("sip keepalive timer", "UDP keep-alive (seconds, 0 = off)", 0),
            boolean("sip outbound support", "SIP outbound support (draft 15)", 0),
            text("sip session timer", "Session timer (seconds, 0 or ≥ 90)", 0),
            text("sip registration retry timer", "Registration retry timer (seconds)"),
            boolean("sip explicit mwi subscription", "Explicit MWI subscription", 0),
            text("sip explicit mwi subscription period", "MWI subscription period (seconds)"),
            boolean("sip send mac", "Send MAC address in REGISTER", 0),
            boolean("sip send line", "Send line number in REGISTER", 0),
            text("sip blf subscription period", "BLF subscription period (seconds)"),
            boolean("sip symmetric udp signaling", "Symmetric UDP signaling", 1),
            boolean("sip whitelist", "Accept SIP only from configured proxies", 0),
            text("ip whitelist", "IP whitelist", help="Comma-separated IPv4 addresses"),
            boolean("sip unregister on boot", "Unregister on boot", 0),
        ),
        *section(
            "RTP, codecs & DTMF",
            text("sip rtp port", "RTP base port", 3000),
            boolean("sip use basic codecs", "Use basic codecs (G711u/a, G729)", 0),
            text("sip customized codec", "Codec preference list", help=CODEC_HELP),
            boolean("sip silence suppression", "Silence suppression", 1),
            boolean("sip out-of-band dtmf", "Out-of-band DTMF (RFC 2833)", 1),
            choice("sip dtmf method", "DTMF method", [(0, "RTP"), (1, "SIP INFO"), (2, "Both")], 0),
            choice("sip srtp mode", "SRTP",
                   [(0, "Disabled"), (1, "SRTP preferred"), (2, "SRTP only"), (3, "SRTP and RTP")], 0),
        ),
        *section(
            "Dial plan",
            text("sip dial plan", "Dial plan", help='e.g. "x+#|xx+*"'),
            boolean("sip dial plan terminator", "Send # as dial terminator", 0),
            text("sip digit timeout", "Inter-digit timeout (seconds)", 4),
            text("emergency dial plan", "Emergency dial plan", help="e.g. 15|17|18|112"),
            text("sip autodial number", "Hotline / autodial number"),
            text("sip autodial timeout", "Autodial timeout (seconds, 0 = immediate)"),
        ),
        *section(
            "Call features",
            boolean("call forward disabled", "Disable call forward menus", 0, on="Disabled (hidden)",
                    off="Allowed"),
            choice("call forward key mode", "Call forward key mode", [(0, "Account"), (1, "Phone"), (2, "Custom")], 0),
            choice("dnd key mode", "DND key mode", [(0, "Account"), (1, "Phone"), (2, "Custom")], 1),
            boolean("directed call pickup", "Directed call pickup", 0),
            text("directed call pickup prefix", "Directed call pickup prefix"),
            text("sip park pickup config", "Park / pickup config", help="<park>;<pickup>;<asterisk|sylantro|broadworks>"),
            boolean("missed calls indicator disabled", "Disable missed calls indicator", 0, on="Disabled",
                    off="Enabled"),
            boolean("callers list disabled", "Disable callers list", 0, on="Disabled", off="Enabled"),
            boolean("redial disabled", "Disable redial", 0, on="Disabled", off="Enabled"),
            boolean("conference disabled", "Disable conference", 0, on="Disabled", off="Enabled"),
            boolean("call transfer disabled", "Disable transfer", 0, on="Disabled", off="Enabled"),
            boolean("call hold reminder", "Call hold reminder", 0),
            text("call hold reminder timer", "Hold reminder delay (seconds)"),
            text("call hold reminder frequency", "Hold reminder frequency (seconds)"),
            text("preferred line", "Preferred line"),
            text("preferred line timeout", "Preferred line timeout (seconds)"),
            boolean("goodbye cancels incoming call", "Goodbye key rejects incoming call"),
            boolean("switch focus to ringing line", "Switch focus to ringing line"),
            boolean("priority alerting enabled", "Priority alerting"),
            choice("blf key mode", "BLF key during active call",
                   [(0, "Send DTMF"), (1, "Hold and dial"), (2, "HTTP GET action uri blf")], 0),
            text("list uri", "BLF/List URI"),
        ),
        *section(
            "Intercom & paging",
            choice("sip intercom type", "Intercom type", [(1, "Phone-side"), (2, "Server-side"), (3, "Off")], 3),
            text("sip intercom prefix code", "Server-side intercom prefix"),
            text("sip intercom line", "Intercom line", 1),
            boolean("sip allow auto answer", "Auto-answer intercom calls", 1),
            boolean("sip intercom mute mic", "Mute mic on intercom answer", 1),
            boolean("sip intercom warning tone", "Intercom warning tone", 1),
            boolean("sip intercom allow barge in", "Allow intercom barge-in"),
            text("paging group listening", "Paging groups listened",
                 help="Multicast address:port list, e.g. 224.0.0.2:10000,239.0.1.20:15000"),
        ),
        *section(
            "Voicemail & MWI",
            text("mwi led line", "MWI LED line (0 = all lines)", 0),
        ),
        *section(
            "Directory & LDAP",
            text("directory 1", "Directory 1 (CSV file / URI)", help="A bare filename is prefixed with tftp://<SFTP host>/"),
            text("directory 1 name", "Directory 1 name"),
            boolean("directory 1 enabled", "Directory 1 enabled", 1),
            text("directory 2", "Directory 2 (CSV file / URI)"),
            text("directory 2 name", "Directory 2 name"),
            boolean("directory 2 enabled", "Directory 2 enabled", 1),
            boolean("directory disabled", "Disable directory", 0, on="Disabled", off="Enabled"),
            boolean("ldap enabled", "LDAP directory"),
            text("ldap name", "LDAP directory name"),
            text("ldap server", "LDAP server", help="e.g. user:password@ldap.company.com:3268"),
            text("ldap base dn", "LDAP base DN"),
            text("ldap user name", "LDAP user name"),
        ),
        *section(
            "XML & action URIs",
            text("xml application URI", "XML application URI"),
            text("xml application title", "XML application title"),
            text("xml application post list", "Allowed XML push servers"),
            text("action uri startup", "Action URI: startup"),
            text("action uri registered", "Action URI: registered"),
            text("action uri registration event", "Action URI: registration event"),
            text("action uri incoming", "Action URI: incoming call"),
            text("action uri outgoing", "Action URI: outgoing call"),
            text("action uri offhook", "Action URI: off-hook"),
            text("action uri onhook", "Action URI: on-hook"),
            text("action uri connected", "Action URI: connected"),
            text("action uri disconnected", "Action URI: disconnected"),
            text("action uri blf", "Action URI: BLF key"),
            text("action uri poll", "Polling action URI"),
            text("action uri poll interval", "Polling interval (seconds)"),
        ),
        *section(
            "Logs & diagnostics",
            text("log server ip", "Syslog server"),
            text("log server port", "Syslog port"),
        ),
        *section(
            "Not in admin guide 6.4",
            choice("contact rcs", "Contact Mitel redirect service (RCS)", [(0, "Off"), (1, "On")]),
            text("aastra md5", "Aastra MD5 config hash"),
            text("mac md5", "MAC config MD5 hash"),
        ),
    ]


def _line_settings():
    """Paramètres par ligne ; « {n} » est remplacé par le numéro de ligne."""
    p = "sip line{n} "
    return [
        *section(
            "Identity",
            text(p + "screen name", "Screen name"),
            text(p + "screen name 2", "Screen name 2"),
            text(p + "user name", "User name (phone number)"),
            text(p + "display name", "Display name (caller ID)"),
            text(p + "auth name", "Authentication name"),
            secret(p + "password", "Password"),
            choice(p + "mode", "Line mode", [(0, "Generic"), (1, "BroadSoft SCA"), (3, "BLA")], 0),
            text(p + "vmail", "Voicemail number"),
        ),
        *section(
            "Servers",
            text(p + "proxy ip", "Proxy server"),
            text(p + "proxy port", "Proxy port"),
            text(p + "backup proxy ip", "Backup proxy server"),
            text(p + "backup proxy port", "Backup proxy port"),
            text(p + "outbound proxy", "Outbound proxy"),
            text(p + "outbound proxy port", "Outbound proxy port"),
            text(p + "backup outbound proxy", "Backup outbound proxy"),
            text(p + "backup outbound proxy port", "Backup outbound proxy port"),
            text(p + "registrar ip", "Registrar server"),
            text(p + "registrar port", "Registrar port"),
            text(p + "backup registrar ip", "Backup registrar server"),
            text(p + "backup registrar port", "Backup registrar port"),
            text(p + "registration period", "Registration period (seconds)"),
        ),
        *section(
            "Line options",
            boolean(p + "call waiting", "Call waiting"),
            choice(p + "dtmf method", "DTMF method", [(0, "RTP"), (1, "SIP INFO"), (2, "Both")]),
            choice(p + "srtp mode", "SRTP",
                   [(0, "Disabled"), (1, "SRTP preferred"), (2, "SRTP only"), (3, "SRTP and RTP")]),
            text(p + "autodial number", "Hotline / autodial number"),
            text(p + "autodial timeout", "Autodial timeout (seconds)"),
            boolean(p + "missed calls enabled", "Missed calls indicator"),
            choice("line{n} ring tone", "Ring tone", [(-1, "Global")] + RING_TONES, -1),
            text(p + "park pickup config", "Park / pickup config"),
        ),
    ]


# --- Paramètres spécifiques aux modèles ---------------------------------------

def _color_display_settings(resolution):
    return [
        *section(
            "Display",
            text("background image", "Idle screen background image",
                 help=f"{resolution} JPG/PNG. A bare filename is prefixed with http://<SFTP host>/"),
            boolean("use color avatars", "Color avatars"),
            choice("idle screen mode", "Idle screen layout", [(0, "Primary (large clock)"), (1, "Secondary (2 names)")], 0),
            choice("idle screen font color", "Idle screen font color", ["blue", "white", "black"], "blue"),
            choice("backlight mode", "Backlight mode", [(1, "Auto")], 1),
            text("bl on time", "Backlight on time (seconds)", 600, help="1-36000"),
            choice("brightness level", "Brightness (active)", _range(1, 5), 3),
            choice("inactivity brightness level", "Brightness (inactive, 0 = black)", _range(0, 4), 1),
        ),
        *section(
            "Screen saver",
            text("screen save time", "Screen saver delay (seconds)", 1800, help="1-14400"),
            text("screen saver background image", "Screen saver image",
                 help=f"{resolution} JPG/PNG. A bare filename is prefixed with http://<SFTP host>/"),
            text("screen saver refresh timer", "Screen saver image refresh (minutes)"),
        ),
        *section(
            "Softkey display",
            boolean("collapsed softkey screen", "Collapse unused softkeys", 1),
            boolean("collapsed more softkey screen", "Remove \"More\" key when not needed", 0),
            boolean("collapsed context user softkey screen", "Collapse user softkeys in call states", 0),
        ),
    ]


def _key_group(gid, label, pattern, count, fields, types=None, names=None):
    g = {"id": gid, "label": label, "pattern": pattern, "count": count, "fields": fields}
    if types:
        g["types"] = types
    if names:
        g["names"] = names
    return g


def _expansion_modules(keys, module_name):
    return [
        _key_group(f"expmod{m}", f"Expansion module {m} ({module_name})", f"expmod{m} key{{n}}", keys,
                   ["type", "label", "value", "line", "locked"], EXPMOD_TYPES)
        for m in range(1, 4)
    ]


def _pnh_keypad():
    return _key_group("pnhkeypad", "Press-and-hold keypad speeddials", "pnhkeypad{n}", 9,
                      ["value", "line", "locked"], names={str(i): f"Keypad {i}" for i in range(1, 10)})


def model_schemas():
    return {
        "6867i": {
            "model": "6867i",
            "description": "Mitel 6867i — 6 top softkeys (20 functions), 4 bottom softkeys (18 functions), "
                           "up to 3 M680i/M685i expansion modules",
            "lines": 24,
            "settings": _color_display_settings("320x240"),
            "key_groups": [
                _key_group("topsoftkey", "Top softkeys", "topsoftkey{n}", 20,
                           ["type", "label", "value", "line", "locked"], TOP_SOFTKEY_TYPES),
                _key_group("softkey", "Bottom softkeys", "softkey{n}", 18,
                           ["type", "label", "value", "line", "states", "locked"], BOTTOM_SOFTKEY_TYPES),
                _pnh_keypad(),
                *_expansion_modules(84, "M680i: keys 1-16 / M685i: keys 1-84"),
            ],
        },
        "6863i": {
            "model": "6863i",
            "description": "Mitel 6863i — 2 lines, 3 programmable keys",
            "lines": 2,
            "settings": [],
            "key_groups": [
                _key_group("prgkey", "Programmable keys", "prgkey{n}", 3,
                           ["type", "value", "line", "locked"], PRGKEY_TYPES),
                _pnh_keypad(),
            ],
        },
        "6920": {
            "model": "6920",
            "description": "Mitel 6920 — 6 top softkeys (20 functions), 4 bottom softkeys (18 functions), "
                           "up to 3 M695 expansion modules",
            "lines": 24,
            "settings": _color_display_settings("320x240"),
            "key_groups": [
                _key_group("topsoftkey", "Top softkeys", "topsoftkey{n}", 20,
                           ["type", "label", "value", "line", "locked"], TOP_SOFTKEY_TYPES),
                _key_group("softkey", "Bottom softkeys", "softkey{n}", 18,
                           ["type", "label", "value", "line", "states", "locked"], BOTTOM_SOFTKEY_TYPES),
                _key_group("hardkey", "Hard keys (remap)", "hardkey{n}", 7,
                           ["type", "value", "line", "locked"], HARDKEY_TYPES,
                           names={"1": "Hold", "2": "Redial", "3": "Goodbye", "4": "Options",
                                  "5": "Voicemail", "6": "Callers", "7": "Directory"}),
                _pnh_keypad(),
                *_expansion_modules(84, "M695"),
            ],
        },
    }


def builtin_schemas():
    schemas = {
        "generic": {
            "model": "generic",
            "description": "Global settings shared by all models",
            "settings": _global_settings(),
            "line_settings": _line_settings(),
        },
        **model_schemas(),
    }
    for s in schemas.values():
        s["version"] = SCHEMA_VERSION
    return schemas
