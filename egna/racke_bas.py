"""Gemensam byggare för smidesräcken i stilen från P. Hellstones förebilder (mail 2026-10-17): fyrkantiga
stolpar FS20 nedgjutna i granitstegen, plan handledare PL40*8 med smidd snäcka i nedre änden, överliggare
PL30*8 på högkant under handledaren, underliggare PL40*8 plant, stående spjälor D12 mellan liggarna med fri
öppning < 100 mm.

Räcket följer en framkantslinje (polylinje i lokala x, z: trapplopp och plana partier med knäckar) och står på
ytan yta(x). Handledaren ligger Hojd lodrätt över linjen och delas i knäckarna (hl/1, hl/2 ... bockas eller
svetsas). Stolparnas lägen ges av konstruktionsskriptet; vid en knäck står stolpen på den plana sidan.
Liggare och spjälor räknas per fack mellan stolparna.

Lokala koordinater: X längs räcket (uppför), Y tvärs (räckesplanet y = 0), Z uppåt. `ursprung`, `ex`, `ey`
placerar räcket i en större modell (översikten T/1).
Snäckan: handledarens nedre ände fortsätter 150 mm rakt förbi stolpen och rullas sedan ihop nedåt i 1,5 varv
(mittlinjeradier 42, 28, 16) – tangerande bågar i en skiss på handledarens kropp, Pad 40.
Måtten räknas ut i Python (sned geometri): ändrade mått kräver ombyggnad (sammanstallning.py bygg).
"""
import math

STAL = "S235JR"
HL_B, HL_T = 40.0, 8.0          # handledare PL40*8, plant
OL_H, OL_T = 30.0, 8.0          # överliggare PL30*8 på högkant
UL_B, UL_T = 40.0, 8.0          # underliggare PL40*8, plant
SPJ_D = 12.0                    # spjäla D12
ST_A = 20.0                     # stolpe FS20
INGJUT = 100.0                  # stolparnas ingjutning i stenen
SNACKA_RAK = 150.0              # rak handledare förbi nedersta stolpen före snäckan
SNACKA_R = (42.0, 28.0, 16.0)   # snäckans mittlinjeradier, tre halvvarv
SPALT = 2.0                     # svetsspalt vid liggarnas ändar
KNACK_SPALT = 1.5               # spalt per sida i handledarens knäck

VARIABLER_RACKE = [
    ("Hojd", 900, "mm, handledarens överkant lodrätt över stegframkant / plan yta"),
    ("Under", 80, "mm, underliggarens mitt lodrätt över stegframkant / plan yta"),
    ("Mellan", 70, "mm, fritt mellan handledare och överliggare"),
]


def snacka_langd():
    return math.pi * sum(SNACKA_R)


def bygg_snacka(k, hl):
    """Snäckan på handledarens startände: skiss i kroppens YZ-plan (handledarens tjockleksriktning och längd,
    änden i z = 0) med yttre och inre bågkedja (tre halvvarv med minskande radie, tangerande) och två
    ändlinjer, fullt bestämd; Pad 40 symmetriskt (handledarens bredd)."""
    import pd
    import Part
    from FreeCAD import Vector as V
    dd = pd.Del(k.doc, hl.Name)
    sk = dd.skiss("Snacka", "YZ")
    R1, R2, R3 = SNACKA_R
    t2 = HL_T / 2
    C = [(-R1, 0.0), (-2 * R1 + R2, 0.0), (-2 * R1 + 2 * R2 - R3, 0.0)]
    vink = [(-math.pi, 0.0), (0.0, math.pi), (-math.pi, 0.0)]       # moturs parametrisering

    def kedja(dr):
        g = []
        for (cx, cy), (a0, a1), R in zip(C, vink, SNACKA_R):
            g.append(sk.geo(Part.ArcOfCircle(Part.Circle(V(cx, cy, 0), V(0, 0, 1), R + dr), a0, a1)))
        sk.begr("Tangent", g[0], pd.START, g[1], pd.SLUT)
        sk.begr("Tangent", g[1], pd.START, g[2], pd.SLUT)
        for gi, R in zip(g, SNACKA_R):
            sk.matt("Radius", gi, varde=R + dr)
            sk.matt("Angle", gi, varde=180)
        sk.placera(g[0], pd.SLUT, dr, 0)                            # startpunkten på handledarens ändyta
        sk.begr("PointOnObject", g[0], pd.MITT, pd.H_AXEL)          # tangent med handledaren
        return g

    yttre, inre = kedja(t2), kedja(-t2)
    x_slut = C[2][0] - R3                                           # snäckans ände (mittlinje)
    l1 = sk.geo(Part.LineSegment(V(-t2, 0, 0), V(t2, 0, 0)))
    l2 = sk.geo(Part.LineSegment(V(x_slut - t2, 0, 0), V(x_slut + t2, 0, 0)))
    sk.begr("Coincident", l1, pd.START, inre[0], pd.SLUT)
    sk.begr("Coincident", l1, pd.SLUT, yttre[0], pd.SLUT)
    sk.begr("Coincident", l2, pd.START, yttre[2], pd.START)
    sk.begr("Coincident", l2, pd.SLUT, inre[2], pd.START)
    dd.kloss(sk, HL_B, "Snacka", symmetrisk=True)
    dd.stada()


