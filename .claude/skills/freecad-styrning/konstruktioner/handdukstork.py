"""Handdukstork (stege) i rostfritt utan värmare – exempel på rörkonstruktion med gerade knän mot vägg,
fiskmunskapade pinnar (k.egen med en ficka i stolpens cirkel), dolda väggfästen i snitt och måttkedja till
upprepade delar (RITNING["kedjor"]: pinnarnas c/c i framvyn).

  python3 scripts/sammanstallning.py bygg konstruktioner/handdukstork.py ut/H1.FCStd --var Antal=6 --var Hojd=900
  python3 scripts/sammanstallning.py ritning ut/H1.FCStd --uppdrag 2026-001 --hal 5.5 --svets 2.0
  python3 scripts/rendera.py ut/H1.FCStd --vyer iso

Två stolpar RÖR32*1.5 med 45° gerade knän: upptill en arm direkt mot väggen, nedtill en arm mot en rosett.
Armarna träs på väggfästen (svarvad rundstång i röret) och låses med en stoppskruv M5 underifrån. Pinnarna
RÖR19*1.5 kapas med fiskmun mot stolparna och svetsas runt om. Godstjockleken är antagen.

Koordinater: X längs väggen (mitt mellan stolparna x = 0), Y ut från väggen negativt (väggen y = 0, framvyn ser
torken framifrån), Z uppåt (z = 0 rosettens underkant).
"""
import math

NAMN = "Handdukstork"
MARKE = "H/1"
VARIABLER = [
    ("CC", 368, "mm, stolparnas c/c"),
    ("Hojd", 1245, "mm, total höjd (armens ovansida till rosettens underkant)"),
    ("Djup", 100, "mm, från vägg till stolparnas framkant"),
    ("Antal", 8, "st, pinnar"),
    ("Delning", 138, "mm, pinnarnas c/c"),
    ("Topp", 101.5, "mm, från överkant till översta pinnens mitt"),
]

REGLER = [dict(villkor="200 <= CC <= 800", text="stolparnas c/c 200–800 mm"),
          dict(villkor="2 <= Antal <= 12", text="2–12 pinnar"),
          dict(villkor="Topp + (Antal - 1) * Delning <= Hojd - 110", text="nedersta pinnen ovanför den nedre armen")]

NOTER = ["EXEMPEL – HANDDUKSTORK I ROSTFRITT UTAN VÄRMARE, EJ FÖR TILLVERKNING",
         "UNDERLAG: GODSTJOCKLEK 1.5 ANTAGEN – BEKRÄFTAS MED RÖRLEVERANTÖR",
         "UTFÖRANDE: KNÄN st/1–ar/1 OCH st/1–ar/2 GERADE 45°, STOLPAR OCH ARMAR SLUTNA",
         "UTFÖRANDE: PINNAR pi/1 FISKMUNSKAPADE MOT STOLPE Ø32",
         "MONTAGE: ARMARNA TRÄS PÅ VÄGGFÄSTEN vf/1, vf/2 OCH LÅSES MED STOPPSKRUV M5 A4 UNDERIFRÅN",
         "MONTAGE: VÄGGFÄSTEN SKRUVAS MED 1 SKRUV 5 MM A4 + PLUGG ENL. VÄGG, FÖRSÄNKT. ROSETT ro/1 TRÄS PÅ vf/2",
         "MONTAGE: vf/1, vf/2 SVARVAS TILL GLIDPASSNING MOT RÖRETS INNERDIAMETER",
         "SVETS: TIG RUNT OM, GENOMSVETSAT I GERINGAR, SLIPAS JÄMNT MED RÖRET",
         "YTBEHANDLING: SPEGELPOLERAD EFTER SVETS, BETAD OCH PASSIVERAD",
         "MATERIAL: ROSTFRITT 1.4404 (316L) ENL. EN 10088, RÖR SVETSADE ENL. EN 10296-2",
         "KONTROLL: STOLPAR PARALLELLA OCH I SAMMA PLAN ±1 MM, PINNAR VÅGRÄTA"]

ROR, PINNE = 32.0, 19.0          # stolpar/armar och pinnar, ytterdiameter
GODS = 1.5                       # antagen godstjocklek
ROSETT_D, ROSETT_T = 90.0, 8.0
TAPP = 28.0                      # väggfästets diameter (svarvas till passning mot rörets innerdiameter)
MTRL = "1.4404"


