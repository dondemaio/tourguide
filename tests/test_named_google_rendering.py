from urllib.parse import parse_qs, urlparse

from backends.google.web.render import GoogleMapsURLRenderer


def visit(name, location, role="visit", place_id=None):
    return {"name": name, "location": location, "role": role,
            "provider_ids": {"google": place_id} if place_id else {}}


def params(visits):
    return parse_qs(urlparse(GoogleMapsURLRenderer().render_visits(visits)).query)


def test_named_visits_and_private_endpoints():
    result = params([visit("Home", "Origin", "start"),
                     visit("Museum & Café", "Main Street 1"),
                     visit("Home", "Origin", "end")])
    assert result["origin"] == ["Origin"]
    assert result["destination"] == ["Origin"]
    assert result["waypoints"] == ["Museum & Café, Main Street 1"]


def test_place_ids():
    result = params([visit("Start", "Origin", "start", "a"),
                     visit("Museum", "Main Street", place_id="b"),
                     visit("Gallery", "Other Street", place_id="c"),
                     visit("End", "End", "end", "d")])
    assert result["origin_place_id"] == ["a"]
    assert result["destination_place_id"] == ["d"]
    assert result["waypoint_place_ids"] == ["b|c"]


def test_partial_ids_and_coordinates():
    result = params([visit("Start", "Origin", "start"),
                     visit("Museum", "Main Street", place_id="b"),
                     visit("Point", "8.5,47.3"),
                     visit("End", "End", "end")])
    assert "waypoint_place_ids" not in result
    assert result["waypoints"] == ["Museum, Main Street|47.3,8.5"]
