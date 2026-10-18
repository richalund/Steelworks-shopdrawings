"""Gemensam byggare för smidesräcken i stilen från P. Hellstones förebilder (mail 2026-10-17): fyrkantiga
stolpar FS20 nedgjutna i granitstegen, plan handledare PL40*8 med smidd snäcka i nedre änden, överliggare
PL30*8 på högkant under handledaren, underliggare PL40*8 plant, stående spjälor D12 mellan liggarna med fri
öppning < 100 mm. Används av egna/konstruktioner/racke_trappa.py (R/1, snett räcke längs trappan),
racke_platta.py (R/2, plant räcke på nedre plattans framkant), racke_platta_sida.py (R/3, plattans sida) och
trappa_oversikt.py (alla tre på trappan). Steg = 0 ger ett plant räcke.

Lokala koordinater: X längs räcket (uppför trappan), Y = tvärs (räckesplanet y = 0), Z uppåt. ±0 = nedre
plattans översida (Steg > 0) resp. plattans översida (Steg = 0). Framkantslinjen (noslinjen) går genom stegens
framkanter: z = Steghojd + x * Steghojd/Stegdjup, första steget vid x = 0. `ursprung`, `ex`, `ey` placerar
räcket i en större modell (översikten).
Snäckan: handledarens nedre ände fortsätter 150 mm rakt förbi stolpen och rullas sedan ihop nedåt i 1,5 varv
(mittlinjeradier 42, 28, 16) – ritad som tangerande bågar i en skiss på handledarens kropp, Pad 40.
Måtten räknas ut i Python (sned geometri): ändrade variabler kräver ombyggnad (sammanstallning.py bygg --var).
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
UTSTICK = 100.0                 # handledarens utstick förbi en ändstolpe (rak ände, och till hörnet vid gering)
GERING_UT = 120.0               # handledaren byggs 120 förbi stolpen och geras 45° i hörnet (stolpen 100 från hörnet)
SPALT = 2.0                     # svetsspalt vid liggarnas ändar

VARIABLER_BAS = [
    ("Hojd", 900, "mm, handledarens överkant lodrätt över stegframkant (plant räcke: över plattan)"),
    ("Under", 80, "mm, underliggarens mitt lodrätt över framkantslinjen"),
    ("Mellan", 70, "mm, fritt mellan handledare och överliggare"),
]


def snacka_langd():
    return math.pi * sum(SNACKA_R)


def bygg_snacka(k, hl):
    """Snäckan på handledarens startände: skiss i kroppens YZ-plan (x = tjockleksriktningen uppåt, y = längs
    handledaren, änden i y = 0) med yttre och inre bågkedja (tre halvvarv med minskande radie, tangerande) och
    två ändlinjer, fullt bestämd; Pad 40 symmetriskt (handledarens bredd)."""
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


def noter_bas(v, n, a_deg, cc, fri, stolp_cc, hl_rak, start, slut, hornmot):
    rader = ["PRELIMINÄR RITNING – OFFERTUNDERLAG, EJ FÖR TILLVERKNING",
             "UNDERLAG: FOTON OCH MÅTT I MAIL FRÅN P. HELLSTONE 2026-10-17, UTFÖRANDE EFTER KUNDENS FÖREBILDER",
             "STEGHÖJD %g OCH STEGDJUP %g ÄR ANTAGNA – ALLA MÅTT KONTROLLMÄTS PÅ PLATS FÖRE TILLVERKNING" % (v["Steghojd"], v["Stegdjup"])
             if n else "LÄNGDEN %g ÄR ANTAGEN – ALLA MÅTT KONTROLLMÄTS PÅ PLATS FÖRE TILLVERKNING" % v["Langd"],
             "±0 = NEDRE PLATTANS ÖVERSIDA, RÄCKESHÖJD %g LODRÄTT ÖVER STEGFRAMKANT, LUTNING %.1f°" % (v["Hojd"], a_deg)
             if n else "±0 = PLATTANS ÖVERSIDA, RÄCKESHÖJD %g" % v["Hojd"],
             "STOLPAR st: FS20, %g mm NEDGJUTNA I KÄRNBORRADE HÅL Ø40 I GRANITEN (INGÅR I LÄNGDEN), c/c MAX %.0f" % (INGJUT, stolp_cc)]
    if start == "snacka":
        rader.append("HANDLEDARE hl/1 PL40*8 PLANT, RAK LÄNGD %.0f + SMIDD SNÄCKA 1,5 VARV (R%g/%g/%g, UTVECKLAD %.0f) = KAPLÄNGD %.0f"
                     % (hl_rak, SNACKA_R[0], SNACKA_R[1], SNACKA_R[2], snacka_langd(), hl_rak + snacka_langd()))
    else:
        rader.append("HANDLEDARE hl/1 PL40*8 PLANT, LÄNGD %.0f" % hl_rak)
    if "gering" in (start, slut):
        rader.append("HANDLEDARENS ÄNDE GERAD 45° I PLATTANS HÖRN MOT %s, SVETSAS IHOP PÅ PLATS OCH SLIPAS" % (hornmot or "ANSLUTANDE RÄCKE"))
    rader += ["SPJÄLOR sp D12 MELLAN LIGGARNA, c/c %.0f, FRI ÖPPNING %.0f (< 100)" % (cc, fri),
              "SVETS: STOLPAR MOT HANDLEDARE a4, LIGGARE MOT STOLPAR a3 RUNT OM, SPJÄLOR MOT LIGGARE a3 RUNT OM",
              "YTBEHANDLING: VARMFÖRZINKAD OCH PULVERLACKAD SVART RAL 9005 (ANTAGET, ENLIGT BESTÄLLNING)"]
    return rader


def bygg_racke(k, v, max_stolp_cc=1200.0, start="snacka", slut="rak", hornmot=None, ursprung=(0, 0, 0),
               ex=(1, 0, 0), ey=(0, 1, 0), prefix="", ritning=True, huvuddel=True):
    """start: "snacka" (rak 150 förbi stolpen + snäcka), "rak" (utstick 100) eller "gering" (45° i hörn, det
    anslutande räcket går åt lokalt -y). slut: "rak" eller "gering". Returnerar dict med stolpar m.m."""
    n = int(v.get("Steg", 0))
    Sh, Sd = (v["Steghojd"], v["Stegdjup"]) if n else (0.0, 1.0)
    H, under, mellan = v["Hojd"], v["Under"], v["Mellan"]
    t = Sh / Sd if n else 0.0                         # lutning
    a = math.atan(t)
    c = math.cos(a)
    ex, ey = [float(q) for q in ex], [float(q) for q in ey]
    ez = [ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0]]
    o = [float(q) for q in ursprung]
    P = lambda x, y, z: tuple(round(o[i] + x * ex[i] + y * ey[i] + z * ez[i], 4) for i in range(3))
    D = lambda x, y, z: tuple(x * ex[i] + y * ey[i] + z * ez[i] for i in range(3))
    pos_ = lambda p: prefix + p
    nos = lambda x: (Sh if n else 0.0) + x * t        # framkantslinjen
    hl_ok = lambda x: nos(x) + H                      # handledarens överkant
    hl_uk = lambda x: hl_ok(x) - HL_T / c             # handledarens underkant (lodrätt)
    hl_mitt = lambda x: hl_ok(x) - HL_T / 2 / c
    ol_mitt = lambda x: hl_uk(x) - mellan - OL_H / 2 / c
    ol_uk = lambda x: ol_mitt(x) - OL_H / 2 / c
    ul_mitt = lambda x: nos(x) + under
    ul_ok = lambda x: ul_mitt(x) + UL_T / 2 / c

    # ---- stolpar: (x, z vid stenens översida)
    if n:
        stolpar = [((kk - 1) * Sd + Sd / 2, kk * Sh) for kk in range(1, n + 1, 2)]
        stolpar.append(((n - 1) * Sd + 250.0, n * Sh))
    else:
        L = v["Langd"]
        m = max(2, int(math.ceil((L - 200.0) / max_stolp_cc)) + 1)
        stolpar = [(100.0 + (L - 200.0) * i / (m - 1), 0.0) for i in range(m)]
    stolp_cc = max(b[0] - a_[0] for a_, b in zip(stolpar, stolpar[1:]))

    def fs20(L):
        def bygg(d):
            sk = d.skiss("Tvarsnitt", "XY")
            sk.rektangel(ST_A, ST_A, namn=("Sida", "Sida2"))
            d.kloss(sk, round(L, 2), "Langd")
        return bygg

    langder = {}
    for i, (x, z) in enumerate(stolpar):
        z0 = z - INGJUT
        z1 = hl_uk(x) + ST_A / 2 * t                  # räcker upp till handledarens underkant på uppsidan
        Lp = round(z1 - z0, 1)
        pos = langder.setdefault(Lp, pos_("st/%d" % (len(langder) + 1)))
        st = k.egen(pos, "FS%g" % ST_A, fs20(Lp), mitt=P(x, 0, z0), rot=(ex, ey, ez), material=STAL, huvuddel=(huvuddel and i == 0))
        if t:
            k.gera(st, P(x - ST_A / 2, 0, hl_uk(x - ST_A / 2)), P(x + ST_A / 2, 0, hl_uk(x + ST_A / 2)))

    # ---- handledare, plant PL40*8 längs lutningen
    x0 = stolpar[0][0] - {"snacka": SNACKA_RAK, "rak": UTSTICK, "gering": GERING_UT}[start]
    x1 = stolpar[-1][0] + {"rak": UTSTICK, "gering": GERING_UT}[slut]
    hl = k.balk(pos_("hl/1"), "PL%g*%g" % (HL_T, HL_B), P(x0, 0, hl_mitt(x0)), P(x1, 0, hl_mitt(x1)), upp=D(0, 0, 1), material=STAL)
    hl_rak = (x1 - x0) / c
    if start == "snacka":
        bygg_snacka(k, hl)
    if start == "gering":                             # hörnet i x = x0 + GERING_UT - UTSTICK (= 0 för plant räcke)
        xh = stolpar[0][0] - UTSTICK
        k.gera(hl, P(xh - HL_B / 2, HL_B / 2, hl_mitt(xh)), P(xh + HL_B / 2, -HL_B / 2, hl_mitt(xh)))
    if slut == "gering":
        xh = stolpar[-1][0] + UTSTICK
        k.gera(hl, P(xh + HL_B / 2, HL_B / 2, hl_mitt(xh)), P(xh - HL_B / 2, -HL_B / 2, hl_mitt(xh)))

    # ---- liggare och spjälor per fack
    cc_max, fri_min = 0.0, 1e9
    snitt_x = None
    lpos = {}                                          # (profil, längd) -> positionsnummer: lika liggare får samma

    def lnr(profil, L):
        return lpos.setdefault((profil, round(L, 1)), pos_("l/%d" % (len(lpos) + 1)))

    for (xa, _), (xb, _) in zip(stolpar, stolpar[1:]):
        fa, fb = xa + ST_A / 2, xb - ST_A / 2         # stolparnas sidor
        # överliggare på högkant: lodräta ändar mot stolparna (gering), byggs med spalt och kapas
        prof = "PL%g*%g" % (OL_T, OL_H)
        ol = k.balk(lnr(prof, (fb - fa - 2 * SPALT) / c), prof, P(fa + SPALT, 0, ol_mitt(fa + SPALT)), P(fb - SPALT, 0, ol_mitt(fb - SPALT)),
                    upp=D(0, 1, 0), material=STAL)
        if t:
            for xf in (fa + SPALT, fb - SPALT):
                k.gera(ol, P(xf, 0, ol_mitt(xf) - 40), P(xf, 0, ol_mitt(xf) + 40))
        # underliggare plant: ändarna vinkelrätt mot lutningen, spalt så hörnen inte går in i stolpen
        g = SPALT + UL_T / 2 * t
        prof = "PL%g*%g" % (UL_T, UL_B)
        k.balk(lnr(prof, (fb - fa - 2 * g) / c), prof, P(fa + g, 0, ul_mitt(fa + g)), P(fb - g, 0, ul_mitt(fb - g)), upp=D(0, 0, 1), material=STAL)
        # spjälor: fri öppning < 100 vågrätt
        w = fb - fa
        m = int(math.ceil((w - 100.0) / (100.0 + SPJ_D)))
        fri = (w - m * SPJ_D) / (m + 1)
        cc_max, fri_min = max(cc_max, fri + SPJ_D), min(fri_min, fri)
        for j in range(m):
            x = fa + fri * (j + 1) + SPJ_D * (j + 0.5)
            if snitt_x is None and j == 1:
                snitt_x = x
            zb, zt = ul_ok(x), ol_uk(x)
            r = SPJ_D / 2
            sp = k.balk(pos_("sp/1"), "D%g" % SPJ_D, P(x, 0, zb - r * t), P(x, 0, zt + r * t), upp=D(0, 1, 0), material=STAL)
            if t:
                k.gera(sp, P(x - r, 0, ul_ok(x - r)), P(x + r, 0, ul_ok(x + r)))
                k.gera(sp, P(x - r, 0, ol_uk(x - r)), P(x + r, 0, ol_uk(x + r)))
    noter = noter_bas(v, n, math.degrees(a), cc_max, fri_min, stolp_cc, hl_rak, start, slut, hornmot)
    if ritning:
        k.ritning(vyer=["fram"], snitt=[dict(namn="A", axel="x", varde=round(snitt_x or stolpar[0][0] + 100, 1), mot="-")], noter=noter)
    return dict(stolpar=stolpar, lutning=math.degrees(a), cc=cc_max, fri=fri_min, noter=noter, hl=(x0, x1))
