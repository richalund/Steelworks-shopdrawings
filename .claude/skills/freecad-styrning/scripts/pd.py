"""Part Design-verktyg som körs inne i FreeCAD: kropp (PartDesign::Body), skisser med namngivna mått mot
kalkylbladet Variabler, features (Pad, Pocket, Hole, Revolution, Groove, Fillet, Chamfer, Mirrored,
LinearPattern, PolarPattern), kontroll och bild.

Mått anges som tal (fasta) eller som uttryck mot variablerna: "Bredd", "Bredd/2 - Kantavstand",
"Hojd - 2*Tjocklek". Variabelnamn (alias i Variabler) får automatiskt prefixet "Variabler.", så uttrycket
lever kvar i FreeCAD och följer med när användaren eller `partdesign.py satt` ändrar en variabel. Ett mått som
är bundet till en enda variabel får variabelns namn som måttnamn; namngivna mått sätts ut på ritningen.

Skissplan (FreeCAD 1.0, uppmätt 2026-10-10): XY = skissens x/y är globalt X/Y, normal +Z. XZ = skissens x
är globalt X, y är globalt Z, normal -Y. YZ = skissens x är globalt Y, y är globalt Z, normal +X.
"""
import re, json, math
import FreeCAD as App
import Part, Sketcher
from FreeCAD import Vector as V, Placement, Rotation

C = Sketcher.Constraint
STAL_DENSITET = 7850.0
ROT, H_AXEL, V_AXEL = -1, -1, -2           # skissens origo (geo -1, pos 1), H-axel (-1), V-axel (-2)
START, SLUT, MITT = 1, 2, 3


def _tal(x):
    return isinstance(x, (int, float))


def _num(q):
    return float(getattr(q, "Value", q))


