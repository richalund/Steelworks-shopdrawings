"""Stålpelare VKR med fotplåt och toppplåt. Pelaren står i origo, Z uppåt.
Fotplåten har 4 hål för kemankare (Ø18 för M16), toppplåten 4 hål för balkanslutning (Ø14 - M12)."""
NAMN = "Pelare"
MARKE = "SP1/1"
VARIABLER = [
    ("Hojd", 2500, "mm, total höjd inkl. plåtar"),
    ("Profil", 100, "mm, VKR-storlek (kvadratisk)"),
    ("Gods", 6.3, "mm, VKR-godstjocklek"),
    ("Fot", 200, "mm, fotplåtens sida"),
    ("FotT", 15, "mm, fotplåtens tjocklek"),
    ("Topp", 150, "mm, toppplåtens sida"),
    ("ToppT", 10, "mm, toppplåtens tjocklek"),
]
RITNING = dict(
    vyer=["fram", "plan"],
    snitt=[dict(namn="A", axel="z", varde=150, mot="-")],
    stomnat="C/3",
    noter=["PRELIMINÄR RITNING – EJ FÖR TILLVERKNING",
           "SVETS: FOT- OCH TOPPLÅT MOT VKR a5 RUNT OM",
           "FOTPLÅT pl/1 FÄSTS MED KEMANKARE M16, UNDERGJUTNING 30 MM",
           "YTBEHANDLING ENLIGT BESTÄLLNING"],
)


def bygg(k, v):
    H, a, t = v["Hojd"], v["Profil"], v["Gods"]
    F, ft, T, tt = v["Fot"], v["FotT"], v["Topp"], v["ToppT"]
    vkr = "VKR%g*%g" % (a, t)
    k.balk("c/1", vkr, (0, 0, ft), (0, 0, H - tt), upp=(0, 1, 0), huvuddel=True)
    fot = k.plat("pl/1", "PL%g*%g" % (ft, F), mitt=(0, 0, ft / 2), langd=F, lriktning=(1, 0, 0), briktning=(0, 1, 0))
    topp = k.plat("pl/2", "PL%g*%g" % (tt, T), mitt=(0, 0, H - tt / 2), langd=T, lriktning=(1, 0, 0), briktning=(0, 1, 0))
    c = F / 2 - 40
    k.hal([fot], [(x, y, ft / 2) for x in (-c, c) for y in (-c, c)], riktning=(0, 0, 1), bult="M16")
    c = T / 2 - 25
    k.hal([topp], [(x, y, H - tt / 2) for x in (-c, c) for y in (-c, c)], riktning=(0, 0, 1), bult="M12x40")
    k.ritning(**RITNING)
