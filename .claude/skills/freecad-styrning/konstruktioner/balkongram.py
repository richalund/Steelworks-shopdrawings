"""Balkongram av UPE140 med IPE100-bjälkar, anslutningsplåtar och däckplåt - testfall efter en svensk sammanställningsritning
(balkongram B/1, A2).

Som i förlagan: ramens UPE-hörn är gerade 45° (k.gera). På UPE-flänsarnas spetsar sitter påsvetsade plåtar pl/1
(fram) och pl/2 (bak), PL120*10 L=140; IPE100-bjälkarnas ändplåtar pl/3 (PL110*10 L=100) bultas mot dem med
4*Ø14 - M12x44 (c/c 55 x 40). Det ger 85 mm från UPE:ns utsida till bjälkänden (65 + 10 + 10) och bjälklängden
Djup - 170 = 1200 (förlagan 1199). Förenklat: bjälkarnas överkant i nivå med UPE:ns (förlagan: i fall 1:100,
+1 fram / +13 bak), däckplåten bultas i UPE-flänsarna.

Koordinater: X = längd (framkant), Y = djup bakåt (framsida y = 0), Z uppåt (underkant ram z = 0).
"""
NAMN = "Balkongram"
MARKE = "B/1"
VARIABLER = [
    ("Langd", 2200, "mm, ramens längd (X)"),
    ("Djup", 1370, "mm, ramens djup (Y) = däckplåtens bredd"),
    ("Bjalkar", 3, "antal IPE-bjälkar, jämnt fördelade"),
    ("Dack", 5, "mm, däckplåtens tjocklek (0 = ingen däckplåt)"),
]
RITNING = dict(
    vyer=["fram", "plan"],                     # framvy överst, planvy under (E-metoden)
    dolda=["plan"],                            # planvyn med dolda linjer (ramen under däckplåten)
    snitt=[dict(namn="A", axel="x", varde=300, mot="-"),      # mot = blickriktning längs axeln
           dict(namn="B", axel="x", varde=575, mot="-")],     # B genom bjälkens hålrad (550 + 27,5)
    stomnat="A-B/2",
    noter=["PRELIMINÄR RITNING – EJ FÖR TILLVERKNING",
           "TESTRITNING UR FREECAD",
           "UPE-RAMENS HÖRN GERADE 45°",
           "SVETS: UPE-HÖRN a4 RUNT OM, PÅSVETSADE PLÅTAR pl/1, pl/2 OCH ÄNDPLÅTAR pl/3 a4",
           "IPE100 MOT pl/1, pl/2: 2x2 M12 8.8 FZV GENOM ÄNDPLÅTARNA pl/3, MONTERAS I VERKSTAD",
           "DÄCKPLÅT pl/7 BULTAS I UPE-FLÄNSARNA: M12 8.8 FZV",
           "YTBEHANDLING ENLIGT BESTÄLLNING"],
)

UPE_H, UPE_B = 140.0, 65.0
IPE_H = 100.0
PL_T = 10.0                                    # tjocklek på anslutningsplåt pl/1, pl/2 och ändplåt pl/3


def bygg(k, v):
    D, n, t = v["Djup"], int(v["Bjalkar"]), v["Dack"]
    zc = UPE_H / 2
    # Längder, lägen och hål längs ramen är uttryck mot Variabler ("Langd", "Djup - 32.5"): de följer med när
    # Langd/Djup ändras i FreeCAD. Antalet bjälkar (Bjalkar) och däckplåtens tjocklek kräver ombyggnad.
    fram = k.balk("b/1", "UPE140", (0, UPE_B / 2, zc), ("Langd", UPE_B / 2, zc), oppning=(0, 1, 0), huvuddel=True)
    bak = k.balk("b/2", "UPE140", (0, "Djup - %g" % (UPE_B / 2), zc), ("Langd", "Djup - %g" % (UPE_B / 2), zc), oppning=(0, -1, 0))
    g1 = k.balk("b/3", "UPE140", (UPE_B / 2, 0, zc), (UPE_B / 2, "Djup", zc), oppning=(1, 0, 0))
    g2 = k.balk("b/3", "UPE140", ("Langd - %g" % (UPE_B / 2), 0, zc), ("Langd - %g" % (UPE_B / 2), "Djup", zc), oppning=(-1, 0, 0))
    # ramens fyra hörn geras 45°: varje UPE kapas genom hörnets yttre och inre punkt
    for (xo, yo, xi, yi), delar_ in ((((0, 0, UPE_B, UPE_B)), (fram, g1)),
                                     (("Langd", 0, "Langd - %g" % UPE_B, UPE_B), (fram, g2)),
                                     ((0, "Djup", UPE_B, "Djup - %g" % UPE_B), (bak, g1)),
                                     (("Langd", "Djup", "Langd - %g" % UPE_B, "Djup - %g" % UPE_B), (bak, g2))):
        for d_ in delar_:
            k.gera(d_, (xo, yo, zc), (xi, yi, zc))
    zi = UPE_H - IPE_H / 2                     # IPE100:s överkant i nivå med UPE:ns
    y_ans = UPE_B + PL_T / 2                   # anslutningsplåtens mitt (på flänsspetsarna)
    y_and = UPE_B + PL_T * 1.5                 # ändplåtens mitt
    y_ipe = UPE_B + 2 * PL_T                   # bjälkänden (85 från UPE:ns utsida)
    for i in range(1, n + 1):
        xu = "Langd * %d / %d" % (i, n + 1)
        k.balk("b/7", "IPE100", (xu, y_ipe, zi), (xu, "Djup - %g" % y_ipe, zi))
        for pos, ya, ye in (("pl/1", y_ans, y_and), ("pl/2", "Djup - %g" % y_ans, "Djup - %g" % y_and)):
            ans = k.plat(pos, "PL120*10", mitt=(xu, ya, zc), langd=UPE_H, lriktning=(0, 0, 1), briktning=(1, 0, 0))
            andp = k.plat("pl/3", "PL110*10", mitt=(xu, ye, zi), langd=IPE_H, lriktning=(0, 0, 1), briktning=(1, 0, 0))
            k.hal([andp, ans], [("%s %+g" % (xu, dx), ye, zi + dz) for dx in (-27.5, 27.5) for dz in (-20, 20)],
                  riktning=(0, 1, 0), bult="M12x44")
    if t > 0:
        dack = k.plat("pl/7", "PL%g*%g" % (t, D), mitt=("Langd / 2", "Djup / 2", UPE_H + t / 2), langd="Langd", bredd="Djup")
        xs = ["Langd * %d / %d" % (2 * i + 1, 2 * (n + 1)) for i in range(n + 1)]
        for y, ram in ((UPE_B * 0.6, fram), ("Djup - %g" % (UPE_B * 0.6), bak)):
            k.hal([dack, ram], [(x, y, UPE_H) for x in xs], riktning=(0, 0, 1), bult="M12x30", langd=40)
    k.ritning(**RITNING)
