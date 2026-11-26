"use strict";
const $ = id => document.getElementById(id);
let map, layer, markers, selected;
let collisionFrame;

function scheduleLabels() {
    cancelAnimationFrame(collisionFrame);
    collisionFrame = requestAnimationFrame(() => {
        if (!markers) return;
        const visible = [];
        markers.eachLayer(marker => {
            const tooltip = marker.getTooltip();
            const node = tooltip && tooltip.getElement();
            if (node && node.isConnected) visible.push({marker, node});
        });
        visible.sort((a, b) => Number(b.marker === selected) - Number(a.marker === selected));
        const occupied = [];
        for (const {marker, node} of visible) {
            const rect = node.getBoundingClientRect();
            const overlaps = occupied.some(other => rect.left < other.right + 4 && rect.right > other.left - 4 && rect.top < other.bottom + 4 && rect.bottom > other.top - 4);
            const show = marker === selected || !overlaps;
            node.style.visibility = show ? 'visible' : 'hidden';
            if (show) occupied.push(rect);
        }
    });
}

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
    markers = L.markerClusterGroup ? L.markerClusterGroup({maxClusterRadius: 45, spiderfyOnMaxZoom: true, showCoverageOnHover: false}) : L.featureGroup();
    markers.addTo(map);
    map.on("moveend zoomend resize tooltipopen", scheduleLabels);
    markers.on("animationend spiderfied unspiderfied", scheduleLabels);
}
function display(data) {
    const route = data.route;
    $("totals").replaceChildren();
    $("visits").replaceChildren();
    $("omitted").replaceChildren();
    $("external").hidden = true;
    $("external").removeAttribute("href");
    if (layer) layer.clearLayers();
    if (markers) markers.clearLayers();
    selected = null;
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
    const groups = new Map();
    route.visits.forEach((visit, index) => {
        const point = coordinate(visit.resolved_location);
        if (!point) return;
        const key = point.join(",");
        if (!groups.has(key)) groups.set(key, {point, visits: []});
        groups.get(key).visits.push({visit, index});
    });
    if (markers) for (const group of groups.values()) {
        const names = [...new Set(group.visits.map(entry => entry.visit.name))];
        const label = group.visits.map(entry => entry.index + 1).join(" / ") + " — " + names.join(" / ") + (group.visits.length > 1 ? " (" + group.visits.map(entry => entry.visit.role).join(" / ") + ")" : "");
        const marker = L.marker(group.point, {title: label});
        marker.bindTooltip(element("span", label), {permanent: true, direction: "auto"});
        const popup = document.createElement("div");
        for (const {visit, index} of group.visits) popup.append(element("div", (index + 1) + ". " + visit.name + " — " + visit.role + " — " + visit.location));
        marker.bindPopup(popup);
        marker.on("click", () => {selected = marker; scheduleLabels();});
        group.marker = marker;
        markers.addLayer(marker);
    }
    route.visits.forEach((visit, index) => {
        const item = document.createElement("li");
        const title = element("button", visit.name + " (" + visit.role + ")");
        title.disabled = true;
        const point = coordinate(visit.resolved_location);
        if (markers && point) {
            const marker = groups.get(point.join(",")).marker;
            title.disabled = false;
            title.addEventListener("click", () => {
                selected = marker;
                const reveal = () => {marker.openPopup(); scheduleLabels();};
                if (markers.zoomToShowLayer) markers.zoomToShowLayer(marker, reveal);
                else {map.setView(point, Math.max(map.getZoom(), 14)); reveal();}
            });
        }
        item.append(title, element("div", visit.location),
            element("div", "Arrival " + time(visit.arrival, route.timezone) + " · Service " + time(visit.service_start, route.timezone) + " · Departure " + time(visit.departure, route.timezone)),
            element("div", "Travel " + duration(visit.travel_seconds) + " · Wait " + duration(visit.waiting_seconds) + " · Visit " + duration(visit.service_seconds)));
        $("visits").append(item);
    });
    if (layer) {
        const bounds = layer.getBounds();
        bounds.extend(markers.getBounds());
        if (bounds.isValid()) map.fitBounds(bounds, {padding: [40, 40], maxZoom: 15});
        scheduleLabels();
    }
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
    const destinations = await request("/api/destinations");
    const byId = new Map(destinations.map(record => [record.id, record]));
    const preview = $("preview");
    preview.replaceChildren();
    const endpoint = (role, node) => element("li", role + ": " + (node.name || node.location) + " — " + node.location + " — " + (Array.isArray(node.time_window) ? node.time_window.join(" to ") : JSON.stringify(node.time_window)));
    preview.append(endpoint("Start", plan.start));
    for (const stop of plan.stops) {
        const record = byId.get(stop.destination_id);
        preview.append(element("li", (record ? record.name : stop.destination_id + " (missing destination)") + (record && record.location ? " — " + record.location : "") + " — " + (stop.service_minutes ?? 0) + " min — " + (stop.required === false ? "Optional (priority " + (stop.priority ?? 3) + ")" : "Required")));
    }
    preview.append(endpoint("End", plan.end));
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