class Del:
    """En Part Design-del: dokument, kalkylbladet Variabler och kroppen."""

    def __init__(self, doc, kropp="Kropp"):
        self.doc = doc
        self.sh = doc.getObject("Variabler")
        self.body = doc.getObject(kropp)
        if self.body is None:
            self.body = doc.addObject("PartDesign::Body", kropp)
        self.alias = set(alias_lista(self.sh)) if self.sh else set()

    # ------------------------------------------------------------ uttryck
    def uttryck(self, v):
        """(uttryck eller None, värde). Tal blir fasta mått, text blir uttryck mot Variabler."""
        if _tal(v):
            return None, float(v)
        s = str(v).strip()
        ex = re.sub(r"(?<![\w.])([A-Za-z_]\w*)(?![\w(.])",
                    lambda m: "Variabler." + m.group(1) if m.group(1) in self.alias else m.group(1), s)
        try:
            val = _num(self.sh.evalExpression(ex))
        except Exception as e:
            raise ValueError("Uttrycket '%s' går inte att räkna: %s" % (s, e))
        return ex, val

    def satt(self, obj, prop, v):
        """Sätt egenskapen `prop` till talet eller uttrycket `v`."""
        ex, val = self.uttryck(v)
        if prop == "Occurrences":                # heltalsegenskap
            val = int(round(val))
        setattr(obj, prop, val)
        if ex:
            obj.setExpression(prop, ex)
        return val

    def kombi(self, mall, *vals):
        """Bygg ett uttryck av flera mått, t.ex. kombi("({0}) - ({1})/2", "Mitt", "Bredd"). Bara tal -> tal."""
        if all(_tal(x) for x in vals):
            return float(eval(mall.format(*["(%r)" % float(x) for x in vals]), {"__builtins__": {}}))
        return mall.format(*vals)

    def _plan(self, plan):
        return next(o for o in self.body.Origin.OriginFeatures if o.Role == plan + "_Plane")

    def axel(self, namn):
        """Kroppens axel X, Y eller Z (för mönster, rotation)."""
        return next(o for o in self.body.Origin.OriginFeatures if o.Role == namn.upper() + "_Axis")

    # ------------------------------------------------------------ skisser och features
    def skiss(self, namn, plan="XY", forskjutning=0, vand=False):
        """Skiss på ett av kroppens origoplan (XY, XZ, YZ), förskjuten längs planets normal. Origoplan i
        stället för ytor: skissen följer med när måtten ändras (inga topologiska namn att tappa)."""
        return Skiss(self, namn, plan, forskjutning, vand)

    def _ny(self, typ, namn):
        self.doc.recompute()                     # skissen måste vara räknad innan featuren kopplas (Hole kräver det)
        f = self.body.newObject(typ, namn)
        if self.body.Tip != f:                   # mönster/spegling blir inte spets av sig själva (FreeCAD 1.0.1)
            self.body.Tip = f
        return f

    def _rakna(self, f):
        self.doc.recompute()
        if "Invalid" in f.State or "Error" in f.State or f.Shape.isNull():
            raise RuntimeError("Featuren %s (%s) gick inte att räkna: %s" % (f.Name, f.TypeId, f.State))
        return f

    def _skar(self, f):
        """Fickor och hål: kontrollera att något skars bort, annars vänd riktningen."""
        fore = f.BaseFeature.Shape.Volume if f.BaseFeature else 0.0
        self._rakna(f)
        if f.Shape.Volume > fore - 1e-6 and not getattr(f, "Midplane", False):
            f.Reversed = not f.Reversed
            self._rakna(f)
            if f.Shape.Volume > fore - 1e-6:
                raise RuntimeError("%s skär inte bort något i någon riktning" % f.Name)
        return f

    def kloss(self, sk, langd, namn="Kloss", symmetrisk=False, omvand=False):
        """Pad: extrudera skissen `langd` längs skissens normal (omvand = andra hållet, symmetrisk = åt båda)."""
        f = self._ny("PartDesign::Pad", namn)
        f.Profile = sk.obj
        self.satt(f, "Length", langd)
        f.Midplane, f.Reversed = symmetrisk, omvand
        return self._rakna(f)

    def ficka(self, sk, djup="genom", namn="Ficka", symmetrisk=None, omvand=False):
        """Pocket. djup = "genom" (genom allt, som standard åt båda hållen) eller ett mått."""
        f = self._ny("PartDesign::Pocket", namn)
        f.Profile = sk.obj
        if djup == "genom":
            f.Type = "ThroughAll"
            f.Midplane = True if symmetrisk is None else symmetrisk
        else:
            f.Type = "Length"
            self.satt(f, "Length", djup)
            f.Midplane = bool(symmetrisk)
        f.Reversed = omvand
        return self._skar(f)

    def hal(self, sk, diameter=None, djup="genom", ganga=None, namn="Hal"):
        """Hole på skissens cirklar. gänga = "M12" ger gängat hål (gängan modelleras inte, hålet får
        borrdiametern). Annars diameter = mått."""
        f = self._ny("PartDesign::Hole", namn)
        f.Profile = sk.obj
        if ganga:
            f.Threaded = True
            f.ThreadType = "ISOMetricProfile"
            f.ThreadSize = ganga
            f.ModelThread = False
        else:
            self.satt(f, "Diameter", diameter)
        if djup == "genom":
            f.DepthType = "ThroughAll"
        else:
            f.DepthType = "Dimension"
            self.satt(f, "Depth", djup)
        f.DrillPoint = "Flat"
        return self._skar(f)

    def varv(self, sk, vinkel=360, axel="V", namn="Varv", spar=False):
        """Revolution (spar=True: Groove) av skissen runt skissens V- eller H-axel, eller kroppens X/Y/Z."""
        f = self._ny("PartDesign::Groove" if spar else "PartDesign::Revolution", namn)
        f.Profile = sk.obj
        f.ReferenceAxis = (sk.obj, [axel + "_Axis"]) if axel in ("V", "H") else (self.axel(axel), [""])
        ex, val = self.uttryck(vinkel)
        f.Angle = val
        if ex:
            f.setExpression("Angle", "(%s) * 1 deg" % ex)
        return self._skar(f) if spar else self._rakna(f)

    def _kantfeature(self, typ, namn, prop, matt, kantval):
        f = self._ny(typ, namn)
        f.addProperty("App::PropertyString", "Kantval", "Parametrar", "Kantval som letas om vid varje ändring (pd.uppdatera)")
        f.Kantval = json.dumps(kantval, ensure_ascii=False)
        self.satt(f, prop, matt)
        kanter = valj_kanter(self, f.BaseFeature.Shape, kantval)
        if not kanter:
            raise RuntimeError("Kantvalet %s hittade inga kanter" % kantval)
        f.Base = (f.BaseFeature, kanter)
        return self._rakna(f)

    def avrunda(self, radie, kantval, namn="Avrundning"):
        """Fillet på kanterna som `kantval` väljer (se valj_kanter)."""
        return self._kantfeature("PartDesign::Fillet", namn, "Radius", radie, kantval)

    def fas(self, storlek, kantval, namn="Fas"):
        """Chamfer (lika ben) på kanterna som `kantval` väljer."""
        return self._kantfeature("PartDesign::Chamfer", namn, "Size", storlek, kantval)

    def spegla(self, features, plan="YZ", namn="Spegling"):
        f = self._ny("PartDesign::Mirrored", namn)
        f.Originals = list(features)
        f.MirrorPlane = (self._plan(plan), [""])
        return self._rakna(f)

    def monster(self, features, riktning="X", langd=100, antal=2, namn="Monster"):
        """LinearPattern: `antal` kopior jämnt fördelade över `langd` (från första till sista)."""
        f = self._ny("PartDesign::LinearPattern", namn)
        f.Originals = list(features)
        f.Direction = (self.axel(riktning), [""])
        self.satt(f, "Length", langd)
        self.satt(f, "Occurrences", antal)
        return self._rakna(f)

    def polart(self, features, axel="Z", vinkel=360, antal=4, namn="Polart"):
        f = self._ny("PartDesign::PolarPattern", namn)
        f.Originals = list(features)
        f.Axis = (self.axel(axel), [""])
        ex, val = self.uttryck(vinkel)
        f.Angle = val
        if ex:
            f.setExpression("Angle", "(%s) * 1 deg" % ex)
        self.satt(f, "Occurrences", antal)
        return self._rakna(f)

    def stada(self):
        """Bara kroppens spets syns; skisser och mellansteg döljs (som när man ritar i GUI:t)."""
        for o in self.body.Group:
            if hasattr(o, "ViewObject") and o.ViewObject is not None:
                o.ViewObject.Visibility = (o == self.body.Tip)
        if self.body.ViewObject is not None:
            self.body.ViewObject.Visibility = True


