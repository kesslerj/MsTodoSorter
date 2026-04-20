import requests
from datetime import datetime
import pytz
import urllib.parse
import re
from dotenv import load_dotenv
import os
import msal

from auth import get_access_token

load_dotenv()

access_token = get_access_token()
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

LIST_ID = os.getenv("LIST_ID")

ALDI = [
    # Obst und Gemüse
    "Obst", 
    "Bananen",
    "Zucchini",
    "Tomaten",
    "Snacktomaten",
    "Gurke",
    "Paprika", 
    "Schalotten",
    "Ingwer",
    "Rosenkohl",
    "Brokkoli",
    "Senf",
    # Konserven etc.
    "Apfelmus",
    "Senf",
    "Kokosnussmilch",
    # Brot und Kaffee
    "Eiweißbrot", 
    "Kaffee",
    # Schoki, Kekse, Nudeln, Reis
    "Schoki",
    "Reis",
    # Kühltheke
    "Aldi Hähnchen-/Putenaufschnitt",
    "Salami",
    "Gouda Aldi",
    "Erzherzog Johann",
    "Parmesan",
    "Stinkekäse",
    "Eiweiß Schokomousse", 
    "Zero Getränke"
    # Haushalt
    "Klopapier",
    "Küchenrolle",
    "Zahnpasta",
    "Frischhaltefolie",
    "Müllbeutel",
    "Biomüllbeutel"
]
EDEKA = [
    # Konserven
    "Passierte Tomaten",
    # Backen
    "Mehl",
    "Backpulver",
    # Brot
    "Paniermehl",
    "Puffies", 
    "Roggen Vollkornbrot GG",
    # Obst, Gemüse und Bio
    "Möhren", 
    "Milch", 
    "Joghurt",
    "GG Erdnüsse ungeschält",
    # Pasta etc.
    "Limettensaft,
    # Fleischregal
    "GG Oliven",
    "Schinken",
    "Schinkenwürfel",
    "Bacon",
    # MoPro 
    "Krautsalat", 
    "Streukäse",
    "Mozzarella",
    "Butter",
    "Streichzart",
    "Frischkäse", 
    "körniger Frischkäse",
    "Eiweißjoghurt",
    "Magerquark", 
    "Sahne",
    "Schmand",
    "Cremefine",
    "Skyr", 
    # Theke
    "Leberwurst / Aufschnitt", 
    "Käse",
    "Käsepapier",
    # TK
    "TK Laugenstangen",
    "TK Himbeeren",
    "Edeka Frosta"
]

SEPARATOR_UNSORTIERT = "----------- UNSORTIERT -----------"
SEPARATOR_ALDI = "----------- ALDI -----------"
SEPARATOR_EDEKA = "----------- EDEKA -----------"
SEPARATORS = {SEPARATOR_UNSORTIERT, SEPARATOR_ALDI, SEPARATOR_EDEKA}


def matches_template(subject, template):
    s = subject.lower().strip()
    t = template.lower()
    # Matcht: exakt, "Joghurt X", "Joghurt 3x", "2 Joghurt", "2x Joghurt",
    #         "Joghurt 2,49", "Joghurt 2,49€", "Joghurt 2,49 €"
    pattern = rf"^(\d+x?\s+)?{re.escape(t)}(\s+\d*x?)?(\s+\d+[.,]\d+\s*€?)?$"
    return bool(re.match(pattern, s))


def find_category_and_position(subject):
    s = subject.strip()
    for i, v in enumerate(ALDI):
        if matches_template(s, v):
            return "aldi", i
    for i, v in enumerate(EDEKA):
        if matches_template(s, v):
            return "edeka", i
    return "unsortiert", 0


def get_all_tasks(folder_id):
    encoded = urllib.parse.quote(folder_id, safe='')
    url = (
        f"https://graph.microsoft.com/beta/me/outlook/taskFolders('{encoded}')/tasks"
        f"?$select=id,subject,status,dueDateTime"
        f"&$filter=status ne 'completed'"
        f"&$top=999"
    )
    resp = requests.get(url, headers=headers)
    print(f"  GET Status: {resp.status_code}")
    return resp.json().get("value", [])


def recreate_task(folder_id, task):
    encoded = urllib.parse.quote(folder_id, safe='')
    body = {"subject": task["subject"]}
    
    if task.get("dueDateTime"):
        dt_str = task["dueDateTime"]["dateTime"]
        tz = task["dueDateTime"]["timeZone"]

        if tz == "UTC":
            # UTC-Zeit in Europe/Berlin umrechnen und nur das Datum nehmen
            dt_utc = datetime.fromisoformat(dt_str.split(".")[0]).replace(tzinfo=pytz.utc)
            dt_berlin = dt_utc.astimezone(pytz.timezone("Europe/Berlin"))
            dt_str = dt_berlin.date().isoformat() + "T12:00:00.0000000"

        body["dueDateTime"] = {"dateTime": dt_str, "timeZone": tz}

    post_url = f"https://graph.microsoft.com/beta/me/outlook/taskFolders('{encoded}')/tasks"
    resp = requests.post(post_url, headers=headers, json=body)
    status = resp.status_code

    if status in (200, 201):
        del_resp = requests.delete(
            f"https://graph.microsoft.com/beta/me/outlook/tasks/{task['id']}",
            headers=headers
        )
        return status, del_resp.status_code
    else:
        print(f"      POST fehlgeschlagen {status}: {resp.text[:200]}")
        return status, None


