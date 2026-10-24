import base64
import http.client
import io
import ipaddress
import json
import os
import platform
import posixpath
import re
import shutil
import socket
import subprocess
import threading
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager

import paramiko
from PIL import Image, ImageOps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
MODEL_DIR = os.path.join(DATA_DIR, "phone_models")
ENDPOINT_FILE = os.path.join(DATA_DIR, "endpoints.json")
WALLPAPER_NAME = "fond_leger.png"

_endpoints_lock = threading.Lock()


class OpError(Exception):
    """Erreur métier dont le message peut être affiché tel quel à l'utilisateur."""


# --- Schémas de modèles ------------------------------------------------------

def initialize_comprehensive_models(force=False):
    if force and os.path.isdir(MODEL_DIR):
        for f in os.listdir(MODEL_DIR):
            if f.endswith(".json"):
                os.remove(os.path.join(MODEL_DIR, f))
    os.makedirs(MODEL_DIR, exist_ok=True)

    model_generic = {
        "model": "generic",
        "description": "Global SIP & Network Settings",
        "settings": [
            {"key": "dhcp", "label": "DHCP (1=On, 0=Off)", "type": "choice", "options": ["1", "0"]},
            {"key": "lldp", "label": "LLDP (1=On, 0=Off)", "type": "choice", "options": ["1", "0"]},
            {"key": "tftp server", "label": "TFTP Server IP Address", "type": "string"},
            {"key": "sip line1 screen name", "label": "Screen Label (Line 1)", "type": "string"},
            {"key": "sip line1 auth name", "label": "SIP Auth Name / Extension", "type": "string"},
            {"key": "sip line1 password", "label": "SIP Auth Password", "type": "string"},
            {"key": "sip line1 user name", "label": "SIP User Name (Display)", "type": "string"},
            {"key": "sip line1 proxy ip", "label": "SIP Proxy / PBX IP", "type": "string"},
            {"key": "sip line1 proxy port", "label": "SIP Proxy Port (Default 5060)", "type": "string"},
            {"key": "sip line1 registrar ip", "label": "Registrar / Server IP", "type": "string"},
            {"key": "sip line1 registrar port", "label": "Registrar Port (Default 5060)", "type": "string"},
            {"key": "aastra md5", "label": "Aastra MD5 Config Hash", "type": "string"},
            {"key": "mac md5", "label": "MAC Config MD5 Hash", "type": "string"},
            {"key": "time server1", "label": "NTP Time Server (fr.pool.ntp.org)", "type": "string"},
            {"key": "date format", "label": "Date Format (0=YYYYMMDD, 1=DDMMYYYY, 2=MMDDYYYY, 3=DDMMYY)", "type": "choice", "options": ["0", "1", "2", "3"]},
            {"key": "time format", "label": "Time Format (1=24H, 0=12H)", "type": "choice", "options": ["0", "1"]},
            {"key": "contact rcs", "label": "Contact RCS (0=Off, 1=On)", "type": "choice", "options": ["0", "1"]},
            {"key": "time zone name", "label": "Time Zone String (e.g., CET-1CEST,M3.5.0,M10.5.0)", "type": "string"},
            {"key": "language 1", "label": "Phone Language file (e.g., French)", "type": "string"},
            {"key": "language 2", "label": "Phone Language file (e.g., Spanish)", "type": "string"},
            {"key": "language 3", "label": "Phone Language file (e.g., German)", "type": "string"},
            {"key": "language", "label": "number of languages (1-3)", "type": "choice", "options": ["1", "2", "3"]},
            {"key": "tone set", "label": "Region Tone (e.g., France, USA)", "type": "string"},
            {"key": "ring tone", "label": "Ringtone ID (1-5)", "type": "choice", "options": ["1", "2", "3", "4", "5"]},
            {"key": "web language", "label": "Web Interface Language (1=Fr, 0=En)", "type": "choice", "options": ["1", "0"]},
            {"key": "input language", "label": "Phone Input Language (e.g., French)", "type": "string"},
            {"key": "sip dial plan", "label": "Dial Plan Rules (Use | to separate)", "type": "string"},
            {"key": "directed call pickup", "label": "Directed Call Pickup (1=On, 0=Off)", "type": "choice", "options": ["1", "0"]},
            {"key": "directed call pickup prefix", "label": "Directed Call Pickup Prefix (e.g., **)", "type": "string"},
            {"key": "handset volume", "label": "Handset Volume (1-10)", "type": "string"},
            {"key": "speaker volume", "label": "Speaker Volume (1-10)", "type": "string"},
            {"key": "ringer volume", "label": "Ringer Volume (1-10)", "type": "string"},
            {"key": "directory 1 name", "label": "Directory Display Name (e.g., Entreprise)", "type": "string"},
            {"key": "directory 1", "label": "Directory File / URI (e.g., contacts.csv)", "type": "string"}
        ]
    }

    settings_6867i = [
        {"key": "background image", "label": "Wallpaper Filename (.png/.jpg)", "type": "string"},
        {"key": "background image display mode", "label": "Wallpaper Scaling (0=Centered, 1=Stretched)", "type": "choice", "options": ["0", "1"]},

        # --- Écran de veille et rétroéclairage ---
        {"key": "screen saver timer", "label": "Screensaver Timeout (Seconds, e.g., 300, 0=Off)", "type": "string"},
        {"key": "screen saver background image", "label": "Screensaver Custom Image (.jpg)", "type": "string"},
        {"key": "backlight mode", "label": "Backlight Mode (0=Off, 1=Auto, 2=Always On)", "type": "choice", "options": ["0", "1", "2"]},
        {"key": "bl on time", "label": "Backlight Auto Dim Timeout (Seconds, e.g., 600)", "type": "string"},
        {"key": "inactivity brightness level", "label": "Dimmed Brightness (0=Black, 1 to 5=Dimmed)", "type": "choice", "options": ["0", "1", "2", "3", "4", "5"]},

        # --- LEDs Principales ---
        {"key": "mwi led", "label": "Message Waiting LED (1=On, 0=Off)", "type": "choice", "options": ["1", "0"]},
        {"key": "ring led", "label": "Ringing LED Indicator (1=On, 0=Off)", "type": "choice", "options": ["1", "0"]},
        {"key": "dnd led", "label": "DND LED Indicator (1=On, 0=Off)", "type": "choice", "options": ["1", "0"]}
    ]

    softkey_types = ["none", "pickup", "speeddial", "blf", "xml", "line", "dnd", "park", "paging"]

    for i in range(1, 11):
        settings_6867i.extend([
            {"key": f"topsoftkey{i} type", "label": f"Top Key {i} Type", "type": "choice", "options": softkey_types},
            {"key": f"topsoftkey{i} label", "label": f"Top Key {i} Display Label", "type": "string"},
            {"key": f"topsoftkey{i} value", "label": f"Top Key {i} Value (Prepend + Dest)", "type": "string"},
            {"key": f"topsoftkey{i} color", "label": f"Top Key {i} LED Color", "type": "choice", "options": ["", "red", "green", "yellow"]}
        ])

    for i in range(1, 21):
        settings_6867i.extend([
            {"key": f"softkey{i} type", "label": f"Key {i} Type", "type": "choice", "options": softkey_types},
            {"key": f"softkey{i} label", "label": f"Key {i} Display Label", "type": "string"},
            {"key": f"softkey{i} value", "label": f"Key {i} Value (Prepend + Dest)", "type": "string"}
        ])

    model_6867i = {"model": "6867i", "description": "Mitel 6867i Configuration", "settings": settings_6867i}

    settings_6863i = []
    pnh_types = ["none", "pickup", "speeddial", "blf", "xml", "line", "dnd", "park", "paging"]

    for i in range(1, 10):
        settings_6863i.extend([
            {"key": f"pnhkeypad{i} type", "label": f"Prog Key {i} Type", "type": "choice", "options": pnh_types},
            {"key": f"pnhkeypad{i} prepend", "label": f"Prog Key {i} Prefix", "type": "string"},
            {"key": f"pnhkeypad{i} value", "label": f"Prog Key {i} Value (Dest)", "type": "string"},
            {"key": f"pnhkeypad{i} line", "label": f"Prog Key {i} Line (Default 1)", "type": "string"}
        ])

    model_6863i = {"model": "6863i", "description": "Mitel 6863i Configuration", "settings": settings_6863i}

    for name, data in [("generic", model_generic), ("6867i", model_6867i), ("6863i", model_6863i)]:
        filepath = os.path.join(MODEL_DIR, f"{name}.json")
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)


