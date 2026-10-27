"""Erzeugt die abfragbaren Dateien unter v1/ aus source/.

    python build.py

source/ ist die Quelle der Wahrheit. v1/ wird nur von diesem Skript geschrieben und danach
nicht mehr verändert: wer Daten ändern will, legt v2/ an, damit laufende Agenten und
Aufgabensätze stabil bleiben.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
VERSION = "v1"
OUT = ROOT / VERSION
FIRST_DAY = date(2026, 10, 26)
LAST_DAY = date(2026, 11, 8)

SLUGS = {"Ulm": "ulm", "München": "muenchen"}


def write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")


def days():
    day = FIRST_DAY
    while day <= LAST_DAY:
        yield day.isoformat()
        day += timedelta(days=1)


def parse_ics(text: str) -> list[dict]:
    text = re.sub(r"\r?\n[ \t]", "", text)  # gefaltete Zeilen zusammenführen
    events = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        fields = {}
        for name, params, value in re.findall(r"^([A-Z]+)((?:;[^:]*)?):(.*)$", block, re.M):
            fields[name] = (params, value.strip())
        start_params, start = fields["DTSTART"]
        _, end = fields.get("DTEND", ("", ""))
        all_day = "VALUE=DATE" in start_params
        events.append(
            {
                "id": fields["UID"][1].split("@")[0],
                "date": f"{start[0:4]}-{start[4:6]}-{start[6:8]}",
                "start": None if all_day else f"{start[9:11]}:{start[11:13]}",
                "end": None if all_day or not end else f"{end[9:11]}:{end[11:13]}",
                "all_day": all_day,
                "title": fields.get("SUMMARY", ("", ""))[1],
                "location": fields.get("LOCATION", ("", ""))[1] or None,
            }
        )
    return events


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)

    # Kalender: jeder Tag im Zeitraum existiert, ein freier Tag ist eine leere Liste
    ics = (SOURCE / "calendar.ics").read_text("utf-8")
    events = parse_ics(ics)
    (OUT / "calendar.ics").parent.mkdir(parents=True, exist_ok=True)
    (OUT / "calendar.ics").write_text(ics, "utf-8")
    for day in days():
        day_events = sorted(
            (e for e in events if e["date"] == day), key=lambda e: (not e["all_day"], e["start"] or "")
        )
        write(OUT / "calendar" / f"{day}.json", {"date": day, "events": day_events})

    # Wetter: nur Tage mit Vorhersage, sonst 404
    weather = json.loads((SOURCE / "weather.json").read_text("utf-8"))
    for city, forecast in weather.items():
        for day, values in forecast.items():
            write(OUT / "weather" / SLUGS[city] / f"{day}.json", {"city": city, "date": day, **values})

    # Fahrplan: nur Strecken und Tage mit Verbindungen, sonst 404
    transit = json.loads((SOURCE / "transit.json").read_text("utf-8"))
    routes = []
    for route, connections in transit.items():
        origin, destination = route.split("->")
        routes.append([SLUGS[origin], SLUGS[destination]])
        for day in sorted({c["date"] for c in connections}):
            write(
                OUT / "transit" / SLUGS[origin] / SLUGS[destination] / f"{day}.json",
                {
                    "from": origin,
                    "to": destination,
                    "date": day,
                    "connections": [
                        {k: v for k, v in c.items() if k != "date"} for c in connections if c["date"] == day
                    ],
                },
            )

    # Notizen: Index plus eine Markdown-Datei pro Notiz
    notes = []
    for path in sorted((SOURCE / "notes").glob("*.md")):
        text = path.read_text("utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        (OUT / "notes").mkdir(parents=True, exist_ok=True)
        (OUT / "notes" / path.name).write_text(text, "utf-8")
        notes.append({"id": path.stem, "date": path.stem[:10], "title": title, "path": f"notes/{path.name}"})
    write(OUT / "notes" / "index.json", {"notes": notes})

    # Kontext: aktueller Zeitpunkt und Signale für proaktives Verhalten
    shutil.copy(SOURCE / "context.json", OUT / "context.json")

    write(
        OUT / "index.json",
        {
            "version": VERSION,
            "days": {"first": FIRST_DAY.isoformat(), "last": LAST_DAY.isoformat()},
            "cities": {slug: name for name, slug in SLUGS.items()},
            "routes": routes,
            "endpoints": {
                "calendar_day": "calendar/{date}.json",
                "calendar_ics": "calendar.ics",
                "weather": "weather/{city}/{date}.json",
                "transit": "transit/{from}/{to}/{date}.json",
                "notes_index": "notes/index.json",
                "note": "notes/{id}.md",
                "context": "context.json",
            },
        },
    )
    print(f"{VERSION}: {sum(1 for p in OUT.rglob('*') if p.is_file())} Dateien")


if __name__ == "__main__":
    build()
