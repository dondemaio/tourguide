"use strict";
const $ = id => document.getElementById(id);
let records = [], editing = null, candidates = [], busy = false, dirty = false;
const selected = new Set(), chosen = new Set();
const days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
function el(tag, value) { const n = document.createElement(tag); if (value !== undefined) n.textContent = value; return n; }
function button(label, action) { const n = el("button", label); n.type = "button"; n.addEventListener("click", action); return n; }
function notice(message, error = false) { $("notice").textContent = message; $("notice").classList.toggle("error", error); }
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
    finally { controls.forEach(n => n.disabled = false); busy = false; drawRecords(); drawCandidates(); $("record-id").readOnly = editing !== null; }
}
function filtered() {
    const query = $("search").value.trim().toLocaleLowerCase();
    return records.filter(r => [r.name,r.id,r.location,...(r.tags || [])].join(" ").toLocaleLowerCase().includes(query))
        .sort((a,b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
}
function checkbox(checked, label, action) {
    const n = el("input"); n.type = "checkbox"; n.checked = checked; n.setAttribute("aria-label", label); n.addEventListener("change", () => action(n.checked)); return n;
}
function drawRecords() {
    const visible = filtered(); $("records").replaceChildren();
    for (const record of visible) {
        const row = el("tr"), pick = el("td"), name = el("td"), actions = el("td");
        pick.append(checkbox(selected.has(record.id), "Select " + record.name, checked => {if (checked) selected.add(record.id); else selected.delete(record.id); updateSelection();}));
        name.append(el("strong",record.name),el("br"),el("small",record.id));
        actions.append(button("Edit", () => {if (canDiscard()) fill(record);}),button("Delete", () => remove(record)));
        row.append(pick,name,el("td",record.location || "Not specified"),actions); $("records").append(row);
    }
    $("count").textContent = visible.length + " of " + records.length + " destinations";
    updateSelection();
}
function updateSelection() {
    const visible = filtered(), count = visible.filter(r => selected.has(r.id)).length;
    $("select-visible").checked = visible.length > 0 && count === visible.length;
    $("select-visible").indeterminate = count > 0 && count < visible.length;
    $("selection").textContent = selected.size + " selected (including hidden search results)";
    $("export-selected").disabled = !selected.size;
}
async function refresh() {
    records = await request("/api/destinations");
    const ids = new Set(records.map(r => r.id));
    for (const id of selected) if (!ids.has(id)) selected.delete(id);
    drawRecords();
}
function canDiscard() { return !dirty || confirm("Discard unsaved destination changes?"); }
function field(label, input) { const n = el("label",label); n.append(input); return n; }
function input(type, value) { const n = el("input"); n.type = type; n.value = value ?? ""; return n; }
function addRule(rule = {}) {
    const row = el("div"); row.className = "rule";
    const date = input("date",rule.date), week = input("number",rule.week_of_month), times = input("text",(rule.times || []).join(", "));
    date.className = "date"; week.className = "week"; week.min = 1; week.max = 5; times.className = "times"; times.placeholder = "09:00-12:00, 13:00-17:00";
    const weekdays = el("div"); weekdays.className = "days";
    for (const day of days) { const box = checkbox((rule.days || []).includes(day),day,() => {dirty = true;}); box.value = day; weekdays.append(field(day,box)); }
    row.append(el("p","Weekdays (or use a specific date)"),weekdays,field("Specific date",date),field("Week of month (optional)",week),field("Time intervals",times),button("Remove rule",() => {row.remove(); dirty = true;}));
    $("hours").append(row);
}
function fill(record = null) {
    editing = record ? record.id : null;
    $("editor-title").textContent = record ? "Edit destination" : "New destination";
    $("record-id").value = record?.id || crypto.randomUUID();
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
    if (hours.length) record.opening_hours = hours;
    return record;
}
function remove(record) {
    if (!confirm("Delete " + record.name + "? Plans referencing this destination may stop working.")) return;
    if (editing === record.id && !canDiscard()) return;
    run(async () => {await request("/api/destinations/"+encodeURIComponent(record.id),"DELETE"); if (editing === record.id) fill(); notice("Deleted " + record.name); await refresh();});
}
function drawCandidates() {
    $("candidates").replaceChildren();
    for (const candidate of candidates) {
        const row = el("tr"), pick = el("td");
        const box = checkbox(chosen.has(candidate.index),"Select candidate "+(candidate.index+1),checked=>{if(checked) chosen.add(candidate.index);else chosen.delete(candidate.index); $("commit").disabled=!chosen.size;});
        box.disabled = candidate.status !== "new"; pick.append(box);
        const detail = el("td"); detail.append(el("div",candidate.message || ""));
        if(candidate.record){const d=el("details");d.append(el("summary","Record details"),el("pre",JSON.stringify(candidate.record,null,2)));detail.append(d);}
        row.append(pick,el("td",candidate.record?.name || "Row "+(candidate.index+1)),el("td",candidate.status.replaceAll("_"," ")),detail);$("candidates").append(row);
    }
    $("select-new").disabled = !candidates.some(c=>c.status==="new");
    $("commit").disabled = !chosen.size;
}
function invalidateReview(){candidates=[];chosen.clear();$("import-summary").textContent="Review required.";drawCandidates();}
$("search").addEventListener("input",drawRecords);
$("select-visible").addEventListener("change",()=>{for(const r of filtered()) if($("select-visible").checked)selected.add(r.id);else selected.delete(r.id);drawRecords();});
for(const id of ["new","cancel"]) $(id).addEventListener("click",()=>{if(canDiscard())fill();});
$("editor").addEventListener("input",()=>{dirty=true;});
$("add-hours").addEventListener("click",()=>{addRule();dirty=true;});
$("editor").addEventListener("submit",event=>{event.preventDefault();run(async()=>{const record=recordFromForm();await request(editing?"/api/destinations/"+encodeURIComponent(editing):"/api/destinations",editing?"PUT":"POST",record);fill(record);notice("Saved "+record.name);await refresh();});});
for(const [id,only] of [["export-all",false],["export-selected",true]]) $(id).addEventListener("click",()=>run(async()=>{
    const format=$("export-format").value, content=await request("/api/export","POST",{format,...(only?{ids:[...selected]}:{})});
    const url=URL.createObjectURL(new Blob([content],{type:"text/plain;charset=utf-8"}));const a=el("a");a.href=url;a.download="destinations."+format;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}));
$("import-content").addEventListener("input",invalidateReview);$("import-format").addEventListener("change",invalidateReview);
$("import-file").addEventListener("change",()=>run(async()=>{invalidateReview();const file=$("import-file").files[0];if(!file)return;if(file.size>2000000)throw new Error("Import exceeds 2 MB");$("import-content").value=await file.text();$("import-format").value=file.name.toLowerCase().endsWith(".csv")?"csv":"yaml";}));
$("review").addEventListener("click",()=>run(async()=>{invalidateReview();candidates=await request("/api/import/review","POST",{format:$("import-format").value,content:$("import-content").value});$("import-summary").textContent=candidates.length+" candidates; "+candidates.filter(c=>c.status==="new").length+" new. Select records to add.";drawCandidates();}));
$("select-new").addEventListener("click",()=>{for(const c of candidates)if(c.status==="new")chosen.add(c.index);drawCandidates();});
$("commit").addEventListener("click",()=>run(async()=>{const results=await request("/api/import/commit","POST",{candidates,selected_indices:[...chosen]});const byIndex=new Map(results.map(c=>[c.index,c]));candidates=candidates.map(c=>byIndex.get(c.index)||c);chosen.clear();$("import-summary").textContent=results.filter(c=>c.status==="added").length+" added; "+results.filter(c=>c.status!=="added").length+" rejected.";await refresh();}));
window.addEventListener("beforeunload",event=>{if(dirty){event.preventDefault();event.returnValue="";}});
fill();run(refresh);
