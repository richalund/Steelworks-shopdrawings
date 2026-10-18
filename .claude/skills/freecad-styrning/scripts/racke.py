"""Räcken för trappor, ramper och plana partier (smidesräcken med stolpar, handledare, följare och spjälor),
byggda som vanliga delar i stal.Konstruktion. Används från ett konstruktionsskript:

  import racke
  def bygg(k, v):
      t = racke.rak_trappa(k, steg=6, steghojd=165, stegdjup=280, bredd=1200, podest=1000, knack_in=60)
      st = racke.fordela([140, t["knack"], t["knack"] + 900], t["stegmitt"], max_cc=1300)
      info = racke.bygg(k, linje=t["linje"], yta=t["yta"], stolpar=st, handledare_x=(80, t["knack"] + 940),
                        hojd=v["Hojd"], handledare="RÖR42.4*2.6", stolpe=dict(profil="VKR40*4", fot="fotplat"))
      racke.ritval(k, info, noter=racke.noter(info) + ["YTBEHANDLING ..."])

Räcket ritas i lokala koordinater: x längs räcket (uppför), y tvärs (räckesplanet y = 0), z uppåt. `ursprung`,
`ex`, `ey` placerar det i en större modell (översikt med flera räcken). `linje` är framkantslinjen (stegens
nosar och plana ytor) som polylinje av (x, z); handledarens överkant ligger `hojd` lodrätt över den. Där linjen
knäcker delas handledaren (bockas eller svetsas). En knäck mitt över en stolpe (se rak_trappa(knack_in=...))
ger raka följare i alla fack och en stolptopp kapad i båda lutningarna.

Utförandet väljs med parametrar, inget är förvalt utöver ett enkelt räcke:
  handledare  "FL40*10" (plattstång), dict(profil="FL40*10", rundad=True) (rundad översida, sidorna `sida` höga),
              "RÖR42.4*2.6", "VKR40*4", "D20" ...
  start/slut  "rak" (standard) eller "snacka" i startänden (smidd snäcka, bara plattstång)
  foljare     None (spjälorna går till handledaren), dict(typ="enkel", profil="FL30*8") (liggande plattstång
              under handledaren, spjälorna svetsas under), dict(typ="dubbel", profil="PL5*20") (två plattstål på
              högkant, ett på var sida om spjälorna); `mellan` = fritt mellan handledare och följare
  underliggare  som foljare (None = spjälorna slutar `under` över linjen)
  spjalor     dict(profil="FS12" | "D12", fri=100) (fri öppning < fri), None = inga spjälor
  stolpe      dict(profil="FS20" | "VKR40*4" | "RÖR42.4*3", fot="ingjutning", djup=100, hal="Ø40")
              eller dict(profil=..., fot="fotplat", plat="PL8*100", bult="M10", cc=60)
Alla mått räknas i Python (sned geometri): ändrade mått kräver ombyggnad (sammanstallning.py bygg).
"""
import math

STAL = "S235JR"
SPALT = 2.0                    # svetsspalt vid följarnas ändar mot stolpen
SNACKA_RAK = 150.0             # rak handledare förbi första stolpen före snäckan (förslag till handledare_x)
SNACKA_R = (42.0, 28.0, 16.0)  # snäckans mittlinjeradier, tre halvvarv (1,5 varv)
VARIABLER = [
    ("Hojd", 900, "mm, handledarens överkant lodrätt över stegframkant / plan yta"),
    ("Under", 80, "mm, underliggarens mitt (eller spjälornas underkant) lodrätt över stegframkant / plan yta"),
    ("Mellan", 70, "mm, fritt mellan handledare och följare"),
]


# ============================================================================================ geometri
class Linje:
    """Framkantslinjen: polylinje genom (x, z)-punkterna, förlängd med ändsegmentens lutning."""

    def __init__(self, pkt):
        self.p = sorted((float(x), float(z)) for x, z in pkt)

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
        """Knäckarna (inre punkter där lutningen ändras) mellan x0 och x1."""
        return [x for x, _ in self.p[1:-1] if x0 < x < x1]


def fordela(fasta, lage=lambda x: x, max_cc=1300.0):
    """Stolplägen: de fasta (sektionernas ändar och knäckar) plus jämnt fördelade mellanstolpar så att c/c blir
    högst max_cc. lage(x) flyttar en mellanstolpe till ett giltigt läge (t.ex. stegmitt); av grannlägena väljs
    det som håller c/c och ligger närmast den jämna delningen."""
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


