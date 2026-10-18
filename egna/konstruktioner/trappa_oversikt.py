"""Översikt T/1: P. Hellstones entrétrappa med räckena R/1 (trappan), R/2 (nedre plattans framkant) och R/3
(plattans sida) på plats, för 3D-visualisering. Trappan, plattan och husväggen ritas som referenskroppar utan
positionsnummer (de syns i modellen och bilderna men ingår inte i materiallistan). Alla trappmått är antagna
ur fotona och mailet (1,5 m bred, knappt 4 m lång, 2,6 m bred nedre platta) och kontrollmäts på plats.

Koordinater: X längs trappan uppåt (första steget i x = 0), Y tvärs (trappans öppna kant y = 0, husväggen i
y = Trappbredd, plattan sticker ut mot gården till y = -(PlattaBredd - Trappbredd)), Z uppåt (plattan ±0).
Räckena står Kant (60) in från stenkanterna. Bygg: sammanstallning.py bygg egna/konstruktioner/trappa_oversikt.py
ut/T1_Trappa_oversikt.FCStd --png, bilder från fler håll: python3 egna/rendera.py ut/T1_Trappa_oversikt.FCStd
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import racke_bas

NAMN = "Trappa med räcken"
MARKE = "T/1"
VARIABLER = [
    ("Steg", 4, "antal steghöjder från nedre plattan till entréplanet"),
    ("Steghojd", 150, "mm, steghöjd (antagen)"),
    ("Stegdjup", 350, "mm, stegdjup (antaget)"),
    ("Trappbredd", 1500, "mm, trappans bredd (enligt mail)"),
    ("Platta", 1500, "mm, nedre plattans längd i trappans riktning (antagen)"),
    ("PlattaBredd", 2600, "mm, nedre plattans bredd tvärs (enligt mail)"),
    ("Vilplan", 1300, "mm, entréplanets längd från översta steget (antagen)"),
    ("Murhojd", 600, "mm, stenkantens höjd över gården (antagen)"),
    ("Kant", 60, "mm, räckets avstånd in från stenkanten"),
]

GRANIT = (0.80, 0.80, 0.77)
FASAD = (0.62, 0.20, 0.18)


def referens(k, namn, x0, x1, y0, y1, z0, z1, farg, transparens=0):
    """Referenskropp (låda) utanför sammanställningen: syns i 3D men saknar positionsnummer."""
    import pd
    import FreeCAD as App
    body = k.doc.addObject("PartDesign::Body", namn)
    d = pd.Del(k.doc, body.Name)
    sk = d.skiss("Kontur", "XY")
    sk.rektangel(x1 - x0, y1 - y0)
    d.kloss(sk, z1 - z0, "Hojd")
    body.Placement = App.Placement(App.Vector((x0 + x1) / 2, (y0 + y1) / 2, z0), App.Rotation())
    d.stada()
    try:
        body.ViewObject.ShapeColor = farg
        body.ViewObject.Transparency = transparens
    except Exception:
        pass
    return body


def bygg(k, v):
    n, Sh, Sd = int(v["Steg"]), v["Steghojd"], v["Stegdjup"]
    TB, PL, PB, VP, MH, kant = v["Trappbredd"], v["Platta"], v["PlattaBredd"], v["Vilplan"], v["Murhojd"], v["Kant"]
    yg = -(PB - TB)                                   # plattans kant mot gården
    # ---- referens: platta, steg, entréplan, husvägg
    referens(k, "Ref_Platta", -PL, 0, yg, TB, -MH, 0, GRANIT)
    for kk in range(1, n):
        referens(k, "Ref_Steg%d" % kk, (kk - 1) * Sd, kk * Sd, 0, TB, -MH, kk * Sh, GRANIT)
    referens(k, "Ref_Entreplan", (n - 1) * Sd, (n - 1) * Sd + VP, 0, TB, -MH, n * Sh, GRANIT)
    referens(k, "Ref_Fasad", -PL, (n - 1) * Sd + VP, TB, TB + 150, -MH, n * Sh + 2200, FASAD, 60)
    # ---- räckena
    bas = dict(Hojd=900, Under=80, Mellan=70)
    r1 = racke_bas.bygg_racke(k, dict(bas, Steg=n, Steghojd=Sh, Stegdjup=Sd), start="snacka", slut="rak",
                              ursprung=(0, kant, 0), prefix="R1 ", ritning=False)
    bas["Hojd"] = 1000
    r2 = racke_bas.bygg_racke(k, dict(bas, Steg=0, Steghojd=0, Stegdjup=1, Langd=PB - kant), start="gering", slut="rak", hornmot="R/3",
                              ursprung=(-PL + kant, yg + kant, 0), ex=(0, 1, 0), ey=(-1, 0, 0), prefix="R2 ", ritning=False, huvuddel=False)
    r3 = racke_bas.bygg_racke(k, dict(bas, Steg=0, Steghojd=0, Stegdjup=1, Langd=PL - kant), start="rak", slut="gering", hornmot="R/2",
                              ursprung=(0, yg + kant, 0), ex=(-1, 0, 0), ey=(0, -1, 0), prefix="R3 ", ritning=False, huvuddel=False)
    k.ritning(vyer=["fram", "plan"], noter=["ÖVERSIKT – RÄCKEN R/1, R/2, R/3 PÅ ENTRÉTRAPPAN, TRAPPMÅTT ANTAGNA UR FOTON",
                                             "TILLVERKNINGSRITNINGAR: R/1, R/2, R/3, GRIND G/1"])
