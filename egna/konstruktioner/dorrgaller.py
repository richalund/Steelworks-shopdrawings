"""Solgaller till dörrglas - efter foto av en entrédörr med strålformat galler (ring i mitten, plattstänger
ut till karmen).

Gallret sitter utanpå dörrens glasöppning: en plan ring pl/1 (PL5, Ø160/Ø120) i mitten och 16 plattstänger
PL20*5 (liggande, bredsidan mot glaset) som strålar ut från ringen till öppningens kant. Vid kanten är varje
stång bockad ned mot karmen (lyft 15 mm över 20 mm) och slutar i en 40 mm fot med ett Ø5,5 hål för träskruv.
Stängerna svetsas mot ringens utsida (a3). Alla mått är ANTAGNA efter fotot: glasöppning 700 x 1050, ring
Ø160, stångändar jämnt fördelade längs karmen (3 per kortsida, 5 per långsida). Lägen och antal stänger
kräver ombyggnad (bygg med --var); ringen och stångprofilen är fasta tal i skriptet.

Koordinater: X = dörrens bredd, Z uppåt, Y = dörrens tjocklek. Karmens yta (fötterna) ligger i y = 0, stängerna
på lyftet framför (y < 0, mot betraktaren i framvyn), glaset bakom karmytan (ritas inte).
"""
import math

NAMN = "Solgaller dörr"
MARKE = "G/1"
VARIABLER = [
    ("Bredd", 700, "mm, glasöppningens bredd (X) - antagen"),
    ("Hojd", 1050, "mm, glasöppningens höjd (Z) - antagen"),
    ("Lyft", 15, "mm, fritt mått karmyta - stångens undersida"),
    ("Fot", 40, "mm, fotens längd på karmen"),
    ("Bock", 20, "mm, bockens längd i planet (lyftet tas upp över detta mått)"),
    ("HalD", 5.5, "mm, hål i foten för träskruv"),
]
RITNING = dict(
    vyer=["fram"],
    snitt=[dict(namn="A", axel="x", varde=0, mot="-")],       # genom ringen och de lodräta stängerna
    noter=["PRELIMINÄR RITNING – ALLA MÅTT ANTAGNA EFTER FOTO, KONTROLLERAS MOT DÖRREN PÅ PLATS",
           "GLASÖPPNING ANTAGEN 700x1050. STÅNGÄNDARNA BOCKAS VID ÖPPNINGENS KANT",
           "STÄNGER sp/1–sp/5 PL20*5 LIGGANDE, SVETSAS MOT RINGEN pl/1 a3 (BÅDA SIDOR)",
           "FÖTTER: 16 st Ø5.5 MITT I FOTEN (20 FRÅN ÄNDEN) FÖR TRÄSKRUV 4.5x40, SKRUVAS I KARMEN. SE DETALJ B",
           "STÅNGLÄNGD I LISTAN = RAK DEL. TILLÄGG PER STÅNG: BOCK 25 + FOT 40 (RAKLÄNGD + 65)",
           "YTBEHANDLING: GRUNDAD OCH MÅLAD, GULDMETALLIC (MÄSSINGSTON) ENLIGT BESTÄLLNING"],
)

RING_D, RING_DI = 160.0, 120.0      # ringens ytter-/innerdiameter
T, B = 5.0, 20.0                    # plattstång PL20*5
STAL = "S235JR"


def bygg(k, v):
    import pd
    W, H, lyft, fot, bock, hd = v["Bredd"], v["Hojd"], v["Lyft"], v["Fot"], v["Bock"], v["HalD"]
    yc = -(lyft + T / 2)                                  # stängernas och ringens mittplan (karmytan y = 0)

    # ---- ringen pl/1: plan skiva Ø160/Ø120 x 5, pad mot -y
    def ring(d):
        sk = d.skiss("Kontur", "XY")
        sk.cirkel(RING_D, namn="D")
        sk.cirkel(RING_DI, namn="Di")
        d.kloss(sk, T, "Ring")
    k.egen("pl/1", "PL%g RING" % T, ring, mitt=(0, yc + T / 2, 0), rot=((1, 0, 0), (0, 0, 1), (0, -1, 0)),
           material=STAL, huvuddel=True)

    # ---- stångändar längs öppningens kant: 3 per kortsida, 5 per långsida (16 st)
    andar = []                                            # (pos, x, z)
    for s in (1, -1):
        for i, x in enumerate((0, round(W / 3))):          # bockdelning avrundad: 117-233-233-117 på 700
            andar.append(("sp/%d" % (i + 1), x, s * H / 2))
            if x:
                andar.append(("sp/%d" % (i + 1), -x, s * H / 2))
        for i, z in enumerate((0, round(H / 5), 2 * round(H / 5))):
            andar.append(("sp/%d" % (i + 3), s * W / 2, z))
            if z:
                andar.append(("sp/%d" % (i + 3), s * W / 2, -z))

    for pos, x, z in andar:
        r = math.hypot(x, z)
        ux, uz = x / r, z / r
        r0 = RING_D / 2 + 1.0                             # 1 mm svetsspalt mot ringen
        L = round(r - r0, 1)
        o = k.balk(pos, "PL%g*%g" % (B, T), (ux * r0, yc, uz * r0), (ux * (r0 + L), yc, uz * (r0 + L)),
                   upp=(0, 1, 0), material=STAL)
        # bockad fot i samma kropp: profil i kroppens YZ-plan (x = tjocklek, y = längs stången), pad = bredden
        dd = pd.Del(k.doc, o.Name)
        sk = dd.skiss("Fotprofil", "YZ")
        p = [(-T / 2, L), (T / 2, L), (T / 2 + lyft, L + bock), (T / 2 + lyft, L + bock + fot),
             (lyft - T / 2, L + bock + fot), (lyft - T / 2, L + bock)]
        g = sk.profil(p, matt={0: T, 2: "Fot", 3: T}, start=(-T / 2, L))
        sk.matt("DistanceX", g[1], pd.START, g[1], pd.SLUT, varde="Lyft")
        sk.matt("DistanceY", g[1], pd.START, g[1], pd.SLUT, varde="Bock")
        sk.begr("Parallel", g[5], g[1])
        dd.kloss(sk, B, "Fot", symmetrisk=True)
        hal = dd.skiss("Skruvhal", "XZ")
        hal.cirkel("HalD", mitt=(0, L + bock + fot / 2), namn="")
        dd.ficka(hal, "genom", "Skruvhal")
        dd.stada()
    k.ritning(**RITNING)
