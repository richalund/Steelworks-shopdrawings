"""Räcken: ram (stolpar, underliggare, överliggare, handledare), utfyllnad och infästning för plana räcken och
trappräcken (lutning), med kontroll av höjd och öppningar. Används från ett konstruktionsskript, se
../konstruktioner/racke.py:

    import racke
    def bygg(k, v):
        r = racke.Racke(k, v["Langd"], v["Hojd"], lutning=v["Lutning"], stolpdelning=v["Stolpdelning"])
        r.ram(stolpe="PL12*50", handledare="PL8*50", underliggare="PL8*40", golvspalt=v["Golvspalt"],
              montage="golv")                      # "golv" (fotplåt), "sida" (sidoplåt mot vang/kant), "ingen"
        r.fyll(racke.Spjalor("PL8*25"))            # eller Ovaler(...), Sprang(...), Skiva(...)
        k.ritning(**r.ritning(RITNING, typ="trappa"))

Koordinater: X längs räcket (0 = första stolpens yttersida), Z uppåt, Y djup (räckets mittplan y = 0).
Golvlinjen är z = x * tan(lutning): golvet för ett plant räcke, linjen genom stegnosarna för ett trappräcke.
Höjden mäts lodrätt från golvlinjen till handledarens ovansida.

Plattstål "PLt*b" har tjockleken i räckets plan och bredden i djupled: en stolpe PL12*50 står med 50 i djupled,
en liggare eller handledare PL8*50 ligger plant. "PLt*b:plan" vänder den (bredden i planet: liggare på högkant,
spjäla med bredsidan framåt, ovalens band).

Varje stång är en egen Part Design-kropp. Plattstål (PL) ritas som en fyrhörning i räckets plan (skiss med
låsta hörn) padad i djupled, så att snedkapade ändar mot lutande liggare blir exakta utan booleska operationer.
Rör, VKR och rundstång byggs med k.balk och snedkapas med k.gera. Lägena är tal: ändras ett mått i Variabler,
bygg om (`sammanstallning.py bygg ... --var Langd=3000`).

Öppningskontrollen rastrerar räckets plan (5 mm) och mäter största cirkel som går fri från alla delar och
golvlinjen (BBR-kulan), plus spalten mellan golvlinjen och närmaste del. Gränsvärdena står i KRAV nedan.
"""
import math

# Gränsvärden (allmänna råd i BBR 8:2321-8:2322, BFS 2011:6 t.o.m. BFS 2020:4). Nya byggregler gäller från
# 2025-07-01 (de gamla fick väljas t.o.m. 2026-06-30) - stäm av mot gällande regler innan ritningen lämnas ut.
KRAV = dict(
    oppning=100.0,              # mm, största fria öppning (kula)
    golvspalt_trappa=50.0,      # mm, räckets underkant - stegnos i trapplopp
    golvspalt_plan=100.0,       # mm, räckets underkant - golv/trapplan
    hojd=dict(trappa=900.0, plan=900.0, balkong=1100.0, loftgang=1100.0, fallhojd=1100.0),
    klattring=800.0,            # mm, inga klätterbara liggare under denna höjd
)
KALLA_KRAV = "BBR 8:2321-8:2322 (BFS 2011:6 T.O.M. 2020:4) - STÄM AV MOT GÄLLANDE BYGGREGLER"

XZ = ((1, 0, 0), (0, 0, 1), (0, -1, 0))        # kroppens x, y, z för en skiss i räckets plan padad i djupled


def tolka(profil):
    """(typ, mått i planet, djup) för en profil. PL t*b: tjockleken i planet och bredden i djupled som standard
    (som en stående räckesstolpe 12x50); "PL25*8:plan" vänder den (bredden i planet)."""
    import stal
    p, _, vrid = profil.partition(":")
    info = stal.tolka(p, kallor=False)
    t = info["typ"]
    if t == "PL":
        return ("PL", info["b"], info["t"]) if vrid == "plan" else ("PL", info["t"], info["b"])
    if t == "R":
        return "R", info["b"], info["h"]
    if t in ("D", "O"):
        return t, info["d"], info["d"]
    raise ValueError("Räckesprofil %s stöds inte (PL, VKR/RHS, D, RÖR)" % profil)


