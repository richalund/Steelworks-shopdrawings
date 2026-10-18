"""Räcke med ovaler av bockat plattstål (exempel): en ram av stolpar, överliggare med rundad handledare och
underliggare, tolv ovaler (stadionform) på lika delning som hänger i överliggaren med en spjäla var och stöttas
mot underliggaren, och korta liggare mellan ovalerna i två höjder. Visar ett ornament av bockat plattstål som en
fullt bestämd skiss (stadionring: två raka sidor och två tangerande bågar, `stadion` nedan), upprepade delar på
lika delning med måttkedja (RITNING["kedjor"]) och en profilerad handledare (k.egen).

  python3 scripts/sammanstallning.py bygg konstruktioner/racke_ovaler.py ut/R2.FCStd --var Langd=2400 --png
  python3 scripts/sammanstallning.py ritning ut/R2.FCStd --uppdrag 2026-001

Uppbyggnad: stolpar st/1 PL10*30, överliggare l/1 PL8*40 plant med handledare h/1 (rundad 40x16, förenklad),
underliggare l/2 PL10*20 på högkant. Ovaler o/1 PL10*20 bockade till 130x570, spjälor sp/1–sp/2 och liggare
sp/3–sp/4 PL10*20. Ovalerna centreras på räckets längd med delningen DELNING.

Räcket är ett ornament för ett plant parti: öppningarna ovanför och under ovalerna är större än 100 mm, så det
uppfyller inte kraven på skydd mot fall där sådant krävs (BBR) utan kompletterande spjälor eller glas.

Koordinater: X = räckets längd från vänster stolpes yttersida, Z uppåt från underliggarens underkant, Y = djup
(räckets mittplan y = 0).
"""
import pd

NAMN = "Racke med ovaler"
MARKE = "R/2"
VARIABLER = [
    ("Langd", 2340, "mm, ramens längd (stolparnas yttersidor)"),
    ("Hojd", 800, "mm, underliggarens underkant till överliggarens ovansida"),
]
REGLER = [dict(villkor="2240 <= Langd <= 2600", text="längden 2240–2600 mm (12 ovaler c/c 187 med liggare mot stolparna)"),
          dict(villkor="760 <= Hojd <= 1000", text="höjden 760–1000 mm (ovalerna 570 höga)")]
RITNING = dict(
    vyer=["fram", "plan"],
    snitt=[dict(namn="A", axel="x", varde=141.5, mot="-")],      # genom första ovalen, spjälorna och liggarna
    kedjor=[dict(pos="o/1", vy="fram")],                          # ovalernas delning i framvyn
    noter=["EXEMPEL – RÄCKE MED OVALER AV BOCKAT PLATTSTÅL, EJ FÖR TILLVERKNING",
           "OVALER o/1 12 st 130x570 c/c 187, PLATTSTÅL 10x20 BOCKAT, UTV. LÄNGD 1226",
           "ÖK o/1 108 UNDER ÖK l/1, LIGGARE sp/3–4 c 228 OCH 582 ÖVER UK",
           "h/1 RUNDAD 40x16 (FÖRENKLAD), SVETSAS MOT l/1 a3 MED HÄFTSVETS c/c 300",
           "SVETS: SPJÄLOR, LIGGARE OCH OVALER a3 RUNT OM",
           "INFÄSTNING (VÄGGFÄSTEN ELLER FOTPLÅTAR) ENL. PLATSEN, EJ RITAD",
           "ÖPPNINGAR >100 MM OVAN OCH UNDER OVALERNA – EJ SKYDD MOT FALL ENL. BBR UTAN KOMPLETTERING",
           "YTBEHANDLING: GRUNDFÄRG + TÄCKFÄRG ENLIGT BESTÄLLNING (ANTAGET)"],
)

STAL = "S235JR"
STOLPE = 30.0           # stolpe PL10*30, 30 i räckets plan
T = 10.0                # godstjocklek (djup) för stolpar, spjälor, liggare och ovaler
BAND = 20.0             # spjälor, liggare och ovaler PL10*20, 20 i räckets plan
OVERL_T = 8.0           # överliggare PL8*40 plant
ANTAL = 12
DELNING = 187.0         # ovalernas c/c
OVAL_B, OVAL_H = 130.0, 570.0      # ovalens yttermått
OVAL_TOPP = 108.0       # överliggarens ovansida till ovalens överkant
LIGG_Z = (582.0, 228.0)            # liggarnas mitthöjd (övre, nedre)