class Skiss:
    """Skiss med hjälpare som lägger geometri, låser den och sätter namngivna mått mot Variabler."""

    def __init__(self, d, namn, plan, forskjutning, vand):
        self.d = d
        sk = d.body.newObject("Sketcher::SketchObject", namn)
        sk.AttachmentSupport = (d._plan(plan), [""])
        sk.MapMode = "FlatFace"
        sk.MapReversed = bool(vand)
        ex, val = d.uttryck(forskjutning)
        sk.AttachmentOffset = Placement(V(0, 0, val), Rotation())
        if ex:
            sk.setExpression(".AttachmentOffset.Base.z", ex)
        self.obj = sk
        self.namn_anvanda = set()
        d.doc.recompute()

    # ------------------------------------------------------------ grundfunktioner
    def geo(self, g, konstruktion=False):
        return self.obj.addGeometry(g, konstruktion)

    def begr(self, typ, *refs):
        """Geometriskt villkor utan värde, t.ex. begr("Horizontal", 0) eller begr("Coincident", 0, 2, 1, 1)."""
        return self.obj.addConstraint(C(typ, *refs))

    def matt(self, typ, *refs, varde, namn=None):
        """Mått (Distance, DistanceX, DistanceY, Radius, Diameter, Angle) med tal eller uttryck. Vinklar i grader."""
        ex, val = self.d.uttryck(varde)
        if typ == "Angle":
            val = math.radians(val)
        i = self.obj.addConstraint(C(typ, *refs, val))
        if namn is None and isinstance(varde, str) and varde.strip() in self.d.alias:
            namn = varde.strip()
        if ex and not namn:
            namn = "_m%d" % i                     # uttryck kräver namn; "_" = sätts inte ut på ritningen
        if namn:
            n, k = namn, 2
            while n in self.namn_anvanda:
                n, k = "%s_%d" % (namn, k), k + 1
            self.obj.renameConstraint(i, n)
            self.namn_anvanda.add(n)
        if ex:
            self.obj.setExpression("Constraints." + n, "(%s) * 1 deg" % ex if typ == "Angle" else ex)
        return i

    def placera(self, geo, pos, x, y, namn=None):
        """Lås en punkt till (x, y) från skissens origo (tal eller uttryck; 0 = på axeln). Ett läge som är
        en enda variabel får variabelns namn och sätts ut på ritningen; namn="" = sätts inte ut."""
        if _tal(x) and _tal(y) and x == 0 and y == 0:
            return self.begr("Coincident", geo, pos, ROT, 1)
        for v, typ, axel in ((x, "DistanceX", V_AXEL), (y, "DistanceY", H_AXEL)):
            if _tal(v) and v == 0:
                self.begr("PointOnObject", geo, pos, axel)
                continue
            _, val = self.d.uttryck(v)
            if val >= 0:
                self.matt(typ, ROT, 1, geo, pos, varde=v, namn=namn)
            else:                                  # negativt läge: mät från punkten till origo
                self.matt(typ, geo, pos, ROT, 1, varde=-v if _tal(v) else "-(%s)" % v, namn=namn)

    def _v(self, v):
        return self.d.uttryck(v)[1]

    # ------------------------------------------------------------ former
    def rektangel(self, b, h, mitt=(0, 0), horn=None, namn=(None, None)):
        """Rektangel b x h (skissens x och y). mitt=(x, y) eller horn=(x, y) för nedre vänstra hörnet.
        Returnerar geometriindex [nederkant, höger, överkant, vänster]."""
        bv, hv = self._v(b), self._v(h)
        if horn is None:
            x0, y0 = self._v(mitt[0]) - bv / 2, self._v(mitt[1]) - hv / 2
        else:
            x0, y0 = self._v(horn[0]), self._v(horn[1])
        P = [(x0, y0), (x0 + bv, y0), (x0 + bv, y0 + hv), (x0, y0 + hv)]
        g = [self.geo(Part.LineSegment(V(*P[i], 0), V(*P[(i + 1) % 4], 0))) for i in range(4)]
        for i in range(4):
            self.begr("Coincident", g[i], SLUT, g[(i + 1) % 4], START)
        self.begr("Horizontal", g[0]); self.begr("Horizontal", g[2])
        self.begr("Vertical", g[1]); self.begr("Vertical", g[3])
        self.matt("DistanceX", g[0], START, g[0], SLUT, varde=b, namn=namn[0])
        self.matt("DistanceY", g[1], START, g[1], SLUT, varde=h, namn=namn[1])
        if horn is not None:
            self.placera(g[0], START, *horn)
        elif all(_tal(m) and m == 0 for m in mitt):
            self.begr("Symmetric", g[0], START, g[1], SLUT, ROT, 1)
        else:
            self.placera(g[0], START, self.d.kombi("{0} - {1}/2", mitt[0], b), self.d.kombi("{0} - {1}/2", mitt[1], h))
        return g

    def rundad_rektangel(self, b, h, r, mitt=(0, 0), horn=None, namn=(None, None, None)):
        """Rektangel b x h med hörnradien r (tangerande bågar, lika radier). Bågarna i skissen i stället för en
        Fillet-feature: radien följer variabeln utan att kanter behöver letas. Returnerar [linjer..., bågar...]."""
        bv, hv, rv = self._v(b), self._v(h), self._v(r)
        if rv <= 0 or 2 * rv >= min(bv, hv):
            raise ValueError("Hörnradien %g passar inte i %g x %g" % (rv, bv, hv))
        if horn is None:
            x0, y0 = self._v(mitt[0]) - bv / 2, self._v(mitt[1]) - hv / 2
        else:
            x0, y0 = self._v(horn[0]), self._v(horn[1])
        x1, y1 = x0 + bv, y0 + hv
        L = [((x0 + rv, y0), (x1 - rv, y0)), ((x1, y0 + rv), (x1, y1 - rv)),
             ((x1 - rv, y1), (x0 + rv, y1)), ((x0, y1 - rv), (x0, y0 + rv))]
        g = [self.geo(Part.LineSegment(V(*a, 0), V(*b_, 0))) for a, b_ in L]
        A = [((x1 - rv, y0 + rv), 1.5 * math.pi, 2 * math.pi), ((x1 - rv, y1 - rv), 0.0, 0.5 * math.pi),
             ((x0 + rv, y1 - rv), 0.5 * math.pi, math.pi), ((x0 + rv, y0 + rv), math.pi, 1.5 * math.pi)]
        a = [self.geo(Part.ArcOfCircle(Part.Circle(V(*c, 0), V(0, 0, 1), rv), s, e)) for c, s, e in A]
        for i in range(4):                       # linje i -> båge i -> linje i+1
            self.begr("Tangent", g[i], SLUT, a[i], START)
            self.begr("Tangent", a[i], SLUT, g[(i + 1) % 4], START)
        self.begr("Horizontal", g[0]); self.begr("Horizontal", g[2])
        self.begr("Vertical", g[1]); self.begr("Vertical", g[3])
        for i in (1, 2, 3):
            self.begr("Equal", a[0], a[i])
        self.matt("Radius", a[0], varde=r, namn=namn[2])
        self.matt("DistanceX", g[3], START, g[1], START, varde=b, namn=namn[0])
        self.matt("DistanceY", g[0], START, g[2], START, varde=h, namn=namn[1])
        if horn is not None:
            hx, hy = horn
            if _tal(hx) and hx == 0:
                self.begr("PointOnObject", ROT, 1, g[3])
            else:
                self.placera(g[3], START, hx, self.d.kombi("{0} + {1} - {2}", hy, h, r))
                hy = None
            if hy is not None:
                if _tal(hy) and hy == 0:
                    self.begr("PointOnObject", ROT, 1, g[0])
                else:
                    self.matt("DistanceY", ROT, 1, g[0], START, varde=hy, namn="")
        elif all(_tal(m) and m == 0 for m in mitt):
            self.begr("Symmetric", g[3], START, g[1], START, ROT, 1)
        else:
            self.placera(g[3], START, self.d.kombi("{0} - {1}/2", mitt[0], b), self.d.kombi("{0} + {1}/2 - {2}", mitt[1], h, r))
        return g + a

    def stadion(self, b, h, mitt=(0, 0), namn=(None, None)):
        """Stadionform (oval med raka sidor) b x h, stående (h längs y), med halvcirkelbågar i ändarna (radie b/2):
        två lodräta linjer och två bågar som tangerar i ändpunkterna. Två stadier i samma skiss (yttre och inre)
        ger en ring, t.ex. en oval av bockat plattstål. Måtten är bredden och den raka delen (h - b).
        Returnerar [höger, vänster, övre båge, undre båge]."""
        bv, hv = self._v(b), self._v(h)
        if bv <= 0 or hv <= bv:
            raise ValueError("Stadion %g x %g: höjden måste vara större än bredden" % (bv, hv))
        mx, my = self._v(mitt[0]), self._v(mitt[1])
        r, c = bv / 2, hv / 2 - bv / 2
        hoger = self.geo(Part.LineSegment(V(mx + r, my - c, 0), V(mx + r, my + c, 0)))
        vanster = self.geo(Part.LineSegment(V(mx - r, my + c, 0), V(mx - r, my - c, 0)))
        topp = self.geo(Part.ArcOfCircle(Part.Circle(V(mx, my + c, 0), V(0, 0, 1), r), 0.0, math.pi))
        botten = self.geo(Part.ArcOfCircle(Part.Circle(V(mx, my - c, 0), V(0, 0, 1), r), math.pi, 2 * math.pi))
        self.begr("Vertical", hoger)
        self.begr("Vertical", vanster)
        for g1, g2 in ((hoger, topp), (topp, vanster), (vanster, botten), (botten, hoger)):
            self.begr("Tangent", g1, SLUT, g2, START)
        self.matt("DistanceX", vanster, START, hoger, START, varde=b, namn=namn[0])
        self.matt("DistanceY", hoger, START, hoger, SLUT, varde=self.d.kombi("{0} - {1}", h, b), namn=namn[1])
        if all(_tal(m) and m == 0 for m in mitt):
            self.begr("Symmetric", topp, MITT, botten, MITT, ROT, 1)
        else:
            self.placera(botten, MITT, mitt[0], self.d.kombi("{0} - ({1})/2 + ({2})/2", mitt[1], h, b))
        return [hoger, vanster, topp, botten]

    def cirkel(self, d, mitt=(0, 0), namn=None):
        """Cirkel med diametern d och mitten i (x, y). Returnerar geometriindex."""
        c = self.geo(Part.Circle(V(self._v(mitt[0]), self._v(mitt[1]), 0), V(0, 0, 1), self._v(d) / 2))
        self.matt("Diameter", c, varde=d, namn=namn)
        self.placera(c, MITT, *mitt)
        return c

    def ellips(self, langd, bredd, mitt=(0, 0), namn=(None, None)):
        """Ellips med storaxeln `langd` längs x och lillaxeln `bredd` längs y, mitten i (x, y). Axlarna läggs in
        som hjälpgeometri (exposeInternalGeometry) och måttsätts till langd och bredd, så att ellipsen blir
        fullt bestämd. Returnerar geometriindex."""
        a, b = self._v(langd) / 2, self._v(bredd) / 2
        e = self.geo(Part.Ellipse(V(self._v(mitt[0]), self._v(mitt[1]), 0), max(a, b), min(a, b)))
        self.obj.exposeInternalGeometry(e)
        linjer = [i for i in range(e + 1, self.obj.GeometryCount) if self.obj.Geometry[i].TypeId == "Part::GeomLineSegment"]
        stor, lill = sorted(linjer, key=lambda i: -self.obj.Geometry[i].length())[:2]
        self.begr("Horizontal", stor if a >= b else lill)
        self.matt("Distance", stor, varde=langd if a >= b else bredd, namn=namn[0] if a >= b else namn[1])
        self.matt("Distance", lill, varde=bredd if a >= b else langd, namn=namn[1] if a >= b else namn[0])
        self.placera(e, MITT, *mitt)
        return e

    def halbild(self, d, ccx, ccy=0, mitt=(0, 0), namn=(None, None, None)):
        """Hål i rektangulärt mönster ccx x ccy kring mitt (4 hål; ccy = 0 eller ccx = 0 ger 2 hål på rad).
        Lika diametrar och symmetri kring mitten, så att mönstret följer variablerna. Returnerar index."""
        dv, ax, ay = self._v(d), self._v(ccx) / 2, self._v(ccy) / 2
        mx, my = self._v(mitt[0]), self._v(mitt[1])
        if all(_tal(m) and m == 0 for m in mitt):
            cp, cpos = ROT, 1
        else:
            cp = self.geo(Part.Point(V(mx, my, 0)), True)
            cpos = 1
            self.placera(cp, 1, *mitt)
        if ax and ay:
            P = [(-ax, -ay), (ax, -ay), (ax, ay), (-ax, ay)]
        elif ax:
            P = [(-ax, 0), (ax, 0)]
        else:
            P = [(0, -ay), (0, ay)]
        c = [self.geo(Part.Circle(V(mx + x, my + y, 0), V(0, 0, 1), dv / 2)) for x, y in P]
        self.matt("Diameter", c[0], varde=d, namn=namn[0])
        for k in c[1:]:
            self.begr("Equal", c[0], k)
        if len(c) == 4:
            self.begr("Symmetric", c[0], MITT, c[2], MITT, cp, cpos)
            self.begr("Symmetric", c[1], MITT, c[3], MITT, cp, cpos)
            self.begr("Horizontal", c[0], MITT, c[1], MITT)
            self.begr("Vertical", c[1], MITT, c[2], MITT)
            self.matt("DistanceX", c[0], MITT, c[1], MITT, varde=ccx, namn=namn[1])
            self.matt("DistanceY", c[1], MITT, c[2], MITT, varde=ccy, namn=namn[2])
        elif ax:
            self.begr("Symmetric", c[0], MITT, c[1], MITT, cp, cpos)
            self.begr("Horizontal", c[0], MITT, c[1], MITT)
            self.matt("DistanceX", c[0], MITT, c[1], MITT, varde=ccx, namn=namn[1])
        else:
            self.begr("Symmetric", c[0], MITT, c[1], MITT, cp, cpos)
            self.begr("Vertical", c[0], MITT, c[1], MITT)
            self.matt("DistanceY", c[0], MITT, c[1], MITT, varde=ccy, namn=namn[2])
        return c

    def profil(self, punkter, matt=None, start=(0, 0), namn=None):
        """Sluten polygon genom punkterna (skisskoordinater, tal). Axelparallella sidor låses vågrätt/lodrätt,
        sidan i (punkt i -> i+1) får längden matt[i] (tal eller uttryck), första punkten låses i `start`.
        Lägg fler villkor med begr/matt om skissen inte blir fullt bestämd. Returnerar linjeindex."""
        n = len(punkter)
        g = []
        for i in range(n):
            a, b = punkter[i], punkter[(i + 1) % n]
            g.append(self.geo(Part.LineSegment(V(a[0], a[1], 0), V(b[0], b[1], 0))))
        for i in range(n):
            self.begr("Coincident", g[i], SLUT, g[(i + 1) % n], START)
        for i in range(n):
            a, b = punkter[i], punkter[(i + 1) % n]
            if abs(a[1] - b[1]) < 1e-9:
                self.begr("Horizontal", g[i])
            elif abs(a[0] - b[0]) < 1e-9:
                self.begr("Vertical", g[i])
        for i, v in (matt or {}).items():
            self.matt("Distance", g[i], varde=v, namn=(namn or {}).get(i))
        if start is not None:
            self.placera(g[0], START, *start, namn="")
        return g


