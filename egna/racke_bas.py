"""Gemensam byggare för smidesräcken i stilen från P. Hellstones förebilder (mail 2026-10-17):
- stolpar FS20, nedgjutna i granitstegen
- handledare FL40*10: plattstål 40x10 med rundad översida (R52, sidorna 6 höga), smidd snäcka i nedre änden
- följare under handledaren och underliggare nedtill: 2 st plattstål PL5*20 på högkant, ett på var sida om
  spjälorna
- spjälor FS12 (fyrkantstång 12x12) mellan följarna, kant i kant med följarnas över- och underkant, fri
  öppning < 100 mm

Räcket följer en framkantslinje (polylinje i lokala x, z: trapplopp och plana partier med knäckar) och står på
ytan yta(x). Handledaren ligger Hojd lodrätt över linjen och delas i knäckarna (hl/1, hl/2 ... bockas eller
svetsas). Stolparnas lägen ges av konstruktionsskriptet; vid en knäck står stolpen på den plana sidan.
Följare, spjälor och fack räknas per fack mellan stolparna.

Lokala koordinater: X längs räcket (uppför), Y tvärs (räckesplanet y = 0), Z uppåt. `ursprung`, `ex`, `ey`
placerar räcket i en större modell (översikten T/1).
Snäckan: handledarens nedre ände fortsätter 150 mm rakt förbi stolpen och rullas sedan ihop nedåt i 1,5 varv
(mittlinjeradier 42, 28, 16) – tangerande bågar i en skiss på handledarens kropp, Pad 40.
Detaljerna (snitt och förstoringar i 1:2) sparas i sammanställningens egenskap Detaljer och ritas av
egna/ritning_detaljer.py efter sammanstallning.py ritning.
Måtten räknas ut i Python (sned geometri): ändrade mått kräver ombyggnad (sammanstallning.py bygg).
"""
import json
import math

STAL = "S235JR"
HL_B, HL_T, HL_SIDA = 40.0, 10.0, 6.0   # handledare 40x10, sidorna 6, rundad översida
HL_R = ((HL_B / 2) ** 2 + (HL_T - HL_SIDA) ** 2) / (2 * (HL_T - HL_SIDA))     # 52
HL_PROFIL = "FL40*10"                 # plattstål 40x10 med rundad översida (namnet ger tjockleken till källnoterna)
FL_H, FL_T = 20.0, 5.0          # följare/underliggare 2 st PL5*20 på högkant
SPJ_A = 12.0                    # spjäla FS12
ST_A = 20.0                     # stolpe FS20
INGJUT = 100.0                  # stolparnas ingjutning i stenen
SNACKA_RAK = 150.0              # rak handledare förbi nedersta stolpen före snäckan
SNACKA_R = (42.0, 28.0, 16.0)   # snäckans mittlinjeradier, tre halvvarv
SPALT = 2.0                     # svetsspalt vid följarnas ändar
KNACK_SPALT = 1.5               # spalt per sida i handledarens knäck
Y_FL = SPJ_A / 2 + FL_T / 2     # följarnas mitt från räckesplanet (8,5)