def rak_trappa(k=None, steg=6, steghojd=165.0, stegdjup=280.0, bredd=1200.0, podest=0.0, knack_in=0.0, y0=0.0,
               z0=0.0, tjocklek=None, farg=(0.82, 0.82, 0.80), prefix="Trappa"):
    """Rak trappa med `steg` stigningar (steg - 1 plansteg + podest överst) som referens: x = 0 vid nedersta
    stegets framkant, trappan mellan y0 och y0 + bredd, golvet nedtill på z0. Med k ritas stegen (och podesten
    om podest > 0) som referenskroppar (k.referens). knack_in flyttar räckeslinjens knäck in på podesten (för en
    stolpe mitt under handledarens knäck, en bit från stenkanten). Returnerar dict med linje (framkantslinjen
    för racke.bygg), yta(x) (stegets/podestens överkant), stegmitt(x) (närmaste stegmitt, för fordela),
    knack (knäckens x) och topp (podestens höjd)."""
    R, G, n = float(steghojd), float(stegdjup), int(steg)
    xp, zt = (n - 1) * G, z0 + n * R
    t = R / G
    xk = xp + knack_in
    langt = xp + max(podest, knack_in) + 1000.0
    linje = [(-G, z0), (xk, zt + knack_in * t), (langt, zt + knack_in * t)] if podest > 0 or knack_in > 0 else [(-G, z0), (xp, zt)]
    if k is not None:
        T_ = tjocklek or R
        for i in range(1, n):
            z = z0 + i * R
            k.referens("%s_steg%d" % (prefix, i), lada=((i - 1) * G, i * G, y0, y0 + bredd, max(z - T_, z0), z), farg=farg)
        if podest > 0:
            k.referens("%s_podest" % prefix, lada=(xp, xp + podest, y0, y0 + bredd, max(zt - T_, z0), zt), farg=farg)

    def yta(x):
        if x < 0:
            return z0
        if x >= xp:
            return zt
        return z0 + (math.floor(x / G) + 1) * R

    def stegmitt(x):
        if x < 0 or x >= xp:
            return x
        return (math.floor(x / G) + 0.5) * G
    return dict(linje=linje, yta=yta, stegmitt=stegmitt, knack=xk, topp=zt, stegdjup=G, steghojd=R)


# ============================================================================================ kroppar
def _hoj(info):
    """Tvärsnittets höjd och bredd (mm) för en profil tolkad av stal.tolka."""
    t = info["typ"]
    if t == "PL":
        return info["t"], info["b"]
    if t in ("D", "O"):
        return info["d"], info["d"]
    if t in ("R", "U", "I", "L"):
        return info["h"], info["b"]
    raise ValueError("profiltyp %s stöds inte i räcket" % t)


def rundad_plattstang(b, t, sida, L):
    """Kropp för en plattstång b x t med plan undersida, sidor `sida` höga och rundad översida (cirkelbåge genom
    hörnen och mitten), lådans mitt i origo, Pad L längs kroppens z. Fullt bestämd skiss."""
    R = ((b / 2) ** 2 + (t - sida) ** 2) / (2 * (t - sida))

    def bygg(d):
        import pd
        import Part
        from FreeCAD import Vector as V
        sk = d.skiss("Tvarsnitt", "XY")
        b2, y0, y1 = b / 2, -t / 2, -t / 2 + sida
        A, B, C, D = (-b2, y0), (b2, y0), (b2, y1), (-b2, y1)
        g = [sk.geo(Part.LineSegment(V(*p, 0), V(*q, 0))) for p, q in ((A, B), (B, C), (D, A))]
        yc = t / 2 - R
        a0, a1 = math.atan2(y1 - yc, b2), math.atan2(y1 - yc, -b2)
        bage = sk.geo(Part.ArcOfCircle(Part.Circle(V(0, yc, 0), V(0, 0, 1), R), a0, a1))
        sk.begr("Coincident", g[0], pd.SLUT, g[1], pd.START)
        sk.begr("Coincident", g[1], pd.SLUT, bage, pd.START)
        sk.begr("Coincident", bage, pd.SLUT, g[2], pd.START)
        sk.begr("Coincident", g[2], pd.SLUT, g[0], pd.START)
        for gi, pt, pp in ((g[0], pd.START, A), (g[0], pd.SLUT, B), (g[1], pd.SLUT, C), (g[2], pd.START, D)):
            sk.placera(gi, pt, pp[0], pp[1], namn="")
        sk.matt("Radius", bage, varde=R, namn="R")
        d.kloss(sk, round(L, 2), "Langd")
    return bygg, R


def snacka_langd():
    return math.pi * sum(SNACKA_R)


