"""TV-skåp i bockad plåt med stomme av fyrkantsrör - efter kundens foton av en vit högglansig skänk med tre
moduler (dörr | två lådor | dörr) på fyra-kantiga ben (förebilden motsvarar IKEA BESTÅ 180x42x74).

Uppbyggnad (en hel stomme, inga skarvar i locket):
- Stomme VKR20*20*2: två gavelramar, fyra långa liggare (fram/bak, uppe/nere) och tvärslåar uppe och nere vid
  mellanväggarna. Åtta ben VKR40*40*3 med toppplåt och fotplåt under stommen.
- Beklädnad PL2 (synliga ytor): lock bockat ned 20 mm i gavlar och bak, gavlar bockade in 20 mm runt framkanten,
  rygg PL1.5 med två kabelurtag. Inredning PL1.5: botten, två mellanväggar med framkant bockad 20 mm, en hylla i
  varje dörrskåp.
- Fronter PL2 bockade som tråg 20 mm djupa (släta, utan handtag): två dörrar och två lådfronter, glipa 3 mm.
  Dörrarna har en svetsad gångjärnslist PL12*50 med Ø35 för gångjärnsskålen; Blum CLIP top 110° utan fjäder och
  TIP-ON (push-open). Lådorna är plåtlådor PL1.5 på Accuride 3832TR push-open-skenor 350 mm.

Koordinater: X längs skåpet (0 = vänster gavel sett framifrån), Y djup (0 = stommens framkant, fronterna i -Y),
Z uppåt (golv z = 0). Måtten räknas ur Variabler vid bygget; ändra med --var och bygg om.
"""

NAMN = "TV-skap"
MARKE = "S/1"
VARIABLER = [
    ("Langd", 1800, "mm, skåpets längd (3 moduler)"),
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
    snitt=[dict(namn="C", axel="z", varde=645, mot="-"),        # vågrätt genom övre gångjärnen och lådskenorna
           dict(namn="A", axel="x", varde=24, mot="-"),         # genom vänster dörrs gångjärn och hyllan
           dict(namn="B", axel="x", varde=900, mot="-")],       # genom lådorna
    detaljer=[dict(vy="A", punkt=(24, 0, 680), radie=60, rubrik="LOCK, DÖRR OCH GÅNGJÄRN",
                   text=["GÅNGJÄRNSLIST pl/10 MED Ø35 SKÅL", "FÄSTE pl/11 FÖR MONTAGEPLATTA"]),
              dict(vy="A", punkt=(24, 20, 110), radie=60, rubrik="BEN OCH STOMMENS UNDERKANT"),
              dict(vy="B", punkt=(900, 0, 600), radie=60, rubrik="LÅDFRONT MOT LÅDA",
                   text=["FRONT pl/8 SKRUVAS MOT la/1"]),
              dict(vy="C", punkt=(20, 10, 645), radie=55, rubrik="GAVEL, DÖRR OCH GÅNGJÄRN (PLAN)"),
              dict(vy="C", punkt=(605, 10, 645), radie=55, rubrik="MELLANVÄGG, SKENA OCH FRONTER (PLAN)")],
    noter=["PRELIMINÄR RITNING EFTER KUNDENS FOTON – EJ FÖR TILLVERKNING FÖRRÄN MÅTT OCH UTFÖRANDE ÄR GODKÄNDA",
           "UNDERLAG: 5 FOTON AV BEFINTLIG SKÄNK (MOTSV. IKEA BESTÅ 180x42x74). GLIPOR, HYLL- OCH LÅDHÖJDER ANTAGNA",
           "STOMME VKR20*20*2 S235JRH SVETSAD a2 RUNT OM, BEN VKR40*40*3 MED PL5 TOPP OCH PL4 FOT. HÖRNSTOLPARNAS ra/1 ÖVRE ÄNDAR SLIPAS R2 MOT LOCKETS BOCKRADIE",
           "BEKLÄDNAD PL2 (LOCK, GAVLAR, FRONTER), INREDNING PL1.5, S235JR, KANTPRESS INRE RADIE = t",
           "LOCK, GAVLAR OCH RYGG PUNKTSVETSAS/NITAS MOT STOMMEN INIFRÅN – INGA SYNLIGA FÖRBAND PÅ UTSIDAN",
           "DÖRRAR: GÅNGJÄRNSLIST pl/10 SVETSAS MOT FRONTENS KANTVIKNINGAR (EJ MOT SYNLIG YTA), 2*Ø35 SKÅL, M4 GÄNGAT",
           "GÅNGJÄRN BLUM 70T3550 + MONTAGEPLATTA PÅ pl/11, ÖVERLAPP 20,5 – KONTROLLERAS MOT BLUMS TABELL",
           "PUSH-OPEN DÖRRAR: BLUM TIP-ON FÖR DÖRRAR I STOMMEN, ENL. LEVERANTÖR, EJ RITAD. SKÅPET SKA FÄSTAS I VÄGG (TIPPSKYDD), FÄSTE ENL. VÄGGTYP",
           "LÅDFRONT MOT LÅDANS GAVEL 4 st M5 (BLINDNITMUTTER I KANTVIKNINGEN). HYLLA PÅ HYLLBÄRARE Ø5, HÅLRAD c/c 32, EJ RITADE",
           "YTBEHANDLING: PULVERLACK VIT HÖGGLANS RAL 9016, BEN PULVERLACK EKTON ENL. BESTÄLLNING",
           ],
)