VARIABLER_RACKE = [
    ("Hojd", 900, "mm, handledarens överkant lodrätt över stegframkant / plan yta"),
    ("Under", 80, "mm, underliggarens mitt lodrätt över stegframkant / plan yta"),
    ("Mellan", 70, "mm, fritt mellan handledare och följare"),
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


def handledarprofil(L):
    """Kropp för handledaren FL40*10: tvärsnitt med plan undersida, 6 höga sidor och rundad översida R52
    (fullt bestämd skiss, lådans mitt i origo), Pad L längs kroppens z."""
    def bygg(d):
        import pd
        import Part
        from FreeCAD import Vector as V
        sk = d.skiss("Tvarsnitt", "XY")
        b2, y0, y1 = HL_B / 2, -HL_T / 2, -HL_T / 2 + HL_SIDA
        A, B, C, D = (-b2, y0), (b2, y0), (b2, y1), (-b2, y1)
        g = [sk.geo(Part.LineSegment(V(*p, 0), V(*q, 0))) for p, q in ((A, B), (B, C), (D, A))]
        yc = HL_T / 2 - HL_R
        a0, a1 = math.atan2(y1 - yc, b2), math.atan2(y1 - yc, -b2)
        bage = sk.geo(Part.ArcOfCircle(Part.Circle(V(0, yc, 0), V(0, 0, 1), HL_R), a0, a1))
        sk.begr("Coincident", g[0], pd.SLUT, g[1], pd.START)
        sk.begr("Coincident", g[1], pd.SLUT, bage, pd.START)
        sk.begr("Coincident", bage, pd.SLUT, g[2], pd.START)
        sk.begr("Coincident", g[2], pd.SLUT, g[0], pd.START)
        for gi, pt, pp in ((g[0], pd.START, A), (g[0], pd.SLUT, B), (g[1], pd.SLUT, C), (g[2], pd.START, D)):
            sk.placera(gi, pt, pp[0], pp[1], namn="")
        sk.matt("Radius", bage, varde=HL_R, namn="R")
        d.kloss(sk, round(L, 2), "Langd")
    return bygg


def gera(k, o, a, b):
    """k.gera (snedkapning genom punkterna a och b) med en lösning för FreeCAD 1.1.3: en Pocket "genom allt"
    med SideType Symmetric skär ingenting där (uppmätt 2026-10-18), så fickan görs om till en symmetrisk längd
    som täcker hela kroppen. Kontrollerar att något skars bort."""
    fore = o.Shape.Volume
    diag = o.Shape.BoundBox.DiagonalLength
    k.gera(o, a, b)
    f = [g for g in o.Group if g.TypeId == "PartDesign::Pocket"][-1]
    if f.Type == "ThroughAll":                 # skär ingenting eller bara ena halvan i FreeCAD 1.1.3
        f.Type = "Length"
        if hasattr(f, "SideType"):
            f.SideType = "Symmetric"
        else:
            f.Midplane = True
        f.Length = 2 * diag + 10
        k.doc.recompute()
    if f.Shape.Volume > fore - 1e-6:
        raise RuntimeError("Snedkapningen av %s skar inte bort något (punkter %s, %s; låda %s)" % (o.Label, a, b, o.Shape.BoundBox))


def fyrkant(a, L):
    def bygg(d):
        sk = d.skiss("Tvarsnitt", "XY")
        sk.rektangel(a, a, namn=("Sida", "Sida2"))
        d.kloss(sk, round(L, 2), "Langd")
    return bygg


def fordela(fasta, lage=lambda x: x, max_cc=1300.0):
    """Stolplägen: de fasta (sektionernas ändar och knäckar) plus jämnt fördelade mellanstolpar så att c/c blir
    högst max_cc. lage(x) flyttar en mellanstolpe till ett giltigt läge (stegmitt i ett lopp); av grannlägena
    väljs det som håller c/c och ligger närmast den jämna delningen."""
    ut = [fasta[0]]
    for a, b in zip(fasta, fasta[1:]):
        n = max(1, int(math.ceil((b - a) / max_cc - 1e-9)))
        prev = a
        for i in range(1, n):
            mal = a + (b - a) * i / n
            kand = sorted({lage(mal), lage(mal - 0.5 * (b - a) / n), lage(mal + 0.5 * (b - a) / n)}, key=lambda x: abs(x - mal))
            ok = [x for x in kand if prev < x < b and x - prev <= max_cc and (b - x) <= max_cc * (n - i)]
            x = (ok or kand)[0]
            ut.append(x)
            prev = x
        ut.append(b)
    return ut


class Linje:
    """Framkantslinjen: polylinje genom knäckpunkterna (x, z), förlängd med ändsegmentens lutning."""

    def __init__(self, pkt):
        self.p = sorted(pkt)

    def _seg(self, x, hoger=True):
        p = self.p
        for i in range(len(p) - 1):
            if x < p[i + 1][0] or (not hoger and x <= p[i + 1][0]):
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
               prefix="", huvuddel=True, extern=()):
    """nos_pkt: framkantslinjens knäckpunkter; yta(x): stenens överkant under en stolpe; stolpar: stolparnas x
    (uppför); hl_x: handledarens ändar (x0, x1); start: "snacka" (snäcka i nedre änden) eller "rak".
    Returnerar dict med fack, handledarbitar, snitt och detaljer för ritningen."""
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
        c, s_ = cos(t), math.sin(math.atan(t))
        zc = nos(a2) + H - HL_T / 2 / c
        L = (b2 - a2) / c
        hl = k.egen(pos_("hl/%d" % (i + 1)), HL_PROFIL, handledarprofil(L), mitt=P(a2, 0, zc),
                    rot=(D(0, 1, 0), D(-s_, 0, c), D(c, 0, s_)), material=STAL)
        if i == 0 and start == "snacka":
            bygg_snacka(k, hl)
        bitar.append(dict(pos=pos_("hl/%d" % (i + 1)), langd=L, lutning=math.degrees(math.atan(t))))

    # ---- stolpar (de i `extern` hör till ett anslutande räcke och byggs inte här, t.ex. R/1:s hörnstolpe för R/2)
    spos = {}
    for i, x in enumerate(stolpar):
        if i in extern:
            continue
        xa, xb = x - ST_A / 2, x + ST_A / 2
        za, zb = hl_uk(xa), hl_uk(xb, hoger=False)
        z0 = yta(x) - INGJUT
        Lp = math.floor((max(za, zb) - z0) * 10 + 1e-6) / 10    # nedåt: toppen får inte gå upp i handledaren
        knack = nos.knackar(xa, xb)
        pos = spos.setdefault((Lp, round(zb - za, 1), bool(knack)), pos_("st/%d" % (len(spos) + 1)))
        st = k.egen(pos, "FS%g" % ST_A, fyrkant(ST_A, Lp), mitt=P(x, 0, z0), rot=(ex, ey, ez), material=STAL,
                    huvuddel=(huvuddel and i == 0))
        if knack:                       # knäckstolpe: toppen kapas i båda lutningarna, möts under handledarens knäck
            tl, tr = nos.lutning(xa), nos.lutning(xb, False)
            if tl <= tr:
                raise ValueError("stolpe x=%g i en inåtknäck (lutningen ökar) stöds inte" % x)
            xi = xa + (zb - za - tr * (xb - xa)) / (tl - tr)         # underkanternas skärning
            zi = za + tl * (xi - xa)
            for (xp, zp, tp) in ((xa, za, tl), (xb, zb, tr)):
                if Lp + z0 - min(zp, zi) > 0.01 or abs(tp) > 1e-6:
                    gera(k, st, P(xp, 0, zp), P(xi, 0, zi))
        elif abs(zb - za) > 0.01:
            gera(k, st, P(xa, 0, za), P(xb, 0, zb))

    # ---- följare, underliggare och spjälor per fack mellan stolparna. Följarna följer handledaren och
    # underliggarna framkantslinjen: i en knäck inne i facket bockas de (två bitar med gering i knäcken).
    lpos, sppos, fack, sp_forst = {}, {}, [], {}
    snitt_x = None

    def nr(tab, prefixtxt, nyckel):
        return tab.setdefault(nyckel, pos_("%s/%d" % (prefixtxt, len(tab) + 1)))

    def mittlinje(fa, fb, z):
        """Polylinje (x, z) från fa till fb med knäck där framkantslinjen knäcker; z(x, hoger) ger mittens höjd.
        Knäckpunkten är skärningen mellan linjerna på var sida (de är förskjutna olika mycket när lutningen ändras),
        så att varje bit blir exakt parallell med handledaren respektive framkantslinjen."""
        pts = [(fa, z(fa, True))]
        for xk in nos.knackar(fa, fb):
            tl, tr = nos.lutning(xk, False), nos.lutning(xk, True)
            zl, zr = z(xk, False), z(xk, True)
            xi = xk + (zr - zl) / (tl - tr) if abs(tl - tr) > 1e-9 else xk
            pts.append((xi, zl + tl * (xi - xk)))
        pts.append((fb, z(fb, False)))
        return pts

    def segment(pl, x):
        for (x0_, z0_), (x1_, z1_) in zip(pl, pl[1:]):
            if x <= x1_ or (x1_, z1_) == pl[-1]:
                t_ = (z1_ - z0_) / (x1_ - x0_)
                return t_, (lambda xx, x0_=x0_, z0_=z0_, t_=t_: z0_ + (xx - x0_) * t_)
        raise ValueError(x)

    def plattstal(pl, pos_fn):
        """2 st PL5*20 på högkant längs mittlinjen pl: lodräta ändar mot stolparna, gering i knäckarna. Varje bit
        byggs förlängd och kapas, så att kapet går genom hela höjden."""
        h2 = FL_H / 2
        for i, ((xa_, za_), (xb_, zb_)) in enumerate(zip(pl, pl[1:])):
            t_ = (zb_ - za_) / (xb_ - xa_)
            c_ = cos(t_)
            mitt_ = lambda x, xa_=xa_, za_=za_, t_=t_: za_ + (x - xa_) * t_
            f_st, f_kn = h2 * abs(t_) + 3, h2 * abs(t_) + FL_H                # förlängning före kap (stolpe/knäck)
            x_s = xa_ - (f_kn if i > 0 else f_st)
            x_e = xb_ + (f_kn if i < len(pl) - 2 else f_st)
            L = (xb_ - xa_) / c_ + h2 * abs(t_) * 2 / c_
            pos = pos_fn(round(L, 1), round(t_, 3))
            for y in (-Y_FL, Y_FL):
                fl = k.balk(pos, prof, P(x_s, y, mitt_(x_s)), P(x_e, y, mitt_(x_e)), upp=D(0, 1, 0), material=STAL)
                for j, xf in ((0, xa_), (1, xb_)):
                    kn = (j == 0 and i > 0) or (j == 1 and i < len(pl) - 2)
                    if not kn:                          # lodrät ände mot stolpen
                        gera(k, fl, P(xf, y, mitt_(xf) - 40), P(xf, y, mitt_(xf) + 40))
                    else:                               # gering i knäcken mot grannbiten
                        xo, zo = pl[i + j - 1] if j == 0 else pl[i + 2]
                        t2 = (zo - (za_ if j == 0 else zb_)) / (xo - xf)
                        c2 = cos(t2)
                        if abs(t2 - t_) < 1e-6:
                            gera(k, fl, P(xf, y, mitt_(xf) - 40), P(xf, y, mitt_(xf) + 40))
                            continue
                        zk = za_ if j == 0 else zb_
                        dx = h2 * (1 / c2 - 1 / c_) / (t_ - t2)        # överkanternas skärning
                        T = (xf + dx, zk + t_ * dx + h2 / c_)
                        B = (xf - dx, zk - t_ * dx - h2 / c_)
                        gera(k, fl, P(T[0], y, T[1]), P(B[0], y, B[1]))

    prof = "PL%g*%g" % (FL_T, FL_H)
    for xa, xb in zip(stolpar, stolpar[1:]):
        fa, fb = xa + ST_A / 2, xb - ST_A / 2
        pl_f = mittlinje(fa + SPALT, fb - SPALT, lambda x, h: hl_uk(x, h) - mellan - FL_H / 2 / cos(nos.lutning(x, h)))
        # på ett plant fack utan knäck (podest/vilplan) mäts underliggaren från stenen, inte från linjen som
        # ligger högre där handledarens knäck flyttats in till stolpen
        plan = not nos.knackar(fa, fb) and abs(nos.lutning((fa + fb) / 2)) < 1e-6
        y_plan = yta((fa + fb) / 2)
        pl_u = mittlinje(fa + SPALT, fb - SPALT, lambda x, h: (y_plan if plan else nos(x)) + under)
        plattstal(pl_f, lambda L, t_: nr(lpos, "l", (L, t_)))
        plattstal(pl_u, lambda L, t_: nr(lpos, "l", (L, t_)))
        # spjälor FS12 mellan följarna, kant i kant med följarnas överkant och underliggarnas underkant
        w = fb - fa
        m = max(1, int(math.ceil((w - 100.0) / (100.0 + SPJ_A))))
        fri = (w - m * SPJ_A) / (m + 1)
        tf0 = segment(pl_f, fa + 1)[0]
        fack.append(dict(fri=fri, cc=fri + SPJ_A, antal=m, lutning=math.degrees(math.atan(tf0))))
        r = SPJ_A / 2
        for j in range(m):
            x = fa + fri * (j + 1) + SPJ_A * (j + 0.5)
            if snitt_x is None and j == 1:
                snitt_x = x
            tf, zf = segment(pl_f, x)
            tu, zu = segment(pl_u, x)
            if abs(tf) < 2e-3:                  # plant parti (knäckens linje ger en lutning på några tusendelar)
                tf, zf = 0.0, (lambda xx, z0_=zf(x): z0_)
            if abs(tu) < 2e-3:
                tu, zu = 0.0, (lambda xx, z0_=zu(x): z0_)
            f_ok = lambda xx: zf(xx) + FL_H / 2 / cos(tf)
            u_uk = lambda xx: zu(xx) - FL_H / 2 / cos(tu)
            zb_, zt_ = u_uk(x) - r * abs(tu), f_ok(x) + r * abs(tf)
            Ls = zt_ - zb_
            if abs(tu) > 1e-4:                  # snedkapad nedtill: hel mm, kapet tar bort överskottet
                Ls = math.ceil(Ls)
                zb_ = zt_ - Ls
            nyckel = (round(Ls), round(math.degrees(math.atan(tu))), round(math.degrees(math.atan(tf))))
            spnr = nr(sppos, "sp", nyckel)
            sp_forst.setdefault(spnr, round(x, 1))
            sp = k.egen(spnr, "FS%g" % SPJ_A, fyrkant(SPJ_A, Ls), mitt=P(x, 0, zb_), rot=(ex, ey, ez), material=STAL)
            if abs(tu) > 1e-4:
                gera(k, sp, P(x - r, 0, u_uk(x - r)), P(x + r, 0, u_uk(x + r)))
            if abs(tf) > 1e-4:
                gera(k, sp, P(x - r, 0, f_ok(x - r)), P(x + r, 0, f_ok(x + r)))
        if len(fack) == 1:                      # vy E längs handledaren genom första facket
            xs = snitt_x if snitt_x is not None else fa + 60
            tf, zf = segment(pl_f, xs)
            tu, zu = segment(pl_u, xs)
            xm = (fa + fb) / 2
            f1 = dict(x=xs, zfl=zf(xs) - FL_H / 2 / cos(tf), zu=zu(xs), fa=fa, fb=fb, t=tf,
                      e_origo=P(xm, 0, (segment(pl_f, xm)[1](xm) + segment(pl_u, xm)[1](xm)) / 2))
    snitt = round(f1["x"], 1)

    # ---- detaljer i 1:2 (ritas av egna/ritning_detaljer.py): punkter i modellen, radie i modellmått
    zs_top = nos(snitt) + H
    zs_fl = f1["zfl"]
    det = [dict(vy="SnittE", punkt=P(snitt, 0, (zs_top + zs_fl) / 2), radie=round((zs_top - zs_fl) / 2 + 14, 1),
                rubrik="HANDLEDARE OCH FÖLJARE", text=["HANDLEDARE %s, RUNDAD ÖVERSIDA R%g" % (HL_PROFIL, HL_R),
                                                      "FÖLJARE 2 st PL5*20, SPJÄLA FS12 EMELLAN", "FRITT %g UNDER HANDLEDAREN" % mellan],
                matt="handledare"),
           dict(vy="SnittE", punkt=P(snitt, 0, f1["zu"]), radie=30.0,
                rubrik="UNDERLIGGARE", text=["UNDERLIGGARE 2 st PL5*20", "SPJÄLA FS12 KANT I KANT MED UNDERKANTEN",
                                             "%g ÖVER STEGFRAMKANT (MITT)" % under], matt="underliggare")]
    x_st = stolpar[1] if len(stolpar) > 2 else stolpar[0]
    det.append(dict(vy="Framvy", punkt=P(x_st, 0, hl_uk(x_st) - mellan / 2 - 10), radie=75.0, rubrik="STOLPE MOT HANDLEDARE",
                    text=["STOLPE FS20 KAPAD I HANDLEDARENS LUTNING, a4", "FÖLJARE MED LODRÄTA ÄNDAR MOT STOLPEN, a3"]))
    if start == "snacka":
        zc0 = nos(x0) + H - HL_T / 2
        det.append(dict(vy="Framvy", punkt=P(x0 - 30, 0, zc0 - 40), radie=72.0, rubrik="SNÄCKA",
                        text=["SMIDD SNÄCKA 1,5 VARV, R%g/%g/%g (MITTLINJE)" % SNACKA_R, "UTVECKLAD LÄNGD %.0f" % snacka_langd()]))
    for xk in nos.knackar(x0, x1):
        vid_stolpe = any(abs(xk - xs) < ST_A / 2 for xs in stolpar)
        det.append(dict(vy="Framvy", punkt=P(xk, 0, nos(xk) + H - 35), radie=70.0, rubrik="KNÄCK I HANDLEDAREN",
                        text=["BOCKAS I ETT STYCKE ELLER SVETSAS OCH SLIPAS"]
                        + (["KNÄCKEN MITT ÖVER STOLPEN, STOLPTOPPEN", "KAPAD I BÅDA LUTNINGARNA, a4"] if vid_stolpe else [])))
        break
    ce, se = cos(f1["t"]), math.sin(math.atan(f1["t"]))
    snitt_e = dict(namn="E", origo=f1["e_origo"], normal=D(-ce, 0, -se), x_omr=[f1["fa"], f1["fb"]],
                   text="TVÄRSNITT: FÖRSTA FACKET SETT LÄNGS HANDLEDAREN")
    knack_i_fack = any(nos.knackar(a + ST_A / 2, b - ST_A / 2) for a, b in zip(stolpar, stolpar[1:]))
    return dict(knack_i_fack=knack_i_fack, fack=fack, bitar=bitar, snitt_x=snitt, sp_x=sorted(sp_forst.values()), stolpar=stolpar, detaljer=det, snitt_e=snitt_e,
                stolp_cc=max(b - a for a, b in zip(stolpar, stolpar[1:])))


