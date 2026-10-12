// Copyright (C) 2026 Jeff Millar, WA1HCO
// SPDX-License-Identifier: GPL-3.0-only
"use strict";

const SCALES = [0.875, 1, 1.125, 1.25, 1.5, 1.75];
const TITLES = {
  sys: "System",
  az: "Azimuth",
  el: "Elevation",
  net: "Network",
  ports: "Ports",
  ui: "Interface",
  safety: "Safety",
  park: "Park",
  preset: "Heading memories",
};

const S = {
  boot: null,
  pages: [],
  specs: {},
  catalog: [],
  doc: null,
  device: { connected: false, dirty: false, settings: {}, errors: {}, axes: { azimuth: true, elevation: true } },
  controllers: [],
  files: [],
  directory: "",
  page: "rotator",
  advanced: false,
  deviceAdvanced: false,
  query: "",
  family: "",
  maker: "",
  selected: "",
  deviceQuery: "",
  pickedTarget: "",
};

function h(tag, attrs) {
  const node = document.createElement(tag);
  const kids = Array.prototype.slice.call(arguments, 2);
  Object.entries(attrs || {}).forEach(function (pair) {
    const key = pair[0];
    const value = pair[1];
    if (value == null || value === false) return;
    if (key === "class") node.className = value;
    else if (key === "hidden") node.hidden = !!value;
    else node.setAttribute(key, String(value));
  });
  kids.flat().forEach(function (kid) {
    if (kid == null || kid === false) return;
    node.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  });
  return node;
}

