"""Skåp i bockad plåt på en stomme av fyrkantsrör (exempel): en låg skänk/TV-bänk med tre moduler – dörr | två
lådor | dörr – på åtta ben. Visar plåtbeklädnad och inredning med k.trag (lock, gavlar, mellanväggar, hyllor,
fronter och lådor), en svetsad stomme med k.balk, egna delar med urtag (k.egen: rygg med kabelurtag,
gångjärnslist med hål för gångjärnsskålen) och beslag som utrymmesmodeller (k.inkop), och en ritning med tre snitt
(ett vågrätt) och detaljer på blad 2.

  python3 scripts/sammanstallning.py bygg konstruktioner/skap.py ut/S1.FCStd --var Langd=1500 --png
  python3 scripts/sammanstallning.py ritning ut/S1.FCStd --uppdrag 2026-001
  python3 scripts/rendera.py ut/S1.FCStd --vyer iso
  python3 scripts/dxf.py ut/S1.FCStd                 # utbredning av alla tråg

Uppbyggnad:
- Stomme VKR20*20*2: två gavelramar, fyra långa liggare och tvärslåar uppe och nere vid mellanväggarna (en hel
  stomme, locket utan skarvar). Ben VKR40*40*3 med toppplåt PL5 och fotplåt PL4.
- Beklädnad PL2: lock bockat ned i gavlarna (framkanten rak och synlig ovanför fronterna), gavlar med
  framkanten inbockad runt stommen. Rygg PL1.5 hela höjden med kabelurtag, täcker lockets och gavlarnas bakkant. Inredning PL1.5: botten, mellanväggar med
  framkanten bockad mot dörrskåpen, en hylla i varje dörrskåp.
- Fronter PL2 som tråg (släta, utan handtag), glipa mellan fronterna. Dörrarna har en gångjärnslist PL12*50
  svetsad mot kantvikningarna med Ø35 för en vanlig gångjärnsskål; lådorna är öppna plåttråg på teleskopskenor.
  Beslagen är utrymmesmodeller: byt dem mot valda beslag ur komponentregistret (k.inkop(komponent=...)).

Koordinater: X längs skåpet (0 = vänster gavel sett framifrån), Y djup (0 = stommens framkant, fronterna i -Y),
Z uppåt (golv z = 0). Måtten räknas ur Variabler vid bygget; ändra med --var och bygg om.
"""

NAMN = "Skap"
MARKE = "S/1"
VARIABLER = [
    ("Langd", 1800, "mm, skåpets längd (3 lika moduler)"),
    ("Djup", 400, "mm, stommens djup inkl. rygg (fronterna 20 mm framför)"),
    ("Hojd", 740, "mm, total höjd till lockets ovansida"),
    ("Benhojd", 100, "mm, golv till stommens underkant"),
    ("Hylla", 420, "mm, hyllans ovansida över golv"),
    ("Glipa", 3, "mm, glipa mellan fronterna"),
    ("Ovrelada", 254, "mm, övre lådfrontens höjd"),
]

REGLER = [dict(villkor="1200 <= Langd <= 2400", text="skåpets längd 1200–2400 mm (tre lika moduler)"),
          dict(villkor="Djup >= 380", text="djupet minst 380 mm (lådskenorna är 350 mm)"),
          dict(villkor="VIKT <= 150", text="skåpet väger högst 150 kg", niva="VARNING")]

