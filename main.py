import dearpygui.dearpygui as dpg
import json
import os
import tempfile
import paramiko
import re
import subprocess
import platform
import urllib.request
import urllib.parse
import urllib.error
import http.client
import base64
from PIL import Image, ImageOps

MODEL_DIR = "phone_models"
TEMP_DIR = tempfile.gettempdir()
ENDPOINT_FILE = "endpoints.json"
CUSTOM_FONT_FILE = "Museo-500.ttf"

def initialize_comprehensive_models():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    model_generic = {
        "model": "generic",
        "description": "Global SIP & Network Settings",
        "settings": [
            {"key": "dhcp", "label": "DHCP (1=On, 0=Off)", "type": "choice", "options": ["1", "0"]},
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

            # Audio & Volume
        {"key": "handset volume", "label": "Handset Volume (1-10)", "type": "string"},
        {"key": "speaker volume", "label": "Speaker Volume (1-10)", "type": "string"},
        {"key": "ringer volume", "label": "Ringer Volume (1-10)", "type": "string"},

            # --- NEW DIRECTORY SETTINGS ---
            {"key": "directory 1 name", "label": "Directory Display Name (e.g., Entreprise)", "type": "string"},
            {"key": "directory 1", "label": "Directory File / URI (e.g., contacts.csv)", "type": "string"}
        ]
    }

    settings_6867i = [
        {"key": "background image", "label": "Wallpaper Filename (.png/.jpg)", "type": "string"},
        {"key": "background image display mode", "label": "Wallpaper Scaling (0=Centered, 1=Stretched)", "type": "choice", "options": ["0", "1"]},
        # Screen Saver Settings
        {"key": "screen saver background", "label": "Screensaver Image File (.jpg)", "type": "string"},
        {"key": "screen saver wait time", "label": "Screensaver Timeout (Seconds, default 300)", "type": "string"}
    ]

    # Ensure softkey_types includes all necessary profiles
    softkey_types = ["none", "pickup", "speeddial", "blf", "xml", "line", "dnd", "park", "paging"]
    
    # 1. Top Softkeys (using a naming convention that avoids purely numeric keys if desired)
    for i in range(1, 11):
        # We include 'prepend' directly here
        settings_6867i.extend([
            {"key": f"topsoftkey{i} type", "label": f"Top Key {i} Type", "type": "choice", "options": softkey_types},
            {"key": f"topsoftkey{i} label", "label": f"Top Key {i} Display Label", "type": "string"},
            {"key": f"topsoftkey{i} value", "label": f"Top Key {i} Value (Prepend + Dest)", "type": "string"}
        ])

    # 2. Bottom Softkeys
    for i in range(1, 21):
        settings_6867i.extend([
            {"key": f"softkey{i} type", "label": f"Key {i} Type", "type": "choice", "options": softkey_types},
            {"key": f"softkey{i} label", "label": f"Key {i} Display Label", "type": "string"},
            {"key": f"softkey{i} value", "label": f"Key {i} Value (Prepend + Dest)", "type": "string"}
        ])
    

    model_6867i = {"model": "6867i", "description": "Mitel 6867i Configuration", "settings": settings_6867i}

    settings_6863i = [        
    ]

    # Generate 6863i Programmable Hard Keys (pnhkeypad 1 through 9)
    pnh_types = ["none", "pickup", "speeddial", "blf", "xml", "line", "dnd", "park", "paging"]
    
    for i in range(1, 10):
        settings_6863i.extend([
            {"key": f"pnhkeypad{i} type", "label": f"Prog Key {i} Type", "type": "choice", "options": pnh_types},
            {"key": f"pnhkeypad{i} prepend", "label": f"Prog Key {i} Prefix", "type": "string"},
            {"key": f"pnhkeypad{i} value", "label": f"Prog Key {i} Value (Dest)", "type": "string"},
            {"key": f"pnhkeypad{i} line", "label": f"Prog Key {i} Line (Default 1)", "type": "string"}
        ])

    # Add the newly created dictionary
    model_6863i = {"model": "6863i", "description": "Mitel 6863i Configuration", "settings": settings_6863i}

    for name, data in [("generic", model_generic), ("6867i", model_6867i), ("6863i", model_6863i)]:
        filepath = f"{MODEL_DIR}/{name}.json"
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)