class Linje:
    """Framkantslinjen: polylinje genom knäckpunkterna (x, z), förlängd med ändsegmentens lutning."""

    def __init__(self, pkt):
        self.p = sorted(pkt)

    def _seg(self, x, hoger=True):
        p = self.p
        for i in range(len(p) - 1):
            if x < p[i + 1][0] or (not hoger and x <= p[i + 1][0]):
                return p[i], p[i + 1]
            if i == len(p) - 2:
                return p[i], p[i + 1]
        return p[-2], p[-1]

    def lutning(self, x, hoger=True):
        a, b = self._seg(x, hoger)
        return (b[1] - a[1]) / (b[0] - a[0])

    def __call__(self, x):
        a, b = self._seg(x)
        return a[1] + (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0])

    def knackar(self, x0, x1):
        """Knäckarna (inre punkter där lutningen ändras) mellan x0 och x1; ändpunkterna förlängs."""
        return [x for x, _ in self.p[1:-1] if x0 < x < x1]


def bygg_racke(k, v, nos_pkt, yta, stolpar, hl_x, start="snacka", ursprung=(0, 0, 0), ex=(1, 0, 0), ey=(0, 1, 0),
               prefix="", huvuddel=True):
    """nos_pkt: framkantslinjens knäckpunkter; yta(x): stenens överkant under en stolpe; stolpar: stolparnas x
    (uppför); hl_x: handledarens ändar (x0, x1); start: "snacka" (snäcka i nedre änden) eller "rak".
    Returnerar dict med fack, handledarbitar m.m. för noterna."""
    H, under, mellan = v["Hojd"], v["Under"], v["Mellan"]
    nos = Linje(nos_pkt)
    ex, ey = [float(q) for q in ex], [float(q) for q in ey]
    ez = [ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0]]
    o = [float(q) for q in ursprung]
    P = lambda x, y, z: tuple(round(o[i] + x * ex[i] + y * ey[i] + z * ez[i], 4) for i in range(3))
    D = lambda x, y, z: tuple(x * ex[i] + y * ey[i] + z * ez[i] for i in range(3))
    pos_ = lambda p: prefix + p
    cos = lambda t: math.cos(math.atan(t))
    hl_uk = lambda x, hoger=True: nos(x) + H - HL_T / cos(nos.lutning(x, hoger))      # handledarens underkant

    # ---- handledare: en bit per lutning, spalt i knäckarna
    x0, x1 = hl_x
    grans = [x0] + nos.knackar(x0, x1) + [x1]
    bitar = []
    for i, (a, b) in enumerate(zip(grans, grans[1:])):
        a2 = a + (KNACK_SPALT if i > 0 else 0.0)
        b2 = b - (KNACK_SPALT if i < len(grans) - 2 else 0.0)
        t = nos.lutning((a + b) / 2)
        zc = lambda x: nos(x) + H - HL_T / 2 / cos(t)
        hl = k.balk(pos_("hl/%d" % (i + 1)), "PL%g*%g" % (HL_T, HL_B), P(a2, 0, zc(a2)), P(b2, 0, zc(b2)), upp=D(0, 0, 1), material=STAL)
        if i == 0 and start == "snacka":
            bygg_snacka(k, hl)
        bitar.append(dict(pos=pos_("hl/%d" % (i + 1)), langd=(b2 - a2) / cos(t), lutning=math.degrees(math.atan(t))))

    # ---- stolpar
    def fs20(L):
        def bygg(d):
            sk = d.skiss("Tvarsnitt", "XY")
            sk.rektangel(ST_A, ST_A, namn=("Sida", "Sida2"))
            d.kloss(sk, round(L, 2), "Langd")
        return bygg

    spos = {}
    for i, x in enumerate(stolpar):
        xa, xb = x - ST_A / 2, x + ST_A / 2
        za, zb = hl_uk(xa), hl_uk(xb, hoger=False)
        z0 = yta(x) - INGJUT
        Lp = round(max(za, zb) - z0, 1)
        nyckel = (Lp, round(zb - za, 1))
        pos = spos.setdefault(nyckel, pos_("st/%d" % (len(spos) + 1)))
        st = k.egen(pos, "FS%g" % ST_A, fs20(Lp), mitt=P(x, 0, z0), rot=(ex, ey, ez), material=STAL, huvuddel=(huvuddel and i == 0))
        if abs(zb - za) > 0.01:
            k.gera(st, P(xa, 0, za), P(xb, 0, zb))

    # ---- liggare och spjälor per fack (raka mellan stolparna)
    lpos, sppos, fack = {}, {}, []
    snitt_x = None
    sp_forst = {}                                       # första spjälan per position (snitt genom varje)

    def nr(tab, prefixtxt, nyckel):
        return tab.setdefault(nyckel, pos_("%s/%d" % (prefixtxt, len(tab) + 1)))

    for xa, xb in zip(stolpar, stolpar[1:]):
        fa, fb = xa + ST_A / 2, xb - ST_A / 2
        ok_a, ok_b = hl_uk(fa) - mellan, hl_uk(fb, hoger=False) - mellan          # överliggarens överkant
        tf = (ok_b - ok_a) / (fb - fa)
        cf = cos(tf)
        ol_ok = lambda x: ok_a + (x - fa) * tf
        ol_mitt = lambda x: ol_ok(x) - OL_H / 2 / cf
        ol_uk = lambda x: ol_ok(x) - OL_H / cf
        ua, ub = nos(fa) + under, nos(fb) + under                                 # underliggarens mitt
        tu = (ub - ua) / (fb - fa)
        cu = cos(tu)
        ul_mitt = lambda x: ua + (x - fa) * tu
        ul_ok = lambda x: ul_mitt(x) + UL_T / 2 / cu
        # överliggare på högkant: lodräta ändar mot stolparna
        prof = "PL%g*%g" % (OL_T, OL_H)
        L = (fb - fa - 2 * SPALT) / cf
        ol = k.balk(nr(lpos, "l", (prof, round(L, 1), round(tf, 3))), prof, P(fa + SPALT, 0, ol_mitt(fa + SPALT)),
                    P(fb - SPALT, 0, ol_mitt(fb - SPALT)), upp=D(0, 1, 0), material=STAL)
        if abs(tf) > 1e-4:
            for xf in (fa + SPALT, fb - SPALT):
                k.gera(ol, P(xf, 0, ol_mitt(xf) - 40), P(xf, 0, ol_mitt(xf) + 40))
        # underliggare plant: ändarna vinkelräta mot lutningen, spalt så hörnen inte går in i stolpen
        g = SPALT + UL_T / 2 * abs(tu)
        prof = "PL%g*%g" % (UL_T, UL_B)
        L = (fb - fa - 2 * g) / cu
        k.balk(nr(lpos, "l", (prof, round(L, 1), round(tu, 3))), prof, P(fa + g, 0, ul_mitt(fa + g)), P(fb - g, 0, ul_mitt(fb - g)),
               upp=D(0, 0, 1), material=STAL)
        # spjälor: fri öppning < 100 vågrätt
        w = fb - fa
        m = max(1, int(math.ceil((w - 100.0) / (100.0 + SPJ_D))))
        fri = (w - m * SPJ_D) / (m + 1)
        fack.append(dict(fri=fri, cc=fri + SPJ_D, antal=m, lutning=math.degrees(math.atan(tf))))
        r = SPJ_D / 2
        for j in range(m):
            x = fa + fri * (j + 1) + SPJ_D * (j + 0.5)
            if snitt_x is None and j == 1:
                snitt_x = x
            zb_, zt_ = ul_ok(x) - r * abs(tu), ol_uk(x) + r * abs(tf)
            Ls = zt_ - zb_
            if abs(tu) > 1e-4:                  # snedkapad nedtill: hel mm, kapet tar bort överskottet
                Ls = math.ceil(Ls)
                zb_ = zt_ - Ls
            nyckel = (round(Ls), round(math.degrees(math.atan(tu))), round(math.degrees(math.atan(tf))))
            spnr = nr(sppos, "sp", nyckel)
            sp_forst.setdefault(spnr, round(x, 1))
            sp = k.balk(spnr, "D%g" % SPJ_D, P(x, 0, zb_), P(x, 0, zt_), upp=D(0, 1, 0), material=STAL)
            if abs(tu) > 1e-4:
                k.gera(sp, P(x - r, 0, ul_ok(x - r)), P(x + r, 0, ul_ok(x + r)))
            if abs(tf) > 1e-4:
                k.gera(sp, P(x - r, 0, ol_uk(x - r)), P(x + r, 0, ol_uk(x + r)))
    snitt = snitt_x or stolpar[0] + 60
    sp_x = sorted(sp_forst.values())
    sp_x[0] = round(snitt, 1)
    return dict(fack=fack, bitar=bitar, snitt_x=round(snitt, 1), sp_x=sp_x, stolpar=stolpar,
                stolp_cc=max(b - a for a, b in zip(stolpar, stolpar[1:])))