R = 20.0            # stommens rör VKR20*20*2
T = 2.0             # synlig beklädnad
t = 1.5             # inredning
FR = 20.0           # frontens djup (tråg)
KANT = 20.0         # bockade kanter
SKENA = 12.7        # Accuride 3832TR, tjocklek enl. datablad
SKENA_L = 350.0
SKENA_H = 45.7
GJ_BORR = 5.0       # Blum: avstånd dörrkant - skålkant (3-7)
GJ_FRAN_KANT = 100.0
STOMME = "S235JRH"
PLAT = "S235JR"


def trag(k, lada, *a, **kw):
    """k.trag och sedan flyttning av bottenskissen så att delens låda blir `lada` = (x0, x1, y0, y1, z0, z1).
    k.trag (skill 2026.10.18) lägger tråget en plåttjocklek fel när delens z pekar i negativ riktning eller bara
    en sida bockas; måtten blir rätt men inte läget."""
    import FreeCAD as App
    from FreeCAD import Vector as V
    o = k.trag(*a, **kw)
    sk = next(x for x in o.OutListRecursive if x.TypeId == "Sketcher::SketchObject")
    bb = o.Shape.BoundBox
    d = V((lada[0] + lada[1]) / 2 - bb.Center.x, (lada[2] + lada[3]) / 2 - bb.Center.y, (lada[4] + lada[5]) / 2 - bb.Center.z)
    if d.Length > 0.01:
        sk.Placement = App.Placement(sk.Placement.Base + d, sk.Placement.Rotation)
        k.doc.recompute()
    bb = o.Shape.BoundBox
    fel = max(abs(bb.XLength - (lada[1] - lada[0])), abs(bb.YLength - (lada[3] - lada[2])), abs(bb.ZLength - (lada[5] - lada[4])))
    if fel > 0.2:
        raise RuntimeError("tråg %s blev %.1f x %.1f x %.1f, väntat lådan %s" % (a[0], bb.XLength, bb.YLength, bb.ZLength, lada))
    return o


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

    # ---------------- stomme VKR20*20*2
    for x in (x0 + R / 2, x1 - R / 2):
        for y in (y0 + R / 2, y1 - R / 2):
            k.balk("ra/1", "VKR20*20*2", (x, y, z0), (x, y, z1), material=STOMME, huvuddel=(x < L / 2 and y < D / 2))
    for x in (x0 + R / 2, x1 - R / 2) + xm:
        for z in (z0 + R / 2, z1 - R / 2):
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

    # ---------------- lock PL2, kanterna ned 20 i gavlarna och bak (framkanten rak, synlig ovanför fronterna)
    trag(k, (0, L, 0, D, H - KANT, H), "pl/1", T, L, D, KANT, mitt=(L / 2, D / 2, H), rot=((1, 0, 0), (0, -1, 0), (0, 0, -1)),
           sidor=("-x", "+x", "-y"), material=PLAT)
    # gavlar PL2 (under lockets kant), framkanten bockad in 20 runt stommens rör
    zg = (z0 + H - KANT) / 2
    trag(k, (0, KANT, 0, y1, z0, H - KANT), "pl/2", T, y1, H - KANT - z0, KANT, mitt=(0, y1 / 2, zg), rot=((0, 1, 0), (0, 0, 1), (1, 0, 0)),
           sidor=("-x",), material=PLAT)
    trag(k, (L - KANT, L, 0, y1, z0, H - KANT), "pl/2", T, y1, H - KANT - z0, KANT, mitt=(L, y1 / 2, zg), rot=((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
           sidor=("+x",), material=PLAT)

    # rygg PL1.5 med två kabelurtag 100x40 R15 i dörrskåpen
    rh = H - KANT - z0

    def rygg(d):
        sk = d.skiss("Platta", "XY")
        sk.rektangel(L, rh, namn=("Bredd", "Hojd"))
        d.kloss(sk, t, "Tjocklek", symmetrisk=True)
        for i, xc in enumerate((M / 2 - L / 2, L / 2 - M / 2)):
            u = d.skiss("Kabel%d" % i, "XY")
            u.rundad_rektangel(100, 40, 15, mitt=(xc, rh / 2 - 70))
            d.ficka(u, "genom", "Kabelurtag%d" % i)
    k.egen("pl/3", "PL%g*%g" % (t, rh), rygg, mitt=(L / 2, D - t / 2, z0 + rh / 2),
           rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)), material=PLAT)

    # botten PL1.5 på de nedre rören, mellan gavelramarna
    k.plat("pl/4", "PL%g*%g" % (t, y1 - y0), mitt=(L / 2, (y0 + y1) / 2, zb + t / 2), langd=x1 - x0 - 2 * R,
           lriktning=(1, 0, 0), briktning=(0, 1, 0), material=PLAT)

    # mellanväggar PL1.5 mellan botten och övre tvärslån, kanterna bockade mot dörrskåpen
    zv0 = zb + t
    hv = zt - zv0
    for i, xc in enumerate(xm):
        s = -1 if i == 0 else 1             # bockningarnas riktning (mot dörrskåpet)
        xa = xc - s * t / 2                 # väggens yttersida (mot lådorna)
        trag(k, (min(xa, xa + s * KANT), max(xa, xa + s * KANT), y0, y1, zv0, zt), "pl/5", t, y1 - y0, hv, KANT, mitt=(xc - s * t / 2, (y0 + y1) / 2, zv0 + hv / 2),
               rot=((0, s, 0), (0, 0, 1), (s, 0, 0)), sidor=("-x", "+x"), material=PLAT)

    # hyllor PL1.5 med fram- och bakkant bockade ned 25
    hy0, hy1 = y0 + 18, y1 - 18
    for xa, xb in ((x0 + R + 2, xm[0] - t / 2 - 2), (xm[1] + t / 2 + 2, x1 - R - 2)):
        trag(k, (xa, xb, hy0, hy1, HY - 25, HY), "pl/6", t, xb - xa, hy1 - hy0, 25, mitt=((xa + xb) / 2, (hy0 + hy1) / 2, HY),
               rot=((1, 0, 0), (0, -1, 0), (0, 0, -1)), sidor=("-y", "+y"), material=PLAT)

    # ---------------- fronter PL2 som tråg 20 djupa, bockade bakåt
    fz0, fz1 = z0 + T, H - T - 2            # 2 mm under locket
    fb = M - G                              # frontbredd (glipa G mellan fronterna, G/2 vid gavlarna)
    rot_f = ((1, 0, 0), (0, 0, -1), (0, 1, 0))
    for pos, xc in (("pl/7", M / 2), ("pl/7", L - M / 2)):
        k.trag(pos, T, fb, fz1 - fz0, FR, mitt=(xc, -FR, (fz0 + fz1) / 2), rot=rot_f, material=PLAT)
    zl = fz1 - OL                           # övre lådfrontens underkant
    k.trag("pl/8", T, fb, OL, FR, mitt=(L / 2, -FR, (zl + fz1) / 2), rot=rot_f, material=PLAT)
    k.trag("pl/9", T, fb, zl - G - 1 - fz0, FR, mitt=(L / 2, -FR, (fz0 + zl - G - 1) / 2), rot=rot_f, material=PLAT)

    # gångjärnslist PL12*50 i dörrarna (mellan över- och underkantens vikning), Ø35 för gångjärnsskålen
    lb, lt = 50.0, 12.0
    lh = fz1 - fz0 - 2 * T
    hz = lh / 2 - (GJ_FRAN_KANT - T)        # skålarnas läge från listens mitt
    for sida in (-1, 1):                    # -1 vänster dörr (gångjärn vänster), +1 höger
        kant = G / 2 if sida < 0 else L - G / 2          # dörrens gångjärnskant
        skal_x = kant - sida * (GJ_BORR + 17.5)
        list_x = kant - sida * (T + lb / 2)
        dx = (skal_x - list_x) * (-sida)                 # skålens läge i listens lokala x

        def list_(d, dx=dx):
            sk = d.skiss("List", "XY")
            sk.rektangel(lb, lh, namn=("Bredd", "Langd"))
            d.kloss(sk, lt, "Tjocklek", symmetrisk=True)
            h = d.skiss("Skal", "XY")
            h.cirkel(35, mitt=(dx, hz))
            h.cirkel(35, mitt=(dx, -hz))
            d.ficka(h, "genom", "Skalhal")
        rot = ((1, 0, 0), (0, 0, 1), (0, -1, 0)) if sida < 0 else ((-1, 0, 0), (0, 0, 1), (0, 1, 0))
        k.egen("pl/10", "PL%g*%g" % (lt, lb), list_, mitt=(list_x, -lt / 2, (fz0 + fz1) / 2), rot=rot, material=PLAT)
        for z in (fz0 + GJ_FRAN_KANT, fz1 - GJ_FRAN_KANT):
            k.inkop("gj/1", komponent="gj-blum-70t3550", mitt=(skal_x, 0, z), rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)))
        # fäste för gångjärnens montageplattor i stommen: PL5*40 mellan gavelramens rör, insida i rörens liv
        fx = x0 + R - 2.5 if sida < 0 else x1 - R + 2.5
        k.plat("pl/11", "PL5*40", mitt=(fx, y0 + 48, (z0 + R + zt) / 2), langd=zt - z0 - R,
               lriktning=(0, 0, 1), briktning=(0, 1, 0), material=PLAT)

    # ---------------- lådor PL1.5 (öppna tråg) på push-open-skenor
    lx0, lx1 = xm[0] + t / 2 + SKENA, xm[1] - t / 2 - SKENA
    for pos, zb_, hl, zs in (("la/1", zl + 58, 150, zl + 98), ("la/2", fz0 + 28, 280, fz0 + 68)):
        k.trag(pos, t, lx1 - lx0, SKENA_L, hl, mitt=((lx0 + lx1) / 2, SKENA_L / 2, zb_), material=PLAT)
        for xs in (xm[0] + t / 2 + SKENA / 2, xm[1] - t / 2 - SKENA / 2):
            k.inkop("sk/1", komponent="skena-accuride-3832tr-350", mitt=(xs, y0 + SKENA_L / 2, zs),
                    rot=((0, 1, 0), (-1, 0, 0), (0, 0, 1)))

    k.utseende({"pl/": "vit", "ra/": "vit", "la/": "vit", "ben/": "tra", "pl/12": "tra", "pl/13": "tra"})
