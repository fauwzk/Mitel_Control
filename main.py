import dearpygui.dearpygui as dpg
import json
import os
import tempfile
import paramiko
import re
import subprocess
import platform
from PIL import Image, ImageOps

MODEL_DIR = "phone_models"
TEMP_DIR = tempfile.gettempdir()
ENDPOINT_FILE = "endpoints.json"
CUSTOM_FONT_FILE = "Roboto-Regular.ttf"

def initialize_comprehensive_models():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    model_generic = {
        "model": "generic",
        "description": "Global Settings & SIP Stack",
        "settings": [
            {"key": "dhcp", "label": "DHCP Enabled", "type": "choice", "options": ["1", "0"]},
            {"key": "download protocol", "label": "Provisioning Protocol", "type": "choice", "options": ["TFTP", "FTP", "HTTP"]},
            {"key": "tftp server", "label": "Config Server IP (TFTP)", "type": "string"},
            {"key": "auto resync mode", "label": "Auto Sync Mode (3=Daily)", "type": "choice", "options": ["3", "2", "1", "0"]},
            {"key": "auto resync time", "label": "Auto Sync Time (HH:MM)", "type": "string"},
            {"key": "time server1", "label": "Primary NTP Server", "type": "string"},
            {"key": "time zone name", "label": "Time Zone String", "type": "string"},
            {"key": "sip proxy ip", "label": "SIP Proxy (FreePBX)", "type": "string"},
            {"key": "sip proxy port", "label": "SIP Proxy Port", "type": "string"},
            {"key": "blf pickup prefix", "label": "BLF Pickup Code", "type": "string"},
            {"key": "language 1", "label": "Language File Map 1", "type": "string"},
            {"key": "language", "label": "Active Phone Language", "type": "choice", "options": ["1", "0"]},
            {"key": "ring led flash rate", "label": "Ringing LED Cadence", "type": "choice", "options": ["1", "2", "3", "4"]},
        ]
    }

    model_6867i = {
        "model": "6867i",
        "description": "Mitel 6867i Color Variant",
        "settings": [
            {"key": "sip line1 screen name", "label": "Line 1 Alpha Label", "type": "string"},
            {"key": "background image", "label": "Wallpaper URL/File", "type": "string"},
            {"key": "softkey1 type", "label": "Softkey 1 Profile", "type": "choice", "options": ["none", "speeddial", "blf", "xml"]},
            {"key": "softkey1 label", "label": "Softkey 1 Display Label", "type": "string"},
            {"key": "softkey1 value", "label": "Softkey 1 Dest Value", "type": "string"}
        ]
    }

    for name, data in [("generic", model_generic), ("6867i", model_6867i)]:
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
        
        self.load_schemas()
        self.load_endpoints()

    def load_schemas(self):
        if not os.path.exists(MODEL_DIR): return
        with open(f"{MODEL_DIR}/generic.json", "r") as f:
            self.generic_schema = json.load(f)
        for file in os.listdir(MODEL_DIR):
            if file.endswith(".json") and file != "generic.json":
                self.available_models.append(file.replace(".json", ""))

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
        lines = [f"# Provisioning Profile"]
        for key, tag in self.active_ui_elements.items():
            val = dpg.get_value(tag)
            if val != "": lines.append(f"{key}: {val}")
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

    # --- Utility: Format MAC to Filename ---
    def format_mac_to_filename(self):
        raw_input = dpg.get_value("current_file_input")
        # Strip everything except hex characters
        clean_mac = re.sub(r'[^a-fA-F0-9]', '', raw_input).lower()
        if len(clean_mac) >= 12:
            # Take the first 12 valid hex chars just in case
            clean_mac = clean_mac[:12]
            new_filename = f"{clean_mac}.cfg"
            self.current_filename = new_filename
            dpg.set_value("current_file_input", new_filename)
            dpg.set_value("status_text", f"Formatted filename: {new_filename}")
        else:
            dpg.set_value("status_text", "Please enter a valid MAC address to format.")

    # --- SFTP Connection Logic (Paramiko) ---
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

    # --- ARP MAC Lookup Logic ---
    def fetch_mac_from_ip(self):
        ip = dpg.get_value("inv_ip_input").strip()
        if not ip:
            dpg.set_value("status_text", "Enter an IP address first to fetch the MAC.")
            return
            
        dpg.set_value("status_text", f"Pinging {ip} to populate ARP table...")
        try:
            # 1. Ping the device so the OS registers it in the ARP cache
            ping_cmd = ['ping', '-n', '1', ip] if platform.system().lower() == 'windows' else ['ping', '-c', '1', '-W', '1', ip]
            subprocess.run(ping_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 2. Query the ARP table for that specific IP
            arp_cmd = ['arp', '-a', ip] if platform.system().lower() == 'windows' else ['arp', '-n', ip]
            output = subprocess.check_output(arp_cmd, universal_newlines=True)
            
            # 3. Use Regex to extract the MAC address
            mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', output)
            if mac_match:
                found_mac = mac_match.group(0).replace('-', ':').upper()
                dpg.set_value("inv_mac_input", found_mac)
                dpg.set_value("status_text", f"Success! Discovered MAC: {found_mac}")
            else:
                dpg.set_value("status_text", f"Phone at {ip} did not respond or isn't on the local subnet.")
        except Exception as e:
            dpg.set_value("status_text", f"ARP Lookup failed: {e}")

    # --- Manual Endpoint Inventory Logic ---
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
dpg.configure_app(docking=True, docking_space=True)

with dpg.font_registry():
    if os.path.exists(CUSTOM_FONT_FILE):
        custom_font = dpg.add_font(CUSTOM_FONT_FILE, 16)
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

# --- Window 1: Configuration Studio ---
with dpg.window(label="Endpoint Configuration Studio", tag="config_window", width=580, height=620):
    with dpg.group(horizontal=True):
        dpg.add_text("Target Phone Type:")
        dpg.add_combo(items=app.available_models, callback=app.on_model_select, width=160)
    with dpg.group(horizontal=True):
        # Allow user to paste a raw MAC and format it directly into a filename
        dpg.add_input_text(tag="current_file_input", default_value="Paste MAC here...", width=160)
        dpg.add_button(label="Format MAC -> .cfg", callback=app.format_mac_to_filename)
        dpg.add_button(label="Push via SFTP", callback=app.ftp_upload)
    dpg.add_separator()
    
    with dpg.tab_bar():
        with dpg.tab(label="Generic Base Options"):
            with dpg.child_window(tag="generic_settings_group", height=-40): pass
            
        with dpg.tab(label="Model Specific Options"):
            # Added the missing model container here to prevent the container stack crash
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
        dpg.add_button(label="<- Auto-Fetch MAC", callback=app.fetch_mac_from_ip) # Native ARP query
        
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

# --- Window 4: Image Loader ---
with dpg.window(label="Asset Image Loader", tag="wallpaper_window", width=380, height=130, pos=[600, 490]):
    dpg.add_text("Auto-converts to 320x240 & pushes via SFTP")
    dpg.add_button(label="Select & Upload Wallpaper...", callback=lambda: dpg.show_item("wallpaper_dialog"), width=-1)

dpg.create_viewport(title='Mitel Setup Studio v6', width=1450, height=720)
dpg.setup_dearpygui()
dpg.show_viewport()

app.build_dynamic_form()
app.refresh_endpoint_list()

dpg.start_dearpygui()
dpg.destroy_context()