def get_or_create_separator(folder_id, all_tasks, subject):
    existing = next((t for t in all_tasks if t["subject"] == subject), None)
    if existing:
        return existing, False  # False = muss noch neu erstellt werden
    encoded = urllib.parse.quote(folder_id, safe='')
    resp = requests.post(
        f"https://graph.microsoft.com/beta/me/outlook/taskFolders('{encoded}')/tasks",
        headers=headers,
        json={"subject": subject}
    )
    print(f"   [CREATED] Separator '{subject}'")
    return resp.json(), True  # True = bereits frisch erstellt


def delete_completed_tasks(folder_id):
    encoded = urllib.parse.quote(folder_id, safe='')
    url = (
        f"https://graph.microsoft.com/beta/me/outlook/taskFolders('{encoded}')/tasks"
        f"?$select=id,subject&$filter=status eq 'completed'&$top=999"
    )
    completed = requests.get(url, headers=headers).json().get("value", [])
    print(f"   {len(completed)} erledigte Tasks gefunden")

    if not completed:
        return

    # Batch-Request: bis zu 20 Requests pro Batch
    batch_headers = {**headers, "Content-Type": "application/json"}
    for i in range(0, len(completed), 20):
        chunk = completed[i:i+20]
        batch_body = {
            "requests": [
                {"id": str(j), "method": "DELETE", "url": f"/me/outlook/tasks/{t['id']}"}
                for j, t in enumerate(chunk)
            ]
        }
        resp = requests.post(
            "https://graph.microsoft.com/beta/$batch",
            headers=batch_headers,
            json=batch_body
        )
        print(f"   [BATCH {resp.status_code}] {len(chunk)} Tasks gelöscht")


print("\n🗑️ Lösche erledigte Tasks...")
delete_completed_tasks(LIST_ID)

print("📋 Lade Einkaufsliste...")
all_tasks = get_all_tasks(LIST_ID)
print(f"   {len(all_tasks)} Tasks geladen")

unsortiert = []
aldi_tasks = []
edeka_tasks = []

for task in all_tasks:
    subj = task["subject"]
    if subj in SEPARATORS:
        continue
    cat, pos = find_category_and_position(subj)
    if cat == "aldi":
        aldi_tasks.append((pos, task))
    elif cat == "edeka":
        edeka_tasks.append((pos, task))
    else:
        unsortiert.append((0, task))

aldi_tasks.sort(key=lambda x: x[0])
edeka_tasks.sort(key=lambda x: x[0])

print(f"\n   Unsortiert: {len(unsortiert)}")
print(f"   Aldi: {len(aldi_tasks)}")
print(f"   Edeka: {len(edeka_tasks)}")

print("\n🔀 Sortiere...")

# Edeka zuerst erstellen → landet ganz unten
for _, task in reversed(edeka_tasks):
    post_s, del_s = recreate_task(LIST_ID, task)
    print(f"   [POST {post_s} | DEL {del_s}] [Edeka] {task['subject']}")

sep_edeka, already_created = get_or_create_separator(LIST_ID, all_tasks, SEPARATOR_EDEKA)
if not already_created:
    post_s, del_s = recreate_task(LIST_ID, sep_edeka)
    print(f"   [POST {post_s} | DEL {del_s}] {SEPARATOR_EDEKA}")

for _, task in reversed(aldi_tasks):
    post_s, del_s = recreate_task(LIST_ID, task)
    print(f"   [POST {post_s} | DEL {del_s}] [Aldi] {task['subject']}")

sep_aldi, already_created = get_or_create_separator(LIST_ID, all_tasks, SEPARATOR_ALDI)
if not already_created:
    post_s, del_s = recreate_task(LIST_ID, sep_aldi)
    print(f"   [POST {post_s} | DEL {del_s}] {SEPARATOR_ALDI}")

for _, task in reversed(unsortiert):
    post_s, del_s = recreate_task(LIST_ID, task)
    print(f"   [POST {post_s} | DEL {del_s}] [Unsortiert] {task['subject']}")

sep_unsortiert, already_created = get_or_create_separator(LIST_ID, all_tasks, SEPARATOR_UNSORTIERT)
if not already_created:
    post_s, del_s = recreate_task(LIST_ID, sep_unsortiert)
    print(f"   [POST {post_s} | DEL {del_s}] {SEPARATOR_UNSORTIERT}")

print("\n✅ EINKAUFSLISTE SORTIERT!")
print(f"   {SEPARATOR_UNSORTIERT} ({len(unsortiert)} Items)")
print(f"   {SEPARATOR_ALDI} ({len(aldi_tasks)} Items)")
print(f"   {SEPARATOR_EDEKA} ({len(edeka_tasks)} Items)")