class MitelStudioApp:
    def __init__(self):
        self.available_models = []
        self.generic_schema = {}
        self.current_schema = {}
        self.active_ui_elements = {}
        self.current_filename = "macaddress.cfg"
        self.endpoints = []
        self.wallpaper_picker_triggered_by = None
        
        self.load_schemas()
        self.load_endpoints()

    def load_schemas(self):
        self.available_models.clear()
        if not os.path.exists(MODEL_DIR): return
        with open(f"{MODEL_DIR}/generic.json", "r") as f:
            self.generic_schema = json.load(f)
        for file in os.listdir(MODEL_DIR):
            if file.endswith(".json") and file != "generic.json":
                self.available_models.append(file.replace(".json", ""))

    def refresh_schemas(self):
        self.load_schemas()
        dpg.configure_item("model_combo", items=self.available_models)
        dpg.set_value("status_text", "JSON schemas reloaded successfully.")
        self.build_dynamic_form()

    def on_model_select(self, sender, app_data):
        with open(f"{MODEL_DIR}/{app_data}.json", "r") as f:
            self.current_schema = json.load(f)
        self.build_dynamic_form()

    def build_dynamic_form(self, loaded_data=None):
        if loaded_data is None: loaded_data = {}
        dpg.delete_item("generic_settings_group", children_only=True)
        dpg.delete_item("model_settings_group", children_only=True)
        self.active_ui_elements.clear()

        def render_fields(schema_settings, parent_group):
            for setting in schema_settings:
                key = setting["key"]
                label = setting["label"]
                stype = setting["type"]
                default_val = loaded_data.get(key, "")

                with dpg.group(parent=parent_group, horizontal=True):
                    dpg.add_text(f"{label}:", color=[160, 210, 255])
                    dpg.add_spacer(width=10)
                    if stype == "string":
                        tag = dpg.add_input_text(default_value=default_val, width=260)
                        self.active_ui_elements[key] = tag
                        

                            
                    elif stype == "choice":
                        options = setting.get("options", [])
                        if default_val not in options and options: default_val = options[0]
                        tag = dpg.add_combo(items=options, default_value=default_val, width=260)
                        self.active_ui_elements[key] = tag

        render_fields(self.generic_schema.get("settings", []), "generic_settings_group")
        if self.current_schema:
            render_fields(self.current_schema.get("settings", []), "model_settings_group")

    def generate_cfg_string(self):
        vals = {}
        prepends = {}
        
        # Gather all current values from the UI
        for key, tag in self.active_ui_elements.items():
            val = dpg.get_value(tag)
            if "prepend" in key:
                prepends[key.replace("prepend", "value")] = val
            else:
                vals[key] = val
        
        # Grab the server IP dynamically from the SFTP window's "Host IP" field
        server_ip = dpg.get_value("ftp_host")
        
        lines = ["# Provisioning Profile"]
        
        for key in sorted(vals.keys()):
            val = vals[key]
            if val != "":
                # 1. Handle Softkey Prepend Logic
                if key in prepends and prepends[key] != "":
                    lines.append(f"{key}: {prepends[key]}{val}")
                
                # 2. Auto-Format HTTP for Images (Mitel often rejects TFTP for images)
                elif key in ["background image", "screen saver background image"]:
                    if not val.startswith("http://") and not val.startswith("https://") and not val.startswith("tftp://"):
                        lines.append(f"{key}: http://{server_ip}/{val}")
                    else:
                        lines.append(f"{key}: {val}")
                        
                # 3. Auto-Format TFTP for the Directory (Since it is in /tftpboot)
                elif key == "directory 1":
                    if not val.startswith("http://") and not val.startswith("https://") and not val.startswith("tftp://"):
                        lines.append(f"{key}: tftp://{server_ip}/{val}")
                    else:
                        lines.append(f"{key}: {val}")
                # 3. Standard Key-Value Pairs
                else:
                    lines.append(f"{key}: {val}")

        return "\n".join(lines) + "\n"

    def parse_cfg_file(self, filepath):
        parsed_data = {}
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    if ':' in line:
                        key, val = line.split(':', 1)
                        parsed_data[key.strip()] = val.strip()
            self.build_dynamic_form(loaded_data=parsed_data)
            self.current_filename = os.path.basename(filepath)
            dpg.set_value("current_file_input", self.current_filename)
            dpg.set_value("status_text", f"Loaded File: {self.current_filename}")
        except Exception as e:
            dpg.set_value("status_text", f"Parsing Failure: {e}")

    def local_open_cb(self, sender, app_data): self.parse_cfg_file(app_data['file_path_name'])
    def local_save_cb(self, sender, app_data):
        try:
            with open(app_data['file_path_name'], 'w') as f: f.write(self.generate_cfg_string())
            dpg.set_value("status_text", "Saved configuration locally.")
        except Exception as e: dpg.set_value("status_text", f"Local write error: {e}")

    def format_mac_to_filename(self):
        raw_input = dpg.get_value("current_file_input")
        # Ensure only alphanumeric characters are kept
        clean_mac = re.sub(r'[^a-fA-F0-9]', '', raw_input).upper() # Changed .lower() to .upper()
        if len(clean_mac) >= 12:
            clean_mac = clean_mac[:12]
            new_filename = f"{clean_mac}.cfg"
            self.current_filename = new_filename
            dpg.set_value("current_file_input", new_filename)
            dpg.set_value("status_text", f"Formatted filename: {new_filename}")
        else:
            dpg.set_value("status_text", "Please enter a valid MAC address.")

    def get_sftp_client(self):
        host = dpg.get_value("ftp_host")
        user = dpg.get_value("ftp_user")
        passwd = dpg.get_value("ftp_pass")
        transport = paramiko.Transport((host, 22))
        transport.connect(username=user, password=passwd)
        return paramiko.SFTPClient.from_transport(transport), transport

    def ftp_connect_and_list(self):
        path = dpg.get_value("ftp_path")
        try:
            sftp, transport = self.get_sftp_client()
            files = sftp.listdir(path)
            cfg_files = [f for f in files if f.endswith('.cfg') or f.endswith('.txt')]
            dpg.configure_item("ftp_file_list", items=cfg_files)
            dpg.set_value("status_text", f"Indexed SFTP active configs in {path}")
            sftp.close()
            transport.close()
        except Exception as e: 
            dpg.set_value("status_text", f"SFTP connection error: {e}")

    def ftp_download(self):
        path = dpg.get_value("ftp_path")
        selected = dpg.get_value("ftp_file_list")
        if not selected: return
        try:
            local_temp_path = os.path.join(TEMP_DIR, selected)
            sftp, transport = self.get_sftp_client()
            sftp.get(f"{path}/{selected}", local_temp_path)
            sftp.close()
            transport.close()
            self.parse_cfg_file(local_temp_path)
            dpg.set_value("status_text", f"Downloaded {selected} via SFTP.")
        except Exception as e: 
            dpg.set_value("status_text", f"Retrieval error: {e}")

    def ftp_upload(self):
        path = dpg.get_value("ftp_path")
        filename = dpg.get_value("current_file_input")
        try:
            local_temp_path = os.path.join(TEMP_DIR, filename)
            with open(local_temp_path, 'w') as f: 
                f.write(self.generate_cfg_string())
            sftp, transport = self.get_sftp_client()
            sftp.put(local_temp_path, f"{path}/{filename}")
            sftp.close()
            transport.close()
            dpg.set_value("status_text", f"Provisioned file {filename} updated via SFTP.")
        except Exception as e: 
            dpg.set_value("status_text", f"Upload execution error: {e}")

    def trigger_config_wallpaper_picker(self, sender, app_data, user_data):
        self.wallpaper_picker_triggered_by = user_data
        dpg.show_item("config_wallpaper_dialog")

    def config_wallpaper_pick_cb(self, sender, app_data):
        filename = os.path.basename(app_data['file_path_name'])
        dpg.set_value(self.wallpaper_picker_triggered_by, filename)
        dpg.set_value("status_text", f"Config image set to: {filename}")
        self.wallpaper_picker_triggered_by = None

    def process_and_upload_wallpaper(self, sender, app_data):
        local_image_path = app_data['file_path_name']
        target_name = "fond_leger.png"
        processed_path = os.path.join(TEMP_DIR, target_name)
        path = dpg.get_value("ftp_path")
        try:
            with Image.open(local_image_path) as img:
                img_fitted = ImageOps.fit(img, (320, 240), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                img_quantized = img_fitted.quantize(colors=256)
                img_quantized.save(processed_path, format="PNG")
                
            sftp, transport = self.get_sftp_client()
            sftp.put(processed_path, f"{path}/{target_name}")
            sftp.close()
            transport.close()
            dpg.set_value("status_text", f"Wallpaper optimized and uploaded as {target_name}!")
        except Exception as e:
            dpg.set_value("status_text", f"Image Pipeline Error: {e}")

    def fetch_mac_from_ip(self):
        ip = dpg.get_value("inv_ip_input").strip()
        if not ip:
            dpg.set_value("status_text", "Enter an IP address first to fetch the MAC.")
            return
            
        dpg.set_value("status_text", f"Pinging {ip} to populate ARP table...")
        try:
            ping_cmd = ['ping', '-n', '1', ip] if platform.system().lower() == 'windows' else ['ping', '-c', '1', '-W', '1', ip]
            subprocess.run(ping_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            arp_cmd = ['arp', '-a', ip] if platform.system().lower() == 'windows' else ['arp', '-n', ip]
            output = subprocess.check_output(arp_cmd, universal_newlines=True)
            
            mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', output)
            if mac_match:
                found_mac = mac_match.group(0).replace('-', ':').upper()
                dpg.set_value("inv_mac_input", found_mac)
                dpg.set_value("status_text", f"Success! Discovered MAC: {found_mac}")
            else:
                dpg.set_value("status_text", f"Phone at {ip} did not respond or isn't on the local subnet.")
        except Exception as e:
            dpg.set_value("status_text", f"ARP Lookup failed: {e}")

    # --- Bulletproof Reboot Function ---
    def reboot_selected_phone(self):
        selected = dpg.get_value("inventory_list")
        if not selected or selected == "No endpoints added yet.":
            dpg.set_value("status_text", "Please select a phone from the inventory to reboot.")
            return
        
        ip_match = re.search(r'\]\s*([0-9\.]+)\s*-', selected)
        if not ip_match:
            dpg.set_value("status_text", "Could not extract IP from selection.")
            return
            
        ip = ip_match.group(1).strip()
        pwd = dpg.get_value("phone_web_pass")
        
        dpg.set_value("status_text", f"Sending URL-encoded XML payload to {ip}...")
        
        # Proper URL Encoding to satisfy the Aastra web server
        xml_string = '<AastraIPPhoneExecute><ExecuteItem URI="Command: Reset"/></AastraIPPhoneExecute>'
        data = urllib.parse.urlencode({'xml': xml_string}).encode('utf-8')
        
        url = f"http://{ip}/"
        
        try:
            req = urllib.request.Request(url, data=data)
            base64string = base64.b64encode(f"admin:{pwd}".encode('utf-8')).decode('utf-8')
            req.add_header("Authorization", f"Basic {base64string}")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            
            urllib.request.urlopen(req, timeout=3)
            dpg.set_value("status_text", f"Reboot command acknowledged by {ip}!")
            
        except (http.client.RemoteDisconnected, ConnectionResetError):
            # The phone successfully cut the line to reboot itself
            dpg.set_value("status_text", f"Success: {ip} dropped connection (Phone is restarting!)")
            
        except urllib.error.URLError as e:
            if "closed" in str(e).lower() or "reset" in str(e).lower() or "10054" in str(e):
                 dpg.set_value("status_text", f"Success: {ip} dropped connection (Phone is restarting!)")
            else:
                 dpg.set_value("status_text", f"Failed to reboot {ip} (Check Whitelist/IP/Pass): {e}")
                 
        except Exception as e:
            dpg.set_value("status_text", f"Failed to reboot {ip}: {e}")

    def load_endpoints(self):
        if os.path.exists(ENDPOINT_FILE):
            try:
                with open(ENDPOINT_FILE, "r") as f:
                    self.endpoints = json.load(f)
            except Exception:
                self.endpoints = []
                
    def save_endpoints(self):
        with open(ENDPOINT_FILE, "w") as f:
            json.dump(self.endpoints, f, indent=4)
            
    def refresh_endpoint_list(self):
        display_list = [f"[{e['mac']}] {e['ip']} - {e['label']}" for e in self.endpoints]
        if not display_list:
            display_list = ["No endpoints added yet."]
        dpg.configure_item("inventory_list", items=display_list)

    def add_endpoint(self):
        mac = dpg.get_value("inv_mac_input").upper().strip()
        ip = dpg.get_value("inv_ip_input").strip()
        label = dpg.get_value("inv_label_input").strip()
        
        if not mac:
            dpg.set_value("status_text", "MAC address is required!")
            return
            
        self.endpoints.append({"mac": mac, "ip": ip, "label": label})
        self.save_endpoints()
        self.refresh_endpoint_list()
        
        dpg.set_value("inv_mac_input", "")
        dpg.set_value("inv_ip_input", "")
        dpg.set_value("inv_label_input", "")
        dpg.set_value("status_text", "Endpoint added to local inventory.")

    def delete_endpoint(self):
        selected = dpg.get_value("inventory_list")
        if not selected or selected == "No endpoints added yet.": return
        
        mac_match = re.search(r'\[(.*?)\]', selected)
        if mac_match:
            mac_to_delete = mac_match.group(1)
            self.endpoints = [e for e in self.endpoints if e['mac'] != mac_to_delete]
            self.save_endpoints()
            self.refresh_endpoint_list()
            dpg.set_value("status_text", "Endpoint removed from inventory.")

    def on_inventory_select(self, sender, app_data):
        selected_text = dpg.get_value(sender)
        mac_match = re.search(r'\[(.*?)\]', selected_text)
        if mac_match:
            raw_mac = mac_match.group(1)
            clean_filename = f"{raw_mac.replace(':', '').lower()}.cfg"
            self.current_filename = clean_filename
            dpg.set_value("current_file_input", clean_filename)
            dpg.set_value("status_text", f"Target file set to: {clean_filename}")


initialize_comprehensive_models()
app = MitelStudioApp()
dpg.create_context()
dpg.configure_app(
    docking=True, 
    docking_space=True, 
    init_file="dpg.ini", 
    auto_save_init_file=True
)

# --- START OF MITEL COLOR THEME ---
with dpg.theme() as mitel_theme:
    with dpg.theme_component(dpg.mvAll):
        # Backgrounds: Dark Slate 
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (28, 33, 40, 255)) 
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (28, 33, 40, 255))
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (35, 40, 48, 255))

        # Title Bars: Mitel Corporate Blue
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (0, 80, 154, 255)) 
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (0, 114, 206, 255)) # Mitel Accent Blue
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (0, 50, 100, 255))
        
        # Buttons: Subtle grey resting, Mitel Blue hovered
        dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 50, 58, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 114, 206, 255)) 
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 80, 154, 255))
        
        # Input Fields (Frames): Darker inlay
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (18, 22, 28, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (0, 114, 206, 100))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (0, 114, 206, 150))
        
        # Tabs
        dpg.add_theme_color(dpg.mvThemeCol_Tab, (0, 80, 154, 150))
        dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (0, 114, 206, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TabActive, (0, 80, 154, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (0, 50, 100, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (0, 80, 154, 255))
        
        # Lists and Dropdowns (Headers)
        dpg.add_theme_color(dpg.mvThemeCol_Header, (0, 114, 206, 120))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (0, 114, 206, 200))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (0, 80, 154, 255))
        
        # Borders and Separators
        dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 65, 75, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Separator, (60, 65, 75, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, (0, 114, 206, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, (0, 80, 154, 255))
        
        # Styling: Round the edges slightly for a modern, polished look
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
        dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 4)
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4)