def _skarning(p, d, q, e):
    """Skärningspunkten mellan linjerna p + s d och q + u e (2D)."""
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-12:
        raise ValueError("parallella linjer")
    s = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (p[0] + s * d[0], p[1] + s * d[1])


class Linje:
    """Lutande linje i räckets plan: z = z0 + t x (t = tan(lutning))."""
    def __init__(self, z0, t):
        self.z0, self.t = z0, t

    def z(self, x):
        return self.z0 + self.t * x

    def upp(self, dz):
        return Linje(self.z0 + dz, self.t)

    def punkt(self, x):
        return (x, self.z(x))

    @property
    def riktning(self):
        n = math.hypot(1, self.t)
        return (1 / n, self.t / n)


class Racke:
    def __init__(self, k, langd, hojd, lutning=0.0, stolpdelning=1200.0, material="S235JR"):
        self.k, self.L, self.H = k, float(langd), float(hojd)
        self.a = math.radians(lutning)
        self.t = math.tan(self.a)
        self.golv = Linje(0.0, self.t)
        self.stolpdelning, self.material = float(stolpdelning), material
        self.former = []                  # (typ, data) i XZ för öppningskontrollen
        self.stolpar, self.fack = [], []
        self.lutning = float(lutning)
        self.noter = []
        self.montering = "ingen"
        self.numrering = {}               # prefix -> [geometrinycklar]: lika delar får samma positionsnummer

    def pos(self, prefix, nyckel):
        """Positionsnummer som i Tekla: "sp" + geometrin -> "sp/1", "sp/2" ... (samma geometri = samma nummer).
        Ett färdigt nummer ("sp/7") används som det är."""
        if "/" in prefix:
            return prefix
        lst = self.numrering.setdefault(prefix, [])
        if nyckel not in lst:
            lst.append(nyckel)
        return "%s/%d" % (prefix, lst.index(nyckel) + 1)

    # ------------------------------------------------------------------ byggstenar
    def stang(self, pos, profil, a, b, kap_a=None, kap_b=None, material=None, huvuddel=False):
        """Rak stång från a till b (punkter (x, z) i räckets plan, mittlinjen). kap_a/kap_b = riktningen (dx, dz)
        för ändens kapplan (lodrätt (0, 1), längs en lutande liggare osv.); None = vinkelrätt mot stången.
        Returnerar kroppen."""
        typ, w, djup = tolka(profil)
        mat = material or self.material
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz)
        u = (dx / L, dz / L)
        n = (-u[1], u[0])
        ka = kap_a or n
        kb = kap_b or n
        sidor = []
        for sg in (-1, 1):
            p = (a[0] + sg * n[0] * w / 2, a[1] + sg * n[1] * w / 2)
            sidor.append((_skarning(p, u, a, ka), _skarning(p, u, b, kb)))
        pts = [sidor[0][0], sidor[0][1], sidor[1][1], sidor[1][0]]
        self.former.append(("poly", pts))
        nyckel = (profil, tuple(sorted(round(math.dist(pts[i], pts[(i + 1) % 4])) for i in range(4))))
        pos = self.pos(pos, nyckel)
        if typ == "PL":
            langd = max(math.dist(*sidor[0]), math.dist(*sidor[1]))
            return self.k.egen(pos, profil.split(":")[0], lambda d: _polygon(d, pts, djup), mitt=(0, djup / 2, 0), rot=XZ,
                               material=mat, huvuddel=huvuddel, langd=round(langd, 1))
        # rör, VKR, rundstång: k.balk förlängd förbi kapplanen, sedan k.gera
        def forl(k_):
            c = abs(u[0] * k_[0] + u[1] * k_[1]) / math.hypot(*k_)
            s_ = math.sqrt(max(1 - c * c, 1e-9))
            return 0.0 if c < 1e-6 else w / 2 * c / s_ + 2
        ea, eb = forl(ka), forl(kb)
        A = (a[0] - u[0] * ea, 0, a[1] - u[1] * ea)
        B = (b[0] + u[0] * eb, 0, b[1] + u[1] * eb)
        o = self.k.balk(pos, profil.split(":")[0], A, B, upp=(0, 1, 0), material=mat, huvuddel=huvuddel)
        for p, k_, e in ((a, ka, ea), (b, kb, eb)):
            if e > 0:
                kn = math.hypot(*k_)
                self.k.gera(o, (p[0] - 40 * k_[0] / kn, 0, p[1] - 40 * k_[1] / kn), (p[0] + 40 * k_[0] / kn, 0, p[1] + 40 * k_[1] / kn))
        return o

    def oval(self, pos, profil, mitt, b, h, material=None):
        """Oval (stadionform) av bockat plattstål, stående, yttermått b x h, mitten i (x, z)."""
        typ, w, djup = tolka(profil if ":" in profil else profil + ":plan")
        if typ != "PL":
            raise ValueError("Ovaler görs av plattstål (PL)")
        utv = round(2 * (h - b) + math.pi * (b - w), 1)

        def bygg(d):
            sk = d.skiss("Oval", "XY")
            sk.stadion(b, h, namn=("Bredd", "_rak"))
            sk.stadion(b - 2 * w, h - 2 * w, namn=("Innerbredd", "_rak_i"))
            d.kloss(sk, djup, "Djup")
        pos = self.pos(pos, ("oval", b, h, profil))
        o = self.k.egen(pos, "OVAL %gx%g %s" % (b, h, profil.split(":")[0]), bygg, mitt=(mitt[0], djup / 2, mitt[1]), rot=XZ,
                        material=material or self.material, langd=utv)
        self.former.append(("ring", (mitt[0], mitt[1], b, h, w)))
        return o

    # ------------------------------------------------------------------ ram
    def ram(self, stolpe="PL12*50", handledare="PL8*50", underliggare="PL8*40", overliggare=None, golvspalt=50.0,
            montage="golv", plat="PL10*100", bult="M10", sida_ned=150.0):
        """Stolpar på jämn delning (högst `stolpdelning`), handledare överst över hela längden, underliggare
        `golvspalt` över golvlinjen mellan stolparna och eventuell överliggare under handledaren.
        Infästning per stolpe: "golv" = kvadratisk fotplåt `plat` med 4 hål (stolpen står på plåten, golvlinjen =
        golvet), "sida" = sidoplåt mot trappvang/bjälklagskant (stolpen förlängs `sida_ned` under golvlinjen,
        plåten får 2 hål), "ingen"."""
        import stal
        self.p_stolpe, self.montering = stolpe, montage
        self.golvspalt = float(golvspalt)
        _, ws, djup_s = tolka(stolpe)
        _, hh, _ = tolka(handledare)
        _, hu, _ = tolka(underliggare)
        lod = 1 / math.cos(self.a)                    # en lutande liggare är tjockare i lodled än i profilen
        self.ws, self.hh, self.hu = ws, hh * lod, hu * lod
        hh, hu = hh * lod, hu * lod
        pinfo = stal.tolka(plat, kallor=False)
        tp, bp = pinfo["t"], pinfo["b"]
        n = max(2, math.ceil((self.L - ws) / self.stolpdelning) + 1)
        xs = [ws / 2 + i * (self.L - ws) / (n - 1) for i in range(n)]
        self.stolpar = xs
        hl_uk = self.hl_uk = self.golv.upp(self.H - hh)                 # handledarens underkant
        lodratt, lang, vagratt = (0.0, 1.0), self.golv.riktning, (1.0, 0.0)
        for x in xs:
            z = self.golv.z(x)
            botten = z + tp if montage == "golv" else z - sida_ned if montage == "sida" else z
            self.stang("st", stolpe, (x, botten), (x, hl_uk.z(x)), kap_a=vagratt, kap_b=lang)
            if montage == "golv":
                fot = self.k.plat("pl/1", plat, mitt=(x, 0, z + tp / 2), langd=bp, lriktning=(1, 0, 0), briktning=(0, 1, 0),
                                  material=self.material)
                c = bp / 2 - 25
                self.k.hal([fot], [(x + sx, sy, z + tp / 2) for sx in (-c, c) for sy in (-c, c)], riktning=(0, 0, 1), bult=bult)
            elif montage == "sida":
                yp = -(djup_s / 2 + tp / 2)
                sp = self.k.plat("pl/1", plat, mitt=(x, yp, z - sida_ned / 2 + 25), langd=sida_ned + 50, lriktning=(0, 0, 1),
                                 briktning=(1, 0, 0), material=self.material)
                self.k.hal([sp], [(x, yp, z - sida_ned + 30), (x, yp, z - 30)], riktning=(0, 1, 0), bult=bult)
            elif montage != "ingen":
                raise ValueError("Okänd montering %s (golv, sida, ingen)" % montage)
        if montage != "ingen":
            self.noter.append("INFÄSTNING: %s %s MED %d st %s PER STOLPE – KONTROLLERAS MOT UNDERLAGET" % (
                "FOTPLÅT" if montage == "golv" else "SIDOPLÅT", plat, 4 if montage == "golv" else 2, bult))
        # handledare: hela längden, lodrätt kapad i ändarna (i liv med stolparnas yttersidor)
        mitt = self.golv.upp(self.H - hh / 2)
        self.stang("h", handledare, mitt.punkt(0.0), mitt.punkt(self.L), kap_a=lodratt, kap_b=lodratt, huvuddel=True)
        ul = self.golv.upp(self.golvspalt + hu / 2)
        topp = hl_uk
        if overliggare:
            _, ho, _ = tolka(overliggare)
            ho *= lod
            topp = hl_uk.upp(-ho)
        self.fyll_uk, self.fyll_ok = self.golv.upp(self.golvspalt + hu), topp
        for xa, xb in zip(xs, xs[1:]):
            a, b = xa + ws / 2, xb - ws / 2
            self.fack.append((a, b))
            self.stang("l", underliggare, ul.punkt(a), ul.punkt(b), kap_a=lodratt, kap_b=lodratt)
            if overliggare:
                ol = hl_uk.upp(-ho / 2)
                self.stang("l", overliggare, ol.punkt(a), ol.punkt(b), kap_a=lodratt, kap_b=lodratt)
        self.k.logg("Räcke: %d stolpar c/c %.0f, %d fack, lutning %g°, höjd %g, montage %s" % (
            n, (self.L - ws) / (n - 1), len(self.fack), self.lutning, self.H, montage))

    def fyll(self, monster):
        """Fyll varje fack med ett utfyllnadsmönster (Spjalor, Ovaler, Sprang, Skiva)."""
        self.monster = monster
        for i, (a, b) in enumerate(self.fack):
            monster.bygg(self, a, b, self.fyll_uk, self.fyll_ok, i)

    # ------------------------------------------------------------------ kontroll och ritning
    def kontroll(self, typ="plan"):
        """Höjd, största fria öppning och golvspalt mot KRAV. Returnerar noter (versaler) och skriver loggrader."""
        import numpy as np
        steg = 5.0
        xs = np.arange(steg / 2, self.L, steg)
        zmax = self.H + abs(self.t) * self.L
        zs = np.arange(-abs(self.t) * self.L, zmax, steg)
        X, Z = np.meshgrid(xs, zs)
        golv = self.golv.z(X)
        inne = (Z > golv) & (Z < self.hl_uk.z(X))
        D = np.where(inne, Z - golv, np.nan)                     # avstånd till golvlinjen (lodrätt, på säkra sidan)
        D = D * math.cos(self.a)
        for typ_, data in self.former:
            if typ_ == "poly":
                D = np.fmin(D, _dist_poly(X, Z, data))
            else:
                D = np.fmin(D, _dist_ring(X, Z, *data))
        D = np.where(inne, D, np.nan)
        kula = 2 * float(np.nanmax(D)) if np.any(inne) else 0.0
        i = np.unravel_index(np.nanargmax(D), D.shape)
        var = (float(X[i]), float(Z[i] - golv[i]))
        spalt = self.golvspalt
        krav_spalt = KRAV["golvspalt_trappa"] if typ == "trappa" else KRAV["golvspalt_plan"]
        krav_h = KRAV["hojd"].get(typ, KRAV["hojd"]["plan"])
        rader, ok = [], True
        if self.H < krav_h:
            ok = False
            rader.append("HÖJD %g < %g (%s)" % (self.H, krav_h, typ.upper()))
        if kula > KRAV["oppning"]:
            ok = False
            rader.append("FRI ÖPPNING Ø%.0f > %g VID x=%.0f, %.0f ÖVER GOLVLINJEN" % (kula, KRAV["oppning"], var[0], var[1]))
        if spalt > krav_spalt:
            ok = False
            rader.append("SPALT VID GOLV %g > %g" % (spalt, krav_spalt))
        status = "UPPFYLLER" if ok else "AVVIKER:"
        not_ = "KONTROLL (%s): HÖJD %g, STÖRSTA FRIA ÖPPNING Ø%.0f, SPALT VID GOLV %g – %s %s" % (
            typ.upper(), self.H, kula, spalt, status, "; ".join(rader) if rader else "KRAVEN")
        self.k.logg("Räckeskontroll: höjd %g (krav %g), största fria öppning Ø%.0f (krav %g) vid x=%.0f z=%.0f över golvlinjen, "
             "golvspalt %g (krav %g): %s" % (self.H, krav_h, kula, KRAV["oppning"], var[0], var[1], spalt, krav_spalt,
                                             "OK" if ok else "AVVIKER"))
        return [not_, "GRÄNSVÄRDEN: " + KALLA_KRAV], ok

    def ritning(self, ritning, typ="plan"):
        """RITNING-dict med räckets noter (montering, kontroll) tillagda. Snitt läggs genom första facket om
        inget snitt är angivet."""
        r = dict(ritning)
        kn, _ = self.kontroll(typ)
        r["noter"] = list(r.get("noter", [])) + self.noter + kn
        if not r.get("snitt") and self.fack:
            a, b = self.fack[0]
            r["snitt"] = [dict(namn="A", axel="x", varde=round(self.monster.snittlage(a, b), 1) if hasattr(self, "monster") else round((a + b) / 2, 1), mot="-")]
        return r