# ---------------------------------------------------------------- kantval (Fillet/Chamfer)
def valj_kanter(d, shape, kantval):
    """Kanter ("EdgeN") som uppfyller alla nycklar i kantval:
       parallell: "X"/"Y"/"Z"         raka kanter längs axeln
       cirkel: true, radie: mått      cirkulära kanter (valfritt med radie)
       lada: ["x", "zmax", ...]       kanten ligger på kroppens yttre gräns: "x" = xmin eller xmax
       vid: {"y": mått, "z": mått}    kantens mittpunkt har de här koordinaterna
       langd: mått                    kantens längd
    Måtten får vara uttryck mot Variabler. En lista med flera kantval ger unionen. Kantvalet sparas i
    featuren och letas om efter varje ändring."""
    if isinstance(kantval, list):
        ut = []
        for k in kantval:
            ut += [e for e in valj_kanter(d, shape, k) if e not in ut]
        return sorted(ut, key=lambda e: int(e[4:]))
    bb = shape.optimalBoundingBox(False, False)
    lo = dict(x=bb.XMin, y=bb.YMin, z=bb.ZMin)
    hi = dict(x=bb.XMax, y=bb.YMax, z=bb.ZMax)
    tol = 0.01
    axlar = dict(X=V(1, 0, 0), Y=V(0, 1, 0), Z=V(0, 0, 1))
    vid = {k: d.uttryck(v)[1] for k, v in kantval.get("vid", {}).items()}
    radie = d.uttryck(kantval["radie"])[1] if "radie" in kantval else None
    langd = d.uttryck(kantval["langd"])[1] if "langd" in kantval else None
    ut = []
    for i, e in enumerate(shape.Edges, start=1):
        typ = e.Curve.TypeId
        if "parallell" in kantval:
            if typ != "Part::GeomLine" or abs(abs(e.Curve.Direction.dot(axlar[kantval["parallell"].upper()])) - 1) > 1e-6:
                continue
        if kantval.get("cirkel"):
            if typ != "Part::GeomCircle" or (radie is not None and abs(e.Curve.Radius - radie) > tol):
                continue
        if langd is not None and abs(e.Length - langd) > tol:
            continue
        m = e.valueAt((e.FirstParameter + e.LastParameter) / 2)
        bb_e = e.BoundBox
        ok = True
        for villkor in kantval.get("lada", []):
            k, sida = villkor[0], villkor[1:]
            emin, emax = getattr(bb_e, k.upper() + "Min"), getattr(bb_e, k.upper() + "Max")
            pa_min = abs(emin - lo[k]) < tol and abs(emax - lo[k]) < tol
            pa_max = abs(emin - hi[k]) < tol and abs(emax - hi[k]) < tol
            if not ((sida in ("", "min") and pa_min) or (sida in ("", "max") and pa_max)):
                ok = False
        for k, v in vid.items():
            if abs(getattr(m, k) - v) > tol:
                ok = False
        if ok:
            ut.append("Edge%d" % i)
    return ut


