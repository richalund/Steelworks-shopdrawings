"""Konsolbord/hyllbord i stål med två hyllplan - efter foto av ett svart hyllbord (antagna mått).

Fyra ben av fyrkantrör VKR20*20*1.5 står på en liggande bottenram av samma rör (gerade 45°-hörn) och bär två
hyllplan av kantbockad plåt 1,5 mm med 40 mm nedvikt kant runt om. Hyllplanen ligger mellan benen och skruvas
med M6-skruv genom benet in i hyllans kant (en skruv per bensida, i olika höjd så att de inte korsar varandra).
Benen fästs mot bottenramen med vinkelbeslag k/1 (PL2, 30x30x40) inne i hörnet: beslaget svetsas mot ramen och
genomskruvas M5 med benet, två skruvar per sida.

Antagna mått (fotot saknar måttuppgifter): bredd 800, djup 300, höjd 750 till övre hyllans ovansida, nedre
hyllans ovansida 400 över golv, rör 20x20x1,5, plåt 1,5 med kant 40.

Koordinater: X = bredd, Y = djup bakåt, Z uppåt (golv z = 0). Bredd, Djup, Hojd, HyllaHojd och Kant ligger i
Variabler; rörstorlek och plåttjocklek är fasta tal (ändring kräver ombyggnad).
"""
NAMN = "Konsolbord"
MARKE = "KB/1"
VARIABLER = [
    ("Bredd", 800, "mm, bordets yttre bredd (X)"),
    ("Djup", 300, "mm, bordets yttre djup (Y)"),
    ("Hojd", 750, "mm, höjd till övre hyllans ovansida"),
    ("HyllaHojd", 400, "mm, nedre hyllans ovansida över golv"),
    ("Kant", 40, "mm, hyllplanens nedvikta kant"),
]
RITNING = dict(
    vyer=["fram", "plan", "hoger"],
    dolda=["plan"],
    snitt=[dict(namn="A", axel="z", varde=40, mot="-")],          # genom vinkelbeslagen, sett uppifrån
    noter=["PRELIMINÄR RITNING EFTER FOTO – ALLA MÅTT ÄR ANTAGNA OCH FASTSTÄLLS MED BESTÄLLAREN",
           "EJ FÖR TILLVERKNING FÖRRÄN MÅTT OCH UTFÖRANDE ÄR GODKÄNDA",
           "HYLLPLAN pl/1 KANTBOCKAS AV PL1.5 TILL 760x260x40, KANT 40 NEDVIKT RUNT OM, HÖRNEN SVETSAS OCH SLIPAS",
           "BOTTENRAM b/1, b/2 GERAS 45° OCH SVETSAS a2 RUNT OM, SLIPAS SLÄTT",
           "VINKELBESLAG k/1 SVETSAS MOT BOTTENRAMEN a2, GENOMSKRUVAS M5x30 MED BENEN",
           "HYLLPLAN SKRUVAS M6x30 GENOM BEN st/1 IN I HYLLANS KANT (GÄNGAD MUTTER/NITMUTTER I KANTEN)",
           "ÖPPNA RÖRÄNDAR I BENENS TOPP FÖRSES MED PLASTPLUGG",
           "YTBEHANDLING: PULVERLACK MATT SVART RAL 9005"],
)

ROR = 20.0            # fyrkantrörets sida
T_PLAT = 1.5          # hyllplanens plåttjocklek
BESLAG_T = 2.0        # vinkelbeslagets tjocklek
BESLAG_B = 30.0       # vinkelbeslagets ben
BESLAG_H = 40.0       # vinkelbeslagets höjd
STAL_ROR = "S235JRH"
STAL_PL = "S235JR"
PROFIL_ROR = "VKR%g*%g*1.5" % (ROR, ROR)


