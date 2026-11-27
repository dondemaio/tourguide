"use strict";
const $ = id => document.getElementById(id);
let records = [], editing = null, busy = false, dirty = false, loaded = false;
const days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
function el(tag, value) { const n = document.createElement(tag); if (value !== undefined) n.textContent = value; return n; }
function button(label, action) { const n = el("button", label); n.type = "button"; n.addEventListener("click", action); return n; }
function notice(message, error = false) { $("notice").textContent = message; $("notice").classList.toggle("error", error); if ($("drawer").open) $("editor-error").textContent = error ? message : ""; }
async function request(path, method = "GET", body) {
    const response = await fetch(path, {method, ...(body === undefined ? {} : {headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)})});
    if (!response.ok) {
        let detail; try { detail = (await response.json()).detail; } catch {}
        throw new Error(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "HTTP " + response.status);
    }
    if (response.status === 204) return null;
    return response.headers.get("content-type")?.includes("application/json") ? response.json() : response.text();
}
async function run(action) {
    if (busy) return;
    busy = true;
    const controls = [...document.querySelectorAll("button,input,textarea,select")].filter(n => !n.disabled);
    controls.forEach(n => n.disabled = true);
    try { await action(); } catch (error) { notice(error.message, true); }
    finally { controls.forEach(n => n.disabled = false); busy = false; drawRecords(); $("record-id").readOnly = editing !== null; }
}
function filtered() {
    const query = $("search").value.trim().toLocaleLowerCase();
    return records.filter(r => [r.name,r.id,r.location,...(r.tags || [])].join(" ").toLocaleLowerCase().includes(query))
        .sort((a,b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
}
function checkbox(checked, label, action) {
    const n = el("input"); n.type = "checkbox"; n.checked = checked; n.setAttribute("aria-label", label); n.addEventListener("change", () => action(n.checked)); return n;
}
function iconButton(label, path, action) {
    const n = button("", action);
    n.className = "icon-button" + (label.startsWith("Delete") ? " delete-icon" : "");
    n.title = label; n.setAttribute("aria-label", label);
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("aria-hidden", "true");
    const shape = document.createElementNS(svg.namespaceURI, "path");
    shape.setAttribute("d", path); svg.append(shape); n.append(svg); return n;
}
function drawRecords() {
    const visible = filtered(); $("records").replaceChildren();
    for (const record of visible) {
        const row = el("tr"), name = el("td"), actions = el("td");
        name.append(el("strong",record.name),el("br"),el("small",record.id));
        actions.className = "row-actions";
        actions.append(iconButton("Edit " + record.name, "M12 20h9M16 4l4 4M4 16L16 4a2.8 2.8 0 0 1 4 4L8 20l-4 1z", () => openEditor(record)),
            iconButton("Delete " + record.name, "M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7", () => remove(record)));
        for (const control of actions.children) control.disabled = busy;
        row.append(name,el("td",record.location || "Not specified"),el("td",(record.tags || []).join(", ")),actions); $("records").append(row);
    }
    $("count").textContent = loaded ? visible.length + " of " + records.length + " destinations" : "Catalog not loaded";
    if (!visible.length) {
        const row = el("tr"), cell = el("td", !loaded ? "Load the catalog using Refresh." : records.length ? "No matching destinations." : "No destinations yet.");
        cell.colSpan = 4; row.append(cell); $("records").append(row);
    }
}
async function refresh() {
    const data = await request("/api/destinations");
    if (!Array.isArray(data)) throw new Error("Unexpected destination list response");
    records = data; loaded = true; drawRecords();
}
function canDiscard() { return !dirty || confirm("Discard unsaved destination changes?"); }
function field(label, input) { const n = el("label",label); n.append(input); return n; }
function input(type, value) { const n = el("input"); n.type = type; n.value = value ?? ""; return n; }
function addRule(rule = {}) {
    const row = el("div"); row.className = "rule";
    const date = input("date",rule.date), week = input("number",rule.week_of_month), times = input("text",(rule.times || []).join(", "));
    date.className = "date"; week.className = "week"; week.min = 1; week.max = 5; times.className = "times"; times.placeholder = "09:00-12:00, 13:00-17:00";
    const weekdays = el("div"); weekdays.className = "days";
    for (const day of days) { const box = checkbox((rule.days || []).some(value => String(value).trim().slice(0,3).toLowerCase() === day.toLowerCase()),day,() => {dirty = true;}); box.value = day; weekdays.append(field(day,box)); }
    row.append(el("p","Weekdays (or use a specific date)"),weekdays,field("Specific date",date),field("Week of month (optional)",week),field("Time intervals",times),button("Remove rule",() => {row.remove(); dirty = true;}));
    $("hours").append(row);
}
function newId() {
    if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    return Array.from(bytes, byte => byte.toString(16).padStart(2,"0")).join("");
}
function openEditor(record = null) {
    if (busy || !canDiscard()) return;
    fill(record); $("editor-error").textContent = "";
    $("drawer").showModal(); $("name").focus();
}
function closeEditor() {
    if (busy || !canDiscard()) return;
    dirty = false; editing = null; $("drawer").close();
}
function fill(record = null) {
    editing = record ? record.id : null;
    $("editor-title").textContent = record ? "Edit destination" : "New destination";
    $("record-id").value = record?.id || newId();
    $("record-id").readOnly = !!record;
    for (const key of ["name","location","website"]) $(key).value = record?.[key] || "";
    $("tags").value = (record?.tags || []).join("\n");
    $("provider-ids").value = record?.provider_ids ? JSON.stringify(record.provider_ids,null,2) : "";
    $("provenance").value = record?.provenance ? JSON.stringify(record.provenance,null,2) : "";
    $("hours").replaceChildren(); for (const rule of record?.opening_hours || []) addRule(rule);
    dirty = false;
}
function recordFromForm() {
    const record = {id:$("record-id").value.trim(),name:$("name").value.trim()};
    for (const key of ["location","website"]) if ($(key).value.trim()) record[key] = $(key).value.trim();
    const tags = $("tags").value.split("\n").map(t => t.trim()).filter(Boolean); if (tags.length) record.tags = tags;
    for (const [id,key] of [["provider-ids","provider_ids"],["provenance","provenance"]]) if ($(id).value.trim()) {
        const value = JSON.parse($(id).value); if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(key + " must be a JSON object"); record[key] = value;
    }
    const hours = [...$("hours").children].map(row => {
        const date = row.querySelector(".date").value, week = row.querySelector(".week").value;
        const weekdays = [...row.querySelectorAll("input[type=checkbox]:checked")].map(n => n.value);
        if (date && (weekdays.length || week)) throw new Error("Use either a date or weekdays with optional week of month.");
        if (!date && !weekdays.length) throw new Error("Select weekdays or a date for every opening rule.");
        return {...(date ? {date} : {days:weekdays}), ...(week ? {week_of_month:Number(week)} : {}), times:row.querySelector(".times").value.split(",").map(t=>t.trim()).filter(Boolean)};
    });
    const original = records.find(r => r.id === editing);
    if (hours.length || original?.opening_hours?.length === 0) record.opening_hours = hours;
    if (!tags.length && original?.tags?.length === 0) record.tags = [];
    return record;
}
function remove(record) {
    if (!confirm("Delete " + record.name + "? Plans referencing this destination may stop working.")) return;
    if (editing === record.id && !canDiscard()) return;
    run(async () => {await request("/api/destinations/"+encodeURIComponent(record.id),"DELETE"); if (editing === record.id) {dirty = false; editing = null; $("drawer").close();} notice("Deleted " + record.name); await refresh();});
}
$("search").addEventListener("input",drawRecords);
$("new").addEventListener("click",()=>openEditor());
$("reload").addEventListener("click",()=>run(async()=>{await refresh();notice("Catalog loaded.");}));
for(const id of ["close","cancel"]) $(id).addEventListener("click",closeEditor);
$("drawer").addEventListener("cancel",event=>{event.preventDefault();closeEditor();});
$("editor").addEventListener("input",()=>{dirty=true;});
$("add-hours").addEventListener("click",()=>{addRule();dirty=true;});
$("editor").addEventListener("submit",event=>{event.preventDefault();run(async()=>{
    const record=recordFromForm();
    await request(editing?"/api/destinations/"+encodeURIComponent(editing):"/api/destinations",editing?"PUT":"POST",record);
    dirty=false; editing=null; $("drawer").close(); notice("Saved "+record.name); await refresh();
});});
window.addEventListener("beforeunload",event=>{if(dirty){event.preventDefault();event.returnValue="";}});
run(async()=>{await refresh();notice("Catalog loaded.");});
