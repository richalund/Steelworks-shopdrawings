r"""Fotplatta: plåt med rundade hörn och fyra hål i rektangulärt mönster (Part Design).
  python scripts/partdesign.py bygg delar/fotplatta.py "<mapp>\Fotplatta.FCStd" --png --step
"""
NAMN = "Fotplatta"
VARIABLER = [
    ("Bredd", 250, "mm, plattans bredd (X)"),
    ("Langd", 250, "mm, plattans längd (Y)"),
    ("Tjocklek", 15, "mm, plåt"),
    ("Hornradie", 20, "mm, hörnradie"),
    ("HalD", 18, "mm, håldiameter"),
    ("CCx", 190, "mm, hålavstånd i X"),
    ("CCy", 190, "mm, hålavstånd i Y"),
]


def bygg(d):
    sk = d.skiss("Kontur", "XY")                       # undersidan i Z = 0, centrerad kring origo
    sk.rundad_rektangel("Bredd", "Langd", "Hornradie")
    d.kloss(sk, "Tjocklek", "Platta")
    hal = d.skiss("Halbild", "XY", forskjutning="Tjocklek")   # på ovansidan, hålen borras nedåt
    hal.halbild("HalD", "CCx", "CCy")
    d.hal(hal, "HalD", namn="Hal")
