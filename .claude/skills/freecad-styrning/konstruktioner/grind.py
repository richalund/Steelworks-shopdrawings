"""Grind mellan två stolpar (exempel på formverktygen): gerad ram VKR40*4 med mellanregel, nedre fyllning som
inbockat plåttråg (k.trag), övre fyllning som laserskuren ornamentplåt i mässing med solfjäder (ornament.py),
gångjärn och lås som inköpta utrymmesmodeller (k.inkop), rörelsekontroll (k.rorelse, scripts/rorelse.py),
produktregler (REGLER, scripts/regler.py) och utseende i 3D-bilderna (k.utseende).

  python3 scripts/sammanstallning.py bygg konstruktioner/grind.py ut/G1.FCStd --var Bredd=1200 --png
  python3 scripts/sammanstallning.py ritning ut/G1.FCStd --uppdrag 2026-001
  python3 scripts/rorelse.py ut/G1.FCStd --oppen 80 --ut ut/G1_oppen.FCStd
  python3 scripts/rendera.py ut/G1_oppen.FCStd --vyer iso
  python3 scripts/dxf.py ut/G1.FCStd                 # laser: ornamentplåten, utbredning: tråget
  python3 scripts/kalkyl.py ut/G1.FCStd               # prisunderlag

Gångjärnens och låsets mått är utrymmesmodeller: byt mot måtten i det valda beslagets datablad.
"""
import ornament

NAMN = "Grind"
MARKE = "G/1"
VARIABLER = [("Bredd", 1000, "mm, grindbladets bredd (ram, yttermått)"),
             ("Hojd", 1100, "mm, grindbladets höjd"),
             ("Markfri", 60, "mm, fritt under bladet"),
             ("Glipa", 30, "mm, mellan stolpe och blad (gångjärnssidan och låssidan)"),
             ("Mellan", 450, "mm, mellanregelns mitt över bladets underkant")]

REGLER = [dict(villkor="600 <= Bredd <= 1500", text="grindbladets bredd 600–1500 mm"),
          dict(villkor="600 <= Hojd <= 1800", text="grindbladets höjd 600–1800 mm"),
          dict(villkor="200 <= Mellan <= Hojd - 250", text="mellanregeln minst 200 mm från underkant och 250 från överkant"),
          dict(villkor="VIKT <= 120", text="grinden väger högst 120 kg (gångjärnens last)", niva="VARNING")]

RITNING = dict(vyer=["fram", "plan"], snitt=[dict(namn="A", axel="x", varde=500, mot="-")],
               noter=["EXEMPEL – GRIND MED ORNAMENTPLÅT, EJ FÖR TILLVERKNING",
                      "RAM VKR40*4 GERAD 45° I HÖRNEN, MELLANREGEL VKR40*4",
                      "NEDRE FYLLNING PL1.5 BOCKAD 30 IN I RAMEN, ÖVRE FYLLNING PL4 MÄSSING LASERSKUREN",
                      "GÅNGJÄRN OCH LÅS: UTRYMMESMODELLER, MÅTT ENLIGT VALT BESLAG",
                      "YTBEHANDLING: RAM OCH STOLPAR PULVERLACKERADE SVART, MÄSSING PATINERAD (ANTAGET)"])


def bygg(k, v):
    B, H, M, G = v["Bredd"], v["Hojd"], v["Markfri"], v["Glipa"]
    Zm = M + v["Mellan"]
    # stolpar och mark
    for x in (-G - 40, B + G + 40):
        k.balk("st/1", "VKR80*4", (x, 0, -400), (x, 0, M + H + 40))
    k.referens("Mark", lada=(-700, B + 700, -900, 900, -400, 0), farg=(0.55, 0.52, 0.45))
    # ram med geringar
    ram = []
    for x in (20, B - 20):
        ram.append((k.balk("ram/1", "VKR40*4", (x, 0, M), (x, 0, M + H), huvuddel=not ram), "v", x))
    for z in (M + 20, M + H - 20):
        ram.append((k.balk("ram/2", "VKR40*4", (0, 0, z), (B, 0, z)), "h", z))
    for o, typ, c in ram:
        for x0, xi in ((0, 40), (B, B - 40)):
            for z0, zi in ((M, M + 40), (M + H, M + H - 40)):
                if (typ == "v" and abs(c - (x0 + xi) / 2) < 1) or (typ == "h" and abs(c - (z0 + zi) / 2) < 1):
                    k.gera(o, (x0, 0, z0), (xi, 0, zi), riktning=(0, 1, 0))
    k.balk("ram/3", "VKR40*4", (40, 0, Zm), (B - 40, 0, Zm))
    # nedre fyllning: tråg med kanterna inåt i ramen, botten mot ramens baksida
    lx, lz0, lz1 = B - 80 - 4, M + 40 + 2, Zm - 20 - 2
    k.trag("pl/1", 1.5, lx, lz1 - lz0, 30, mitt=(B / 2, 18, (lz0 + lz1) / 2), rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)), material="S235JR")
    # övre fyllning: laserskuren ornamentplåt i mässing
    oz0, oz1 = Zm + 20 + 2, M + H - 40 - 2
    ob, oh = B - 80 - 4, oz1 - oz0

    def ornamentplat(d):
        sk = d.skiss("Platta", "XY")
        sk.rektangel(ob, oh, namn=("Bredd", "Hojd"))
        d.kloss(sk, 4, "Tjocklek", symmetrisk=True)
        o = d.skiss("Solfjader", "XY")
        r = min(ob / 2 - 40, oh - 60)
        ornament.solfjader(o, 0.25 * r, r, 11, 10, 170, 0.5, mitt=(0, -oh / 2 + 30))
        ornament.bagar(o, 0.2 * r, 12, 1, 0, mitt=(0, -oh / 2 + 30))
        d.ficka(o, "genom", "Utskarning")
    k.egen("or/1", "PL4*%g" % round(ob), ornamentplat, mitt=(B / 2, 0, (oz0 + oz1) / 2),
           rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)), material="CuZn37")
    # beslag: gångjärnsaxeln i glipan framför stolpens framkant (annars slår bladet i stolpen innan 90°, se
    # rorelse.py), lås på låssidan (utrymmesmodeller)
    gx, gy = -G / 2, -45
    for z in (M + 150, M + H - 150):
        k.inkop("gj/1", "GÅNGJÄRN", cylinder=(20, 120), mitt=(gx, gy, z - 60), vikt=0.5)
    k.inkop("la/1", "GRINDLÅS", lada=(100, 30, 150), mitt=(B - 70, -35, Zm + 160), vikt=1.5)
    k.rorelse("GRIND", ["ram/1", "ram/2", "ram/3", "pl/1", "or/1", "la/1", "gj/1"], axel=((gx, gy, 0), (0, 0, 1)),
              fran=0, till=-100, gangjarn=[(gx, gy, M + 150), (gx, gy, M + H - 150)])
    k.utseende({"st/": "svart", "ram/": "svart", "pl/": "svart", "or/": "patinerad"})