def hyllplan(d):
    """Kantbockat hyllplan: plåt med nedvikt kant runt om. Tvärsnittet (U nedåt) i YZ-planet pressas längs X
    med längden Bredd - 2 ROR (= längden i materiallistan), gavlarna läggs till som egna Pad. Kroppens origo i
    hyllans nedre hörn (kantens underkant), hyllans ovansida på z = Kant. Yttermått: (Bredd - 2 ROR) x (Djup - 2 ROR)."""
    t, W = T_PLAT, "Djup - %g" % (2 * ROR)
    sk = d.skiss("Tvarsnitt", "YZ")
    sk.profil([(0, 0), (0, 40), (260, 40), (260, 0), (260 - t, 0), (260 - t, 40 - t), (t, 40 - t), (t, 0)],
              matt={0: "Kant", 1: W, 3: t, 4: "Kant - %g" % t, 6: "Kant - %g" % t, 7: t})
    d.kloss(sk, "Bredd - %g" % (2 * ROR), "Hylla")
    g1 = d.skiss("Gavel1", "YZ")
    g1.rektangel("Djup - %g" % (2 * ROR + 2 * t), "Kant - %g" % t, horn=(t, 0), namn=("", ""))
    d.kloss(g1, t, "GavelV")
    g2 = d.skiss("Gavel2", "YZ", forskjutning="Bredd - %g" % (2 * ROR + t))
    g2.rektangel("Djup - %g" % (2 * ROR + 2 * t), "Kant - %g" % t, horn=(t, 0), namn=("", ""))
    d.kloss(g2, t, "GavelH")


def beslag(d):
    """Vinkelbeslag PL2 30x30, höjd 40: L-formad kontur i XY, Pad uppåt. Hörnet i origo, benen längs +X och +Y."""
    sk = d.skiss("Kontur", "XY")
    b, t = BESLAG_B, BESLAG_T
    sk.profil([(0, 0), (b, 0), (b, t), (t, t), (t, b), (0, b)], matt={0: b, 1: t, 2: b - t, 3: b - t})
    d.kloss(sk, BESLAG_H, "Vinkel")