def bygg_snacka(k, hl, b, t):
    """Smidd snäcka på handledarens startände: skiss i kroppens YZ-plan (tjockleksriktning och längd, änden i
    z = 0) med yttre och inre bågkedja (tre halvvarv med minskande radie, tangerande) och två ändlinjer, fullt
    bestämd; Pad b symmetriskt (handledarens bredd). Snäckan rullas nedåt."""
    import pd
    import Part
    from FreeCAD import Vector as V
    dd = pd.Del(k.doc, hl.Name)
    sk = dd.skiss("Snacka", "YZ")
    R1, R2, R3 = SNACKA_R
    t2 = t / 2
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
    x_slut = C[2][0] - R3
    l1 = sk.geo(Part.LineSegment(V(-t2, 0, 0), V(t2, 0, 0)))
    l2 = sk.geo(Part.LineSegment(V(x_slut - t2, 0, 0), V(x_slut + t2, 0, 0)))
    sk.begr("Coincident", l1, pd.START, inre[0], pd.SLUT)
    sk.begr("Coincident", l1, pd.SLUT, yttre[0], pd.SLUT)
    sk.begr("Coincident", l2, pd.START, yttre[2], pd.START)
    sk.begr("Coincident", l2, pd.SLUT, inre[2], pd.START)
    dd.kloss(sk, b, "Snacka", symmetrisk=True)
    dd.stada()


def _skena(spec, standard):
    """Normalisera foljare/underliggare: None, "dubbel"/"enkel" eller dict(typ, profil)."""
    if spec is None or spec is False:
        return None
    if isinstance(spec, str):
        spec = dict(typ=spec)
    s = dict(standard.get(spec.get("typ", "dubbel"), {}), **spec)
    if s["typ"] not in ("dubbel", "enkel"):
        raise ValueError("följare/underliggare: typ dubbel eller enkel, fick %s" % s["typ"])
    return s