# ---------------------------------------------------------------- befintlig fil
def alias_lista(sh):
    """Variablerna i kalkylbladet (alias i kolumn B, rad 2-200), i bladets ordning."""
    ut = []
    for r in range(2, 201):
        a = sh.getAlias("B%d" % r)
        if a:
            ut.append(a)
    return ut


def hitta_kropp(doc):
    kroppar = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    if not kroppar:
        raise RuntimeError("Filen har ingen Part Design-kropp (PartDesign::Body)")
    return kroppar[0]


def uppdatera(doc):
    """Räkna om och leta om kanterna för Fillet/Chamfer med sparat kantval (efter en måttändring)."""
    doc.recompute()
    d = Del(doc, hitta_kropp(doc).Name)
    for f in d.body.Group:
        if hasattr(f, "Kantval") and f.Kantval:
            kanter = valj_kanter(d, f.BaseFeature.Shape, json.loads(f.Kantval))
            if not kanter:
                raise RuntimeError("Kantvalet i %s hittade inga kanter efter ändringen" % f.Name)
            if sorted(kanter) != sorted(f.Base[1]):
                f.Base = (f.BaseFeature, kanter)
            doc.recompute()
    doc.recompute()
    return d


def matt_text(sk, c, i):
    try:
        return sk.getDatum(i).UserString
    except Exception:
        return "%g" % c.Value