def ritning(k, info, noter_):
    """Framvy och ett snitt genom en spjäla av varje position (A, B, C ...), så att alla får positionsbubbla."""
    snitt = [dict(namn=chr(65 + i), axel="x", varde=x, mot="-") for i, x in enumerate(info["sp_x"])]
    k.ritning(vyer=["fram"], snitt=snitt, noter=noter_)


def noter(beskr, v, info, start, slut_text, extra=()):
    """Noter för räckesritningarna: beskrivning (var räcket sitter), mått och utförande."""
    import trappa_hellstone as T
    fri = min(f["fri"] for f in info["fack"])
    cc = max(f["cc"] for f in info["fack"])
    bitar = info["bitar"]
    hl = " + ".join("%s %.0f" % (b["pos"], b["langd"]) for b in bitar)
    rader = ["PRELIMINÄR RITNING – OFFERTUNDERLAG, EJ FÖR TILLVERKNING",
             "UNDERLAG: FOTON OCH MÅTT I MAIL FRÅN P. HELLSTONE 2026-10-17, UTFÖRANDE EFTER KUNDENS FÖREBILDER",
             beskr,
             "STEGHÖJD %g, STEGDJUP %g/%g ÄR ANTAGNA UR FOTON – ALLA MÅTT KONTROLLMÄTS PÅ PLATS FÖRE TILLVERKNING"
             % (T.R, T.G_OVRE, T.G_NEDRE),
             "RÄCKESHÖJD %g LODRÄTT ÖVER STEGFRAMKANT OCH PLAN YTA, ±0 = GÅNGEN VID TRAPPANS FOT" % v["Hojd"],
             "STOLPAR st: FS20, %g mm NEDGJUTNA I KÄRNBORRADE HÅL Ø40 I GRANITEN (INGÅR I LÄNGDEN), c/c MAX %.0f"
             % (INGJUT, info["stolp_cc"])]
    if start == "snacka":
        rader.append("HANDLEDARE PL40*8 PLANT: %s, NEDRE ÄNDEN SMIDD SNÄCKA 1,5 VARV (R%g/%g/%g, UTVECKLAD %.0f) PÅ %s"
                     % (hl, SNACKA_R[0], SNACKA_R[1], SNACKA_R[2], snacka_langd(), bitar[0]["pos"]))
    else:
        rader.append("HANDLEDARE PL40*8 PLANT: %s" % hl)
    if len(bitar) > 1:
        rader.append("HANDLEDARENS KNÄCK %s BOCKAS I ETT STYCKE ELLER SVETSAS OCH SLIPAS"
                     % " / ".join("%s %s" % (b["pos"], "PLAN" if abs(b["lutning"]) < 0.05 else "%.1f°" % b["lutning"]) for b in bitar))
    rader.append(slut_text)
    rader += list(extra)
    rader += ["SPJÄLOR sp D12 MELLAN LIGGARNA, c/c MAX %.0f, FRI ÖPPNING MIN %.0f (< 100)" % (cc, fri),
              "SVETS: STOLPAR MOT HANDLEDARE a4, LIGGARE MOT STOLPAR a3 RUNT OM, SPJÄLOR MOT LIGGARE a3 RUNT OM",
              "YTBEHANDLING: VARMFÖRZINKAD OCH PULVERLACKAD SVART RAL 9005 (ANTAGET, ENLIGT BESTÄLLNING)"]
    return rader