RITNING = dict(
    vyer=["fram", "plan"],
    snitt=[dict(namn="C", axel="z", varde=645, mot="-"),        # vågrätt genom de övre gångjärnen och lådskenorna
           dict(namn="A", axel="x", varde=24, mot="-"),         # genom vänster dörrs gångjärn och hyllan
           dict(namn="B", axel="x", varde=900, mot="-")],       # genom lådorna
    detaljer=[dict(vy="A", punkt=(24, 0, 680), radie=60, rubrik="LOCK, DÖRR OCH GÅNGJÄRN",
                   text=["GÅNGJÄRNSLIST pl/10 MED Ø35 SKÅL", "FÄSTE pl/11 FÖR MONTAGEPLATTA"]),
              dict(vy="A", punkt=(24, 20, 110), radie=60, rubrik="BEN OCH STOMMENS UNDERKANT"),
              dict(vy="B", punkt=(900, 0, 600), radie=60, rubrik="LÅDFRONT MOT LÅDA"),
              dict(vy="C", punkt=(20, 10, 645), radie=55, rubrik="GAVEL, DÖRR OCH GÅNGJÄRN (PLAN)"),
              dict(vy="C", punkt=(605, 10, 645), radie=55, rubrik="MELLANVÄGG, SKENA OCH FRONTER (PLAN)")],
    noter=["EXEMPEL – SKÅP I BOCKAD PLÅT MED STOMME AV VKR, EJ FÖR TILLVERKNING",
           "STOMME VKR20*20*2 SVETSAD a2 RUNT OM, BEN VKR40*40*3 MED PL5 TOPP OCH PL4 FOT",
           "BEKLÄDNAD PL2 (LOCK, GAVLAR, FRONTER), INREDNING PL1.5, KANTPRESS INRE RADIE = t",
           "LOCK, GAVLAR OCH RYGG PUNKTSVETSAS/NITAS MOT STOMMEN INIFRÅN – INGA SYNLIGA FÖRBAND",
           "RYGGEN TÄCKER LOCKETS OCH GAVLARNAS BAKKANT (MOT VÄGG)",
           "GÅNGJÄRNSLIST pl/10 SVETSAS MOT FRONTENS KANTVIKNINGAR (EJ MOT SYNLIG YTA)",
           "GÅNGJÄRN, LÅDSKENOR OCH PUSH-OPEN: UTRYMMESMODELLER, MÅTT ENLIGT VALT BESLAG",
           "HYLLBÄRARE OCH VÄGGFÄSTE (TIPPSKYDD) ENL. LEVERANTÖR, EJ RITADE",
           "YTBEHANDLING: PULVERLACK VIT RAL 9016 (ANTAGET)"],
)

R = 20.0            # stommens rör VKR20*20*2
T = 2.0             # synlig beklädnad
t = 1.5             # inredning
FR = 20.0           # frontens djup (tråg)
KANT = 20.0         # bockade kanter
SKENA = (350.0, 12.7, 45.7)     # teleskopskena: längd, tjocklek, höjd (utrymmesmodell)
SKAL = (35.0, 13.0)             # gångjärnsskål: diameter, djup (utrymmesmodell)
GJ_BORR = 5.0       # avstånd dörrkant - skålkant
GJ_FRAN_KANT = 100.0
STOMME = "S235JRH"
PLAT = "S235JR"


