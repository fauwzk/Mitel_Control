"use strict";

const $ = (sel) => document.querySelector(sel);

const state = {
    generic: { settings: [] },
    models: [],
    modelSchema: null,
    values: {},          // valeurs courantes, indexées par clé de config
    ftpSelected: null,
    inventory: [],
    inventorySelected: null,
};

const PERSISTED_INPUTS = ["ftp-host", "ftp-user", "ftp-path"];

// --- Utilitaires -------------------------------------------------------------

function setStatus(message, kind = "info") {
    const el = $("#status");
    el.textContent = message;
    el.className = `statusbar ${kind}`;
}

async function api(path, { json, form, method } = {}) {
    const opts = { method: method || (json || form ? "POST" : "GET"), headers: {} };
    if (json !== undefined) {
        opts.headers["Content-Type"] = "application/json";
        opts.body = JSON.stringify(json);
    } else if (form) {
        opts.body = form;
    }
    const res = await fetch(path, opts);
    if (res.status === 401) {
        location.href = "/login";
        throw new Error("Session expired");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
}

// Exécute une action en désactivant le bouton et en affichant les erreurs dans la barre d'état
async function run(button, busyMessage, fn) {
    if (button) button.disabled = true;
    if (busyMessage) setStatus(busyMessage, "busy");
    try {
        await fn();
    } catch (e) {
        setStatus(e.message, "error");
    } finally {
        if (button) button.disabled = false;
    }
}

function sftpCreds() {
    return {
        host: $("#ftp-host").value.trim(),
        user: $("#ftp-user").value,
        password: $("#ftp-pass").value,
        path: $("#ftp-path").value.trim(),
    };
}

function storageGet(key) {
    try { return localStorage.getItem(key); } catch { return null; }
}
function storageSet(key, value) {
    try { localStorage.setItem(key, value); } catch { /* stockage indisponible */ }
}

// --- Formulaire dynamique ----------------------------------------------------

function currentSettings() {
    return [...state.generic.settings, ...(state.modelSchema ? state.modelSchema.settings : [])];
}

function renderFields(settings, container) {
    container.replaceChildren();
    for (const setting of settings) {
        const field = document.createElement("label");
        field.className = "field";
        field.dataset.search = `${setting.label} ${setting.key}`.toLowerCase();

        const title = document.createElement("span");
        title.textContent = setting.label;
        const key = document.createElement("small");
        key.textContent = setting.key;

        let input;
        let value = state.values[setting.key] ?? "";
        if (setting.type === "choice") {
            const options = setting.options || [];
            input = document.createElement("select");
            for (const opt of options) {
                const o = document.createElement("option");
                o.value = opt;
                o.textContent = opt === "" ? "(empty)" : opt;
                input.append(o);
            }
            if (!options.includes(value) && options.length) value = options[0];
        } else {
            input = document.createElement("input");
            input.type = "text";
        }
        input.value = value;
        state.values[setting.key] = value;
        input.addEventListener("input", () => { state.values[setting.key] = input.value; });

        field.append(title, key, input);
        container.append(field);
    }
}

function buildForm() {
    renderFields(state.generic.settings, $("#generic-fields"));
    renderFields(state.modelSchema ? state.modelSchema.settings : [], $("#model-fields"));
    $("#model-empty").hidden = Boolean(state.modelSchema && state.modelSchema.settings.length);
    applyFilter();
}

function collectValues() {
    const values = {};
    for (const s of currentSettings()) values[s.key] = state.values[s.key] ?? "";
    return values;
}

function buildRawEditor(loaded) {
    const keys = new Set(currentSettings().map((s) => s.key));
    const mapped = [];
    const unmapped = [];
    for (const [k, v] of Object.entries(loaded)) {
        if (keys.has(k)) mapped.push(`${k}: ${v}`);
        else unmapped.push(`[CUSTOM] ${k}: ${v}`);
    }
    let text = "# --- STANDARD SETTINGS (Edit these via the UI Tabs) ---\n";
    text += "# Note: Edits to standard settings in this box are ignored on save.\n";
    if (mapped.length) text += mapped.join("\n") + "\n";
    text += "\n# --- CUSTOM SETTINGS (Editable) ---\n";
    text += "# Note: Keep the [CUSTOM] tag so the app knows to save these.\n";
    text += unmapped.length ? unmapped.join("\n") + "\n" : "[CUSTOM] new_variable: value\n";
    $("#raw-editor").value = text;
}

function applyFilter() {
    const q = $("#field-filter").value.trim().toLowerCase();
    document.querySelectorAll(".field").forEach((f) => {
        f.hidden = Boolean(q) && !f.dataset.search.includes(q);
    });
}

async function selectModel(name) {
    $("#model-select").value = name || "";
    state.modelSchema = name ? await api(`/api/schemas/${encodeURIComponent(name)}`) : null;
    buildForm();
}

async function loadSchemas(data) {
    const res = data || await api("/api/schemas");
    state.generic = res.generic;
    state.models = res.models;
    const select = $("#model-select");
    const previous = select.value;
    select.replaceChildren(new Option("— generic only —", ""));
    for (const m of state.models) select.append(new Option(m, m));
    await selectModel(state.models.includes(previous) ? previous : "");
    if (res.auth) $("#logout-form").hidden = false;
}

// Applique un fichier .cfg analysé par le serveur (local ou SFTP)
async function applyParsedConfig(res, origin) {
    state.values = { ...res.data };
    await selectModel(res.model || "");
    buildRawEditor(res.data);
    $("#current-file").value = res.filename;
    setStatus(res.model
        ? `Loaded ${res.filename} from ${origin}. Auto-detected model: ${res.model}`
        : `Loaded ${res.filename} from ${origin} (Generic Mode)`, "ok");
}

function configPayload() {
    return { values: collectValues(), raw: $("#raw-editor").value };
}

// --- Studio ------------------------------------------------------------------

function initStudio() {
    $("#model-select").addEventListener("change", (e) =>
        run(null, null, () => selectModel(e.target.value)));

    $("#refresh-schemas").addEventListener("click", (e) => run(e.currentTarget, "Reloading schemas…", async () => {
        await loadSchemas();
        setStatus("JSON schemas reloaded successfully.", "ok");
    }));

    $("#regen-models").addEventListener("click", (e) => {
        if (!confirm("Delete and regenerate all JSON phone models from the built-in defaults?")) return;
        run(e.currentTarget, "Regenerating models…", async () => {
            await loadSchemas(await api("/api/schemas/regenerate", { json: {} }));
            setStatus("JSON models regenerated.", "ok");
        });
    });

    $("#format-mac").addEventListener("click", () => {
        const clean = $("#current-file").value.replace(/[^a-fA-F0-9]/g, "").toUpperCase();
        if (clean.length >= 12) {
            const filename = `${clean.slice(0, 12)}.cfg`;
            $("#current-file").value = filename;
            setStatus(`Formatted filename: ${filename}`, "ok");
        } else {
            setStatus("Please enter a valid MAC address.", "error");
        }
    });

    $("#load-file").addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const form = new FormData();
        form.append("file", file);
        run(null, `Parsing ${file.name}…`, async () => {
            await applyParsedConfig(await api("/api/config/parse", { form }), "local file");
        }).finally(() => { e.target.value = ""; });
    });

    $("#save-file").addEventListener("click", (e) => run(e.currentTarget, null, async () => {
        const { content } = await api("/api/config/generate", {
            json: { ...configPayload(), server_ip: $("#ftp-host").value.trim() },
        });
        const name = $("#current-file").value.trim() || "macaddress.cfg";
        const url = URL.createObjectURL(new Blob([content], { type: "text/plain" }));
        const a = Object.assign(document.createElement("a"), { href: url, download: name });
        document.body.append(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        setStatus(`Saved ${name} locally.`, "ok");
    }));

    $("#push-sftp").addEventListener("click", (e) => {
        const filename = $("#current-file").value.trim();
        run(e.currentTarget, `Uploading ${filename}…`, async () => {
            const res = await api("/api/sftp/upload", { json: { ...sftpCreds(), ...configPayload(), filename } });
            setStatus(`Provisioned file ${res.filename} updated via SFTP.`, "ok");
        });
    });

    $("#field-filter").addEventListener("input", applyFilter);

    const tabs = document.querySelectorAll(".tabs button");
    const showTab = (name) => {
        tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
        document.querySelectorAll(".tab-panel").forEach((p) => { p.hidden = p.dataset.panel !== name; });
        storageSet("mitel.tab", name);
    };
    tabs.forEach((t) => t.addEventListener("click", () => showTab(t.dataset.tab)));
    const savedTab = storageGet("mitel.tab");
    if (savedTab && document.querySelector(`.tabs [data-tab="${savedTab}"]`)) showTab(savedTab);

    buildRawEditor({});
}