def _polygon(d, pts, djup):
    """Sluten polygon (punkter i räckets plan, globala x/z) på kroppens XY-skiss med låsta hörn, padad `djup`."""
    import Part
    import pd
    from FreeCAD import Vector as V
    sk = d.skiss("Tvarsnitt", "XY")
    g = [sk.geo(Part.LineSegment(V(*pts[i], 0), V(*pts[(i + 1) % len(pts)], 0))) for i in range(len(pts))]
    for i in range(len(g)):
        sk.begr("Coincident", g[i], pd.SLUT, g[(i + 1) % len(g)], pd.START)
        sk.placera(g[i], pd.START, round(pts[i][0], 4), round(pts[i][1], 4), namn="")
    d.kloss(sk, djup, "Djup")


def _dist_poly(X, Z, pts):
    """Avstånd från punkterna till en konvex polygon (0 inuti)."""
    import numpy as np
    D = np.full(X.shape, np.inf)
    inne = np.ones(X.shape, bool)
    n = len(pts)
    yta = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1 if yta > 0 else -1
    for i in range(n):
        (x1, z1), (x2, z2) = pts[i], pts[(i + 1) % n]
        ex, ez = x2 - x1, z2 - z1
        L2 = ex * ex + ez * ez or 1e-12
        s = np.clip(((X - x1) * ex + (Z - z1) * ez) / L2, 0, 1)
        D = np.fmin(D, np.hypot(X - x1 - s * ex, Z - z1 - s * ez))
        inne &= sgn * (ex * (Z - z1) - ez * (X - x1)) >= 0
    return np.where(inne, 0.0, D)