async function api(method, path, body) {
  const options = { method: method, headers: {} };
  if (body !== undefined) {
    options.headers["content-type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  const text = await response.text();
  let payload = {};
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch (_err) {
      payload = { message: text };
    }
  }
  if (!response.ok) {
    const error = new Error(payload.message || response.statusText);
    error.payload = payload;
    throw error;
  }
  return payload;
}

function notice(text) {
  const node = document.querySelector("#notice");
  node.hidden = !text;
  node.textContent = text || "";
}

function axisOf(name) {
  if (name.startsWith("az.") || name.endsWith(".az")) return "az";
  if (name.startsWith("el.") || name.endsWith(".el")) return "el";
  return "";
}

function axisAllowed(name, axes) {
  const axis = axisOf(name);
  if (axis === "az") return !!axes.azimuth;
  if (axis === "el") return !!axes.elevation;
  return true;
}

function specList(names) {
  return names.map(function (name) { return S.specs[name]; }).filter(Boolean);
}

function applyScale(index) {
  const next = Math.max(0, Math.min(SCALES.length - 1, index));
  localStorage.setItem("rotatorctl.textScale", String(next));
  document.documentElement.style.fontSize = (SCALES[next] * 100) + "%";
}

function currentScale() {
  const raw = localStorage.getItem("rotatorctl.textScale");
  if (raw == null || raw === "") return 1;
  const stored = Number(raw);
  return Number.isInteger(stored) ? stored : 1;
}

function setupFont() {
  applyScale(currentScale());
  document.querySelector("#fontDown").addEventListener("click", function () {
    applyScale(currentScale() - 1);
  });
  document.querySelector("#fontUp").addEventListener("click", function () {
    applyScale(currentScale() + 1);
  });
}

function paintChrome() {
  const dirty = S.page === "controllers" ? !!S.device.dirty : !!(S.doc && S.doc.dirty);
  const banner = document.querySelector("#dirty");
  banner.hidden = !dirty;
  banner.textContent = S.page === "controllers"
    ? "Unsaved changes on the controller. Save writes them after you confirm."
    : "Unsaved configuration. Save writes a .rotcfg file. Push sends it to a controller later.";
  document.querySelector("#fileName").textContent = S.doc ? S.doc.filename + "  ·  " + S.doc.name : "Untitled.rotcfg";
  document.querySelector("#modePill").textContent = S.device.connected ? "CONNECTED" : "OFFLINE";
  document.querySelector("#subtitle").textContent = S.device.connected
    ? (S.device.name || S.device.serial) + " · " + S.device.target
    : "Offline configuration";
  document.querySelector("#pushBtn").disabled = !S.device.connected;
  document.title = "Rotator Controller" + (dirty ? " *" : "");
  document.querySelectorAll("#pageNav button").forEach(function (button) {
    button.setAttribute("aria-current", button.dataset.page === S.page ? "page" : "false");
  });
}

function buildNav() {
  const nav = document.querySelector("#pageNav");
  nav.replaceChildren.apply(nav, S.pages.map(function (page) {
    const button = h("button", { type: "button", "data-page": page.id }, page.title);
    button.addEventListener("click", function () {
      S.page = page.id;
      paintMain();
    });
    return button;
  }));
}

function filteredPresets() {
  const query = S.query.trim().toLowerCase();
  return S.catalog.filter(function (preset) {
    if (S.family && preset.family !== S.family) return false;
    if (S.maker && preset.maker !== S.maker) return false;
    if (!query) return true;
    const blob = [preset.id, preset.maker, preset.model, preset.family, preset.axes]
      .concat(preset.aliases || [], preset.alias_of || [])
      .join(" ")
      .toLowerCase();
    return blob.indexOf(query) !== -1;
  });
}

function renderRotator() {
  const families = Array.from(new Set(S.catalog.map(function (item) { return item.family; }).filter(Boolean))).sort();
  const makers = Array.from(new Set(S.catalog.map(function (item) { return item.maker; }).filter(Boolean))).sort();
  const shown = filteredPresets();
  if (!S.selected && shown[0]) S.selected = shown[0].id;
  const search = h("input", { id: "presetSearch", type: "search", placeholder: "Search model, maker, family, or alias", value: S.query });
  search.addEventListener("input", function () {
    S.query = search.value;
    paintMain();
    const again = document.querySelector("#presetSearch");
    again.focus();
    again.setSelectionRange(again.value.length, again.value.length);
  });
  const family = h("select", { id: "familyFilter" }, h("option", { value: "" }, "All families"));
  families.forEach(function (name) { family.append(h("option", { value: name }, name)); });
  family.value = S.family;
  family.addEventListener("change", function () { S.family = family.value; paintMain(); });
  const maker = h("select", { id: "makerFilter" }, h("option", { value: "" }, "All manufacturers"));
  makers.forEach(function (name) { maker.append(h("option", { value: name }, name)); });
  maker.value = S.maker;
  maker.addEventListener("change", function () { S.maker = maker.value; paintMain(); });
  const list = h("ul", { id: "presetList", class: "preset-list" });
  shown.forEach(function (preset) {
    const button = h("button", { type: "button", "data-id": preset.id, "aria-selected": preset.id === S.selected ? "true" : "false" }, preset.maker + " " + preset.model);
    button.addEventListener("click", function () {
      S.selected = preset.id;
      paintMain();
    });
    list.append(h("li", {}, button));
  });
  const selected = S.catalog.find(function (item) { return item.id === S.selected; }) || shown[0];
  return h("section", {},
    h("h2", {}, "Rotator"),
    h("div", { class: "filters" }, search, family, maker),
    h("p", { id: "presetCount" }, shown.length + " of " + S.catalog.length),
    h("div", { class: "split" }, list, selected ? renderDetail(selected) : h("p", {}, "No rotators match."))
  );
}

function renderDetail(preset) {
  const facts = h("ul", { class: "facts" });
  preset.facts.forEach(function (fact) {
    const value = fact.value + (fact.unverified ? " [?]" : "");
    facts.append(h("li", {}, fact.label + ": " + value));
  });
  const unverified = h("p", {}, (preset.unverified || []).map(function (path) { return path + " [?]"; }).join(", "));
  const settings = h("ul", { class: "settings-list" });
  (preset.settings || []).forEach(function (row) {
    settings.append(h("li", {}, row.label + " = " + row.value));
  });
  const overrides = h("ul", { class: "override-list", id: "overrideList" });
  const current = S.doc && S.doc.preset === preset.id ? S.doc.overrides : {};
  Object.keys(current || {}).forEach(function (name) {
    const spec = S.specs[name];
    const label = spec ? spec.label : name;
    const presetValue = (preset.settings.find(function (row) { return row.name === name; }) || {}).value || "";
    overrides.append(h("li", {}, label + ": preset " + presetValue + " → custom " + current[name]));
  });
  const use = h("button", { id: "usePreset", type: "button" }, "Use this rotator");
  use.disabled = !preset.can_apply;
  use.addEventListener("click", async function () {
    try {
      S.doc = await api("POST", "api/preset/apply", { id: preset.id });
      notice("");
      paintMain();
    } catch (err) {
      notice(err.message);
    }
  });
  const picker = h("select", { id: "overrideName" });
  (preset.settings || []).forEach(function (row) {
    picker.append(h("option", { value: row.name }, row.label));
  });
  const value = h("input", { id: "overrideValue", type: "text", placeholder: "Custom value" });
  const set = h("button", { id: "setOverride", type: "button" }, "Set override");
  set.addEventListener("click", async function () {
    if (!picker.value) return;
    try {
      S.doc = await api("POST", "api/override", { name: picker.value, value: value.value });
      notice("");
      paintMain();
    } catch (err) {
      notice(err.message);
    }
  });
  const alias = (preset.alias_of || []).length
    ? h("p", {}, "Alias of " + preset.alias_of.join(", "))
    : null;
  return h("div", { class: "detail", id: "presetDetail" },
    h("h2", {}, preset.maker + " " + preset.model),
    alias,
    facts,
    unverified,
    h("h3", {}, "Settings this preset writes"),
    settings,
    h("h3", {}, "Custom overrides"),
    overrides,
    preset.can_apply ? h("div", { class: "override-row" }, picker, value, set) : null,
    use
  );
}

function renderField(spec, value, errorText, onCommit) {
  const row = h("div", { class: "field", "data-name": spec.name });
  const label = h("label", { for: "field-" + spec.name, title: spec.name + "\n" + (spec.help || "") }, spec.label || spec.name);
  let control;
  if (spec.type === "bool" || spec.type === "enum") {
    const options = spec.type === "bool" ? ["true", "false"] : spec.enum;
    control = h("select", { id: "field-" + spec.name });
    options.forEach(function (option) { control.append(h("option", { value: option }, option)); });
    control.value = value;
  } else {
    control = h("input", { id: "field-" + spec.name, type: "text", value: value == null ? "" : value });
  }
  if (spec.readonly) control.disabled = true;
  control.addEventListener("change", function () { onCommit(spec.name, control.value); });
  row.append(label);
  if (spec.advanced) row.append(h("span", { class: "field-key" }, spec.name));
  row.append(control);
  row.append(h("div", { class: "field-error" }, errorText || ""));
  return row;
}

function renderGroups(specs, values, errors, axes, advanced, onCommit) {
  const buckets = new Map();
  specs.forEach(function (spec) {
    const prefix = spec.name.split(".")[0];
    if (!buckets.has(prefix)) buckets.set(prefix, []);
    buckets.get(prefix).push(spec);
  });
  const fragment = document.createDocumentFragment();
  buckets.forEach(function (items, prefix) {
    const group = h("section", { id: "group-" + prefix + (advanced ? "-advanced" : ""), class: "group" });
    group.append(h("h3", {}, TITLES[prefix] || prefix));
    let visible = 0;
    items.forEach(function (spec) {
      const row = renderField(spec, values[spec.name], errors[spec.name], onCommit);
      if (!axisAllowed(spec.name, axes)) row.hidden = true;
      else visible += 1;
      group.append(row);
    });
    if (!visible) group.hidden = true;
    fragment.append(group);
  });
  return fragment;
}

function renderForm(page, values, errors, axes, advanced, onToggle, onCommit) {
  const names = page.fields || [];
  const specs = specList(names);
  const plain = specs.filter(function (spec) { return !spec.advanced; });
  const extra = specs.filter(function (spec) { return spec.advanced; });
  const body = h("div", { id: "advancedBody", hidden: !advanced });
  body.append(renderGroups(extra, values, errors, axes, true, onCommit));
  const toggle = h("button", { id: "advancedToggle", type: "button", "aria-expanded": advanced ? "true" : "false" }, "Advanced");
  toggle.addEventListener("click", onToggle);
  const root = h("section", {}, h("h2", {}, page.title), page.intro ? h("p", { class: "intro" }, page.intro) : null);
  root.append(renderGroups(plain, values, errors, axes, false, onCommit));
  if (extra.length) root.append(toggle, body);
  return root;
}

async function commitOffline(name, value) {
  try {
    S.doc = await api("POST", "api/document/edit", { name: name, value: value });
    notice("");
    paintChrome();
    const slot = document.querySelector('.field[data-name="' + name + '"] .field-error');
    if (slot) slot.textContent = "";
  } catch (err) {
    const slot = document.querySelector('.field[data-name="' + name + '"] .field-error');
    if (slot) slot.textContent = err.message;
    notice(err.message);
  }
}

async function commitDevice(name, value) {
  try {
    S.device = await api("POST", "api/device/edit", { name: name, value: value });
    notice("");
    paintChrome();
    const slot = document.querySelector('.field[data-name="' + name + '"] .field-error');
    if (slot) slot.textContent = (S.device.errors && S.device.errors[name]) || "";
  } catch (err) {
    notice(err.message);
  }
}

function deviceMatches(spec, query) {
  if (!query) return true;
  const blob = (spec.name + " " + (spec.label || "") + " " + (spec.help || "")).toLowerCase();
  return blob.indexOf(query) !== -1;
}

function renderControllers() {
  const root = h("section", {}, h("h2", {}, "Controllers"), h("p", { class: "intro" }, "USB and network discovery stay here. The rest of the app edits an offline configuration until you connect."));
  const host = h("input", { id: "addHost", type: "text", placeholder: "Host", value: "127.0.0.1" });
  const port = h("input", { id: "addPort", type: "text", placeholder: "Port", value: "4533" });
  const addNet = h("button", { id: "addNetwork", type: "button" }, "Add network");
  addNet.addEventListener("click", async function () {
    try {
      const payload = await api("POST", "api/controllers/add", { kind: "tcp", host: host.value, port: Number(port.value) });
      S.controllers = payload.controllers;
      notice("");
      paintMain();
    } catch (err) {
      notice(err.message);
    }
  });
  const serial = h("input", { id: "addSerial", type: "text", placeholder: "Serial path" });
  const addSerial = h("button", { id: "addSerialBtn", type: "button" }, "Add serial");
  addSerial.addEventListener("click", async function () {
    try {
      const payload = await api("POST", "api/controllers/add", { kind: "serial", path: serial.value });
      S.controllers = payload.controllers;
      notice("");
      paintMain();
    } catch (err) {
      notice(err.message);
    }
  });
  const scan = h("button", { id: "scanBtn", type: "button" }, "Scan");
  scan.addEventListener("click", async function () {
    try {
      const payload = await api("POST", "api/controllers/scan", { timeout: 0.8 });
      S.controllers = payload.controllers;
      notice("");
      paintMain();
    } catch (err) {
      notice(err.message);
    }
  });
  const list = h("ul", { id: "controllerList", class: "controller-list" });
  S.controllers.forEach(function (info) {
    const target = (info.endpoints[0] || {}).target || "";
    const button = h("button", { type: "button", "data-target": target, "aria-selected": target && target === S.pickedTarget ? "true" : "false" }, info.text);
    button.addEventListener("click", function () {
      S.pickedTarget = target;
      paintMain();
    });
    list.append(h("li", {}, button));
  });
  const connect = h("button", { id: "connectBtn", type: "button" }, "Connect");
  connect.addEventListener("click", async function () {
    if (!S.pickedTarget) {
      notice("Choose a controller first.");
      return;
    }
    try {
      S.device = await api("POST", "api/controllers/connect", { target: S.pickedTarget });
      notice("");
      paintMain();
    } catch (err) {
      if (err.payload && err.payload.error === "dirty") {
        const discard = window.confirm("Discard unsaved controller changes and connect?");
        if (!discard) return;
        S.device = await api("POST", "api/controllers/connect", { target: S.pickedTarget, discard: true });
        paintMain();
        return;
      }
      notice(err.message);
    }
  });
  root.append(h("div", { class: "row-actions" }, scan, host, port, addNet, serial, addSerial, connect), list);
  if (S.device.connected) root.append(renderDeviceEditor());
  root.append(renderPhaseMenus());
  return root;
}

function renderDeviceEditor() {
  const schema = (S.device.schema && S.device.schema.settings) || [];
  const query = S.deviceQuery.trim().toLowerCase();
  const specs = schema.filter(function (spec) { return deviceMatches(spec, query); });
  const plain = specs.filter(function (spec) { return !spec.advanced; });
  const extra = specs.filter(function (spec) { return spec.advanced; });
  const forceAdvanced = S.deviceAdvanced || (query && extra.length > 0);
  const search = h("input", { id: "deviceSearch", type: "search", placeholder: "Filter settings", value: S.deviceQuery });
  search.addEventListener("input", function () {
    S.deviceQuery = search.value;
    paintMain();
    const again = document.querySelector("#deviceSearch");
    if (again) {
      again.focus();
      again.setSelectionRange(again.value.length, again.value.length);
    }
  });
  const save = h("button", { id: "deviceSave", type: "button" }, "Save to controller");
  save.addEventListener("click", saveDevice);
  const backup = h("button", { id: "backupBtn", type: "button" }, "Backup");
  backup.addEventListener("click", downloadBackup);
  const restore = h("button", { id: "restoreBtn", type: "button" }, "Restore");
  restore.addEventListener("click", function () { pickText(restoreFile); });
  const compare = h("button", { id: "compareBtn", type: "button" }, "Compare");
  compare.addEventListener("click", function () { pickText(compareFile); });
  const copy = h("button", { id: "copyBtn", type: "button" }, "Copy from selected");
  copy.addEventListener("click", async function () {
    if (!S.pickedTarget || S.pickedTarget === S.device.target) {
      notice("Select another controller to copy from.");
      return;
    }
    try {
      S.device = await api("POST", "api/device/copy", { target: S.pickedTarget });
      notice("");
      paintMain();
    } catch (err) {
      notice(err.message);
    }
  });
  const body = h("div", { id: "advancedBody", hidden: !forceAdvanced });
  body.append(renderGroups(extra, S.device.settings, S.device.errors || {}, S.device.axes, true, commitDevice));
  const toggle = h("button", { id: "advancedToggle", type: "button", "aria-expanded": forceAdvanced ? "true" : "false" }, "Advanced");
  toggle.addEventListener("click", function () {
    S.deviceAdvanced = !S.deviceAdvanced;
    paintMain();
  });
  const editor = h("section", { id: "deviceEditor" },
    h("h3", {}, "Connected settings"),
    h("div", { class: "filters" }, search, save, backup, restore, compare, copy)
  );
  editor.append(renderGroups(plain, S.device.settings, S.device.errors || {}, S.device.axes, false, commitDevice));
  if (extra.length) editor.append(toggle, body);
  return editor;
}

function renderPhaseMenus() {
  const operate = h("details", {}, h("summary", {}, "Operate"));
  (S.boot.operate || []).forEach(function (label) {
    operate.append(h("button", { type: "button", disabled: "disabled" }, label));
  });
  const upgrade = h("details", {}, h("summary", {}, "Upgrade"));
  (S.boot.upgrade || []).forEach(function (label) {
    const button = h("button", { type: "button", disabled: "disabled", title: (S.boot.dfu || []).join(" ") }, label);
    upgrade.append(button);
  });
  return h("div", { class: "menus" }, operate, upgrade);
}

function paintMain() {
  const page = S.pages.find(function (item) { return item.id === S.page; }) || S.pages[0];
  const main = document.querySelector("#main");
  let node;
  if (!page || page.id === "rotator") node = renderRotator();
  else if (page.id === "controllers") node = renderControllers();
  else {
    node = renderForm(page, S.doc.settings, {}, S.doc.axes, S.advanced, function () {
      S.advanced = !S.advanced;
      paintMain();
    }, commitOffline);
  }
  main.replaceChildren(node);
  paintChrome();
}

function confirmDiff(preview, title, acceptLabel) {
  const dialog = document.querySelector("#diff");
  document.querySelector("#diffTitle").textContent = title;
  document.querySelector("#diffIntro").textContent = preview.changes.length
    ? "These values will change."
    : "Nothing will change.";
  const table = h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Setting"), h("th", {}, "Before"), h("th", {}, "After"))));
  const body = h("tbody");
  preview.changes.forEach(function (change) {
    body.append(h("tr", {}, h("td", {}, change.label + " (" + change.name + ")"), h("td", {}, change.before), h("td", {}, change.after)));
  });
  table.append(body);
  document.querySelector("#diffTable").replaceChildren(table);
  const note = document.querySelector("#diffNote");
  note.hidden = !preview.note;
  note.textContent = preview.note || "";
  const accept = document.querySelector("#diffAccept");
  accept.textContent = acceptLabel;
  accept.hidden = !preview.changes.length || preview.blocked;
  return new Promise(function (resolve) {
    dialog.addEventListener("close", function () { resolve(dialog.returnValue === "save"); }, { once: true });
    dialog.showModal();
  });
}

async function saveOffline() {
  try {
    const preview = await api("POST", "api/document/preview", {});
    if (preview.blocked) {
      notice("Fix the highlighted fields before saving.");
      return;
    }
    if (!preview.changes.length) {
      notice("Nothing to write.");
      return;
    }
    const ok = await confirmDiff(preview, "Save configuration", "Save");
    if (!ok) return;
    const name = S.doc.filename === "Untitled.rotcfg" ? "station.rotcfg" : S.doc.filename;
    S.doc = await api("POST", "api/document/save", { name: name });
    notice("Saved " + S.doc.filename);
    paintChrome();
  } catch (err) {
    notice(err.message);
  }
}

async function saveDevice() {
  try {
    const preview = await api("POST", "api/device/preview", {});
    if (preview.blocked) {
      notice("Fix the highlighted fields before saving.");
      return;
    }
    if (!preview.changes.length) {
      notice("Nothing to write.");
      return;
    }
    const ok = await confirmDiff(preview, "Save to controller", "Save");
    if (!ok) return;
    S.device = await api("POST", "api/device/save", {});
    notice("Saved to the controller.");
    paintMain();
  } catch (err) {
    notice(err.message);
  }
}

async function downloadRotcfg() {
  const response = await fetch("api/document/download");
  if (!response.ok) {
    notice("Download failed.");
    return;
  }
  const blob = await response.blob();
  const link = h("a", { href: URL.createObjectURL(blob), download: S.doc.filename === "Untitled.rotcfg" ? "station.rotcfg" : S.doc.filename });
  link.click();
}

async function downloadBackup() {
  const response = await fetch("api/device/backup", { method: "POST" });
  if (!response.ok) {
    notice("Backup failed.");
    return;
  }
  const blob = await response.blob();
  const link = h("a", { href: URL.createObjectURL(blob), download: "rotator-settings.txt" });
  link.click();
}

function pickText(done) {
  const input = document.querySelector("#filePick");
  input.onchange = async function () {
    const file = input.files && input.files[0];
    input.value = "";
    if (!file) return;
    done(await file.text());
  };
  input.click();
}

async function restoreFile(text) {
  try {
    const preview = await api("POST", "api/device/restore", { text: text, apply: false });
    const ok = await confirmDiff(preview, "Restore to controller", "Restore");
    if (!ok) return;
    S.device = await api("POST", "api/device/restore", { text: text, apply: true });
    notice("Restored.");
    paintMain();
  } catch (err) {
    notice(err.message);
  }
}

async function compareFile(text) {
  try {
    const preview = await api("POST", "api/device/compare", { text: text });
    await confirmDiff(preview, "Compare", "Close");
  } catch (err) {
    notice(err.message);
  }
}

async function openFolder() {
  const payload = await api("GET", "api/files");
  S.files = payload.files;
  S.directory = payload.directory;
  document.querySelector("#folderPath").textContent = payload.directory;
  const list = document.querySelector("#folderList");
  list.replaceChildren.apply(list, (payload.files.length ? payload.files : ["(empty)"]).map(function (name) {
    if (name === "(empty)") return h("li", {}, name);
    const button = h("button", { type: "button" }, name);
    button.addEventListener("click", async function () {
      S.doc = await api("POST", "api/files/open", { name: name });
      document.querySelector("#folderDialog").close();
      S.page = "rotator";
      if (S.doc.preset) S.selected = S.doc.preset;
      notice("");
      paintMain();
    });
    return h("li", {}, button);
  }));
  document.querySelector("#folderDialog").showModal();
}

function connectSocket() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(proto + "://" + location.host + location.pathname.replace(/\/$/, "") + "/api/ws");
  socket.addEventListener("open", function () { socket.send("hello"); });
}