def stadion(sk, b, h, namn=("b", "h")):
    """Sluten stadionform b x h (halvcirkelbågar i ändarna, radie b/2) kring skissens origo: två lodräta linjer och
    två bågar, tangerande i ändpunkterna. Fullt bestämd av bredden, höjden och bågmittarnas symmetri kring origo."""
    import Part
    from FreeCAD import Vector as V
    import math
    r, c = b / 2.0, h / 2.0 - b / 2.0
    hoger = sk.geo(Part.LineSegment(V(r, -c, 0), V(r, c, 0)))
    vanster = sk.geo(Part.LineSegment(V(-r, c, 0), V(-r, -c, 0)))
    topp = sk.geo(Part.ArcOfCircle(Part.Circle(V(0, c, 0), V(0, 0, 1), r), 0.0, math.pi))
    botten = sk.geo(Part.ArcOfCircle(Part.Circle(V(0, -c, 0), V(0, 0, 1), r), math.pi, 2 * math.pi))
    sk.begr("Vertical", hoger)
    sk.begr("Vertical", vanster)
    sk.begr("Tangent", hoger, pd.SLUT, topp, pd.START)
    sk.begr("Tangent", topp, pd.SLUT, vanster, pd.START)
    sk.begr("Tangent", vanster, pd.SLUT, botten, pd.START)
    sk.begr("Tangent", botten, pd.SLUT, hoger, pd.START)
    sk.matt("DistanceX", vanster, pd.START, hoger, pd.START, varde=b, namn=namn[0])
    sk.matt("DistanceY", hoger, pd.START, hoger, pd.SLUT, varde=h - b, namn=namn[1])
    sk.begr("Symmetric", topp, pd.MITT, botten, pd.MITT, pd.ROT, 1)
    return [hoger, vanster, topp, botten]


def oval(d):
    """Oval av plattstål: stadionring (yttre OVAL_B x OVAL_H, bandet BAND brett) padad T i djupled."""
    sk = d.skiss("Oval", "XY")
    stadion(sk, OVAL_B, OVAL_H, namn=("Bredd", "_rak"))
    stadion(sk, OVAL_B - 2 * BAND, OVAL_H - 2 * BAND, namn=("Innerbredd", "_rak_i"))
    d.kloss(sk, T, "Djup")


def handledare(d):
    """Rundad handledare 40 x 16 (halvrund profil, förenklad) längs hela räcket."""
    sk = d.skiss("Profil", "XY")
    sk.rundad_rektangel(40, 16, 7.5, namn=("b", "h", "r"))
    d.kloss(sk, "Langd", "Langd")


def bygg(k, v):
    L, H = v["Langd"], v["Hojd"]
    z_ok = H - OVERL_T                        # överliggarens underkant
    upp = (0, 1, 0)                           # plattstålets tjocklek i djupled
    # ram
    k.balk("st/1", "PL10*30", (STOLPE / 2, 0, 0), (STOLPE / 2, 0, z_ok), upp=upp, material=STAL)
    k.balk("st/1", "PL10*30", (L - STOLPE / 2, 0, 0), (L - STOLPE / 2, 0, z_ok), upp=upp, material=STAL)
    k.plat("l/1", "PL8*40", mitt=("Langd / 2", 0, H - OVERL_T / 2), langd="Langd", lriktning=(1, 0, 0),
           briktning=(0, 1, 0), material=STAL, huvuddel=True)
    k.egen("h/1", "HL40*16", handledare, mitt=(0, 0, H + 8),
           rot=((0, 1, 0), (0, 0, 1), (1, 0, 0)), material=STAL)
    k.balk("l/2", "PL10*20", (STOLPE, 0, BAND / 2), (L - STOLPE, 0, BAND / 2), upp=upp, material=STAL)
    # ovaler med spjälor
    kant = (L - (ANTAL - 1) * DELNING) / 2
    z_ovtopp = H - OVAL_TOPP
    z_ovbott = z_ovtopp - OVAL_H
    xs = [kant + i * DELNING for i in range(ANTAL)]
    for x in xs:
        k.egen("o/1", "OVAL %gx%g" % (OVAL_B, OVAL_H), oval, mitt=(x, T / 2, (z_ovtopp + z_ovbott) / 2),
               rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)), material=STAL)
        k.balk("sp/1", "PL10*20", (x, 0, z_ovtopp), (x, 0, z_ok), upp=upp, material=STAL)
        k.balk("sp/2", "PL10*20", (x, 0, BAND), (x, 0, z_ovbott), upp=upp, material=STAL)
    # liggare mellan ovalerna och mot stolparna, två höjder
    kanter = [STOLPE] + [x for x0 in xs for x in (x0 - OVAL_B / 2, x0 + OVAL_B / 2)] + [L - STOLPE]
    for a, b in zip(kanter[0::2], kanter[1::2]):
        pos = "sp/3" if a == STOLPE or b == L - STOLPE else "sp/4"
        for z in LIGG_Z:
            k.balk(pos, "PL10*20", (a, 0, z), (b, 0, z), upp=upp, material=STAL)
    k.ritning(**RITNING)
