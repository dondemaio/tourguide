"use strict";
const $ = id => document.getElementById(id);
let map, layer;

function element(tag, text) {
    const node = document.createElement(tag);
    node.textContent = text;
    return node;
}
async function request(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data));
    }
    return data;
}
function duration(seconds) {
    const minutes = Math.floor(seconds / 60);
    return Math.floor(minutes / 60) + "h " + (minutes % 60) + "m " + (seconds % 60) + "s";
}
function time(value, timezone) {
    return new Intl.DateTimeFormat("en-GB", {timeZone: timezone, hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"}).format(new Date(value));
}
function coordinate(value) {
    if (typeof value !== "string") return null;
    const parts = value.split(",");
    if (parts.length !== 2 || parts.some(p => !p.trim())) return null;
    const [lon, lat] = parts.map(Number);
    return Number.isFinite(lon) && Number.isFinite(lat) && Math.abs(lon) <= 180 && Math.abs(lat) <= 90 ? [lat, lon] : null;
}
function initializeMap() {
    if (!window.L) {
        $("map-note").textContent = "Map library unavailable. The itinerary still works.";
        return;
    }
    map = L.map("map").setView([47, 8], 7);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    layer = L.featureGroup().addTo(map);
}
function display(data) {
    const route = data.route;
    $("totals").replaceChildren();
    $("visits").replaceChildren();
    $("omitted").replaceChildren();
    $("external").hidden = true;
    $("external").removeAttribute("href");
    if (layer) layer.clearLayers();
    $("map-note").textContent = map ? (data.geometry_warning || "") : "Map library unavailable. The itinerary still works.";
    for (const [label, key] of [["Elapsed", "elapsed_seconds"], ["Travel", "travel_seconds"], ["Waiting", "waiting_seconds"], ["Service", "service_seconds"]]) {
        const card = element("div", label);
        card.append(element("strong", duration(route.totals[key])));
        $("totals").append(card);
    }
    if (layer && data.geometry) {
        try {
            L.geoJSON(data.geometry, {style: {color: "#176b69", weight: 5}}).addTo(layer);
        } catch {
            $("map-note").textContent = "Road geometry could not be displayed.";
        }
    }
    route.visits.forEach((visit, index) => {
        const item = document.createElement("li");
        const title = element("button", visit.name + " (" + visit.role + ")");
        title.disabled = true;
        const point = coordinate(visit.resolved_location);
        if (layer && point) {
            const marker = L.marker(point, {title: (index + 1) + ". " + visit.name}).addTo(layer);
            marker.bindTooltip(element("span", (index + 1) + ". " + visit.name), {permanent: true, direction: "auto"});
            marker.bindPopup(element("div", visit.name + " — " + visit.location));
            title.disabled = false;
            title.addEventListener("click", () => {map.setView(point, Math.max(map.getZoom(), 14)); marker.openPopup();});
        }
        item.append(title, element("div", visit.location),
            element("div", "Arrival " + time(visit.arrival, route.timezone) + " · Service " + time(visit.service_start, route.timezone) + " · Departure " + time(visit.departure, route.timezone)),
            element("div", "Travel " + duration(visit.travel_seconds) + " · Wait " + duration(visit.waiting_seconds) + " · Visit " + duration(visit.service_seconds)));
        $("visits").append(item);
    });
    if (layer && layer.getBounds().isValid()) map.fitBounds(layer.getBounds(), {padding: [40, 40], maxZoom: 15});
    for (const visit of route.omitted_visits || []) {
        const reason = visit.reason === "no_fitting_opening_window" ? "No fitting opening window" : "Not selected by solver";
        $("omitted").append(element("li", visit.name + " — " + reason + " (priority " + visit.priority + ")"));
    }
    if (!$("omitted").children.length) $("omitted").append(element("li", "None"));
    if (typeof data.rendering === "string") {
        try {
            const url = new URL(data.rendering);
            if (url.protocol === "https:" && ["www.google.com", "maps.google.com"].includes(url.hostname) && url.pathname.startsWith("/maps")) {
                $("external").href = url.href;
                $("external").hidden = false;
            }
        } catch {}
    }
}
async function loadPlan() {
    const plan = await request("/api/plans/default");
    $("plan").textContent = plan.stops.length + " planned visits · " + plan.timezone + " · " + plan.start.time_window[0];
    return plan;
}
function status(message, error = false) {
    $("status").textContent = message;
    $("status").classList.toggle("error", error);
}
async function calculate() {
    $("calculate").disabled = true;
    status("Calculating route…");
    try {
        const plan = await loadPlan();
        const data = await request("/api/routes", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(plan)});
        display(data);
        status("Route calculated · " + data.route.timezone + " · " + data.route.solver_status);
    } catch (error) {
        status("Calculation failed: " + error.message + ". Any displayed result is from the previous calculation.", true);
    } finally {
        $("calculate").disabled = false;
    }
}
initializeMap();
$("calculate").addEventListener("click", calculate);
loadPlan().then(() => {$("calculate").disabled = false;}).catch(error => {
    status("Could not load configured plan: " + error.message, true);
    $("calculate").disabled = false;
});