# Apply the theme globally to the application
dpg.bind_theme(mitel_theme)
# --- END OF MITEL COLOR THEME ---

with dpg.font_registry():
    if os.path.exists(CUSTOM_FONT_FILE):
        custom_font = dpg.add_font(CUSTOM_FONT_FILE, 12)
        dpg.bind_font(custom_font)

with dpg.viewport_menu_bar():
    with dpg.menu(label="File"):
        dpg.add_menu_item(label="Load File", callback=lambda: dpg.show_item("load_dialog"))
        dpg.add_menu_item(label="Save File", callback=lambda: dpg.show_item("save_dialog"))
    with dpg.menu(label="Windows"):
        dpg.add_menu_item(label="Config Studio", callback=lambda: dpg.show_item("config_window"))
        dpg.add_menu_item(label="SFTP Manager", callback=lambda: dpg.show_item("ftp_window"))
        dpg.add_menu_item(label="Device Inventory", callback=lambda: dpg.show_item("inventory_window"))

with dpg.file_dialog(directory_selector=False, show=False, callback=app.local_open_cb, tag="load_dialog", width=500, height=350):
    dpg.add_file_extension(".cfg")
with dpg.file_dialog(directory_selector=False, show=False, callback=app.local_save_cb, tag="save_dialog", width=500, height=350):
    dpg.add_file_extension(".cfg")