# ============================================================================================ räcket
def bygg(k, linje, stolpar, handledare_x, hojd=900.0, under=80.0, mellan=70.0, yta=None,
         handledare="FL40*10", start="rak", foljare=None, underliggare=None, spjalor=None, stolpe=None,
         ursprung=(0, 0, 0), ex=(1, 0, 0), ey=(0, 1, 0), prefix="", huvuddel=True, extern=(), material=STAL):
    """Bygger räcket och returnerar info (fack, bitar, stolpar, detaljer och delvy för ritningen, texter till
    noterna). stolpar = stolparnas x (uppför); extern = index för stolpar som hör till ett anslutande räcke och
    inte byggs här (t.ex. en gemensam hörnstolpe); handledare_x = handledarens ändar (x0, x1)."""
    import stal
    H = float(hojd)
    nos = Linje(linje)
    yta = yta or nos
    ex, ey = [float(q) for q in ex], [float(q) for q in ey]
    ez = [ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0]]
    o = [float(q) for q in ursprung]
    P = lambda x, y, z: tuple(round(o[i] + x * ex[i] + y * ey[i] + z * ez[i], 4) for i in range(3))
    D = lambda x, y, z: tuple(x * ex[i] + y * ey[i] + z * ez[i] for i in range(3))
    pos_ = lambda p: prefix + p
    cos = lambda t: math.cos(math.atan(t))
    EY = D(0, 1, 0)

    # ---- val
    hl = dict(profil=handledare) if isinstance(handledare, str) else dict(handledare)
    hl_info = stal.tolka(hl["profil"], kallor=False)
    hl_t, hl_b = _hoj(hl_info)
    rundad = bool(hl.get("rundad")) and hl_info["typ"] == "PL"
    if start == "snacka" and hl_info["typ"] != "PL":
        raise ValueError("snäcka går bara på en handledare av plattstång (FL/PL), fick %s" % hl["profil"])
    st = dict(dict(profil="FS20", fot="ingjutning", djup=100.0, hal="Ø40"), **(stolpe or {}))
    st_info = stal.tolka(st["profil"], kallor=False)
    st_a = _hoj(st_info)[1]                                     # bredd längs räcket
    fol = _skena(foljare, dict(dubbel=dict(profil="PL5*20"), enkel=dict(profil="FL30*8")))
    und = _skena(underliggare, dict(dubbel=dict(profil="PL5*20"), enkel=dict(profil="FL30*8")))
    sp = None if spjalor is None or spjalor is False else dict(dict(profil="FS12", fri=100.0), **(spjalor if isinstance(spjalor, dict) else {}))
    sp_a = _hoj(stal.tolka(sp["profil"], kallor=False))[1] if sp else 0.0

    def skenmatt(s):
        """(höjd i räckesplanet, bredd tvärs, y-lägen för bitarna) för en följare/underliggare."""
        i = stal.tolka(s["profil"], kallor=False)
        t_, b_ = i["t"], i["b"]
        if s["typ"] == "dubbel":
            y = sp_a / 2 + t_ / 2
            return b_, t_, (-y, y)
        return t_, b_, (0.0,)
    hl_uk = lambda x, hoger=True: nos(x) + H - hl_t / cos(nos.lutning(x, hoger))      # handledarens underkant

    # ---- handledare: en bit per lutning, gerad i knäckarna (planet genom över- och underkanternas skärningar)
    x0, x1 = handledare_x
    knackar = nos.knackar(x0, x1)
    grans = [x0] + knackar + [x1]
    gering = []                                  # (x, z) överkant och underkant i varje knäck
    for xk in knackar:
        tl, tr = nos.lutning(xk, False), nos.lutning(xk, True)
        ztop = nos(xk) + H
        zl, zr = ztop - hl_t / cos(tl), ztop - hl_t / cos(tr)
        xi = xk + (zr - zl) / (tl - tr)
        gering.append(((xk, ztop), (xi, zl + tl * (xi - xk))))
    bitar, hl_obj = [], []
    for i, (a, b) in enumerate(zip(grans, grans[1:])):
        ext_a = abs(gering[i - 1][1][0] - gering[i - 1][0][0]) + hl_t / 2 + 1 if i > 0 else 0.0
        ext_b = abs(gering[i][1][0] - gering[i][0][0]) + hl_t / 2 + 1 if i < len(grans) - 2 else 0.0
        a2, b2 = a - ext_a, b + ext_b
        t = nos.lutning((a + b) / 2)
        c, s_ = cos(t), math.sin(math.atan(t))
        zc0 = nos(a) + H - hl_t / 2 / c - t * ext_a
        L = (b2 - a2) / c
        pos = pos_("hl/%d" % (i + 1))
        if rundad:
            byggf, R_hl = rundad_plattstang(hl_b, hl_t, float(hl.get("sida", hl_t * 0.6)), L)
            ob = k.egen(pos, hl["profil"], byggf, mitt=P(a2, 0, zc0), rot=(EY, D(-s_, 0, c), D(c, 0, s_)), material=material)
        else:
            R_hl = None
            ob = k.balk(pos, hl["profil"], P(a2, 0, zc0), P(b2, 0, zc0 + t * (b2 - a2)), upp=D(-s_, 0, c), material=material)
        if i == 0 and start == "snacka":
            bygg_snacka(k, ob, hl_b, hl_t)
        for j in ([i - 1] if i > 0 else []) + ([i] if i < len(grans) - 2 else []):
            (xt, zt), (xu, zu) = gering[j]
            k.gera(ob, P(xt, 0, zt), P(xu, 0, zu), riktning=EY)
        hl_obj.append(ob)
        bitar.append(dict(pos=pos, langd=L, lutning=math.degrees(math.atan(t))))     # som i materiallistan

    # ---- stolpar
    spos, st_obj = {}, {}
    for i, x in enumerate(stolpar):
        if i in extern:
            continue
        xa, xb = x - st_a / 2, x + st_a / 2
        za, zb = hl_uk(xa), hl_uk(xb, hoger=False)
        if st["fot"] == "ingjutning":
            z0 = yta(x) - float(st["djup"])
        else:
            z0 = yta(x) + stal.tolka(st.get("plat", "PL8*100"), kallor=False)["t"]
        ztop = math.floor(max(za, zb) * 10 + 1e-6) / 10       # nedåt: toppen får inte gå upp i handledaren
        Lp = round(ztop - z0, 1)
        knack = nos.knackar(xa, xb)
        pos = spos.setdefault((Lp, round(zb - za, 1), bool(knack)), pos_("st/%d" % (len(spos) + 1)))
        so = k.balk(pos, st["profil"], P(x, 0, z0), P(x, 0, ztop), upp=EY, material=material, huvuddel=(huvuddel and i == 0))
        st_obj[i] = so
        if knack:                      # knäckstolpe: toppen kapas i båda lutningarna, möts under handledarens knäck
            tl, tr = nos.lutning(xa), nos.lutning(xb, False)
            if tl <= tr:
                raise ValueError("stolpe x=%g i en inåtknäck (lutningen ökar) stöds inte" % x)
            xi = xa + (zb - za - tr * (xb - xa)) / (tl - tr)            # underkanternas skärning
            zi = za + tl * (xi - xa)
            for (xp, zp, tp) in ((xa, za, tl), (xb, zb, tr)):
                if ztop - min(zp, zi) > 0.01 or abs(tp) > 1e-6:
                    k.gera(so, P(xp, 0, zp), P(xi, 0, zi), riktning=EY)
        elif abs(zb - za) > 0.01:
            k.gera(so, P(xa, 0, za), P(xb, 0, zb), riktning=EY)
        if st["fot"] == "fotplat":
            pl_info = stal.tolka(st.get("plat", "PL8*100"), kallor=False)
            pt, pb = pl_info["t"], pl_info["b"]
            fp = k.plat(pos_("fp/1"), st.get("plat", "PL8*100"), mitt=P(x, 0, yta(x) + pt / 2), langd=pb,
                        lriktning=D(1, 0, 0), briktning=EY, material=material)
            cc = float(st.get("cc", pb - 40))
            k.hal([fp], [P(x + dx, dy, yta(x) + pt / 2) for dx in (-cc / 2, cc / 2) for dy in (-cc / 2, cc / 2)],
                  riktning=D(0, 0, 1), bult=st.get("bult", "M10"))

    # ---- följare, underliggare och spjälor per fack mellan stolparna
    lpos, sppos, fack, sp_forst = {}, {}, [], {}
    snitt_x, f1 = None, None

    def nr(tab, prefixtxt, nyckel):
        return tab.setdefault(nyckel, pos_("%s/%d" % (prefixtxt, len(tab) + 1)))

    def mittlinje(fa, fb, z):
        """Polylinje (x, z) från fa till fb med knäck där framkantslinjen knäcker; knäckpunkten är skärningen
        mellan linjerna på var sida (de är förskjutna olika mycket när lutningen ändras)."""
        pts = [(fa, z(fa, True))]
        for xk in nos.knackar(fa, fb):
            tl, tr = nos.lutning(xk, False), nos.lutning(xk, True)
            zl, zr = z(xk, False), z(xk, True)
            xi = xk + (zr - zl) / (tl - tr) if abs(tl - tr) > 1e-9 else xk
            pts.append((xi, zl + tl * (xi - xk)))
        pts.append((fb, z(fb, False)))
        return pts

    def segment(pl, x):
        for (xa_, za_), (xb_, zb_) in zip(pl, pl[1:]):
            if x <= xb_ or (xb_, zb_) == pl[-1]:
                t_ = (zb_ - za_) / (xb_ - xa_)
                return t_, (lambda xx, xa_=xa_, za_=za_, t_=t_: za_ + (xx - xa_) * t_)
        raise ValueError(x)

    def skena(pl, s, pos_fn):
        """En följare/underliggare längs mittlinjen pl: lodräta ändar mot stolparna, gering i knäckarna. Varje bit
        byggs förlängd och kapas, så att kapet går genom hela höjden."""
        hp, bt, ys = skenmatt(s)
        h2 = hp / 2
        for i, ((xa_, za_), (xb_, zb_)) in enumerate(zip(pl, pl[1:])):
            t_ = (zb_ - za_) / (xb_ - xa_)
            c_ = cos(t_)
            mitt_ = lambda x, xa_=xa_, za_=za_, t_=t_: za_ + (x - xa_) * t_
            f_st, f_kn = h2 * abs(t_) + 3, h2 * abs(t_) + hp                 # förlängning före kap (stolpe/knäck)
            x_s = xa_ - (f_kn if i > 0 else f_st)
            x_e = xb_ + (f_kn if i < len(pl) - 2 else f_st)
            L = (xb_ - xa_) / c_ + h2 * abs(t_) * 2 / c_
            pos = pos_fn(round(L, 1), round(t_, 3), s["profil"])
            for y in ys:
                upp = EY if s["typ"] == "dubbel" else D(-math.sin(math.atan(t_)), 0, c_)
                fl = k.balk(pos, s["profil"], P(x_s, y, mitt_(x_s)), P(x_e, y, mitt_(x_e)), upp=upp, material=material)
                for j, xf in ((0, xa_), (1, xb_)):
                    kn = (j == 0 and i > 0) or (j == 1 and i < len(pl) - 2)
                    if not kn:
                        k.gera(fl, P(xf, y, mitt_(xf) - 40), P(xf, y, mitt_(xf) + 40), riktning=EY)
                        continue
                    xo, zo = pl[i + j - 1] if j == 0 else pl[i + 2]
                    t2 = (zo - (za_ if j == 0 else zb_)) / (xo - xf)
                    if abs(t2 - t_) < 1e-6:
                        k.gera(fl, P(xf, y, mitt_(xf) - 40), P(xf, y, mitt_(xf) + 40), riktning=EY)
                        continue
                    zk = za_ if j == 0 else zb_
                    dx = h2 * (1 / cos(t2) - 1 / c_) / (t_ - t2)               # överkanternas skärning
                    k.gera(fl, P(xf + dx, y, zk + t_ * dx + h2 / c_), P(xf - dx, y, zk - t_ * dx - h2 / c_), riktning=EY)

    for xa, xb in zip(stolpar, stolpar[1:]):
        fa, fb = xa + st_a / 2, xb - st_a / 2
        plan = not nos.knackar(fa, fb) and abs(nos.lutning((fa + fb) / 2)) < 1e-6
        y_plan = yta((fa + fb) / 2)
        golv = lambda x, h: (y_plan if plan else nos(x))      # på ett plant fack mäts underkanten från ytan
        if fol:
            hp = skenmatt(fol)[0]
            pl_f = mittlinje(fa + SPALT, fb - SPALT, lambda x, h: hl_uk(x, h) - mellan - hp / 2 / cos(nos.lutning(x, h)))
            skena(pl_f, fol, lambda L, t_, p: nr(lpos, "l", (L, t_, p)))
        else:
            pl_f = mittlinje(fa, fb, lambda x, h: hl_uk(x, h))
        if und:
            pl_u = mittlinje(fa + SPALT, fb - SPALT, lambda x, h: golv(x, h) + under)
            skena(pl_u, und, lambda L, t_, p: nr(lpos, "l", (L, t_, p)))
        else:
            pl_u = mittlinje(fa, fb, lambda x, h: golv(x, h) + under)
        # spjälor: mellan dubbla följare kant i kant med deras över-/underkant, annars mot enkel följares underkant,
        # handledarens underkant, enkel underliggares överkant eller fritt `under` över linjen
        w = fb - fa
        tf0 = segment(pl_f, fa + 1)[0]
        if sp:
            m = max(1, int(math.ceil((w - sp["fri"]) / (sp["fri"] + sp_a))))
            fri = (w - m * sp_a) / (m + 1)
        else:
            m, fri = 0, w
        fack.append(dict(fri=fri, cc=fri + sp_a, antal=m, lutning=math.degrees(math.atan(tf0)), fa=fa, fb=fb))
        r = sp_a / 2
        for j in range(m):
            x = fa + fri * (j + 1) + sp_a * (j + 0.5)
            if snitt_x is None and j == 1:
                snitt_x = x
            tf, zf = segment(pl_f, x)
            tu, zu = segment(pl_u, x)
            if abs(tf) < 2e-3:                  # plant parti (knäckens linje ger en lutning på några tusendelar)
                tf, zf = 0.0, (lambda xx, z0_=zf(x): z0_)
            if abs(tu) < 2e-3:
                tu, zu = 0.0, (lambda xx, z0_=zu(x): z0_)
            if fol and fol["typ"] == "dubbel":
                topp = lambda xx: zf(xx) + skenmatt(fol)[0] / 2 / cos(tf)
            elif fol:
                topp = lambda xx: zf(xx) - skenmatt(fol)[0] / 2 / cos(tf)
            else:
                topp = zf                               # handledarens underkant
            if und and und["typ"] == "dubbel":
                botten = lambda xx: zu(xx) - skenmatt(und)[0] / 2 / cos(tu)
            elif und:
                botten = lambda xx: zu(xx) + skenmatt(und)[0] / 2 / cos(tu)
            else:
                botten = zu
            zb_, zt_ = botten(x) - r * abs(tu), topp(x) + r * abs(tf)
            Ls = zt_ - zb_
            if abs(tu) > 1e-4:                  # snedkapad nedtill: hel mm, kapet tar bort överskottet
                Ls = math.ceil(Ls)
                zb_ = zt_ - Ls
            nyckel = (round(Ls), round(math.degrees(math.atan(tu))), round(math.degrees(math.atan(tf))))
            spnr = nr(sppos, "sp", nyckel)
            sp_forst.setdefault(spnr, round(x, 1))
            so = k.balk(spnr, sp["profil"], P(x, 0, zb_), P(x, 0, zb_ + Ls), upp=EY, material=material)
            if abs(tu) > 1e-4:
                k.gera(so, P(x - r, 0, botten(x - r)), P(x + r, 0, botten(x + r)), riktning=EY)
            if abs(tf) > 1e-4:
                k.gera(so, P(x - r, 0, topp(x - r)), P(x + r, 0, topp(x + r)), riktning=EY)
        if f1 is None:                          # vy längs handledaren genom första facket
            xs = snitt_x if snitt_x is not None else (fa + fb) / 2
            tf, zf = segment(pl_f, xs)
            tu, zu = segment(pl_u, xs)
            f1 = dict(x=xs, zf=zf(xs), zu=zu(xs), fa=fa, fb=fb, t=tf)

    # ---- ritningens detaljer (blad 2) och delvy längs handledaren
    det = []
    ce, se = cos(f1["t"]), math.sin(math.atan(f1["t"]))
    xs = f1["x"]
    def x_omr(ob):                              # kroppens utsträckning längs räcket (lokalt x)
        bb = ob.Shape.BoundBox
        xs_ = [sum((q - o_) * e_ for q, o_, e_ in zip(h_, o, ex))
               for h_ in [(a_, b_, c_) for a_ in (bb.XMin, bb.XMax) for b_ in (bb.YMin, bb.YMax) for c_ in (bb.ZMin, bb.ZMax)]]
        return min(xs_), max(xs_)
    namn_e = []
    for ob in k.grupp.Group:
        if not hasattr(ob, "Pos") or not ob.Pos.startswith(prefix):
            continue
        p_ = ob.Pos[len(prefix):]
        xa_, xb_ = x_omr(ob)
        if p_.startswith(("l/", "sp/")) and f1["fa"] - 1 <= xa_ and xb_ <= f1["fb"] + 1:
            namn_e.append(ob.Name)
        elif ob in hl_obj and xa_ < f1["fb"] and xb_ > f1["fa"]:
            pad = next((f for f in ob.Group if f.TypeId == "PartDesign::Pad"), ob)   # profilen utan snäckan
            namn_e.append(pad.Name)
    delvy = dict(namn="E", normal=D(-ce, 0, -se), kallor=namn_e, text=["SETT LÄNGS HANDLEDAREN, FÖRSTA FACKET"])
    hl_txt = "HANDLEDARE %s%s" % (hl["profil"], ", RUNDAD ÖVERSIDA R%.0f" % R_hl if rundad else "")
    m_hl = ([dict(typ="d", varde=hl_b)] if hl_info["typ"] in ("O", "D") else [dict(typ="x", varde=hl_b, lage="over")]) + \
        ([dict(typ="r", varde=round(R_hl, 1))] if rundad else [])
    ztop_s = nos(xs) + H
    if fol:
        hp, bt, ys = skenmatt(fol)
        txt = ["%s, %s" % (hl_txt, "FRITT %g UNDER" % mellan),
               "FÖLJARE %s%s" % ("2 st " if fol["typ"] == "dubbel" else "", fol["profil"])]
        z_l = f1["zf"] - hp / 2
        m_f = [dict(typ="x", varde=bt, lage="over")] + ([dict(typ="x", varde=sp_a, lage="over")] if sp and fol["typ"] == "dubbel" else [])
    else:
        txt, z_l, m_f = [hl_txt] + (["SPJÄLORNA SVETSAS UNDER HANDLEDAREN"] if sp else []), ztop_s - hl_t - 20, []
    det.append(dict(vy="E", punkt=P(xs, 0, (ztop_s + z_l) / 2), radie=round((ztop_s - z_l) / 2 + 14, 1),
                    rubrik="HANDLEDARE OCH FÖLJARE" if fol else "HANDLEDARE", text=txt, matt=m_hl + m_f))
    if und:
        hp, bt, ys = skenmatt(und)
        det.append(dict(vy="E", punkt=P(xs, 0, f1["zu"]), radie=max(30.0, hp + 10), rubrik="UNDERLIGGARE",
                        text=["UNDERLIGGARE %s%s" % ("2 st " if und["typ"] == "dubbel" else "", und["profil"]),
                              "%g ÖVER STEGFRAMKANT (MITT)" % under],
                        matt=[dict(typ="x", varde=bt, lage="under")] + ([dict(typ="x", varde=sp_a, lage="under")] if sp and und["typ"] == "dubbel" else [])))
    x_st = stolpar[1] if len(stolpar) > 2 else stolpar[0]
    det.append(dict(vy="fram", punkt=P(x_st, 0, hl_uk(x_st) - (mellan / 2 if fol else 0) - 10), radie=75.0, rubrik="STOLPE MOT HANDLEDARE",
                    text=["STOLPE %s KAPAD I HANDLEDARENS LUTNING, a4" % st["profil"]]
                    + (["FÖLJARE MED LODRÄTA ÄNDAR MOT STOLPEN, a3"] if fol else [])))
    if start == "snacka":
        zc0 = nos(x0) + H - hl_t / 2
        det.append(dict(vy="fram", punkt=P(x0 - 30, 0, zc0 - 40), radie=72.0, rubrik="SNÄCKA",
                        text=["SMIDD SNÄCKA 1,5 VARV, R%g/%g/%g (MITTLINJE)" % SNACKA_R, "UTVECKLAD LÄNGD %.0f" % snacka_langd()]))
    for xk in nos.knackar(x0, x1):
        vid_stolpe = any(abs(xk - x_) < st_a / 2 for x_ in stolpar)
        det.append(dict(vy="fram", punkt=P(xk, 0, nos(xk) + H - 35), radie=70.0, rubrik="KNÄCK I HANDLEDAREN",
                        text=["BOCKAS I ETT STYCKE ELLER SVETSAS OCH SLIPAS"]
                        + (["KNÄCKEN MITT ÖVER STOLPEN, STOLPTOPPEN", "KAPAD I BÅDA LUTNINGARNA, a4"] if vid_stolpe else [])))
        break
    if st["fot"] == "fotplat":
        x_f = stolpar[0] if 0 not in extern else stolpar[1]
        det.append(dict(vy="fram", punkt=P(x_f, 0, yta(x_f) + 10), radie=70.0, rubrik="FOTPLÅT",
                        text=["FOTPLÅT %s, 4 HÅL FÖR %s c/c %g" % (st.get("plat", "PL8*100"), st.get("bult", "M10"),
                                                                    float(st.get("cc", stal.tolka(st.get("plat", "PL8*100"), kallor=False)["b"] - 40))),
                              "STOLPE MOT FOTPLÅT a4 RUNT OM"]))
    knack_i_fack = any(nos.knackar(a + st_a / 2, b - st_a / 2) for a, b in zip(stolpar, stolpar[1:]))
    return dict(fack=fack, bitar=bitar, stolpar=list(stolpar), extern=list(extern), stolp_cc=max(b - a for a, b in zip(stolpar, stolpar[1:])),
                snitt_x=round(snitt_x if snitt_x is not None else f1["x"], 1), sp_x=sorted(sp_forst.values()), detaljer=det, delvy=delvy,
                knack_i_fack=knack_i_fack, hojd=H, under=under, mellan=mellan, handledare=hl, rundad=rundad, R_hl=R_hl,
                start=start, foljare=fol, underliggare=und, spjalor=sp, stolpe=st)


