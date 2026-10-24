import hmac
import logging
import os
import secrets
from functools import wraps

from flask import Flask, jsonify, redirect, request, send_from_directory, session, url_for

import mitel_core as core

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,
)
log = logging.getLogger("mitel")

if not APP_PASSWORD:
    log.warning("APP_PASSWORD non défini : l'interface est accessible sans authentification.")

core.initialize_data()


# --- Authentification --------------------------------------------------------

@app.before_request
def require_login():
    if not APP_PASSWORD or session.get("auth") is True:
        return None
    if request.endpoint in ("login", "static"):
        return None
    if request.path.startswith("/api/"):
        return jsonify(error="Authentication required"), 401
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if APP_PASSWORD and hmac.compare_digest(request.form.get("password", ""), APP_PASSWORD):
            session.clear()
            session["auth"] = True
            session.permanent = True
            return redirect(url_for("index"))
        return redirect(url_for("login", error=1))
    return send_from_directory(STATIC_DIR, "login.html")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


# --- API ---------------------------------------------------------------------

def api(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except core.OpError as e:
            return jsonify(error=str(e)), 400
        except Exception as e:
            log.exception("API error")
            return jsonify(error=f"{type(e).__name__}: {e}"), 502
    return wrapper


def body():
    return request.get_json(silent=True) or {}


def sftp_creds(data):
    return {
        "host": data.get("host", ""),
        "user": data.get("user", ""),
        "password": data.get("password", ""),
    }


@app.get("/api/schemas")
@api
def schemas():
    return jsonify(generic=core.load_schema("generic"), models=core.list_models(), auth=bool(APP_PASSWORD))


@app.get("/api/schemas/<name>")
@api
def schema(name):
    return jsonify(core.load_schema(name))


@app.post("/api/schemas/regenerate")
@api
def regenerate_schemas():
    core.initialize_comprehensive_models(force=True)
    return jsonify(generic=core.load_schema("generic"), models=core.list_models())


@app.post("/api/config/generate")
@api
def generate_config():
    data = body()
    content = core.generate_cfg_string(data.get("values", {}), data.get("raw", ""), data.get("server_ip", ""))
    return jsonify(content=content)


@app.post("/api/config/parse")
@api
def parse_config():
    upload = request.files.get("file")
    if not upload:
        raise core.OpError("No file received.")
    name = core.safe_filename(upload.filename)
    parsed, model = core.parse_cfg_text(upload.read().decode("utf-8", errors="replace"), name)
    return jsonify(data=parsed, model=model, filename=name)


@app.post("/api/sftp/list")
@api
def sftp_list():
    data = body()
    return jsonify(files=core.sftp_list(sftp_creds(data), data.get("path", "")))


@app.post("/api/sftp/download")
@api
def sftp_download():
    data = body()
    name = core.safe_filename(data.get("name"))
    parsed, model = core.parse_cfg_text(core.sftp_read(sftp_creds(data), data.get("path", ""), name), name)
    return jsonify(data=parsed, model=model, filename=name)


@app.post("/api/sftp/upload")
@api
def sftp_upload():
    data = body()
    name = core.safe_filename(data.get("filename"))
    content = core.generate_cfg_string(data.get("values", {}), data.get("raw", ""), data.get("host", ""))
    core.sftp_write(sftp_creds(data), data.get("path", ""), name, content)
    return jsonify(filename=name)


@app.post("/api/sftp/wallpaper")
@api
def sftp_wallpaper():
    upload = request.files.get("file")
    if not upload:
        raise core.OpError("No image received.")
    name = core.process_and_upload_wallpaper(sftp_creds(request.form), request.form.get("path", ""), upload.stream)
    return jsonify(filename=name)


@app.get("/api/endpoints")
@api
def endpoints():
    return jsonify(endpoints=core.load_endpoints())


@app.post("/api/endpoints")
@api
def add_endpoint():
    data = body()
    return jsonify(endpoints=core.add_endpoint(data.get("mac"), data.get("ip"), data.get("label")))


@app.delete("/api/endpoints/<mac>")
@api
def delete_endpoint(mac):
    return jsonify(endpoints=core.delete_endpoint(mac))


@app.post("/api/phone/fetch-mac")
@api
def fetch_mac():
    return jsonify(mac=core.fetch_mac_from_ip(body().get("ip")))


@app.post("/api/phone/reboot")
@api
def reboot():
    data = body()
    return jsonify(message=core.reboot_phone(data.get("ip"), data.get("password", "")))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)), debug=True)