def _dist_ring(X, Z, cx, cz, b, h, w):
    """Avstånd till en stadionring (yttre b x h, bandbredd w)."""
    import numpy as np

    def sd(bb, hh):                                         # signerat avstånd till stadion bb x hh
        r, c = bb / 2, hh / 2 - bb / 2
        dz = np.clip(Z - cz, -c, c)
        return np.hypot(X - cx, Z - cz - dz) - r
    yt, inn = sd(b, h), sd(b - 2 * w, h - 2 * w)
    return np.maximum(np.maximum(yt, -inn), 0.0)


# ---------------------------------------------------------------------- utfyllnadsmönster
class Spjalor:
    """Lodräta spjälor jämnt fördelade i facket så att den fria öppningen blir högst `max_oppning`. Snedkapade mot
    lutande liggare i trappräcken."""
    def __init__(self, profil="PL8*25", max_oppning=95.0, pos="sp"):
        self.profil, self.max_oppning, self.pos = profil, max_oppning, pos

    def lagen(self, a, b):
        _, w, _ = tolka(self.profil)
        n = max(1, math.ceil((b - a - self.max_oppning) / (w + self.max_oppning)))
        g = (b - a - n * w) / (n + 1)
        return [a + g * (i + 1) + w * (i + 0.5) for i in range(n)]

    def snittlage(self, a, b):
        return self.lagen(a, b)[0]

    def bygg(self, r, a, b, uk, ok, i):
        lang = r.golv.riktning
        for x in self.lagen(a, b):
            r.stang(self.pos, self.profil, uk.punkt(x), ok.punkt(x), kap_a=lang, kap_b=lang)


