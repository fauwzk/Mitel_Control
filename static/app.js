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

// --- Schémas et clés ---------------------------------------------------------

const MAX_LINES = 24;
const KEY_FIELD_LABELS = { type: "Type", label: "Label", value: "Value", line: "Line", states: "States", locked: "Locked" };

function lineCount() {
    return state.modelSchema && state.modelSchema.lines ? state.modelSchema.lines : MAX_LINES;
}

function keyGroups() {
    return state.modelSchema && state.modelSchema.key_groups ? state.modelSchema.key_groups : [];
}

function groupKey(group, n, field) {
    return `${group.pattern.replace("{n}", n)} ${field}`;
}

function lineKey(setting, n) {
    return setting.key.replace("{n}", n);
}

// Liste ordonnée de toutes les clés gérées par l'interface pour le modèle courant
function allKeys() {
    const keys = [];
    for (const s of state.generic.settings) keys.push(s.key);
    for (const s of (state.modelSchema ? state.modelSchema.settings || [] : [])) keys.push(s.key);
    for (let n = 1; n <= lineCount(); n++) {
        for (const s of state.generic.line_settings || []) keys.push(lineKey(s, n));
    }
    for (const g of keyGroups()) {
        for (let n = 1; n <= g.count; n++) for (const f of g.fields) keys.push(groupKey(g, n, f));
    }
    return keys;
}

function collectValues() {
    const values = {};
    for (const k of allKeys()) {
        const v = state.values[k];
        if (v !== undefined && v !== "") values[k] = v;
    }
    return values;
}

const isSet = (key) => state.values[key] !== undefined && state.values[key] !== "";

// --- Champs ------------------------------------------------------------------

function normalizeOptions(options) {
    return (options || []).map((o) => (typeof o === "object" ? o : { value: o, label: o === "" ? "(empty)" : o }));
}

let datalistSeq = 0;
const datalists = new Map();

function datalistFor(values) {
    const id = values.join("\u0001");
    if (!datalists.has(id)) {
        const dl = document.createElement("datalist");
        dl.id = `dl-${++datalistSeq}`;
        for (const v of values) dl.append(new Option(v, v));
        document.body.append(dl);
        datalists.set(id, dl.id);
    }
    return datalists.get(id);
}

function makeSelect(options, value, onChange) {
    const select = document.createElement("select");
    const opts = normalizeOptions(options);
    if (value !== "" && !opts.some((o) => String(o.value) === value)) {
        opts.push({ value, label: `${value} (custom)` });
    }
    for (const o of opts) select.append(new Option(o.label, o.value));
    select.value = value;
    select.addEventListener("change", () => onChange(select.value));
    return select;
}

function makeInput(type, value, onChange, { suggestions, placeholder } = {}) {
    const input = document.createElement("input");
    input.type = type === "password" ? "password" : "text";
    input.autocomplete = type === "password" ? "new-password" : "off";
    input.value = value;
    if (placeholder) input.placeholder = placeholder;
    if (suggestions && suggestions.length) input.setAttribute("list", datalistFor(suggestions));
    input.addEventListener("input", () => onChange(input.value));
    return input;
}

function setValue(key, value) {
    state.values[key] = value;
    scheduleBadges();
}

function fieldControl(setting, key) {
    let value = state.values[key] ?? "";
    if (setting.type === "choice") {
        const opts = normalizeOptions(setting.options);
        // Anciens schémas sans option vide : la première option sert de valeur par défaut
        if (value === "" && opts.length && !opts.some((o) => o.value === "")) {
            value = String(opts[0].value);
            state.values[key] = value;
        }
        return makeSelect(setting.options, value, (v) => setValue(key, v));
    }
    return makeInput(setting.type, value, (v) => setValue(key, v), { suggestions: setting.suggestions });
}

function renderField(setting, key) {
    const field = document.createElement("label");
    field.className = "field";
    field.dataset.search = `${setting.label} ${key}`.toLowerCase();
    field.dataset.key = key;

    const title = document.createElement("span");
    title.textContent = setting.label;
    const meta = document.createElement("small");
    const parts = [key];
    if (setting.default !== undefined) parts.push(`default ${setting.default}`);
    meta.textContent = parts.join(" · ");
    field.append(title, meta, fieldControl(setting, key));
    if (setting.help) {
        const help = document.createElement("em");
        help.textContent = setting.help;
        field.append(help);
    }
    return field;
}