function wire() {
  document.querySelector("#newBtn").addEventListener("click", async function () {
    if (S.doc && S.doc.dirty && !window.confirm("Discard unsaved configuration?")) return;
    S.doc = await api("POST", "api/document/new", {});
    S.selected = "";
    S.page = "rotator";
    notice("");
    paintMain();
  });
  document.querySelector("#openBtn").addEventListener("click", function () {
    pickText(async function (text) {
      try {
        S.doc = await api("POST", "api/document/upload", { text: text });
        if (S.doc.preset) S.selected = S.doc.preset;
        notice("");
        paintMain();
      } catch (err) {
        notice(err.message);
      }
    });
  });
  document.querySelector("#folderBtn").addEventListener("click", function () { openFolder().catch(function (err) { notice(err.message); }); });
  document.querySelector("#saveBtn").addEventListener("click", saveOffline);
  document.querySelector("#downloadBtn").addEventListener("click", downloadRotcfg);
  document.querySelector("#pushBtn").addEventListener("click", async function () {
    try {
      S.device = await api("POST", "api/document/push", {});
      notice("Pushed writable settings.");
      paintChrome();
    } catch (err) {
      notice(err.message);
    }
  });
  document.querySelector("#quitBtn").addEventListener("click", async function () {
    try { await api("POST", "api/shutdown", {}); } catch (_err) { /* the helper may already be gone */ }
    document.body.replaceChildren(h("p", {}, "Rotator Controller has quit. You can close this tab."));
  });
  document.querySelector("#stop").title = "Phase 2 sends GS-232 " + ((S.boot && S.boot.stop) || "S") + " on the shared port";
}

