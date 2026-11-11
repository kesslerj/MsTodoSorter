import pytest

from sortierung import lade_regeln, plan, zuordnung
from testfaelle import FAELLE

REGELN = lade_regeln()
LAEDEN = {l["name"]: l["eintraege"] for l in REGELN["laeden"]}


@pytest.mark.parametrize("text,laden,eintrag,menge", FAELLE)
def test_zuordnung(text, laden, eintrag, menge):
    z = zuordnung(text, REGELN)
    assert z["laden"] == laden
    if laden == "unsortiert":
        assert z["pos"] == 0
    elif eintrag is None:
        assert z["pos"] == -1
    else:
        assert z["pos"] == LAEDEN[laden].index(eintrag)
    assert z["menge"] == menge


class TestGoudaPrefixParity:
    """"Aldi Gouda [X]" muss exakt wie "Gouda [X]" sortiert werden."""

    SUFFIXES = ["", " 3x", " 2,49 €", " X", " gerieben"]

    def test_prefixed_matches_unprefixed(self):
        for suffix in self.SUFFIXES:
            plain = zuordnung(f"Gouda{suffix}", REGELN)
            prefixed = zuordnung(f"Aldi Gouda{suffix}", REGELN)
            assert (plain["laden"], plain["pos"]) == (prefixed["laden"], prefixed["pos"])
            assert plain["laden"] == "aldi"


def _items(*texte):
    return [{"summary": t, "uid": f"u{i}"} for i, t in enumerate(texte)]


class TestPlan:
    def test_reihenfolge_von_unten_nach_oben(self):
        p = plan(_items("Milch", "Fischstäbchen", "Bananen", "Joghurt"), REGELN)
        angelegt = [e["summary"] for e in p["anlegen"]]
        # Neues steht oben: zuerst EDEKA von unten (Joghurt hinter Milch), zuletzt UNSORTIERT
        assert angelegt == [
            "Joghurt", "Milch", "----------- EDEKA -----------",
            "Bananen", "----------- ALDI -----------",
            "Fischstäbchen", "----------- UNSORTIERT -----------",
        ]
        assert p["zahlen"] == {"edeka": 2, "aldi": 1, "unsortiert": 1, "doppelt": 0}
        assert p["unsortiert"] == ["Fischstäbchen"]

    def test_doppelte_ohne_menge_werden_geloescht(self):
        p = plan(_items("Milch", "milch ", "Milch"), REGELN)
        assert p["loeschen"] == ["u1", "u2"]
        assert p["zahlen"]["doppelt"] == 2

    def test_doppelte_mit_menge_bleiben(self):
        p = plan(_items("500g Möhren", "500g Möhren", "Milch", "2 Milch"), REGELN)
        assert p["loeschen"] == []
        assert [e["summary"] for e in p["anlegen"]].count("500g Möhren") == 2

    def test_alte_trenner_werden_ersetzt(self):
        p = plan(_items("----------- ALDI -----------", "Bananen"), REGELN)
        assert p["loeschen"] == ["u0"]
        assert p["zahlen"]["doppelt"] == 0
        assert [e["summary"] for e in p["anlegen"]].count("----------- ALDI -----------") == 1

    def test_faelligkeit_und_beschreibung_bleiben(self):
        items = [{"summary": "Milch", "uid": "u0", "due": "2026-11-20", "description": "fettarm"}]
        e = plan(items, REGELN)["anlegen"][0]
        assert (e["summary"], e["alt"], e["due"], e["description"]) == ("Milch", "u0", "2026-11-20", "fettarm")
