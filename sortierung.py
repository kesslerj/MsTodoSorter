"""Zuordnung der Einkaufsliste zu Läden, ohne Zugriff auf MS To Do.

Die Regeln stehen in sortierregeln.yaml. Quelle ist die Datei in der
Home-Assistant-Config (einkaufsliste/sortierregeln.yaml), hier liegt eine
Kopie. Home Assistant nutzt dieselbe Logik als Jinja-Makro
(custom_templates/einkaufsliste.jinja); die Tests in test_sort_todos.py
gelten für beide.
"""

import os
import re

import yaml

REGELN_DATEI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sortierregeln.yaml")


def lade_regeln(pfad=REGELN_DATEI):
    with open(pfad, encoding="utf-8") as f:
        return yaml.safe_load(f)


def glaetten(text, regeln):
    t = re.sub(r"\s+", " ", str(text).lower()).strip()
    for alt, neu in (regeln.get("schreibweisen") or {}).items():
        t = t.replace(alt, neu)
    return t.strip()


def _zahlwoerter(regeln):
    w = "|".join(regeln["mengen"]["zahlwoerter"])
    return rf"(?:(?:{w})+)(?:\s+(?:{w})+)*"


def _einheiten(regeln):
    return "(?:" + "|".join(regeln["mengen"]["einheiten"]) + ")"


def menge_vorne(regeln):
    """Mengenangabe am Anfang samt folgendem Leerzeichen."""
    return rf"^(?:\d+(?:[.,]\d+)?|{_zahlwoerter(regeln)})\s*x?\s*(?:{_einheiten(regeln)}\.?)?\s+"


def menge_hinten(regeln):
    """Mengenangabe am Ende: "Joghurt 5x", "Sahne zwei mal", "Hack 500g"."""
    return (
        rf"\s(?:\d+(?:[.,]\d+)?\s*(?:x|mal|{_einheiten(regeln)}\.?)|x\s*\d+|"
        rf"{_zahlwoerter(regeln)}\s*mal)$"
    )


def treffer(rest, eintraege):
    """Index des längsten passenden Eintrags, -1 ohne Treffer.

    Passt, wenn der Text gleich dem Eintrag ist oder mit Eintrag + Leerzeichen
    beginnt. Der längste gewinnt, sonst schluckt "Reis" das "Reis hellblau".
    """
    pos, laenge = -1, -1
    for i, e in enumerate(eintraege):
        t = re.sub(r"\s+", " ", e.lower()).strip()
        if (rest == t or rest.startswith(t + " ")) and len(t) > laenge:
            pos, laenge = i, len(t)
    return pos


def zuordnung(text, regeln):
    """{"laden", "pos", "menge", "schluessel"} wie das Jinja-Makro zuordnung()."""
    g = glaetten(text, regeln)
    vorne = menge_vorne(regeln)
    rest = re.sub(vorne, "", g)
    menge = rest != g or bool(re.search(menge_hinten(regeln), g))

    # 1. Einträge der Läden, Läden in Reihenfolge
    for laden in regeln["laeden"]:
        p = treffer(rest, laden["eintraege"])
        if p >= 0:
            return {"laden": laden["name"], "pos": p, "menge": menge, "schluessel": g}

    # 2. Laden-Präfix, danach wieder eine Menge erlaubt ("Aldi 2 Gouda")
    for alias, name in (regeln.get("praefixe") or {}).items():
        if rest.startswith(alias + " "):
            r1 = rest[len(alias):].strip()
            r2 = re.sub(vorne, "", r1)
            laden = next(l for l in regeln["laeden"] if l["name"] == name)
            return {
                "laden": name,
                "pos": treffer(r2, laden["eintraege"]),
                "menge": menge or r2 != r1,
                "schluessel": g,
            }

    return {"laden": "unsortiert", "pos": 0, "menge": menge, "schluessel": g}


def plan(items, regeln):
    """Wie das Jinja-Makro plan(): was neu angelegt und was gelöscht wird.

    items: [{"summary", "uid", optional "due", "description"}], in der
    Reihenfolge der Liste. "anlegen" ist die Reihenfolge des Neuanlegens: MS To
    Do zeigt Neues oben, also zuerst der letzte Laden von unten nach oben,
    zuletzt der Trenner UNSORTIERT. Doppelte Einträge ohne Mengenangabe und
    alte Trenner landen in "loeschen".
    """
    trenner = [regeln["unsortiert"]["trenner"]] + [l["trenner"] for l in regeln["laeden"]]
    gruppen, gesehen, loeschen, unsortiert = {}, [], [], []
    alte_trenner = 0
    for i in items:
        text = i["summary"].strip()
        if text in trenner:
            loeschen.append(i["uid"])
            alte_trenner += 1
            continue
        z = zuordnung(text, regeln)
        if not z["menge"] and z["schluessel"] in gesehen:
            loeschen.append(i["uid"])
            continue
        if not z["menge"]:
            gesehen.append(z["schluessel"])
        e = {"summary": i["summary"], "alt": i["uid"], "pos": z["pos"]}
        for k in ("due", "description"):
            if i.get(k):
                e[k] = i[k]
        gruppen.setdefault(z["laden"], []).append(e)
        if z["laden"] == "unsortiert":
            unsortiert.append(i["summary"])

    anlegen, zahlen = [], {}
    for laden in reversed(regeln["laeden"]):
        g = sorted(gruppen.get(laden["name"], []), key=lambda e: e["pos"])
        anlegen += list(reversed(g)) + [{"summary": laden["trenner"]}]
        zahlen[laden["name"]] = len(g)
    u = gruppen.get("unsortiert", [])
    anlegen += list(reversed(u)) + [{"summary": regeln["unsortiert"]["trenner"]}]
    zahlen["unsortiert"] = len(u)
    zahlen["doppelt"] = len(loeschen) - alte_trenner
    return {"anlegen": anlegen, "loeschen": loeschen, "unsortiert": unsortiert, "zahlen": zahlen}