def bygg(k, v):
    B, D, H, HH, KANT = v["Bredd"], v["Djup"], v["Hojd"], v["HyllaHojd"], v["Kant"]
    r = ROR / 2
    # ---- bottenram: två långa och två korta rör, gerade 45° i hörnen, liggande på golvet
    fram = k.balk("b/1", PROFIL_ROR, (0, r, r), ("Bredd", r, r), upp=(0, 0, 1), material=STAL_ROR)
    bak = k.balk("b/1", PROFIL_ROR, (0, "Djup - %g" % r, r), ("Bredd", "Djup - %g" % r, r), upp=(0, 0, 1), material=STAL_ROR)
    vanster = k.balk("b/2", PROFIL_ROR, (r, 0, r), (r, "Djup", r), upp=(0, 0, 1), material=STAL_ROR)
    hoger = k.balk("b/2", PROFIL_ROR, ("Bredd - %g" % r, 0, r), ("Bredd - %g" % r, "Djup", r), upp=(0, 0, 1), material=STAL_ROR)
    for d_, horn_ in ((fram, ((0, 0), (B, 0))), (bak, ((0, D), (B, D))), (vanster, ((0, 0), (0, D))), (hoger, ((B, 0), (B, D)))):
        for xo, yo in horn_:                       # varje rör geras i sina två ändar
            xi = ROR if xo == 0 else B - ROR
            yi = ROR if yo == 0 else D - ROR
            k.gera(d_, (xo, yo, r), (xi, yi, r))
    # ---- ben: står på bottenramen, toppen i nivå med övre hyllans ovansida
    horn = [(r, r), ("Bredd - %g" % r, r), (r, "Djup - %g" % r), ("Bredd - %g" % r, "Djup - %g" % r)]
    ben = [k.balk("st/1", PROFIL_ROR, (x, y, ROR), (x, y, "Hojd"), upp=(0, 1, 0), material=STAL_ROR, huvuddel=(i == 0))
           for i, (x, y) in enumerate(horn)]
    # ---- hyllplan: mellan benen, ovansidan på Hojd resp. HyllaHojd
    ovre = k.egen("pl/1", "PL%g*%g" % (T_PLAT, 300 - 2 * ROR), hyllplan, mitt=(ROR, ROR, "Hojd - Kant"), material=STAL_PL)
    nedre = k.egen("pl/1", "PL%g*%g" % (T_PLAT, 300 - 2 * ROR), hyllplan, mitt=(ROR, ROR, "HyllaHojd - Kant"), material=STAL_PL)
    # ---- vinkelbeslag i hörnen ovanpå ramen, mot benens innersidor; svetsas mot ramen
    rotz = {0: ((1, 0, 0), (0, 1, 0), (0, 0, 1)), 90: ((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
            180: ((-1, 0, 0), (0, -1, 0), (0, 0, 1)), 270: ((0, -1, 0), (1, 0, 0), (0, 0, 1))}
    beslag_lagen = [((ROR, ROR, ROR), 0), (("Bredd - %g" % ROR, ROR, ROR), 90),
                    (("Bredd - %g" % ROR, "Djup - %g" % ROR, ROR), 180), ((ROR, "Djup - %g" % ROR, ROR), 270)]
    besl = [k.egen("k/1", "PL%g*%g" % (BESLAG_T, BESLAG_B), beslag, mitt=m, rot=rotz[a], material=STAL_PL)
            for m, a in beslag_lagen]
    # ---- skruvhål hyllplan-ben: M6 genom benet in i hyllans kant. Y-skruv (genom fram-/baksidan) 12 mm under
    #      hyllans ovansida, X-skruv (genom gaveln) 28 mm under, så att de inte korsas i benet.
    for hylla, z in ((ovre, "Hojd"), (nedre, "HyllaHojd")):
        zy, zx = "%s - 12" % z, "%s - 28" % z
        k.hal([ben[0], ben[1], hylla], [(r, r, zy), ("Bredd - %g" % r, r, zy)], (0, 1, 0), bult="M6x30", langd=60)
        k.hal([ben[2], ben[3], hylla], [(r, "Djup - %g" % r, zy), ("Bredd - %g" % r, "Djup - %g" % r, zy)], (0, 1, 0), bult="M6x30", langd=60)
        k.hal([ben[0], ben[2], hylla], [(r, r, zx), (r, "Djup - %g" % r, zx)], (1, 0, 0), bult="M6x30", langd=60)
        k.hal([ben[1], ben[3], hylla], [("Bredd - %g" % r, r, zx), ("Bredd - %g" % r, "Djup - %g" % r, zx)], (1, 0, 0), bult="M6x30", langd=60)
    # ---- skruvhål beslag-ben: M5 genom benet och beslaget, två per sida (z = 32 och 48), mitt på beslagets ben
    c = ROR + BESLAG_B / 2 + 1                     # beslagets ben: från ROR till ROR + 30; skruven i mitten + 1
    zz = (ROR + 12, ROR + 28)
    k.hal([ben[0], besl[0], ben[1], besl[1]], [(r, r, z) for z in zz] + [("Bredd - %g" % r, r, z) for z in zz], (0, 1, 0), bult="M5x30", langd=50)
    k.hal([ben[2], besl[2], ben[3], besl[3]], [(r, "Djup - %g" % r, z) for z in zz] + [("Bredd - %g" % r, "Djup - %g" % r, z) for z in zz], (0, 1, 0), bult="M5x30", langd=50)
    k.hal([ben[0], besl[0], ben[2], besl[3]], [(r, r, z) for z in zz] + [(r, "Djup - %g" % r, z) for z in zz], (1, 0, 0), bult="M5x30", langd=50)
    k.hal([ben[1], besl[1], ben[3], besl[2]], [("Bredd - %g" % r, r, z) for z in zz] + [("Bredd - %g" % r, "Djup - %g" % r, z) for z in zz], (1, 0, 0), bult="M5x30", langd=50)
    k.ritning(**RITNING)