def ritning(k, info, noter_):
    """Framvy och snitt A genom en spjäla; detaljerna sparas i Sammanstallning.Detaljer för ritning_detaljer.py."""
    k.ritning(vyer=["fram"], snitt=[dict(namn="A", axel="x", varde=info["snitt_x"], mot="-")], noter=noter_)
    g = k.grupp
    if not hasattr(g, "Detaljer"):
        g.addProperty("App::PropertyString", "Detaljer", "Stal", "detaljer i 1:2 (JSON) för egna/ritning_detaljer.py")
    g.Detaljer = json.dumps(dict(snitt=info["snitt_e"], detaljer=info["detaljer"]), ensure_ascii=False)


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
             "RÄCKESHÖJD %g LODRÄTT ÖVER STEGFRAMKANT, ±0 = GÅNGEN VID TRAPPANS FOT" % v["Hojd"],
             "STOLPAR st: FS20, %g mm NEDGJUTNA I KÄRNBORRADE HÅL Ø40 I GRANITEN (INGÅR I LÄNGDEN), c/c MAX %.0f"
             % (INGJUT, info["stolp_cc"])]
    if start == "snacka":
        rader.append("HANDLEDARE %s (PLATTSTÅL 40x10, RUNDAD ÖVERSIDA): %s, SMIDD SNÄCKA PÅ %s (UTVECKLAD %.0f)"
                     % (HL_PROFIL, hl, bitar[0]["pos"], snacka_langd()))
    else:
        rader.append("HANDLEDARE %s (PLATTSTÅL 40x10, RUNDAD ÖVERSIDA): %s" % (HL_PROFIL, hl))
    if len(bitar) > 1:
        rader.append("HANDLEDARENS KNÄCK %s BOCKAS I ETT STYCKE ELLER SVETSAS OCH SLIPAS"
                     % " / ".join("%s %s" % (b["pos"], "PLAN" if abs(b["lutning"]) < 0.05 else "%.1f°" % b["lutning"]) for b in bitar))
    rader.append(slut_text)
    rader += list(extra)
    rader += ["FÖLJARE OCH UNDERLIGGARE l: 2 st PL5*20 PÅ HÖGKANT, ETT PÅ VAR SIDA OM SPJÄLORNA, "
              + ("BOCKAS/GERAS I KNÄCKEN" if info.get("knack_i_fack") else "RAKA MELLAN STOLPARNA"),
              "SPJÄLOR sp FS12 MELLAN FÖLJARNA, c/c MAX %.0f, FRI ÖPPNING MIN %.0f (< 100)" % (cc, fri),
              "SVETS: STOLPAR MOT HANDLEDARE a4, FÖLJARE MOT STOLPAR OCH SPJÄLOR a3 – DETALJER SE BLAD 2",
              "YTBEHANDLING: VARMFÖRZINKAD OCH PULVERLACKAD SVART RAL 9005 (ANTAGET, ENLIGT BESTÄLLNING)"]
    return rader