with dpg.file_dialog(directory_selector=False, show=False, callback=app.process_and_upload_wallpaper, tag="wallpaper_dialog", width=500, height=350):
    dpg.add_file_extension(".jpg")
    dpg.add_file_extension(".png")

with dpg.file_dialog(directory_selector=False, show=False, callback=app.config_wallpaper_pick_cb, tag="config_wallpaper_dialog", width=500, height=350):
    dpg.add_file_extension(".png", color=(0, 255, 0, 255))
    dpg.add_file_extension(".jpg", color=(0, 255, 0, 255))

# --- Window 1: Configuration Studio ---
with dpg.window(label="Endpoint Configuration Studio", tag="config_window", width=580, height=620):
    with dpg.group(horizontal=True):
        dpg.add_text("Target Phone Type:")
        dpg.add_combo(items=app.available_models, callback=app.on_model_select, width=160, tag="model_combo")
        dpg.add_button(label="Refresh JSON", callback=app.refresh_schemas)
    with dpg.group(horizontal=True):
        dpg.add_input_text(tag="current_file_input", default_value="Paste MAC here...", width=160)
        dpg.add_button(label="Format MAC -> .cfg", callback=app.format_mac_to_filename)
        dpg.add_button(label="Push via SFTP", callback=app.ftp_upload)
    dpg.add_separator()
    
    with dpg.tab_bar():
        with dpg.tab(label="Generic Base Options"):
            with dpg.child_window(tag="generic_settings_group", height=-40): pass
            
        with dpg.tab(label="Model Specific Options"):
            with dpg.child_window(tag="model_settings_group", height=-40): pass
            
    dpg.add_separator()
    dpg.add_text("Ready", tag="status_text")