// --- SFTP --------------------------------------------------------------------

function renderFtpFiles(files) {
    const list = $("#ftp-files");
    list.replaceChildren();
    state.ftpSelected = null;
    if (!files.length) {
        list.innerHTML = '<li class="placeholder">No .cfg / .txt files found.</li>';
        return;
    }
    for (const name of files) {
        const li = document.createElement("li");
        li.textContent = name;
        li.addEventListener("click", () => {
            list.querySelectorAll("li").forEach((x) => x.classList.remove("selected"));
            li.classList.add("selected");
            state.ftpSelected = name;
        });
        li.addEventListener("dblclick", () => $("#ftp-download").click());
        list.append(li);
    }
}

function initSftp() {
    for (const id of PERSISTED_INPUTS) {
        const saved = storageGet(`mitel.${id}`);
        if (saved !== null) $(`#${id}`).value = saved;
        $(`#${id}`).addEventListener("change", (e) => storageSet(`mitel.${id}`, e.target.value));
    }

    $("#ftp-list").addEventListener("click", (e) => run(e.currentTarget, "Connecting to SFTP…", async () => {
        const creds = sftpCreds();
        const { files } = await api("/api/sftp/list", { json: creds });
        renderFtpFiles(files);
        setStatus(`Indexed SFTP active configs in ${creds.path}`, "ok");
    }));

    $("#ftp-download").addEventListener("click", (e) => {
        if (!state.ftpSelected) {
            setStatus("Select a file in the SFTP list first.", "error");
            return;
        }
        run(e.currentTarget, `Downloading ${state.ftpSelected}…`, async () => {
            const res = await api("/api/sftp/download", { json: { ...sftpCreds(), name: state.ftpSelected } });
            await applyParsedConfig(res, "SFTP");
        });
    });

    $("#wallpaper-file").addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const form = new FormData();
        for (const [k, v] of Object.entries(sftpCreds())) form.append(k, v);
        form.append("file", file);
        run(null, `Optimizing and uploading ${file.name}…`, async () => {
            const res = await api("/api/sftp/wallpaper", { form });
            setStatus(`Wallpaper optimized and uploaded as ${res.filename}!`, "ok");
        }).finally(() => { e.target.value = ""; });
    });
}