// Regroupe les paramètres par section dans des blocs repliables
function renderSections(settings, container, keyOf = (s) => s.key) {
    container.replaceChildren();
    const bySection = new Map();
    for (const s of settings) {
        const name = s.section || "Settings";
        if (!bySection.has(name)) bySection.set(name, []);
        bySection.get(name).push(s);
    }
    for (const [name, list] of bySection) {
        const details = document.createElement("details");
        details.className = "section";
        const openKey = `mitel.section.${container.id}.${name}`;
        details.open = storageGet(openKey) !== "0";
        details.addEventListener("toggle", () => storageSet(openKey, details.open ? "1" : "0"));
        const summary = document.createElement("summary");
        const title = document.createElement("span");
        title.textContent = name;
        const badge = document.createElement("span");
        badge.className = "badge";
        summary.append(title, badge);
        const grid = document.createElement("div");
        grid.className = "fields";
        for (const s of list) grid.append(renderField(s, keyOf(s)));
        details.append(summary, grid);
        container.append(details);
    }
}

// --- Onglet Lignes -----------------------------------------------------------

let currentLine = 1;

function renderLines() {
    if (currentLine > lineCount()) currentLine = 1;
    const chips = $("#line-chips");
    chips.replaceChildren();
    for (let n = 1; n <= lineCount(); n++) {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = `Line ${n}`;
        b.dataset.line = n;
        b.classList.toggle("active", n === currentLine);
        b.addEventListener("click", () => { currentLine = n; renderLines(); applyFilter(); });
        chips.append(b);
    }
    renderSections(state.generic.line_settings || [], $("#line-fields"), (s) => lineKey(s, currentLine));
    updateBadges();
}

// --- Onglet Touches ----------------------------------------------------------

let currentGroup = null;

function rowConfigured(group, n) {
    return group.fields.some((f) => isSet(groupKey(group, n, f)));
}

function renderKeys() {
    const groups = keyGroups();
    $("#keys-empty").hidden = groups.length > 0;
    if (!groups.some((g) => g.id === currentGroup)) currentGroup = groups.length ? groups[0].id : null;

    const chips = $("#key-group-chips");
    chips.replaceChildren();
    for (const g of groups) {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = g.label;
        b.dataset.group = g.id;
        b.classList.toggle("active", g.id === currentGroup);
        b.addEventListener("click", () => { currentGroup = g.id; renderKeys(); });
        chips.append(b);
    }

    const table = $("#keys-table");
    table.replaceChildren();
    const group = groups.find((g) => g.id === currentGroup);
    $("#key-group-hint").textContent = group
        ? `${group.count} keys · parameters "${group.pattern.replace("{n}", "N")} ${group.fields.join(" / ")}"`
        : "";
    if (!group) return;

    const head = table.createTHead().insertRow();
    head.insertCell().textContent = "Key";
    for (const f of group.fields) head.insertCell().textContent = KEY_FIELD_LABELS[f] || f;
    const body = table.createTBody();
    const lineOptions = [{ value: "", label: "—" }, ...Array.from({ length: lineCount() }, (_, i) => String(i + 1))];

    for (let n = 1; n <= group.count; n++) {
        const row = body.insertRow();
        const name = group.names && group.names[n] ? `${n} · ${group.names[n]}` : String(n);
        row.insertCell().textContent = name;
        for (const f of group.fields) {
            const key = groupKey(group, n, f);
            const value = state.values[key] ?? "";
            const onChange = (v) => { setValue(key, v); row.classList.toggle("configured", rowConfigured(group, n)); };
            let control;
            if (f === "type") {
                control = makeSelect([{ value: "", label: "—" }, ...(group.types || [])], value, onChange);
            } else if (f === "line") {
                control = makeSelect(lineOptions, value, onChange);
            } else if (f === "locked") {
                control = makeSelect([{ value: "", label: "—" }, { value: "0", label: "No" }, { value: "1", label: "Yes" }],
                    value, onChange);
            } else {
                control = makeInput("string", value, onChange,
                    f === "states" ? { placeholder: "idle connected incoming outgoing busy" } : {});
            }
            control.title = key;
            control.setAttribute("aria-label", `Key ${name} ${f}`);
            const cell = row.insertCell();
            cell.className = `col-${f}`;
            cell.append(control);
        }
        row.classList.toggle("configured", rowConfigured(group, n));
    }
    updateBadges();
}

