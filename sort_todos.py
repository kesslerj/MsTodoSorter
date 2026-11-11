"""Einkaufsliste in MS To Do sortieren, direkt über die Graph-API.

Rückfalloption fürs Handy. Normal sortiert Home Assistant per Knopf, mit
derselben Logik (sortierung.py) und denselben Regeln (sortierregeln.yaml).
"""

import os
import urllib.parse
from datetime import date, datetime

import pytz
import requests
from dotenv import load_dotenv

from auth import get_access_token
from sortierung import lade_regeln, plan

load_dotenv()

access_token = get_access_token()
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}

LIST_ID = os.getenv("LIST_ID")
UNSORTIERT_DATEI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unsortiert.txt")


def tasks_url(folder_id):
    encoded = urllib.parse.quote(folder_id, safe="")
    return f"https://graph.microsoft.com/beta/me/outlook/taskFolders('{encoded}')/tasks"


def get_all_tasks(folder_id):
    url = (
        f"{tasks_url(folder_id)}?$select=id,subject,status,dueDateTime"
        f"&$filter=status ne 'completed'&$top=999"
    )
    resp = requests.get(url, headers=headers)
    print(f"  GET Status: {resp.status_code}")
    return resp.json().get("value", [])


def due_body(task):
    if not task.get("dueDateTime"):
        return None
    dt_str = task["dueDateTime"]["dateTime"]
    tz = task["dueDateTime"]["timeZone"]
    if tz == "UTC":
        # UTC-Zeit in Europe/Berlin umrechnen und nur das Datum nehmen
        dt_utc = datetime.fromisoformat(dt_str.split(".")[0]).replace(tzinfo=pytz.utc)
        dt_berlin = dt_utc.astimezone(pytz.timezone("Europe/Berlin"))
        dt_str = dt_berlin.date().isoformat() + "T12:00:00.0000000"
    return {"dateTime": dt_str, "timeZone": tz}


def anlegen(folder_id, subject, task=None):
    body = {"subject": subject}
    due = due_body(task) if task else None
    if due:
        body["dueDateTime"] = due
    resp = requests.post(tasks_url(folder_id), headers=headers, json=body)
    if resp.status_code not in (200, 201):
        print(f"      POST fehlgeschlagen {resp.status_code}: {resp.text[:200]}")
    return resp.status_code


def loeschen(task_ids):
    # Batch-Request: bis zu 20 Requests pro Batch
    for i in range(0, len(task_ids), 20):
        chunk = task_ids[i:i + 20]
        body = {
            "requests": [
                {"id": str(j), "method": "DELETE", "url": f"/me/outlook/tasks/{t}"}
                for j, t in enumerate(chunk)
            ]
        }
        resp = requests.post("https://graph.microsoft.com/beta/$batch", headers=headers, json=body)
        print(f"   [BATCH {resp.status_code}] {len(chunk)} Tasks gelöscht")


def delete_completed_tasks(folder_id):
    url = f"{tasks_url(folder_id)}?$select=id,subject&$filter=status eq 'completed'&$top=999"
    completed = requests.get(url, headers=headers).json().get("value", [])
    print(f"   {len(completed)} erledigte Tasks gefunden")
    loeschen([t["id"] for t in completed])


def unsortiert_protokollieren(texte):
    """Einträge ohne Zuordnung anhängen, um sie in die Regeln aufzunehmen."""
    if not texte:
        return
    with open(UNSORTIERT_DATEI, "a", encoding="utf-8") as f:
        for t in texte:
            f.write(f"{date.today().isoformat()}\t{t}\n")
    print(f"   {len(texte)} Einträge ohne Zuordnung in {UNSORTIERT_DATEI}")


def main():
    regeln = lade_regeln()

    print("\n🗑️ Lösche erledigte Tasks...")
    delete_completed_tasks(LIST_ID)

    print("📋 Lade Einkaufsliste...")
    all_tasks = get_all_tasks(LIST_ID)
    print(f"   {len(all_tasks)} Tasks geladen")
    nach_id = {t["id"]: t for t in all_tasks}

    p = plan([{"summary": t["subject"], "uid": t["id"]} for t in all_tasks], regeln)
    print(f"   {p['zahlen']}")

    print("\n🔀 Sortiere...")
    for e in p["anlegen"]:
        task = nach_id.get(e.get("alt"))
        status = anlegen(LIST_ID, e["summary"], task)
        if task and status in (200, 201):
            loeschen([task["id"]])
        print(f"   [POST {status}] {e['summary']}")

    if p["loeschen"]:
        print(f"\n🧹 {len(p['loeschen'])} doppelte Einträge und alte Trenner löschen")
        loeschen(p["loeschen"])

    unsortiert_protokollieren(p["unsortiert"])
    print("\n✅ EINKAUFSLISTE SORTIERT!")


if __name__ == "__main__":
    main()