// --- Inventaire --------------------------------------------------------------

function renderInventory(endpoints) {
    state.inventory = endpoints;
    state.inventorySelected = null;
    const list = $("#inventory");
    list.replaceChildren();
    if (!endpoints.length) {
        list.innerHTML = '<li class="placeholder">No endpoints added yet.</li>';
        return;
    }
    for (const ep of endpoints) {
        const li = document.createElement("li");
        li.textContent = `[${ep.mac}] ${ep.ip} - ${ep.label}`;
        li.addEventListener("click", () => {
            list.querySelectorAll("li").forEach((x) => x.classList.remove("selected"));
            li.classList.add("selected");
            state.inventorySelected = ep;
            const filename = `${ep.mac.replace(/:/g, "").toLowerCase()}.cfg`;
            $("#current-file").value = filename;
            setStatus(`Target file set to: ${filename}`, "ok");
        });
        list.append(li);
    }
}

function initInventory() {
    $("#fetch-mac").addEventListener("click", (e) => {
        const ip = $("#inv-ip").value.trim();
        if (!ip) {
            setStatus("Enter an IP address first to fetch the MAC.", "error");
            return;
        }
        run(e.currentTarget, `Pinging ${ip} to populate ARP table…`, async () => {
            const { mac } = await api("/api/phone/fetch-mac", { json: { ip } });
            $("#inv-mac").value = mac;
            setStatus(`Success! Discovered MAC: ${mac}`, "ok");
        });
    });

    $("#add-endpoint").addEventListener("click", (e) => run(e.currentTarget, null, async () => {
        const { endpoints } = await api("/api/endpoints", {
            json: { mac: $("#inv-mac").value, ip: $("#inv-ip").value, label: $("#inv-label").value },
        });
        renderInventory(endpoints);
        $("#inv-mac").value = "";
        $("#inv-ip").value = "";
        $("#inv-label").value = "";
        setStatus("Endpoint added to inventory.", "ok");
    }));

    $("#delete-endpoint").addEventListener("click", (e) => {
        const ep = state.inventorySelected;
        if (!ep) return;
        run(e.currentTarget, null, async () => {
            const { endpoints } = await api(`/api/endpoints/${encodeURIComponent(ep.mac)}`, { method: "DELETE" });
            renderInventory(endpoints);
            setStatus("Endpoint removed from inventory.", "ok");
        });
    });

    $("#reboot-phone").addEventListener("click", (e) => {
        const ep = state.inventorySelected;
        if (!ep) {
            setStatus("Please select a phone from the inventory to reboot.", "error");
            return;
        }
        run(e.currentTarget, `Sending URL-encoded XML payload to ${ep.ip}…`, async () => {
            const { message } = await api("/api/phone/reboot", { json: { ip: ep.ip, password: $("#phone-pass").value } });
            setStatus(message, "ok");
        });
    });
}

// --- Démarrage ---------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    initStudio();
    initSftp();
    initInventory();
    run(null, "Loading…", async () => {
        await loadSchemas();
        renderInventory((await api("/api/endpoints")).endpoints);
        setStatus("Ready");
    });
});
