# Initial Web UI

Start using docker/compose-up-build.sh and open http://localhost:8000/.
The configured YAML plan is loaded automatically. Click Calculate route to calculate the current file, inspect the itinerary, totals, omitted visits and map. Click a visit name to focus its marker.

The API retains the configured rendering output. For OSRM cost calculations it additionally supplies GeoJSON road geometry (reusing the configured rendering if already GeoJSON). Other cost providers currently show markers only when coordinates are available. Geometry failures are reported without discarding the itinerary when the configured renderer succeeds. No straight lines are presented as road geometry.

Leaflet 1.9.4 is loaded from unpkg with integrity checks; OpenStreetMap tiles are requested from the browser. Internet access is required for the map library and basemap, and tile requests disclose the viewed map area to the tile service. The itinerary works without Leaflet. No separate frontend build or container is required.

Plan editing, saved plans and destination management UI remain later roadmap tasks. This is a trusted local application, not a public deployment.