# --- Window 2: SFTP Sync (SSH native) ---
with dpg.window(label="SFTP Server Sync", tag="ftp_window", width=380, height=420, pos=[600, 40]):
    dpg.add_input_text(label="Host IP", tag="ftp_host", default_value="10.19.13.1", width=180)
    dpg.add_input_text(label="SSH User", tag="ftp_user", default_value="root", width=180)
    dpg.add_input_text(label="SSH Pass", tag="ftp_pass", password=True, width=180)
    dpg.add_input_text(label="Target Dir", tag="ftp_path", default_value="/tftpboot", width=180)
    dpg.add_button(label="Connect & List Files", callback=app.ftp_connect_and_list, width=-1)
    dpg.add_separator()
    dpg.add_listbox(items=[], tag="ftp_file_list", num_items=12, width=-1)
    dpg.add_button(label="Download Selected File", callback=app.ftp_download, width=-1)

# --- Window 3: Endpoint Inventory ---
with dpg.window(label="Endpoint Inventory Manager", tag="inventory_window", width=420, height=350, pos=[990, 40]):
    dpg.add_text("Local Handset Database", color=[100, 200, 255])
    
    with dpg.group(horizontal=True):
        dpg.add_text("IP:   ")
        dpg.add_input_text(tag="inv_ip_input", width=150)
        dpg.add_button(label="<- Auto-Fetch MAC", callback=app.fetch_mac_from_ip)
        
    with dpg.group(horizontal=True):
        dpg.add_text("MAC:  ")
        dpg.add_input_text(tag="inv_mac_input", width=150)
        
    with dpg.group(horizontal=True):
        dpg.add_text("Label:")
        dpg.add_input_text(tag="inv_label_input", default_value="Bureau", width=150)
        
    with dpg.group(horizontal=True):
        dpg.add_button(label="Add to Database", callback=app.add_endpoint)
        dpg.add_button(label="Delete Selected", callback=app.delete_endpoint)
        
    dpg.add_separator()
    dpg.add_text("Saved Devices (Click to setup file):")
    dpg.add_listbox(items=[], tag="inventory_list", num_items=8, width=-1, callback=app.on_inventory_select)
    
    dpg.add_separator()
    with dpg.group(horizontal=True):
        dpg.add_input_text(label="Phone Web Password", tag="phone_web_pass", default_value="22222", password=True, width=100)
        dpg.add_button(label="Reboot Selected Phone", callback=app.reboot_selected_phone)

# --- Window 4: Image Loader ---
with dpg.window(label="Asset Image Loader", tag="wallpaper_window", width=380, height=130, pos=[600, 490]):
    dpg.add_text("Auto-converts to 320x240 & pushes via SFTP")
    dpg.add_button(label="Select & Upload Wallpaper...", callback=lambda: dpg.show_item("wallpaper_dialog"), width=-1)

dpg.create_viewport(title='Mitel Config Manager', width=1680, height=720)
dpg.setup_dearpygui()
dpg.show_viewport()

app.build_dynamic_form()
app.refresh_endpoint_list()

dpg.start_dearpygui()
dpg.destroy_context()