// --- Compteurs de paramètres renseignés ---------------------------------------

let badgeTimer = null;
function scheduleBadges() {
    clearTimeout(badgeTimer);
    badgeTimer = setTimeout(updateBadges, 150);
}

function setBadge(el, count) {
    if (el) el.textContent = count ? String(count) : "";
}

function updateBadges() {
    const countSettings = (settings) => settings.filter((s) => isSet(s.key)).length;
    setBadge($("#badge-generic"), countSettings(state.generic.settings));
    setBadge($("#badge-model"), countSettings(state.modelSchema ? state.modelSchema.settings || [] : []));

    let lines = 0;
    for (let n = 1; n <= lineCount(); n++) {
        const used = (state.generic.line_settings || []).some((s) => isSet(lineKey(s, n)));
        if (used) lines++;
        const chip = document.querySelector(`#line-chips [data-line="${n}"]`);
        if (chip) chip.classList.toggle("has-data", used);
    }
    setBadge($("#badge-lines"), lines);

    let keys = 0;
    for (const g of keyGroups()) {
        let used = 0;
        for (let n = 1; n <= g.count; n++) if (rowConfigured(g, n)) used++;
        keys += used;
        const chip = document.querySelector(`#key-group-chips [data-group="${g.id}"]`);
        if (chip) chip.dataset.count = used || "";
    }
    setBadge($("#badge-keys"), keys);

    document.querySelectorAll("details.section").forEach((d) => {
        const n = [...d.querySelectorAll(".field")].filter((f) => isSet(f.dataset.key)).length;
        setBadge(d.querySelector("summary .badge"), n);
    });
}

// --- Construction du formulaire ------------------------------------------------

function buildForm() {
    renderSections(state.generic.settings, $("#generic-fields"));
    const modelSettings = state.modelSchema ? state.modelSchema.settings || [] : [];
    renderSections(modelSettings, $("#model-fields"));
    $("#model-empty").hidden = modelSettings.length > 0;
    $("#model-description").textContent = state.modelSchema ? state.modelSchema.description || "" : "";
    renderLines();
    renderKeys();
    applyFilter();
}

function buildRawEditor(loaded) {
    const keys = new Set(allKeys());
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
    text += unmapped.length ? unmapped.join("\n") + "\n" : "# Example: [CUSTOM] new_variable: value\n";
    $("#raw-editor").value = text;
}

function applyFilter() {
    const q = $("#field-filter").value.trim().toLowerCase();
    document.querySelectorAll(".field").forEach((f) => {
        f.hidden = Boolean(q) && !f.dataset.search.includes(q);
    });
    document.querySelectorAll("details.section").forEach((d) => {
        const visible = [...d.querySelectorAll(".field")].some((f) => !f.hidden);
        d.hidden = Boolean(q) && !visible;
        if (q && visible) d.open = true;
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
    await selectModel(res.model || $("#model-select").value);
    buildRawEditor(res.data);
    $("#current-file").value = res.filename;
    setStatus(res.model
        ? `Loaded ${res.filename} from ${origin}. Detected model: ${res.model}`
        : `Loaded ${res.filename} from ${origin} (model not detected, keeping current selection)`, "ok");
}

function configPayload() {
    return { values: collectValues(), raw: $("#raw-editor").value };
}

// Modèle déduit du libellé d'un poste de l'inventaire (ex. « 6920i » → 6920)
function modelFromLabel(label) {
    const l = (label || "").toLowerCase();
    return state.models.find((m) => l.includes(m.toLowerCase().replace(/i$/, ""))) || null;
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

    $("#new-config").addEventListener("click", () => {
        if (!confirm("Clear every setting of the current configuration?")) return;
        state.values = {};
        buildForm();
        buildRawEditor({});
        setStatus("New empty configuration.", "ok");
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
            const model = modelFromLabel(ep.label);
            if (model && model !== $("#model-select").value) {
                run(null, null, async () => {
                    await selectModel(model);
                    setStatus(`Target file set to: ${filename} (model ${model})`, "ok");
                });
            } else {
                setStatus(`Target file set to: ${filename}`, "ok");
            }
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
