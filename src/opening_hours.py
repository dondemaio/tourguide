import re

from dateutil.parser import isoparse


def parse_opening_hours(oh_strings, base_dt):
    """
    Convert opening_hours like ['Mo-Fr 08:00-12:00', ...] to time windows for a specific day.
    base_dt: datetime of route start (used as reference for relative seconds)
    Returns: list of tuples (start_sec, end_sec)
    """
    """
    - id: "Grünig + Elmiger AG"
      location: "Industriestrasse 22, 6102 Malters"
      opening_hours:
        - "Mo-Fr 08:00-12:00"
        - "Mo-Fr 13:30-17:30"
    """
    windows = []
    for oh in oh_strings:
        # naive parsing for a single day: '08:00-12:00'
        m = re.match(r'(\d{2}):(\d{2})-(\d{2}):(\d{2})', oh)
        if m:
            sh, sm, eh, em = map(int, m.groups())
            start_dt = base_dt.replace(hour=sh, minute=sm, second=0)
            end_dt = base_dt.replace(hour=eh, minute=em, second=0)
            start_sec = int((start_dt - base_dt).total_seconds())
            end_sec = int((end_dt - base_dt).total_seconds())
            windows.append((start_sec, end_sec))
    return windows


# vämuätli chli quatsch...
def nodes_to_opening_hours(nodes):
    result = []
    for n in nodes:
        entry = {"id": n["id"], "location": n["location"]}
        if "time_window" in n:
            start_dt, end_dt = n["time_window"]
            # Keep as datetime style for start/end nodes, otherwise convert to hh:mm
            if n["id"] in ("start", "end"):
                entry["time_window"] = [start_dt, end_dt]
            else:
                start = isoparse(start_dt).strftime("%H:%M")
                end = isoparse(end_dt).strftime("%H:%M")
                entry["opening_hours"] = [{"days": ["Mon"], "times": [f"{start}-{end}"]}]
        elif "time_windows" in n:
            oh = []
            for tw in n["time_windows"]:
                start = isoparse(tw[0]).strftime("%H:%M")
                end = isoparse(tw[1]).strftime("%H:%M")
                oh.append({"days": ["Mon"], "times": [f"{start}-{end}"]})
            entry["opening_hours"] = oh
        result.append(entry)
    return result
