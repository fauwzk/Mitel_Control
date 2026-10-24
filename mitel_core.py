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

from phone_schemas import SCHEMA_VERSION, builtin_schemas

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
    """Écrit les schémas intégrés dans MODEL_DIR.

    Un fichier existant est conservé, sauf s'il date d'une version de schéma plus ancienne
    (il est alors sauvegardé en .bak puis remplacé) ou si force=True.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, data in builtin_schemas().items():
        filepath = os.path.join(MODEL_DIR, f"{name}.json")
        if os.path.exists(filepath) and not force:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    current = json.load(f).get("version", 1)
            except Exception:
                current = 0
            if current >= SCHEMA_VERSION:
                continue
            shutil.copy(filepath, filepath + ".bak")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


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

    # 1. Variables standards issues du formulaire (dans l'ordre du schéma)
    for key in vals:
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


def _strip_comment(val):
    # Un "#" hors guillemets commence un commentaire (un "#" entre guillemets est un dièse)
    in_quotes = False
    for i, c in enumerate(val):
        if c == '"':
            in_quotes = not in_quotes
        elif c == "#" and not in_quotes:
            return val[:i].strip()
    return val.strip()


def _model_from_inventory(filename):
    mac = re.sub(r"[^0-9A-F]", "", (filename or "").upper())[:12]
    if len(mac) != 12:
        return None
    for ep in load_endpoints():
        if re.sub(r"[^0-9A-F]", "", ep.get("mac", "").upper()) == mac:
            label = ep.get("label", "").lower()
            for model in list_models():
                if model.lower().rstrip("i") in label:
                    return model
    return None


def parse_cfg_text(text, filename=None):
    parsed_data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            parsed_data[key.strip()] = _strip_comment(val)

    # Le modèle déclaré dans l'inventaire (libellé du poste) prime sur la détection par clés
    detected_model = _model_from_inventory(filename)
    if not detected_model:
        keys = list(parsed_data)
        if any(k.startswith("hardkey") for k in keys):
            detected_model = "6920"
        elif any(k.startswith("prgkey") for k in keys):
            detected_model = "6863i"
        elif any(k.startswith(("softkey", "topsoftkey", "expmod")) for k in keys):
            detected_model = "6867i"
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