def bygg(k, v):
    cc, H, D, P, T = v["CC"], v["Hojd"], v["Djup"], v["Delning"], v["Topp"]
    r = ROR / 2
    ya = -(D - r)                                    # stolparnas axel
    z_ovre = H - r                                   # övre armens axel
    z_nedre = ROSETT_D / 2                           # nedre armens axel = rosettens mitt
    ror = "RÖR%g*%g" % (ROR, GODS)
    k.referens("Vägg", lada=(-cc / 2 - 250, cc / 2 + 250, 0, 60, -150, H + 150), farg=(0.93, 0.92, 0.9))
    for i, x in enumerate((-cc / 2, cc / 2)):
        # stolpe, gerad i båda ändar mot armarna (yttre hörnet = framkant, inre = bakkant)
        st = k.balk("st/1", ror, (x, ya, z_nedre - r), (x, ya, H), material=MTRL, huvuddel=i == 0)
        k.gera(st, (x, -D, H), (x, -D + ROR, H - ROR), riktning=(1, 0, 0))
        k.gera(st, (x, -D, z_nedre - r), (x, -D + ROR, z_nedre + r), riktning=(1, 0, 0))
        # övre arm direkt mot väggen, nedre arm mot rosetten
        a1 = k.balk("ar/1", ror, (x, 0, z_ovre), (x, -D, z_ovre), material=MTRL)
        k.gera(a1, (x, -D, H), (x, -D + ROR, H - ROR), riktning=(1, 0, 0))
        a2 = k.balk("ar/2", ror, (x, -ROSETT_T, z_nedre), (x, -D, z_nedre), material=MTRL)
        k.gera(a2, (x, -D, z_nedre - r), (x, -D + ROR, z_nedre + r), riktning=(1, 0, 0))
        # stoppskruvens hål i armens undersida (bara genom det nedre godset)
        for a, z in ((a1, z_ovre), (a2, z_nedre)):
            k.hal([a], [(x, -ROSETT_T - 12, z - r + GODS / 2)], (0, 0, 1), d=4.2, bult="M5", langd=GODS + 2)
        # dolda väggfästen och rosett
        f1 = k.balk("vf/1", "D%g" % TAPP, (x, 0, z_ovre), (x, -30, z_ovre), material=MTRL)
        f2 = k.balk("vf/2", "D%g" % TAPP, (x, 0, z_nedre), (x, -ROSETT_T - 30, z_nedre), material=MTRL)
        k.hal([f1], [(x, -15, z_ovre)], (0, 1, 0), d=5.5)
        k.hal([f2], [(x, -19, z_nedre)], (0, 1, 0), d=5.5)

        def rosett(d):
            sk = d.skiss("Rosett", "XY")
            sk.cirkel(ROSETT_D, namn="Diameter")
            sk.cirkel(TAPP + 0.5, namn="Hal")
            d.kloss(sk, ROSETT_T, "Tjocklek", symmetrisk=True)
        k.egen("ro/1", "D%g*%g" % (ROSETT_D, ROSETT_T), rosett, mitt=(x, -ROSETT_T / 2, z_nedre),
               rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)), material=MTRL)

    # pinnar: rör mellan stolparna; Pad med kaplängden (fiskmunnens långa sida), sedan en ficka med stolparnas
    # cirklar som ger fiskmunnen
    kap = round(cc - 2 * math.sqrt(r ** 2 - (PINNE / 2) ** 2), 1)

    def pinnen(d):
        sk = d.skiss("Ror", "YZ")
        sk.cirkel(PINNE, namn="Diameter")
        sk.cirkel(PINNE - 2 * GODS, namn="Innerdiameter")
        d.kloss(sk, kap, "Langd", symmetrisk=True)
        fm = d.skiss("Fiskmun", "XY")
        fm.cirkel(ROR, mitt=(-cc / 2, 0), namn="")
        fm.cirkel(ROR, mitt=(cc / 2, 0), namn="")
        d.ficka(fm, "genom", "Kap")
    for n in range(int(v["Antal"])):
        k.egen("pi/1", "RÖR%g*%g" % (PINNE, GODS), pinnen, mitt=(0, ya, H - T - n * P), material=MTRL)
    k.utseende({p: "rostfritt" for p in ("st/", "ar/", "pi/", "ro/", "vf/")})
    # snittet genom vänstra stolpens axel visar väggfästen och stoppskruvshål; detaljer av knäna på blad 2
    k.ritning(vyer=["fram"], snitt=[dict(namn="A", axel="x", varde=-cc / 2, mot="-")], noter_blad=True, bubblor="rad",
              kedjor=[dict(pos="pi/1", vy="fram")],
              detaljer=[dict(vy="A", punkt=(-cc / 2, -55, H - 40), radie=75, rubrik="ÖVRE KNÄ OCH VÄGGFÄSTE vf/1",
                             text=["ARM ar/1 DIREKT MOT VÄGG", "STOPPSKRUV M5 UNDERIFRÅN"],
                             matt=[dict(typ="x", varde=D, lage="over")]),
                        dict(vy="A", punkt=(-cc / 2, -55, z_nedre + 5), radie=75, rubrik="NEDRE KNÄ, ROSETT ro/1 OCH vf/2",
                             text=["ROSETT Ø%gx%g TRÄS PÅ vf/2" % (ROSETT_D, ROSETT_T), "STOPPSKRUV M5 UNDERIFRÅN"],
                             matt=[dict(typ="x", varde=ROSETT_T, lage="under")])],
              noter=NOTER)