def initialize_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    seed = os.path.join(BASE_DIR, "endpoints.json")
    if not os.path.exists(ENDPOINT_FILE) and os.path.exists(seed):
        shutil.copy(seed, ENDPOINT_FILE)
    initialize_comprehensive_models()


def list_models():
    if not os.path.isdir(MODEL_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(MODEL_DIR) if f.endswith(".json") and f != "generic.json")


def load_schema(name):
    if name != "generic" and name not in list_models():
        raise OpError(f"Unknown model: {name}")
    with open(os.path.join(MODEL_DIR, f"{name}.json"), "r", encoding="utf-8") as f:
        return json.load(f)


# --- Fichiers .cfg -----------------------------------------------------------

def generate_cfg_string(values, raw_text, server_ip):
    vals = {}
    prepends = {}
    for key, val in values.items():
        if "prepend" in key:
            prepends[key.replace("prepend", "value")] = val
        else:
            vals[key] = val

    lines = ["# Provisioning Profile"]

    # 1. Variables standards issues du formulaire
    for key in sorted(vals.keys()):
        val = vals[key]
        if val == "":
            continue
        if key in prepends and prepends[key] != "":
            lines.append(f"{key}: {prepends[key]}{val}")
        elif key in ["background image", "screen saver background image"]:
            if not val.startswith(("http://", "https://", "tftp://")):
                lines.append(f"{key}: http://{server_ip}/{val}")
            else:
                lines.append(f"{key}: {val}")
        elif key == "directory 1":
            if not val.startswith(("http://", "https://", "tftp://")):
                lines.append(f"{key}: tftp://{server_ip}/{val}")
            else:
                lines.append(f"{key}: {val}")
        else:
            lines.append(f"{key}: {val}")

    # 2. Variables personnalisées de l'éditeur brut (lignes marquées [CUSTOM])
    custom_lines_found = False
    for rline in (raw_text or "").split("\n"):
        rline = rline.strip()
        if rline.startswith("[CUSTOM]"):
            if not custom_lines_found:
                lines.append("\n# Custom / Unmapped Settings")
                custom_lines_found = True
            clean_line = rline.replace("[CUSTOM]", "", 1).strip()
            if clean_line:
                lines.append(clean_line)

    return "\n".join(lines) + "\n"