async function init() {
  setupFont();
  S.boot = await api("GET", "api/boot");
  S.pages = (await api("GET", "api/pages")).pages;
  if (!S.boot.features.discovery) {
    S.pages = S.pages.filter(function (page) { return page.id !== "controllers"; });
  }
  const schema = await api("GET", "api/schema");
  schema.settings.forEach(function (spec) { S.specs[spec.name] = spec; });
  S.catalog = (await api("GET", "api/catalog")).presets;
  S.doc = await api("GET", "api/document");
  if (S.doc.preset) S.selected = S.doc.preset;
  document.querySelector("#footnote").textContent = S.boot.idle_seconds
    ? "This tab is the app. Quit stops the helper now. Closing the last tab stops it after " + S.boot.idle_seconds + " seconds. The address in the bar is this session's key."
    : "This tab is the app. The address in the bar is this session's key.";
  if (!S.boot.features.files) {
    ["openBtn", "folderBtn", "downloadBtn"].forEach(function (id) { document.querySelector("#" + id).hidden = true; });
  }
  if (!S.boot.features.shutdown) document.querySelector("#quitBtn").hidden = true;
  buildNav();
  wire();
  paintMain();
  connectSocket();
  window.setInterval(function () { api("POST", "api/heartbeat", {}).catch(function () {}); }, 8000);
}

init().catch(function (err) { notice(err.message || String(err)); });