def ritval(k, info, noter=(), vyer=None, snitt=True):
    """Ritningens standardval: framvy (och planvy med fotplåtarnas hål), snitt A genom en spjäla (blicken mot
    -x), delvy E längs handledaren och detaljerna på blad 2 (sammanstallning.py ritning). Gäller ett räcke
    byggt med standardriktningarna (ex = x)."""
    vyer = vyer or (("fram", "plan") if info["stolpe"]["fot"] == "fotplat" else ("fram",))
    sn = [dict(namn="A", axel="x", varde=info["snitt_x"], mot="-")] if snitt else []
    k.ritning(vyer=list(vyer), snitt=sn, noter=list(noter), detaljer=info["detaljer"], delvyer=[info["delvy"]])


def noter(info, svets=True):
    """Utförandenoter för räcket (höjd, stolpar, handledare, följare, spjälor, svets). Projektets egna rader
    (underlag, plats, ytbehandling) läggs till av konstruktionsskriptet."""
    st, hl = info["stolpe"], info["handledare"]
    bitar = info["bitar"]
    rader = ["RÄCKESHÖJD %g LODRÄTT ÖVER STEGFRAMKANT" % info["hojd"]]
    if st["fot"] == "ingjutning":
        rader.append("STOLPAR st: %s, %g mm NEDGJUTNA I %s (INGÅR I LÄNGDEN), c/c MAX %.0f"
                     % (st["profil"], float(st["djup"]), "KÄRNBORRADE HÅL %s" % st["hal"] if st.get("hal") else "UNDERLAGET", info["stolp_cc"]))
    else:
        rader.append("STOLPAR st: %s PÅ FOTPLÅT fp/1 %s MED 4 %s, c/c MAX %.0f" % (st["profil"], st.get("plat", "PL8*100"), st.get("bult", "M10"), info["stolp_cc"]))
    hlt = "HANDLEDARE %s%s: %s" % (hl["profil"], " (RUNDAD ÖVERSIDA R%.0f)" % info["R_hl"] if info["rundad"] else "",
                                   " + ".join("%s %.0f" % (b["pos"], b["langd"]) for b in bitar))
    if info["start"] == "snacka":
        hlt += ", SMIDD SNÄCKA PÅ %s (UTVECKLAD %.0f)" % (bitar[0]["pos"], snacka_langd())
    rader.append(hlt)
    if len(bitar) > 1:
        rader.append("HANDLEDARENS KNÄCK %s BOCKAS I ETT STYCKE ELLER SVETSAS OCH SLIPAS"
                     % " / ".join("%s %s" % (b["pos"], "PLAN" if abs(b["lutning"]) < 0.05 else "%.1f°" % b["lutning"]) for b in bitar))
    for namn, s in (("FÖLJARE", info["foljare"]), ("UNDERLIGGARE", info["underliggare"])):
        if s:
            rader.append("%s l: %s, %s" % (namn, "2 st %s PÅ HÖGKANT, ETT PÅ VAR SIDA OM SPJÄLORNA" % s["profil"] if s["typ"] == "dubbel"
                                           else "%s LIGGANDE" % s["profil"],
                                           "BOCKAS/GERAS I KNÄCKEN" if info["knack_i_fack"] else "RAKA MELLAN STOLPARNA"))
    if info["spjalor"]:
        cc = max(f["cc"] for f in info["fack"])
        rader.append("SPJÄLOR sp %s, c/c MAX %.0f, FRI ÖPPNING MAX %.0f (< %g)" % (info["spjalor"]["profil"], cc,
                                                                                 max(f["fri"] for f in info["fack"]), info["spjalor"]["fri"]))
    if svets:
        rader.append("SVETS: STOLPAR MOT HANDLEDARE a4%s – DETALJER SE BLAD 2"
                     % (", FÖLJARE MOT STOLPAR OCH SPJÄLOR a3" if info["foljare"] or info["underliggare"] else ", SPJÄLOR a3"))
    return rader