def parse_cfg_text(text):
    parsed_data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            parsed_data[key.strip()] = val.strip()

    detected_model = None
    for key in parsed_data:
        if key.startswith("softkey") or key.startswith("topsoftkey"):
            detected_model = "6867i"
            break
        elif key.startswith("pnhkeypad"):
            detected_model = "6863i"
            break
    if detected_model not in list_models():
        detected_model = None

    return parsed_data, detected_model


def safe_filename(name):
    clean = posixpath.basename((name or "").replace("\\", "/")).strip()
    if not clean or clean in (".", ".."):
        raise OpError("Invalid filename.")
    return clean


# --- SFTP --------------------------------------------------------------------

@contextmanager
def sftp_session(creds):
    host = (creds.get("host") or "").strip()
    if not host:
        raise OpError("SFTP host is required.")
    sock = socket.create_connection((host, 22), timeout=10)
    transport = paramiko.Transport(sock)
    try:
        transport.connect(username=creds.get("user", ""), password=creds.get("password", ""))
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            yield sftp
        finally:
            sftp.close()
    finally:
        transport.close()


def sftp_list(creds, path):
    with sftp_session(creds) as sftp:
        files = sftp.listdir(path)
    return sorted(f for f in files if f.endswith(".cfg") or f.endswith(".txt"))


