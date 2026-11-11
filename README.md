# MS Todo Einkaufsliste sortieren

Sortiert die Einkaufsliste in MS To Do nach Läden und Regalreihenfolge: oben UNSORTIERT, dann ALDI und EDEKA, jeweils mit Trennzeile. Erledigte Einträge werden gelöscht, doppelte ohne Mengenangabe zusammengeführt.

Im Alltag sortiert Home Assistant per Knopf, mit derselben Logik und denselben Regeln. Dieses Skript ist die Rückfalloption fürs Handy.

## Aufbau

- `sortierregeln.yaml`: Läden mit ihren Einträgen, Laden-Präfixe, Alexa-Schreibweisen, Mengenangaben. **Quelle ist die Datei in der HA-Config** (`einkaufsliste/sortierregeln.yaml`), hier liegt eine Kopie. Nach Änderungen dort die Kopie hier nachziehen.
- `sortierung.py`: die Zuordnung ohne Zugriff auf MS To Do. Das Gegenstück in HA ist `custom_templates/einkaufsliste.jinja`.
- `testfaelle.py`: Testfälle, die für beide gelten. In HA werden sie über die Template-API gegen das Jinja-Makro geprüft.
- `sort_todos.py`: liest die Liste über die Graph-API, sortiert und schreibt Einträge ohne Zuordnung nach `unsortiert.txt`.

## Run

    pip install -r requirements.txt

File `.env`:

    CLIENT_ID=...
    LIST_ID=...

`CLIENT_ID` ist die App-Registrierung „ToDoSorter“ (nur persönliche Konten). Beim ersten Lauf fragt `auth.py` per Device-Login an, danach hält `token_cache.json` den Refresh-Token.

    python sort_todos.py

## Tests

    pip install -r requirements-dev.txt
    python -m pytest

## Todos
- Dokumentieren, wo die List-Id herkommt
