# agentic-interaction-data

Mock-Daten für die Übung *Agentic Interaction* (WS 2026/27, Universität Ulm): Kalender, Fahrplan,
Wetter, Notizen und Kontext für zwei erfundene Wochen (26.10.–08.11.2026). Alle Daten sind
erfunden, es gibt keine personenbezogenen Daten.

Die Daten werden **abgefragt, nicht kopiert**. Eure Werkzeuge lesen sie per HTTP-GET.

## Basis-URL

```
DATA_BASE_URL=https://jhbelz.github.io/agentic-interaction-data/v1
```

Die Variable gehört in eure `.env`. Kein Schlüssel, keine Anmeldung.

## Endpunkte

| Pfad unter `DATA_BASE_URL` | Inhalt |
|---|---|
| `index.json` | Zeitraum, Städte, Strecken, Liste der Endpunkte |
| `calendar/{date}.json` | Termine eines Tages, z. B. `calendar/2026-10-29.json` |
| `calendar.ics` | der ganze Kalender als ICS |
| `weather/{city}/{date}.json` | Wettervorhersage, z. B. `weather/ulm/2026-10-29.json` |
| `transit/{from}/{to}/{date}.json` | Zugverbindungen, z. B. `transit/ulm/muenchen/2026-10-29.json` |
| `notes/index.json` | Liste der Notizen |
| `notes/{id}.md` | eine Notiz als Markdown |
| `context.json` | aktueller Zeitpunkt, Ruhezeiten, Hinweise |

Datum immer als `YYYY-MM-DD`. Städte als Kürzel aus `index.json` (`ulm`, `muenchen`).

**HTTP 404 heißt: keine Daten.** Für jeden Tag im Zeitraum gibt es eine Kalenderdatei (ein
freier Tag hat eine leere Liste). Wetter und Verbindungen gibt es nur für einzelne Tage. Euer
Werkzeug sollte einen 404 als Ergebnis behandeln, nicht als Absturz.

## Beispiel

```python
import json, os, urllib.request

base = os.environ["DATA_BASE_URL"]
with urllib.request.urlopen(f"{base}/calendar/2026-10-29.json") as response:
    day = json.load(response)
print([event["title"] for event in day["events"]])
```

```bash
curl "$DATA_BASE_URL/weather/ulm/2026-10-29.json"
```

## Änderungen schreiben

Die Daten sind schreibgeschützt. Werkzeuge, die etwas anlegen oder ändern (zum Beispiel einen
Termin), halten ihre Änderungen lokal in eurem Repo-Ordner und committen sie nicht.

## Versionen

`v1/` ändert sich nicht mehr. Neue oder korrigierte Daten kommen als `v2/` dazu und werden in
Moodle angekündigt. So bleibt ein Lauf von heute in drei Wochen reproduzierbar.

## Ohne Netz

```bash
git clone https://github.com/jhbelz/agentic-interaction-data.git
cd agentic-interaction-data && python -m http.server 8000
# in eurer .env:
DATA_BASE_URL=http://localhost:8000/v1
```

## Für die Pflege

`source/` ist die Quelle der Wahrheit, `build.py` erzeugt daraus `v1/`. Daten nur in `source/`
ändern und eine neue Version bauen; `v1/` nie von Hand bearbeiten.