class Ovaler:
    """Stående ovaler av bockat plattstål på lika delning, hängda i överliggaren/handledaren med en spjäla och
    stöttade mot underliggaren, med korta liggare mellan ovalerna och mot stolparna i höjderna `liggare`
    (andel av fackets höjd nerifrån). Bara plana räcken."""
    def __init__(self, b=130.0, h=None, profil="PL10*20:plan", delning=187.0, topp=100.0, botten=100.0, liggare=(0.27, 0.73)):
        self.b, self.h, self.profil, self.delning = b, h, profil, delning
        self.topp, self.botten, self.liggare = topp, botten, liggare

    def lagen(self, a, b):
        n = max(1, int((b - a - self.b) // self.delning) + 1)
        x0 = (a + b) / 2 - (n - 1) * self.delning / 2
        return [x0 + i * self.delning for i in range(n)]

    def snittlage(self, a, b):
        return self.lagen(a, b)[0]

    def bygg(self, r, a, b, uk, ok, i):
        if abs(r.t) > 1e-9:
            raise ValueError("Ovaler stöds bara i plana räcken (lutning 0)")
        z0, z1 = uk.z(0), ok.z(0)
        h = self.h or (z1 - z0 - self.topp - self.botten)
        zt = z1 - self.topp
        zb = zt - h
        if zb < z0 + 10:
            raise ValueError("Ovalen %g ryms inte i facket (%g)" % (h, z1 - z0))
        p = self.profil if ":" in self.profil else self.profil + ":plan"
        xs = self.lagen(a, b)
        for x in xs:
            r.oval("o", p, (x, (zt + zb) / 2), self.b, h)
            r.stang("sp", p, (x, zt), (x, z1))
            r.stang("sp", p, (x, z0), (x, zb))
        kanter = [a] + [e for x in xs for e in (x - self.b / 2, x + self.b / 2)] + [b]
        rak0, rak1 = zb + self.b / 2, zt - self.b / 2
        for xa, xb in zip(kanter[0::2], kanter[1::2]):
            if xb - xa < 1:
                continue
            for f in self.liggare:
                z = z0 + f * (z1 - z0)
                if rak0 <= z <= rak1:
                    r.stang("sp", p, (xa, z), (xb, z), kap_a=(0, 1), kap_b=(0, 1))


class Sprang:
    """Lodräta stänger med förskjutna rektangulära språng (som en modern smidesgrind): varje stång går ner från
    överkant, gör ett vågrätt språng `forskjutning` åt sidan på en höjd ur `monster` och fortsätter ner. Mönstret
    är en lista per stång med (höjdandel, riktning +1/-1) eller None för rak stång. Grannstänger får inte springa
    mot varandra (krock) eller isär (öppning 2 x delning): efter +1 kommer +1 eller rak, före -1 kommer -1 eller
    rak, och efter -1 kommer rak - annars ValueError. Delningen väljs så att öppningarna håller sig under max."""
    STANDARD = [None, (0.75, 1), (0.55, 1), None, (0.30, -1), (0.50, -1), None, (0.65, 1), None, (0.40, -1)]

    def __init__(self, profil="PL10*10:plan", delning=None, forskjutning=None, monster=None, max_oppning=95.0):
        self.profil, self.delning, self.forskjutning = profil, delning, forskjutning
        self.monster = monster or self.STANDARD
        self.max_oppning = max_oppning

    def lagen(self, a, b):
        _, w, _ = tolka(self.profil)
        d = self.delning or (self.max_oppning + w) * 0.62      # sprången öppnar luckor: tätare än raka spjälor
        n = max(1, int((b - a - w) // d))
        g = (b - a) / (n + 1)
        return [a + g * (i + 1) for i in range(n)], g

    def snittlage(self, a, b):
        return self.lagen(a, b)[0][0]

    def bygg(self, r, a, b, uk, ok, i):
        _, w, _ = tolka(self.profil)
        xs, g = self.lagen(a, b)
        f_ = self.forskjutning or g / 2
        lang = r.golv.riktning
        seq = [self.monster[(j + i * len(xs)) % len(self.monster)] for j in range(len(xs))]
        for j, (m1, m2) in enumerate(zip(seq, seq[1:])):
            s1, s2 = (m1 or (0, 0))[1], (m2 or (0, 0))[1]
            if s1 > 0 and s2 < 0:
                raise ValueError("Språng: stång %d och %d springer mot varandra (krock)" % (j + 1, j + 2))
            if s1 < 0 and s2 > 0:
                raise ValueError("Språng: stång %d och %d springer isär (öppning 2 x delning)" % (j + 1, j + 2))
        for j, x in enumerate(xs):
            m = seq[j]
            if m is None:
                r.stang("sp", self.profil, uk.punkt(x), ok.punkt(x), kap_a=lang, kap_b=lang)
                continue
            andel, sida = m
            x2 = x + sida * f_
            if not a + w < x2 < b - w:
                x2 = x - sida * f_
            zj = uk.z(x2) + andel * (ok.z(x) - uk.z(x2))
            r.stang("sp", self.profil, (x, zj + w / 2), ok.punkt(x), kap_a=(1, 0), kap_b=lang)
            lo, hi = min(x, x2) - w / 2, max(x, x2) + w / 2
            r.stang("sp", self.profil, (lo, zj), (hi, zj), kap_a=(0, 1), kap_b=(0, 1))
            r.stang("sp", self.profil, uk.punkt(x2), (x2, zj - w / 2), kap_a=lang, kap_b=(1, 0))


class Skiva:
    """En skiva per fack (glas, perforerad plåt, nät i ram) med spel mot stolpar och liggare. Glaset hålls av
    klämmor eller list som inte ritas (not)."""
    def __init__(self, t=10.0, material="Glas härdat laminerat", profil=None, spel=10.0):
        self.t, self.material, self.spel = t, material, spel
        self.profil = profil or "GLAS %g" % t

    def snittlage(self, a, b):
        return (a + b) / 2

    def bygg(self, r, a, b, uk, ok, i):
        s = self.spel
        pts = [(a + s, uk.z(a + s) + s), (b - s, uk.z(b - s) + s), (b - s, ok.z(b - s) - s), (a + s, ok.z(a + s) - s)]
        t = self.t
        r.k.egen(r.pos("gl", (round(b - a), round(pts[3][1] - pts[0][1]), round(pts[2][1] - pts[1][1]))), self.profil, lambda d: _polygon(d, pts, t), mitt=(0, t / 2, 0), rot=XZ, material=self.material)
        r.former.append(("poly", pts))
        if i == 0:
            r.noter.append("%s HÅLLS MED KLÄMMOR/LIST ENL. LEVERANTÖR, EJ RITADE" % self.profil)
