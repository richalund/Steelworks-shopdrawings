"""Primärbalk på pelare (förstärkning av ett befintligt bjälklag): IPE-balk med hålgrupper i underflänsen mot
pelarnas toppplåtar och livavstyvningar på båda sidor om livet vid varje pelare – efter en svensk K-handling
(tillverkning balkar, A1) för en entresol.

- Pelarlägen: Kant + n x Spann (konstruktörens "CA"-mått som kontrolleras på plats, därför variabler).
- Hålgrupp 4*Ø11 c/c 150 x 70 i underflänsen per pelare, för 2+2 M10 genom toppplåten (se pelare.py).
- Livavstyvning pl/1 PL10*50, höjd = livets fria höjd avrundad nedåt; hörnen mot livet rundas med profilens
  livradie r (12 för IPE220), så att plåten går fri från radien utan fas och utan krock.
- Hålen sitter i underflänsen: ritningen visar balken underifrån (vy "under"), annars syns de inte som cirklar.
  Detaljblad med balkänden underifrån och livavstyvningen.

Koordinater: X längs balken, Y tvärs, Z uppåt; balkens underkant z = 0.
"""
import stal

NAMN = "Primarbalk"
MARKE = "SB1"
VARIABLER = [
    ("Langd", 8000, "mm, balkens längd (CA, kontrolleras på plats)"),
    ("Kant", 100, "mm, balkände till första pelarens centrum"),
    ("Spann", 2600, "mm, pelare c/c (CA, kontrolleras på plats)"),
    ("Pelare", 4, "antal pelare (kräver ombyggnad)"),
]
PROFIL = "IPE220"
HAL = dict(ccx=150, ccy=70, d=11, bult="M10x40")       # mot toppplåt PL10*120 L=200 på pelaren
STYV = dict(bredd=50, t=10)

RITNING = dict(
    vyer=["fram", "under"],                              # underflänsens hål syns underifrån
    snitt=[dict(namn="A", axel="x", varde=100, mot="-")],
    detaljer=[dict(vy="under", punkt=(100, 0, 0), radie=150, rubrik="BALKÄNDE, UNDERFLÄNS (UNDERIFRÅN)",
                   text=["4*Ø11 c/c 150 x 70, 25 FRÅN BALKÄNDE"],
                   matt=[dict(typ="y", varde=110, lage="vanster"), dict(typ="d", varde=11, lage="over")]),
              dict(vy="fram", punkt=(2700, 0, 110), radie=150, rubrik="LIVAVSTYVNING pl/1 VID PELARE",
                   text=["pl/1 PL10*50 L=200, BÅDA SIDOR", "R12 MOT LIVET (LIVRADIE)"],
                   matt=[dict(typ="y", varde=200, lage="hoger")])],
    noter=["PRELIMINÄR RITNING – EJ FÖR TILLVERKNING",
           "TESTRITNING UR FREECAD",
           "CA-MÅTT (LANGD, SPANN) KONTROLLERAS PÅ PLATS",
           "SVETS: LIVAVSTYVNINGAR pl/1 a4 (BÅDA SIDOR OM LIVET VID VARJE PELARE)",
           "R12 PÅ pl/1 VÄND MOT LIVET (LIVRADIE)",
           "MONTAGE: BALK MOT PELARE 2+2 M10 8.8 MED MUTTER OCH BRICKOR, PELARE SE pelare.py",
           "YTBEHANDLING ENLIGT BESTÄLLNING"],
)


def bygg(k, v):
    p = stal.tolka(PROFIL, kallor=False)
    h, tw, tf, r = p["h"], p["tw"], p["tf"], p["r"]
    hs = int((h - 2 * tf) // 5 * 5)                      # livets fria höjd, avrundad nedåt till 5 mm
    b = k.balk("b/1", PROFIL, (0, 0, h / 2), ("Langd", 0, h / 2), upp=(0, 0, 1), huvuddel=True)

    def livavstyvning(d):                                # x ut från livet, y = höjd, z = tjocklek
        sk = d.skiss("Kontur", "XY")
        sk.rektangel(STYV["bredd"], hs, namn=("Bredd", "Hojd"))
        d.kloss(sk, STYV["t"], "Platta")
        d.avrunda(r, {"parallell": "Z", "lada": ["xmin", "y"]}, "Livradie")   # hörnen mot livet

    ym = tw / 2 + STYV["bredd"] / 2
    for i in range(int(v["Pelare"])):
        x = "Kant" if i == 0 else "Kant + %d * Spann" % i
        k.hal([b], [("%s %+g" % (x, dx), dy, tf / 2) for dx in (-HAL["ccx"] / 2, HAL["ccx"] / 2)
                    for dy in (-HAL["ccy"] / 2, HAL["ccy"] / 2)],
              riktning=(0, 0, 1), d=HAL["d"], bult=HAL["bult"], langd=2 * tf)   # bara genom underflänsen
        for s in (1, -1):
            k.egen("pl/1", "PL%g*%g" % (STYV["t"], STYV["bredd"]), livavstyvning,
                   mitt=("%s %+g" % (x, -s * STYV["t"] / 2), s * ym, h / 2),
                   rot=((0, s, 0), (0, 0, 1), (s, 0, 0)), material="S355N")
    k.ritning(**RITNING)