def bygg(k, v):
    L, D, H, BEN = v["Langd"], v["Djup"], v["Hojd"], v["Benhojd"]
    G, HY, OL = v["Glipa"], v["Hylla"], v["Ovrelada"]
    M = L / 3.0                             # modulbredd
    xm = (M, 2 * M)                         # mellanväggarnas mitt
    # stommens yttermått (beklädnaden utanpå)
    x0, x1 = T, L - T
    y0, y1 = T, D - T
    z0, z1 = BEN, H - T
    zt = z1 - R                             # övre rörens underkant
    zb = z0 + R                             # nedre rörens överkant

    # ---------------- stomme VKR20*20*2. Hörnstolparna slutar under gavlarnas övre rör ra/4, som går hela djupet:
    # lockets bockradie ligger då mot rörens rundade kanter och inte mot en kapad rörände.
    for x in (x0 + R / 2, x1 - R / 2):
        for y in (y0 + R / 2, y1 - R / 2):
            k.balk("ra/1", "VKR20*20*2", (x, y, z0), (x, y, zt), material=STOMME, huvuddel=(x < L / 2 and y < D / 2))
        k.balk("ra/4", "VKR20*20*2", (x, y0, z1 - R / 2), (x, y1, z1 - R / 2), material=STOMME)
    for x in (x0 + R / 2, x1 - R / 2) + xm:
        for z in ((z0 + R / 2,) if x in (x0 + R / 2, x1 - R / 2) else (z0 + R / 2, z1 - R / 2)):
            k.balk("ra/2", "VKR20*20*2", (x, y0 + R, z), (x, y1 - R, z), material=STOMME)
    for y in (y0 + R / 2, y1 - R / 2):
        for z in (z0 + R / 2, z1 - R / 2):
            k.balk("ra/3", "VKR20*20*2", (x0 + R, y, z), (x1 - R, y, z), material=STOMME)

    # ---------------- ben VKR40*40*3 med toppplåt PL5 60x60 och fotplåt PL4 40x40
    for x in (x0 + 32, xm[0], xm[1], x1 - 32):
        for y in (y0 + 42, y1 - 42):
            k.plat("pl/12", "PL5*60", mitt=(x, y, z0 - 2.5), langd=60, lriktning=(1, 0, 0), briktning=(0, 1, 0), material=PLAT)
            k.balk("ben/1", "VKR40*40*3", (x, y, 4), (x, y, z0 - 5), material=STOMME)
            k.plat("pl/13", "PL4*40", mitt=(x, y, 2), langd=40, lriktning=(1, 0, 0), briktning=(0, 1, 0), material=PLAT)

    # ---------------- lock PL2: delens z nedåt, kanterna ned 20 i gavlarna; bakkanten täcks av ryggen
    k.trag("pl/1", T, L, D - t, KANT, mitt=(L / 2, (D - t) / 2, H), rot=((1, 0, 0), (0, -1, 0), (0, 0, -1)),
           sidor=("-x", "+x"), material=PLAT)
    # gavlar PL2 under lockets kant, framkanten (lokal -x resp. +x) bockad in runt stommens rör
    zg = (z0 + H - KANT) / 2
    k.trag("pl/2", T, y1, H - KANT - z0, KANT, mitt=(0, y1 / 2, zg), rot=((0, 1, 0), (0, 0, 1), (1, 0, 0)),
           sidor=("-x",), material=PLAT)
    k.trag("pl/2", T, y1, H - KANT - z0, KANT, mitt=(L, y1 / 2, zg), rot=((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
           sidor=("+x",), material=PLAT)

    # rygg PL1.5 hela höjden (täcker gavlarnas och lockets bakkant) med ett kabelurtag 100x40 i varje dörrskåp
    rh = H - z0

    def rygg(d):
        sk = d.skiss("Platta", "XY")
        sk.rektangel(L, rh, namn=("Bredd", "Hojd"))
        d.kloss(sk, t, "Tjocklek", symmetrisk=True)
        for i, xc in enumerate((M / 2 - L / 2, L / 2 - M / 2)):
            u = d.skiss("Kabel%d" % i, "XY")
            u.rundad_rektangel(100, 40, 15, mitt=(xc, rh / 2 - 90))
            d.ficka(u, "genom", "Kabelurtag%d" % i)
    k.egen("pl/3", "PL%g*%g" % (t, rh), rygg, mitt=(L / 2, D - t / 2, z0 + rh / 2),
           rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)), material=PLAT)

    # botten PL1.5 på de nedre rören, mellan gavelramarna
    k.plat("pl/4", "PL%g*%g" % (t, y1 - y0), mitt=(L / 2, (y0 + y1) / 2, zb + t / 2), langd=x1 - x0 - 2 * R,
           lriktning=(1, 0, 0), briktning=(0, 1, 0), material=PLAT)

    # mellanväggar PL1.5 mellan botten och övre tvärslån, kanterna bockade mot dörrskåpen (bort från lådorna)
    zv0 = zb + t
    hv = zt - zv0
    for i, xc in enumerate(xm):
        s = -1 if i == 0 else 1
        k.trag("pl/5", t, y1 - y0, hv, KANT, mitt=(xc - s * t / 2, (y0 + y1) / 2, zv0 + hv / 2),
               rot=((0, s, 0), (0, 0, 1), (s, 0, 0)), sidor=("-x", "+x"), material=PLAT)

    # hyllor PL1.5 med fram- och bakkant bockade ned 25
    hy0, hy1 = y0 + 18, y1 - 18
    for xa, xb in ((x0 + R + 2, xm[0] - t / 2 - 2), (xm[1] + t / 2 + 2, x1 - R - 2)):
        k.trag("pl/6", t, xb - xa, hy1 - hy0, 25, mitt=((xa + xb) / 2, (hy0 + hy1) / 2, HY),
               rot=((1, 0, 0), (0, -1, 0), (0, 0, -1)), sidor=("-y", "+y"), material=PLAT)

    # ---------------- fronter PL2 som tråg 20 djupa, bockade bakåt
    fz0, fz1 = z0 + T, H - T - 2            # 2 mm under locket
    fb = M - G                              # frontbredd (glipa G mellan fronterna, G/2 vid gavlarna)
    rot_f = ((1, 0, 0), (0, 0, -1), (0, 1, 0))
    for xc in (M / 2, L - M / 2):
        k.trag("pl/7", T, fb, fz1 - fz0, FR, mitt=(xc, -FR, (fz0 + fz1) / 2), rot=rot_f, material=PLAT)
    zl = fz1 - OL                           # övre lådfrontens underkant
    k.trag("pl/8", T, fb, OL, FR, mitt=(L / 2, -FR, (zl + fz1) / 2), rot=rot_f, material=PLAT)
    k.trag("pl/9", T, fb, zl - G - 1 - fz0, FR, mitt=(L / 2, -FR, (fz0 + zl - G - 1) / 2), rot=rot_f, material=PLAT)

    # gångjärnslist PL12*50 i dörrarna (mellan över- och underkantens vikning) med Ø35 för gångjärnsskålen
    lb, lt = 50.0, 12.0
    lh = fz1 - fz0 - 2 * T
    hz = lh / 2 - (GJ_FRAN_KANT - T)        # skålarnas läge från listens mitt
    for sida in (-1, 1):                    # -1 vänster dörr (gångjärn vänster), +1 höger
        kant = G / 2 if sida < 0 else L - G / 2          # dörrens gångjärnskant
        skal_x = kant - sida * (GJ_BORR + SKAL[0] / 2)
        list_x = kant - sida * (T + lb / 2)
        dx = (skal_x - list_x) * (-sida)                 # skålens läge i listens lokala x

        def list_(d, dx=dx):
            sk = d.skiss("List", "XY")
            sk.rektangel(lb, lh, namn=("Bredd", "Langd"))
            d.kloss(sk, lt, "Tjocklek", symmetrisk=True)
            h = d.skiss("Skal", "XY")
            h.cirkel(SKAL[0], mitt=(dx, hz))
            h.cirkel(SKAL[0], mitt=(dx, -hz))
            d.ficka(h, "genom", "Skalhal")
        rot = ((1, 0, 0), (0, 0, 1), (0, -1, 0)) if sida < 0 else ((-1, 0, 0), (0, 0, 1), (0, 1, 0))
        k.egen("pl/10", "PL%g*%g" % (lt, lb), list_, mitt=(list_x, -lt / 2, (fz0 + fz1) / 2), rot=rot, material=PLAT)
        for z in (fz0 + GJ_FRAN_KANT, fz1 - GJ_FRAN_KANT):
            k.inkop("gj/1", "GÅNGJÄRN (UTRYMMESMODELL, SKÅL)", cylinder=SKAL, mitt=(skal_x, 0, z),
                    rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)), vikt=0.1)
        # fäste för gångjärnens montageplattor: PL5*40 mellan gavelramens rör, insidan i rörens liv
        fx = x0 + R - 2.5 if sida < 0 else x1 - R + 2.5
        k.plat("pl/11", "PL5*40", mitt=(fx, y0 + 48, (z0 + R + zt) / 2), langd=zt - z0 - R,
               lriktning=(0, 0, 1), briktning=(0, 1, 0), material=PLAT)

    # ---------------- lådor PL1.5 (öppna tråg) på teleskopskenor
    sl, st, sh = SKENA
    lx0, lx1 = xm[0] + t / 2 + st, xm[1] - t / 2 - st
    for pos, zb_, hl, zs in (("la/1", zl + 58, 150, zl + 98), ("la/2", fz0 + 28, 280, fz0 + 68)):
        k.trag(pos, t, lx1 - lx0, sl, hl, mitt=((lx0 + lx1) / 2, sl / 2, zb_), material=PLAT)
        for xs in (xm[0] + t / 2 + st / 2, xm[1] - t / 2 - st / 2):
            k.inkop("sk/1", "TELESKOPSKENA (UTRYMMESMODELL)", lada=SKENA, mitt=(xs, y0 + sl / 2, zs),
                    rot=((0, 1, 0), (-1, 0, 0), (0, 0, 1)), vikt=0.5)

    k.utseende({"pl/": "vit", "ra/": "vit", "la/": "vit", "ben/": "tra", "pl/12": "tra", "pl/13": "tra"})
