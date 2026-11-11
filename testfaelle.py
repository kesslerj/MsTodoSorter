"""Testfälle der Zuordnung, für sortierung.py und das Jinja-Makro in HA.

(Text, Laden, Eintrag, Menge)
  Eintrag: Name des erwarteten Listeneintrags, None = nur Laden-Präfix
           erkannt (Position -1), bei "unsortiert" immer None.
  Menge:   ob eine Mengenangabe erkannt werden muss.
"""

FAELLE = [
    # Grundfälle
    ("Joghurt", "edeka", "Joghurt", False),
    ("joghurt", "edeka", "Joghurt", False),
    ("  Joghurt  ", "edeka", "Joghurt", False),
    ("Bananen", "aldi", "Bananen", False),
    ("Bionade", "edeka", "Bionade", False),
    ("Passierte Tomaten", "edeka", "Passierte Tomaten", False),
    ("Fischstäbchen", "unsortiert", None, False),
    # Freie Zusätze und Preise
    ("Joghurt Natur", "edeka", "Joghurt", False),
    ("Joghurt X", "edeka", "Joghurt", False),
    ("Joghurt 2,49", "edeka", "Joghurt", False),
    ("Joghurt 2,49€", "edeka", "Joghurt", False),
    ("Joghurt 2,49 €", "edeka", "Joghurt", False),
    ("Joghurteis", "unsortiert", None, False),
    ("Milch", "edeka", "Milch", False),
    # Mengen vorne
    ("2 Joghurt", "edeka", "Joghurt", True),
    ("2x Joghurt", "edeka", "Joghurt", True),
    ("2x Bananen", "aldi", "Bananen", True),
    ("500g Möhren", "edeka", "Möhren", True),
    ("500 g Möhren", "edeka", "Möhren", True),
    ("500 Gramm Möhren", "edeka", "Möhren", True),
    ("500gr. Möhren", "edeka", "Möhren", True),
    ("fünf hundert gramm Möhren", "edeka", "Möhren", True),
    ("fünfhundert Gramm Möhren", "edeka", "Möhren", True),
    ("Vier hundert gramm Möhren", "edeka", "Möhren", True),
    ("2,5 kg Bananen", "aldi", "Bananen", True),
    ("Ein kilo Bananen", "aldi", "Bananen", True),
    ("Zwei magerquark", "edeka", "Magerquark", True),
    ("Drei stangen paprika", "aldi", "Paprika", True),
    ("Sechs paprika", "aldi", "Paprika", True),
    ("eine Gurke", "aldi", "Gurke", True),
    ("2 Liter Milch", "edeka", "Milch", True),
    # Mengen hinten
    ("Joghurt 3x", "edeka", "Joghurt", True),
    ("Joghurt 5x", "edeka", "Joghurt", True),
    ("Sahne zwei mal", "edeka", "Sahne", True),
    ("Möhren 500g", "edeka", "Möhren", True),
    # Keine Menge, obwohl es so aussieht
    ("Eis", "edeka", "Eis", False),
    ("Eiweißbrot", "aldi", "Eiweißbrot", False),
    ("Achterbahn", "unsortiert", None, False),
    ("Zehnkornbrot", "unsortiert", None, False),
    ("2 Lauch", "unsortiert", None, True),
    # Schreibweisen von Alexa
    ("T. k. himbeeren", "edeka", "TK Himbeeren", False),
    ("T. k. laugenstangen", "edeka", "TK Laugenstangen", False),
    ("Körniger frischkäse", "edeka", "körniger Frischkäse", False),
    # Laden-Präfixe
    ("Edeka Bionade", "edeka", "Bionade", False),
    ("edeka Bionade", "edeka", "Bionade", False),
    ("Aldi Schoki", "aldi", "Schoki", False),
    ("Aldi Bionade", "aldi", None, False),
    ("Edeka Fischstäbchen", "edeka", None, False),
    ("Aldi Fischstäbchen", "aldi", None, False),
    ("Edeka 2x Bionade", "edeka", "Bionade", True),
    ("Aldi 2x Gouda", "aldi", "Gouda", True),
    ("Aldi Gouda gerieben", "aldi", "Gouda", False),
    ("EdekaBionade", "unsortiert", None, False),
    ("GG Fischstäbchen", "edeka", None, False),
    ("gg Fischstäbchen", "edeka", None, False),
    ("GG Milch", "edeka", "Milch", False),
    ("GG Gouda", "edeka", None, False),
    ("GGMilch", "unsortiert", None, False),
    ("GG Oliven", "edeka", "GG Oliven", False),
    ("Roggen Vollkornbrot GG", "edeka", "Roggen Vollkornbrot GG", False),
    ("Edeka Flens 12,49", "edeka", None, False),
    # Ergänzt am 11.11.2026 aus dem Protokoll
    ("Fünf hundert gramm hackfleisch", "edeka", "Hackfleisch", True),
    ("Abraham Schinken", "edeka", "Abraham Schinken", False),
    ("Schinken", "edeka", "Schinken", False),
    ("Würstchen", "edeka", "Würstchen", False),
    ("2 Gläser Würstchen", "edeka", "Würstchen", True),
    ("Wiener würstchen", "unsortiert", None, False),
    # Längster Treffer gewinnt, erster Laden bei Treffern in mehreren
    ("Reis", "aldi", "Reis", False),
    ("Reis hellblau", "aldi", "Reis hellblau", False),
    ("Käse", "edeka", "Käse", False),
    ("Käsepapier", "edeka", "Käsepapier", False),
    ("körniger Frischkäse", "edeka", "körniger Frischkäse", False),
    ("Chipsfrisch", "aldi", "Chipsfrisch", False),
    ("Edeka Chipsfrisch", "edeka", "Chipsfrisch", False),
]