def sftp_read(creds, path, name):
    buf = io.BytesIO()
    with sftp_session(creds) as sftp:
        sftp.getfo(posixpath.join(path, safe_filename(name)), buf)
    return buf.getvalue().decode("utf-8", errors="replace")


def sftp_write(creds, path, name, content):
    with sftp_session(creds) as sftp:
        sftp.putfo(io.BytesIO(content.encode("utf-8")), posixpath.join(path, safe_filename(name)))


def process_and_upload_wallpaper(creds, path, stream):
    buf = io.BytesIO()
    try:
        with Image.open(stream) as img:
            img_fitted = ImageOps.fit(img, (320, 240), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            img_fitted.quantize(colors=256).save(buf, format="PNG")
    except Exception as e:
        raise OpError(f"Image Pipeline Error: {e}")
    buf.seek(0)
    with sftp_session(creds) as sftp:
        sftp.putfo(buf, posixpath.join(path, WALLPAPER_NAME))
    return WALLPAPER_NAME


# --- Téléphones --------------------------------------------------------------

def _validate_ip(ip):
    try:
        return str(ipaddress.ip_address((ip or "").strip()))
    except ValueError:
        raise OpError(f"Invalid IP address: {ip!r}")


def fetch_mac_from_ip(ip):
    ip = _validate_ip(ip)
    windows = platform.system().lower() == "windows"
    ping_cmd = ["ping", "-n", "1", ip] if windows else ["ping", "-c", "1", "-W", "1", ip]
    subprocess.run(ping_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)

    arp_cmd = ["arp", "-a", ip] if windows else ["arp", "-n", ip]
    try:
        output = subprocess.check_output(arp_cmd, universal_newlines=True, timeout=5)
    except Exception as e:
        raise OpError(f"ARP Lookup failed: {e}")

    mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", output)
    if not mac_match:
        raise OpError(f"Phone at {ip} did not respond or isn't on the local subnet.")
    return mac_match.group(0).replace("-", ":").upper()


def reboot_phone(ip, pwd):
    ip = _validate_ip(ip)
    xml_string = '<AastraIPPhoneExecute><ExecuteItem URI="Command: Reset"/></AastraIPPhoneExecute>'
    data = urllib.parse.urlencode({"xml": xml_string}).encode("utf-8")

    req = urllib.request.Request(f"http://{ip}/", data=data)
    token = base64.b64encode(f"admin:{pwd}".encode("utf-8")).decode("utf-8")
    req.add_header("Authorization", f"Basic {token}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        urllib.request.urlopen(req, timeout=3)
        return f"Reboot command acknowledged by {ip}!"
    except (http.client.RemoteDisconnected, ConnectionResetError):
        return f"Success: {ip} dropped connection (Phone is restarting!)"
    except urllib.error.URLError as e:
        if "closed" in str(e).lower() or "reset" in str(e).lower() or "10054" in str(e):
            return f"Success: {ip} dropped connection (Phone is restarting!)"
        raise OpError(f"Failed to reboot {ip} (Check Whitelist/IP/Pass): {e}")
    except Exception as e:
        raise OpError(f"Failed to reboot {ip}: {e}")


# --- Inventaire --------------------------------------------------------------

def load_endpoints():
    if not os.path.exists(ENDPOINT_FILE):
        return []
    try:
        with open(ENDPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_endpoints(endpoints):
    with open(ENDPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(endpoints, f, indent=4)


def add_endpoint(mac, ip, label):
    mac = (mac or "").upper().strip()
    if not mac:
        raise OpError("MAC address is required!")
    with _endpoints_lock:
        endpoints = load_endpoints()
        endpoints.append({"mac": mac, "ip": (ip or "").strip(), "label": (label or "").strip()})
        _save_endpoints(endpoints)
    return endpoints


def delete_endpoint(mac):
    with _endpoints_lock:
        endpoints = [e for e in load_endpoints() if e["mac"] != mac]
        _save_endpoints(endpoints)
    return endpoints