def kontroll(doc, logg, densitet=STAL_DENSITET):
    """Logga variabler, skisser (fullt bestämda, namngivna mått), features, låda och massa. Returnerar dict."""
    doc.recompute()
    body = hitta_kropp(doc)
    sh = doc.getObject("Variabler")
    var = {}
    if sh:
        logg("Variabler:")
        for a in alias_lista(sh):
            var[a] = sh.get(a)
            try:
                beskr = sh.get("C" + sh.getCellFromAlias(a)[1:])
            except Exception:
                beskr = ""
            logg("    %-14s %-8s %s" % (a, sh.get(a), beskr))
    skisser = []
    for o in body.Group:
        if o.TypeId != "Sketcher::SketchObject":
            continue
        o.solve()
        namngivna = ["%s %s" % (c.Name, matt_text(o, c, i)) for i, c in enumerate(o.Constraints) if c.Name]
        fb = bool(o.FullyConstrained)
        skisser.append(dict(namn=o.Name, fullt_bestamd=fb))
        logg("Skiss %-12s fullt bestämd=%s%s  %s" % (o.Name, fb, "" if fb else "  <-- OBS", ", ".join(namngivna)))
    fel = []
    logg("Features:")
    for o in body.Group:
        if o.TypeId.startswith("PartDesign::") and o.TypeId not in ("PartDesign::Body",):
            st = "fel: %s" % o.State if ("Invalid" in o.State or "Error" in o.State) else "ok"
            if st != "ok":
                fel.append(o.Name)
            logg("    %-14s %-26s %s%s" % (o.Name, o.TypeId, st, "  (spets)" if o == body.Tip else ""))
    if fel:
        raise RuntimeError("Features med fel efter omräkning: %s" % fel)
    s = body.Shape
    bb = s.optimalBoundingBox(False, False)
    massa = s.Volume * 1e-9 * densitet
    logg("Kropp %s: giltig=%s, %d solid(er)" % (body.Name, s.isValid(), len(s.Solids)))
    logg("Låda mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f  (%.1f x %.1f x %.1f)" % (
        bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax, bb.XLength, bb.YLength, bb.ZLength))
    logg("Massa: %.3f kg (%g kg/m3)   volym %.1f cm3" % (massa, densitet, s.Volume / 1000.0))
    ej = [k["namn"] for k in skisser if not k["fullt_bestamd"]]
    if ej:
        logg("OBS: skisser som inte är fullt bestämda: %s" % ", ".join(ej))
    return dict(variabler=var, lada=(bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax), massa=massa,
                volym_cm3=s.Volume / 1000.0, solider=len(s.Solids), giltig=s.isValid(), skisser=skisser,
                ej_bestamda=ej)


def bild(doc, obj, fil, pump):
    """Isometrisk PNG med bara `obj` synlig (kräver GUI)."""
    import FreeCADGui as Gui
    gd = Gui.getDocument(doc.Name)
    for o in doc.Objects:
        if hasattr(o, "ViewObject") and o.ViewObject is not None and o.TypeId.startswith(("Part", "Sketcher::")):
            o.ViewObject.Visibility = False
    obj.ViewObject.Visibility = True
    if obj.TypeId == "PartDesign::Body" and obj.Tip is not None:
        obj.Tip.ViewObject.Visibility = True
    try:
        obj.ViewObject.ShapeColor = (0.62, 0.64, 0.67)
    except Exception:
        pass
    pump(0.3)
    vy = gd.ActiveView
    vy.viewIsometric()
    vy.fitAll()
    pump(0.3)
    vy.saveImage(fil, 1600, 1200, "White")
