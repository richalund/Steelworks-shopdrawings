"""Sammanställningsritning för stålkonstruktioner i Tekla-stil (svenska smidesritningar) (A2 liggande).

  python sammanstallning.py bygg <konstruktion.py> <ut.FCStd> [--var Langd=2400] [--png] [--step]
  python sammanstallning.py ritning <modell.FCStd> --uppdrag 2026-001 --objekt "KV EXEMPEL 1" "Byggbolaget AB" "Exempelgatan 1, Stockholm"
        [--foretag "Firma AB" --adress "Gatan 1" "123 45 Staden" "firma.se 08-123 45 67"] [--ritad-av AB --handlaggare AB --ansvarig "A. Bson"]
        [--bet A --rev "A|Bultad anslutning ram–väggfäste|2026-10-07|AB"] [--stomnat A-B/2] [--not "..."]
        [--snitt A:x=300:- ...] [--skala 10] [--skala-snitt 10] [--hal 22] [--svets 3.0] [--ut <mapp>]

Företag, adress, signaturer och logga i titelblocket tas från foretag.json (scripts/foretag.py satt ...) eller
miljövariablerna FC_FORETAG, FC_ADRESS (rader åtskilda med |), FC_RITAD_AV, FC_HANDLAGGARE, FC_ANSVARIG och
FC_LOGGA om de inte ges på kommandoraden.

`bygg` kör ett konstruktionsskript (se ../konstruktioner/ och stal.py) och sparar modellen: delar med
positionsnummer (Pos), profil, material och längd, hålgrupper och ritningens standardval.

`ritning` lägger ett A2-blad (mallar/A2_tekla.svg) i modellens .FCStd:
  - framvy och planvy (E-metoden) till vänster, snitten A-A, B-B ... till höger med egen skala, isometri nere
    till höger;
  - positionsbubblor (pl/3, b/1 ...) - varje positionsnummer en gång, i den vy där delen syns bäst
    (huvuddelen som "B/1 b/1 UPE140");
  - hålangivelser 4*Ø14 - M12x44 i vyer där hålen syns som cirklar;
  - måttkedjor till hål och hålgruppernas mitt, totalmått;
  - materiallista (STYCKLIT. | PROFIL | MATERIAL | ANT. | LÄNGD | AREA/st | VIKT/st, sorterad på vikt, TOTALT)
    med rutan ALLMÄNNA NOTERINGAR, noter i versaler nere till vänster och titelblocket ifyllt.
Exporterar <modell>.pdf, <modell>.png och <modell>_materiallista.csv.

Snitt: NAMN:AXEL=VÄRDE[:+|-], t.ex. A:x=300:- = snittplanet x = 300, blicken mot -x (materialet på
x < 300 visas). Standard: konstruktionsskriptets RITNING["snitt"].
"""
import os, sys, math, json, time, argparse

SKALOR = [1, 2, 5, 10, 15, 20, 25, 30, 50, 75, 100]
FONT = "Arial Narrow"
SVART = (0.0, 0.0, 0.0)
FORST, STEG = 8.0, 7.0            # första måttnivån från vyn och avståndet mellan nivåer (mm på papperet)
BUBBEL = 14.0                     # band under vyn för positionsbubblor
HALRAD = 10.0                     # band ovanför måtten för hålangivelser
SNITTMARK = 6.0                   # extra avstånd till mått och bubblor i en vy med snittlinjer (bokstäverna)
VYDEF = {"fram": ("Framvy", (0, -1, 0), (1, 0, 0)), "plan": ("Planvy", (0, 0, 1), (1, 0, 0)),
         "bak": ("Bakvy", (0, 1, 0), (-1, 0, 0)), "under": ("Undervy", (0, 0, -1), (1, 0, 0)),
         "vanster": ("Vanstervy", (-1, 0, 0), (0, -1, 0)), "hoger": ("Hogervy", (1, 0, 0), (0, 1, 0))}
ISO = ((-1, -1, 1), (1, -1, 0))   # framifrån vänster, ovanifrån


def args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("lage", choices=["bygg", "ritning"])
    ap.add_argument("fil", help="bygg: konstruktionsskriptet; ritning: modellens .FCStd")
    ap.add_argument("ut_fil", nargs="?", help="bygg: .FCStd att skapa")
    ap.add_argument("--var", action="append", default=[], metavar="NAMN=VÄRDE")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--step", action="store_true")
    ap.add_argument("--uppdrag", default="")
    ap.add_argument("--objekt", nargs="*", default=None, help="upp till tre rader: fastighet/projekt, kund, adress")
    import foretag
    u = foretag.las()
    ap.add_argument("--foretag", default=u["foretag"], help="företagsnamn i titelblocket (standard: foretag.json eller FC_FORETAG)")
    ap.add_argument("--adress", nargs="*", default=u["adress"], help="upp till tre adressrader i titelblocket (standard: foretag.json eller FC_ADRESS, rader åtskilda med |)")
    ap.add_argument("--ritad-av", dest="ritad_av", default=u["ritad_av"], help="RITAD/KONSTR AV (standard: foretag.json eller FC_RITAD_AV)")
    ap.add_argument("--handlaggare", default=u["handlaggare"], help="HANDLÄGGARE (standard: foretag.json eller FC_HANDLAGGARE)")
    ap.add_argument("--ansvarig", default=u["ansvarig"], help="ANSVARIG (standard: foretag.json eller FC_ANSVARIG)")
    ap.add_argument("--logga", default=u["logga"], help="PNG/JPEG i stället för företagsnamnet (standard: foretag.json eller FC_LOGGA)")
    ap.add_argument("--datum", default=None)
    ap.add_argument("--bet", default="")
    ap.add_argument("--rev", default="", help="BET|ÄNDRINGEN AVSER|DATUM|SIGN (eller BET|ANT|TEXT|DATUM|SIGN)")
    ap.add_argument("--stomnat", default=None, help="systemlinje, t.ex. A-B/2")
    ap.add_argument("--etapp", default="1")
    ap.add_argument("--antal", default="1", help="antal att tillverka")
    ap.add_argument("--not", dest="noter", action="append", default=None, help="not (versaler); ersätter modellens noter")
    ap.add_argument("--snitt", action="append", default=None, help="A:x=300:- (ersätter modellens snitt)")
    ap.add_argument("--vyer", default=None, help="t.ex. fram,plan")
    ap.add_argument("--skala", type=float, default=None)
    ap.add_argument("--skala-snitt", dest="skala_snitt", type=float, default=None)
    ap.add_argument("--hal", default="22", help="standardhål i ALLMÄNNA NOTERINGAR (mm)")
    ap.add_argument("--svets", default="3.0", help="standardsvets a-mått i ALLMÄNNA NOTERINGAR (mm)")
    ap.add_argument("--utan-kallor", dest="utan_kallor", action="store_true",
                    help="inga noter om var profilmåtten och materialkvaliteterna är verifierade (kallor.py)")
    ap.add_argument("--ut", default=None)
    a = ap.parse_args(argv)
    if a.lage == "bygg" and not a.ut_fil:
        ap.error("bygg kräver konstruktionsskript och ut-fil")
    return a


def tolka_snitt(s):
    """'A:x=300:-' -> dict(namn='A', axel='x', varde=300.0, mot='-')."""
    delar = s.split(":")
    namn, (axel, varde) = delar[0], delar[1].split("=")
    return dict(namn=namn, axel=axel.lower(), varde=float(varde.replace(",", ".")), mot=delar[2] if len(delar) > 2 else "")


def fmt(x, dec=1):
    s = ("%." + str(dec) + "f") % x
    return s.rstrip("0").rstrip(".") if "." in s else s


def skaltext(n):
    return "1:%s" % fmt(n) if n >= 1 else "%s:1" % fmt(1.0 / n)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ------------------------------------------------------------------ SVG-symboler (materiallista, noter, rubriker)
def svg(w, h, innehall):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" viewBox="0 0 %g %g">%s</svg>'
            % (w, h, w, h, "".join(innehall)))


def s_lin(x1, y1, x2, y2, b=0.13):
    return '<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#000" stroke-width="%g" stroke-linecap="square"/>' % (x1, y1, x2, y2, b)


def s_txt(x, y, s, h=3.33, anchor="start", font=FONT):
    a = ' text-anchor="%s"' % anchor if anchor != "start" else ""
    return '<text x="%g" y="%g" font-family="%s" font-size="%g" fill="#000"%s>%s</text>' % (x, y, font, h, a, esc(s))


def materiallista_svg(rader, marke, antal, hal, svets):
    """Materiallista + ALLMÄNNA NOTERINGAR, mått uppmätta ur Tekla-ritningen (130 mm bred, rader 5 mm).
    Returnerar (svg, bredd, höjd)."""
    n = len(rader)
    W, H = 130.0, 26.0 + 5.0 * n
    e = [s_lin(0, 0, W, 0), s_lin(0, 11, W, 11, 0.3), s_lin(0, 16, W, 16, 0.3), s_lin(0, 21, W, 21, 0.2),
         s_lin(0, 21 + 5 * n, W, 21 + 5 * n, 0.3), s_lin(0, H, W, H), s_lin(0, 0, 0, H), s_lin(W, 0, W, H)]
    for x in (21, 49, 70, 82):
        e.append(s_lin(x, 16, x, 21 + 5 * n, 0.3))
    for x in (98, 114):
        e.append(s_lin(x, 16, x, H, 0.3))
    for i in range(1, n):
        e.append(s_lin(0, 21 + 5 * i, W, 21 + 5 * i, 0.08))
    e += [s_txt(4.2, 7.4, "ALLMÄNNA NOTERINGAR:", 4.67),
          s_txt(62, 4.9, "ALLA HÅL ÄR  %s mm OM EJ ANNAT ANGES" % hal),
          s_txt(62, 9.0, "ALLA SVETSAR ÄR %s mm OM EJ ANNAT ANGES" % svets),
          s_txt(2.2, 15.0, "MATERIALLISTA FÖR ETT GODS MÄRKT:"), s_txt(62.1, 15.0, marke),
          s_txt(127, 15.0, "%s  st. TILLVERKAS" % antal, anchor="end")]
    for x, t in ((2, "STYCKLIT."), (23, "PROFIL"), (51, "MATERIAL"), (73, "ANT."), (85, "LÄNGD"), (101.3, "AREA/st"), (118, "VIKT/st")):
        e.append(s_txt(x, 20.0, t))
    ta = tv = 0.0
    for i, r in enumerate(rader):
        y = 25.0 + 5 * i
        e += [s_txt(2, y, r["pos"]), s_txt(23, y, r["profil"]), s_txt(53.2, y, r["material"]),
              s_txt(79, y, str(r["antal"]), anchor="end"), s_txt(93.8, y, fmt(r["langd"], 0), anchor="end"),
              s_txt(109.8, y, "%.1f" % r["area"], anchor="end"), s_txt(126.2, y, "%.1f" % r["vikt"], anchor="end")]
        ta += r["antal"] * r["area"]
        tv += r["antal"] * r["vikt"]
    y = H - 1.0
    e += [s_txt(96, y, "TOTALT", anchor="end"), s_txt(109.8, y, "%.1f" % ta, anchor="end"), s_txt(126.1, y, "%.1f" % tv, anchor="end")]
    return svg(W, H, e), W, H, ta, tv


def noter_svg(noter, h=4.0, rad=6.0):
    w = 225.0
    H = rad * len(noter) + 1.5
    return svg(w, H, [s_txt(0, h * 0.85 + rad * i, s, h) for i, s in enumerate(noter)]), w, H


def rubrik_svg(titel, skala):
    """'A - A' understruken med skalan under, som Tekla."""
    w, h = 40.0, 13.0
    tb = len(titel) * 2.4
    return svg(w, h, [s_txt(w / 2, 5.5, titel, 4.67, "middle"), s_lin(w / 2 - tb / 2, 6.6, w / 2 + tb / 2, 6.6, 0.2),
                      s_txt(w / 2 - tb / 2, 10.8, skala, 3.33)]), w, h


# =====================================================================================================
# Jobbet: inne i FreeCAD med GUI
# =====================================================================================================
def _jobb():
    import runpy
    import FreeCAD as App, FreeCADGui as Gui, Part
    from FreeCAD import Vector as V
    from PySide import QtGui
    import fcapi, stal, foretag
    from fcapi import logg, pump

    skillmapp = os.path.dirname(fcapi.jobb()["skriptmapp"])
    MALL = os.path.join(skillmapp, "mallar", "A2_tekla.svg")

    def tolka_var(lista):
        ut = {}
        for s in lista:
            k, v = s.split("=", 1)
            ut[k.strip()] = float(v.strip().replace(",", "."))
        return ut

    # ------------------------------------------------------------------ bygg
    def bygg(a):
        mod = runpy.run_path(a["fil"])
        namn, marke = mod.get("NAMN", "Konstruktion"), mod.get("MARKE", "X/1")
        v = {k: float(std) for k, std, _ in mod.get("VARIABLER", [])}
        nya = tolka_var(a["var"])
        okanda = set(nya) - set(v)
        if okanda:
            raise RuntimeError("Okända variabler %s. Skriptet har: %s" % (sorted(okanda), ", ".join(v)))
        v.update(nya)
        doc = App.newDocument("".join(c for c in namn if c.isalnum()) or "Konstruktion")
        beskr = {k_: b_ for k_, _, b_ in mod.get("VARIABLER", [])}
        k = stal.Konstruktion(doc, marke, namn, logg=logg, variabler=[(k_, fmt(x, 4), beskr.get(k_, "")) for k_, x in v.items()])
        mod["bygg"](k, v)
        if k.grupp.Ritning in ("", "{}") and mod.get("RITNING"):
            k.ritning(**mod["RITNING"])
        doc.Comment = "Byggd med sammanstallning.py från %s, variabler %s" % (os.path.basename(a["fil"]), json.dumps(v))
        doc.recompute()
        g, ds, hg = stal.delar(doc)
        rader = stal.materiallista(ds)
        logg("Variabler: " + ", ".join("%s=%s" % (k_, fmt(x)) for k_, x in v.items()))
        logg("%-6s %-12s %-8s %4s %7s %7s %8s" % ("POS", "PROFIL", "MATERIAL", "ANT", "LÄNGD", "AREA/st", "VIKT/st"))
        for r in rader:
            logg("%-6s %-12s %-8s %4d %7s %7.2f %8.2f%s" % (r["pos"], r["profil"], r["material"], r["antal"], fmt(r["langd"]), r["area"], r["vikt"],
                                                         "  OBS: olika geometri: %s" % ", ".join(r["fel"]) if r["fel"] else ""))
        tv = sum(r["antal"] * r["vikt"] for r in rader)
        alla = Part.makeCompound([o.Shape for o in ds])
        bb = alla.BoundBox
        logg("Delar %d, positioner %d, hålgrupper %d, vikt %.1f kg, låda %.0f x %.0f x %.0f mm" % (len(ds), len(rader), len(hg), tv, bb.XLength, bb.YLength, bb.ZLength))
        ogiltiga = [o.Label for o in ds if not o.Shape.isValid() or len(o.Shape.Solids) != 1]
        if ogiltiga:
            logg("OBS: ogiltig geometri eller inte en solid:", ogiltiga)
        skisser = [f for o in ds for f in o.Group if f.TypeId == "Sketcher::SketchObject"]
        for f in skisser:
            f.solve()
        ej = ["%s/%s" % (f.getParentGeoFeatureGroup().Label, f.Name) for f in skisser if not f.FullyConstrained]
        fel = ["%s/%s" % (o.Label, f.Name) for o in ds for f in o.Group if "Invalid" in f.State or "Error" in f.State]
        logg("Skisser %d, fullt bestämda: %s; features med fel: %s" % (len(skisser), "alla" if not ej else "INTE " + ", ".join(ej), ", ".join(fel) or "inga"))
        krock = []
        for i, o1 in enumerate(ds):
            for o2 in ds[i + 1:]:
                if o1.Shape.BoundBox.intersect(o2.Shape.BoundBox):
                    c = o1.Shape.common(o2.Shape)
                    if c.Volume > 1.0:
                        krock.append("%s/%s %.0f mm3" % (o1.Label, o2.Label, c.Volume))
        logg("Krockar (överlappande delar): %s" % (", ".join(krock) if krock else "inga"))
        fil = os.path.abspath(a["ut_fil"])
        doc.saveAs(fil)
        logg("Sparat:", fil)
        bas = os.path.splitext(fil)[0]
        if a.get("step"):
            alla.exportStep(bas + ".step")
            logg("STEP:", bas + ".step")
        if a.get("png"):
            gd = Gui.getDocument(doc.Name)
            pump(0.3)
            gd.ActiveView.viewIsometric()
            gd.ActiveView.fitAll()
            pump(0.3)
            gd.ActiveView.saveImage(bas + "_modell.png", 1600, 1200, "White")
            logg("PNG:", bas + "_modell.png")
        return dict(vikt=tv, rader=len(rader), krockar=krock)

    # ------------------------------------------------------------------ ritningshjälpare
    def textbredd(s, h):
        f = QtGui.QFont(FONT)
        f.setPixelSize(100)
        return QtGui.QFontMetricsF(f).horizontalAdvance(s) / 100.0 * h * 1.371   # TechDraw ritar h med 1,371 h em

    def projicera(shape, d, x):
        d, x = V(d).normalize(), V(x).normalize()
        y = d.cross(x)
        bb = shape.optimalBoundingBox(False, False)
        horn = [V(p, q, r) for p in (bb.XMin, bb.XMax) for q in (bb.YMin, bb.YMax) for r in (bb.ZMin, bb.ZMax)]
        xs, ys = [p.dot(x) for p in horn], [p.dot(y) for p in horn]
        return min(xs), max(xs), min(ys), max(ys)

    def antal_kanter(v):
        n = 0
        while True:
            try:
                if v.getEdgeByIndex(n) is None:
                    return n
            except Exception:
                return n
            n += 1

    def stil(d, fs=3.0):
        d.FormatSpec = "%.1w"
        vo = d.ViewObject
        vo.Font, vo.Fontsize, vo.Arrowsize, vo.LineWidth, vo.Color = FONT, fs, 2.0, 0.13, SVART
        return d

    class Vy:
        """En TechDraw-vy (DrawViewPart eller DrawViewSection) med pappersberäkning för modellpunkter."""

        def __init__(self, doc, page, namn, kalla, d, x, skala, px, py, snitt=None):
            if snitt:
                v = doc.addObject("TechDraw::DrawViewSection", namn)
                page.addView(v)
                v.BaseView = snitt["bas"].v
                v.Source = kalla
                v.SectionNormal = V(*snitt["normal"])
                v.SectionOrigin = V(*snitt["origo"])
                v.SectionSymbol = snitt["namn"]
                v.SectionDirection = snitt["riktning"]
            else:
                v = doc.addObject("TechDraw::DrawViewPart", namn)
                page.addView(v)
                v.Source = kalla
            v.Direction, v.XDirection = V(*d), V(*x)
            v.ScaleType, v.Scale = "Custom", 1.0 / skala
            v.X, v.Y = px, py
            self.v, self.doc, self.page, self.s, self.n = v, doc, page, 1.0 / skala, skala
            self.d, self.x = V(*d).normalize(), V(*x).normalize()
            self.y = self.d.cross(self.x)
            self.c = None

        def klar(self):
            for _ in range(400):
                pump(0.05)
                if self.v.getVisibleEdges():
                    return True
            raise RuntimeError("Vyn %s räknades aldrig klart" % self.v.Name)

        def _kalibrera(self, p):
            tag = self.v.makeCosmeticLine3D(p, p + self.x * 0.01)
            ce = self.v.getCosmeticEdge(tag)
            st = ce.Start
            f = ce.Format
            f["visible"] = False
            ce.Format = f
            pp = self.v.projectPoint(p)
            self.c = (pp.x - st.x, pp.y - st.y)

        def papper(self, p):
            if self.c is None:
                self._kalibrera(p)
            pp = self.v.projectPoint(p)
            return (self.v.X.Value + self.s * (pp.x - self.c[0]), self.v.Y.Value + self.s * (pp.y - self.c[1]))

        def punkt(self, sx, sy):
            """Modellpunkt med de projicerade koordinaterna (sx, sy) i vyn."""
            return self.x * sx + self.y * sy

        def linje(self, a, b):
            tag = self.v.makeCosmeticLine3D(a, b)
            ce = self.v.getCosmeticEdge(tag)
            ce.Format = {"style": 0, "weight": 0.1, "color": SVART + (1.0,), "visible": False}
            self.v.recompute()
            return "Edge%d" % (antal_kanter(self.v) - 1)

        def matt(self, typ, a, b, etikett, namn="Matt"):
            d = self.doc.addObject("TechDraw::DrawViewDimension", namn)
            d.Type, d.MeasureType = typ, "Projected"
            d.References2D = [(self.v, self.linje(a, b))]
            self.page.addView(d)
            d.X, d.Y = etikett[0] - self.v.X.Value, etikett[1] - self.v.Y.Value
            return stil(d)

        def ballong(self, text, origo, lage, form="Inspection"):
            """Positionsbubbla (form Inspection = avlång som Tekla) eller hålangivelse (form Line = understruken
            text). Ballongens X/Y och Origin är OSKALADE modellmått relativt vyns mitt (uppmätt)."""
            b = self.doc.addObject("TechDraw::DrawViewBalloon", "Ballong")
            b.SourceView = self.v
            self.page.addView(b)
            b.Text, b.BubbleShape, b.EndType = text, form, "None"
            b.OriginX, b.OriginY = (origo[0] - self.v.X.Value) / self.s, (origo[1] - self.v.Y.Value) / self.s
            b.X, b.Y = (lage[0] - self.v.X.Value) / self.s, (lage[1] - self.v.Y.Value) / self.s
            b.KinkLength = 0.0
            vo = b.ViewObject
            vo.Font, vo.Fontsize, vo.LineWidth, vo.Color = FONT, 3.0, 0.13, SVART
            return b

    def symbol(doc, page, namn, svgtext, x0, y0, w, h):
        """SVG-symbol med övre vänstra hörnet i (x0, y0) på papperet (Y uppåt). FreeCAD ritar symbolens mm med
        faktorn 90/96 - skalan 96/90 ger rätt storlek (uppmätt)."""
        s = doc.addObject("TechDraw::DrawViewSymbol", namn)
        s.Symbol = svgtext
        page.addView(s)
        s.Scale = 96.0 / 90.0
        s.X, s.Y = x0 + w / 2, y0 - h / 2
        return s

    def rensa(doc):
        """Ta bort ritningsobjekt från en tidigare körning. Ett blad tar med sig sina vyer, så gå på namn."""
        # Vyer först, sedan blad och mallar, och låt TechDraws bakgrundsberäkning bli klar innan:
        # att ta bort ett blad vars vyer fortfarande räknas kraschar FreeCAD (sett i 1.x på Linux).
        td = [o for o in doc.Objects if o.TypeId.startswith("TechDraw::")]
        ordning = {"TechDraw::DrawPage": 1, "TechDraw::DrawSVGTemplate": 2}
        namn = [o.Name for o in sorted(td, key=lambda o: ordning.get(o.TypeId, 0))]
        if namn and fcapi.har_gui():
            fcapi.pump(1.0)
        borta = 0
        for n in namn:
            if doc.getObject(n) is not None:
                doc.removeObject(n)
                borta += 1
        doc.recompute()
        return borta

    def stall_in():
        """TechDraw-inställningar för jobbet (sparas inte: FreeCAD avslutas med os._exit)."""
        for grp, typ, k, val in [("Dimensions", "Int", "ArrowStyle", 2),             # snedstreck (tick) som Tekla
                                 ("Dimensions", "Float", "FontSize", 3.4),           # snittbokstäverna: 1,39 x FontSize em
                                 ("Dimensions", "String", "FontName", FONT),
                                 ("Labels", "String", "LabelFont", FONT),
                                 ("Labels", "Float", "LabelSize", 3.0)]:
            pg = App.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/" + grp)
            getattr(pg, "Set" + typ)(k, val)
        # bubblorna fylls med sidans färg (standard ljusgrå F1F3F5) och linjerna är mörkgrå: svart/vitt som Tekla
        pg = App.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/Colors")
        for k in ("PageColor", "FaceColor"):
            pg.SetUnsigned(k, 0xFFFFFFFF)
        for k in ("NormalColor", "HiddenColor", "SectionColor", "CenterColor", "VertexColor"):
            pg.SetUnsigned(k, 0x000000FF)

    # ------------------------------------------------------------------ synlighet (positionsbubblor)
    def halvrum(shape, origo, normal):
        """Delen av shape på sidan -normal om planet (det som visas i snittet)."""
        bb = shape.BoundBox
        if not bb.isValid():
            return None
        R = bb.DiagonalLength + (V(*origo) - bb.Center).Length + 10
        n = V(*normal).normalize()
        c = V(*origo) - n * R
        box = Part.makeBox(2 * R, 2 * R, 2 * R)
        box.translate(V(-R, -R, -R) + c)
        try:
            r = shape.common(box)
        except Exception:
            return None
        return r if r.Volume > 1e-6 else None

    def ytpunkt(f):
        c = f.CenterOfMass
        if f.isInside(c, 0.01, True):
            u, v = f.Surface.parameter(c)
            return c, u, v
        u0, u1, v0, v1 = f.ParameterRange
        for i in (0.5, 0.25, 0.75, 0.1, 0.9):
            for j in (0.5, 0.25, 0.75, 0.1, 0.9):
                u, v = u0 + (u1 - u0) * i, v0 + (v1 - v0) * j
                p = f.valueAt(u, v)
                if f.isInside(p, 0.01, True):
                    return p, u, v
        return None

    def skymd(p, d, hinder, langd):
        if langd <= 0.1:
            return False
        a, b = p + d * 0.05, p + d * langd
        seg = Part.LineSegment(a, b).toShape()
        for s in hinder:
            if not s.BoundBox.intersect(a, d):
                continue
            if s.distToShape(seg)[0] < 1e-3:
                return True
        return False

    def synlig_yta(shape, alla, d, snitt=None):
        """(projicerad area, punkt) för delens största synliga yta i vyn med riktningen d (mot betraktaren), eller
        None. I ett snitt räknas snittytor (i planet) som synliga."""
        langd = 1e5
        if snitt:
            n, o = V(*snitt["normal"]), V(*snitt["origo"])
        kand = []
        for f in shape.Faces:
            if f.Area < 1.0:
                continue
            q = ytpunkt(f)
            if q is None:
                continue
            p, u, v = q
            try:
                nrm = f.normalAt(u, v)
            except Exception:
                continue
            k = nrm.dot(d)
            if snitt and abs((p - o).dot(n)) < 1e-4 and k > 0.99:
                kand.append((f.Area * 2, p, True))                    # snittyta: syns alltid, väger dubbelt
            elif k > 0.3:
                kand.append((f.Area * k, p, False))
        kand.sort(key=lambda t: -t[0])
        hinder = [s for s in alla if s is not shape] + [shape]
        for area, p, fri in kand[:5]:
            if fri:
                return area, p
            L = (o - p).dot(n) if snitt else langd
            if L <= 0.05:
                continue
            if not skymd(p, d, hinder, L):
                return area, p
        return None

    def sprid(poster, xmin, xmax, luft=2.5):
        """Lägg ut poster (x_onskat, bredd) på en rad utan överlapp. Returnerar x-mitt per post."""
        ordn = sorted(range(len(poster)), key=lambda i: poster[i][0])
        x = {}
        prev = None
        for i in ordn:
            xi, wi = poster[i]
            xi = max(xi, xmin + wi / 2)
            if prev is not None:
                xi = max(xi, x[prev] + poster[prev][1] / 2 + wi / 2 + luft)
            x[i] = xi
            prev = i
        if ordn and x[ordn[-1]] + poster[ordn[-1]][1] / 2 > xmax:     # skjut tillbaka från höger
            over = x[ordn[-1]] + poster[ordn[-1]][1] / 2 - xmax
            for i in ordn:
                x[i] -= over
            for j in range(len(ordn) - 2, -1, -1):
                a, b = ordn[j], ordn[j + 1]
                x[a] = min(x[a], x[b] - poster[b][1] / 2 - poster[a][1] / 2 - luft)
        return [x[i] for i in range(len(poster))]

    # ------------------------------------------------------------------ ritning
    def ritning(a):
        stall_in()
        fil = os.path.abspath(a["fil"])
        utmapp = os.path.abspath(a["ut"]) if a.get("ut") else os.path.dirname(fil)
        os.makedirs(utmapp, exist_ok=True)
        bas = os.path.join(utmapp, os.path.splitext(os.path.basename(fil))[0])
        doc = App.openDocument(fil)
        logg("Rensade gamla ritningsobjekt:", rensa(doc))
        g, ds, hg = stal.delar(doc)
        cfg = json.loads(g.Ritning or "{}")
        marke = g.Marke
        vyer_k = a["vyer"].split(",") if a.get("vyer") else cfg.get("vyer", ["fram", "plan"])
        dolda = cfg.get("dolda", [])
        snittdef = [tolka_snitt(s) for s in a["snitt"]] if a.get("snitt") else cfg.get("snitt", [])
        noter = a["noter"] if a.get("noter") else cfg.get("noter", [])
        rader = stal.materiallista(ds)
        for r in rader:
            if r["fel"]:
                logg("OBS: %s har delar med olika geometri: %s" % (r["pos"], ", ".join(r["fel"])))
        # var profilmåtten (sparat vid bygget) och materialkvaliteterna (verifieras nu) kommer ifrån -> noter
        kallrader = []
        if not a.get("utan_kallor"):
            import kallor
            try:
                kl = json.loads(getattr(g, "Kallor", "") or "[]")
            except ValueError:
                kl = []
            tjock, varm = {}, {}
            for r in rader:
                t = kallor.tjocklek(r["profil"])
                tjock[r["material"]] = max(tjock.get(r["material"], 0.0), t or 0.0) or None
                varm[r["material"]] = varm.get(r["material"], False) or r["profil"].upper().startswith(("KKR", "KCKR"))
            mat = {m: kallor.material(m, tjock[m], varm[m]) for m in tjock}
            kallrader = kallor.noter(kl, mat, bredd=70)
            for s_ in kallrader:
                logg("Not:", s_)
            for s_ in kallor.notiser():
                logg("Källor OBS:", s_)
            for s_ in kallor.fel():
                logg("Källor FEL:", s_)
            noter = list(noter) + kallrader
        alla = [o.Shape for o in ds]
        komp = Part.makeCompound(alla)
        huvud = doc.getObject(g.Huvuddel) if g.Huvuddel else None

        # ---- vyernas definitioner (snitt: halvrummet som visas)
        vdef = []
        for k in vyer_k:
            namn, d, x = VYDEF[k]
            vdef.append(dict(namn=namn, d=V(*d), x=V(*x), shapes=alla, delar=list(ds), dolda=k in dolda, snitt=None, extra=0.0))
        for s in snittdef:
            ax = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}[s["axel"]]
            bb = komp.BoundBox
            mitt = bb.Center
            origo = V(mitt.x, mitt.y, mitt.z)
            setattr(origo, s["axel"], s["varde"])
            mot = s.get("mot") or ("+" if getattr(mitt, s["axel"]) > s["varde"] else "-")
            blick = ax * (1 if mot == "+" else -1)            # blickriktning
            normal = -blick                                   # materialet på -normal-sidan visas
            d = normal                                        # vyns riktning pekar mot betraktaren
            x = V(0, 0, 1).cross(d) if abs(d.z) < 0.9 else V(1, 0, 0)
            bas_ = next((v for v in vdef if v["snitt"] is None and abs(v["d"].dot(normal)) < 1e-6), None)
            if bas_ is None:
                logg("OBS: snitt %s saknar en vy där snittlinjen syns - hoppas över" % s["namn"])
                continue
            bas_["extra"] = SNITTMARK                      # plats för snittbokstäverna ovanför och under vyn
            kvar, kdelar = [], []
            for o in ds:
                h = halvrum(o.Shape, origo, normal)
                if h is not None:
                    kvar.append(h)
                    kdelar.append(o)
            sx = normal.dot(bas_["x"])
            sy = normal.dot(bas_["d"].cross(bas_["x"]))
            rikt = ("Right" if sx > 0 else "Left") if abs(sx) > abs(sy) else ("Up" if sy > 0 else "Down")
            vdef.append(dict(namn="Snitt" + s["namn"], d=d, x=x, shapes=kvar, delar=kdelar, dolda=False, extra=0.0,
                             snitt=dict(namn=s["namn"], normal=tuple(normal), origo=tuple(origo), riktning=rikt, basnamn=bas_["namn"])))
            logg("Snitt %s-%s: planet %s = %s, blicken mot %s%s, %d delar kvar" % (s["namn"], s["namn"], s["axel"], fmt(s["varde"]), mot, s["axel"], len(kdelar)))

        # ---- hålgrupper per vy (cirklar: axeln längs vyns riktning; i snitt även hål som snittplanet skär)
        for vd in vdef:
            vd["hal_x"], vd["hal_y"], vd["grupp_x"], vd["grupp_y"], vd["hal"], vd["skymda"], vd["halpts"] = set(), set(), set(), set(), [], [], {}
            vd["skymd_hal"] = {}
            ext = projicera(Part.makeCompound(vd["shapes"]), vd["d"], vd["x"])
            vd["ext"] = ext
            y = vd["d"].cross(vd["x"])
            sett = vd["sett"] = set()
            for gi, h in sorted(enumerate(hg), key=lambda t: -sum(V(*p).dot(vd["d"]) for p in t[1]["punkter"]) / len(t[1]["punkter"])):
                ax = V(*h["riktning"])
                pts = [V(*p) for p in h["punkter"]]
                if vd["snitt"]:
                    n, o = V(*vd["snitt"]["normal"]), V(*vd["snitt"]["origo"])
                    pts_kvar = [p for p in pts if (p - o).dot(n) < h["d"] / 2]
                else:
                    pts_kvar = pts
                if not pts_kvar:
                    continue
                if abs(abs(ax.dot(vd["d"])) - 1) < 1e-6:
                    # hål som skyms av en annan del (t.ex. fotplåtens hål under toppplåten) räknas inte, men sparas
                    # som reserv för hålangivelsen om gruppen inte syns i någon vy
                    alla_pts = pts_kvar
                    if vd["snitt"]:
                        n, o = V(*vd["snitt"]["normal"]), V(*vd["snitt"]["origo"])
                        pts_kvar = [p for p in pts_kvar if not skymd(p, vd["d"], vd["shapes"], (o - p).dot(n))]
                    else:
                        pts_kvar = [p for p in pts_kvar if not skymd(p, vd["d"], vd["shapes"], 1e5)]
                    if not pts_kvar:
                        vd["skymd_hal"][gi] = alla_pts
                        continue
                    vd["halpts"][gi] = pts_kvar
                    nyckel = tuple(sorted((round(p.dot(vd["x"]), 1), round(p.dot(y), 1)) for p in pts_kvar))
                    if nyckel in sett:
                        vd["skymda"].append(gi)
                        continue                               # samma hål bakom (t.ex. bakre ramen) - redan med
                    sett.add(nyckel)
                    vd["hal"].append(gi)
                    for p in pts_kvar:
                        vd["hal_x"].add(round(p.dot(vd["x"]), 1))
                        vd["hal_y"].add(round(p.dot(y), 1))
                    c = sum(pts_kvar, V()) * (1.0 / len(pts_kvar))
                    vd["grupp_x"].add(round(c.dot(vd["x"]), 1))
                    vd["grupp_y"].add(round(c.dot(y), 1))
                elif vd["snitt"] and abs(ax.dot(vd["d"])) < 1e-6:
                    n, o = V(*vd["snitt"]["normal"]), V(*vd["snitt"]["origo"])
                    skurna = [p for p in pts if abs((p - o).dot(n)) < h["d"] / 2]
                    for p in skurna:                           # hålets läge tvärs axeln
                        if abs(ax.dot(vd["x"])) > 0.99:
                            vd["hal_y"].add(round(p.dot(y), 1))
                        elif abs(ax.dot(y)) > 0.99:
                            vd["hal_x"].add(round(p.dot(vd["x"]), 1))

            def kedjor(hal, grupp, lo, hi):
                ut = []
                inre = sorted(v for v in hal if lo + 0.5 < v < hi - 0.5)
                if inre:
                    ut.append([lo] + inre + [hi])
                gr = sorted(v for v in grupp if lo + 0.5 < v < hi - 0.5)
                if len(grupp) >= 2 and gr and gr != inre:
                    ut.append([lo] + gr + [hi])
                ut.append([lo, hi])
                return ut
            vd["kedja_x"] = kedjor(vd["hal_x"], vd["grupp_x"], ext[0], ext[1])
            vd["kedja_y"] = kedjor(vd["hal_y"], vd["grupp_y"], ext[2], ext[3])
            w, h_ = ext[1] - ext[0], ext[3] - ext[2]
            vd["w"], vd["h"] = w, h_
            vd["topp"] = FORST - 3 + STEG * len(vd["kedja_x"]) + (HALRAD if vd["hal"] else 0) + 2 + vd["extra"]
            vd["vanster"] = FORST - 3 + STEG * len(vd["kedja_y"]) + 2
            vd["botten"] = BUBBEL + (14.0 if vd["snitt"] else 0.0) + vd["extra"]

        # ---- hålgrupper som inte syns i någon vy (t.ex. bultförbandet bakom UPE-livet): hålangivelsen i första vyn
        # där hålen ligger längs blickriktningen, som Teklas ledare till dolda hål, och med i måttkedjorna
        anvanda = {gi for vd in vdef for gi in vd["hal"] + vd["skymda"]}
        for gi in range(len(hg)):
            if gi in anvanda:
                continue
            for vd in vdef:
                if gi in vd["skymd_hal"]:
                    y = vd["d"].cross(vd["x"])
                    pts = vd["skymd_hal"][gi]
                    nyckel = tuple(sorted((round(p.dot(vd["x"]), 1), round(p.dot(y), 1)) for p in pts))
                    if nyckel in vd["sett"]:
                        vd["skymda"].append(gi)
                    else:
                        vd["sett"].add(nyckel)
                        vd["hal"].append(gi)
                        vd["halpts"][gi] = pts
                        for p in pts:
                            vd["hal_x"].add(round(p.dot(vd["x"]), 1))
                            vd["hal_y"].add(round(p.dot(y), 1))
                        c = sum(pts, V()) * (1.0 / len(pts))
                        vd["grupp_x"].add(round(c.dot(vd["x"]), 1))
                        vd["grupp_y"].add(round(c.dot(y), 1))
                        ext = vd["ext"]
                        vd["kedja_x"] = kedjor(vd["hal_x"], vd["grupp_x"], ext[0], ext[1])
                        vd["kedja_y"] = kedjor(vd["hal_y"], vd["grupp_y"], ext[2], ext[3])
                        vd["topp"] = FORST - 3 + STEG * len(vd["kedja_x"]) + HALRAD + 2 + vd["extra"]
                        vd["vanster"] = FORST - 3 + STEG * len(vd["kedja_y"]) + 2
                    anvanda.add(gi)
                    break

        # ---- skalor och placering: huvudvyer i en kolumn till vänster, snitt i en kolumn till höger
        huvud_v = [vd for vd in vdef if vd["snitt"] is None]
        snitt_v = [vd for vd in vdef if vd["snitt"]]
        # noterna nere till vänster (underkant y = 26) och materiallistan bestämmer hur långt ner vyerna får gå
        ml, mw, mh, ta, tv = materiallista_svg(rader, marke, a["antal"], a["hal"], a["svets"])
        nsvg, nw, nh_ = noter_svg(noter) if noter else (None, 0.0, 0.0)
        Y0, X0 = 392.0, 50.0

        def kolumn(lst, n):
            hojd = sum(vd["topp"] + vd["h"] / n + vd["botten"] for vd in lst) + 4 * (len(lst) - 1)
            bredd = max(vd["vanster"] for vd in lst) + max(vd["w"] for vd in lst) / n
            return bredd, hojd
        def y_min(bredd):
            y1 = max(26.0 + nh_ + 6, 60.0)
            return max(y1, 20.0 + mh + 6) if X0 + bredd > 270 else y1

        def ryms(k):
            b, h = kolumn(huvud_v, k)
            return b <= 330 and h <= Y0 - y_min(b)
        n = a.get("skala") or next((k for k in SKALOR if ryms(k)), SKALOR[-1])
        bv, _ = kolumn(huvud_v, n)
        vl = max(vd["vanster"] for vd in huvud_v)
        xc = X0 + vl + max(vd["w"] for vd in huvud_v) / n / 2
        y = Y0
        for vd in huvud_v:
            vd["n"] = n
            y -= vd["topp"]
            vd["pos"] = (xc, y - vd["h"] / n / 2)
            y -= vd["h"] / n + vd["botten"] + 4
        xr0 = X0 + bv + 22
        ns = None
        if snitt_v:
            yr1 = 92.0
            ns = a.get("skala_snitt") or next((k for k in SKALOR if min(n, 5) <= k <= n * 1.0001 and kolumn(snitt_v, k)[0] <= 568 - xr0 and kolumn(snitt_v, k)[1] <= Y0 - yr1), None)
            if ns is None:
                ns = next((k for k in SKALOR if kolumn(snitt_v, k)[0] <= 568 - xr0 and kolumn(snitt_v, k)[1] <= Y0 - yr1), SKALOR[-1])
            vls = max(vd["vanster"] for vd in snitt_v)
            y = Y0
            for vd in snitt_v:
                vd["n"] = ns
                y -= vd["topp"]
                vd["pos"] = (xr0 + vls + vd["w"] / ns / 2, y - vd["h"] / ns / 2)
                y -= vd["h"] / ns + vd["botten"] + 4
            ylagst = y
        else:
            ylagst = Y0
        logg("Skala huvudvyer %s, snitt %s" % (skaltext(n), skaltext(ns) if ns else "-"))

        # ---- blad, mall, vyer
        page = doc.addObject("TechDraw::DrawPage", "Sammanstallningsritning")
        tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Mall")
        tpl.Template = foretag.mall_med_logga(MALL, a.get("logga"), utmapp)
        if a.get("logga"):
            logg("Logga i titelblocket:", a["logga"])
        page.Template = tpl
        vyobj = {}
        for vd in vdef:
            sn = None
            if vd["snitt"]:
                sn = dict(vd["snitt"], bas=vyobj[vd["snitt"]["basnamn"]])
            vy = Vy(doc, page, vd["namn"], list(ds) if not sn else list(ds), tuple(vd["d"]), tuple(vd["x"]), vd["n"], *vd["pos"], snitt=sn)
            if vd["dolda"]:
                vy.v.HardHidden = True
            vyobj[vd["namn"]] = vy
            vd["vy"] = vy
        # isometri i ytan nere till höger (under snitten, ovanför revisionstabellen)
        ni = None
        ix0, ix1, iy0, iy1 = max(xr0, 410.0), 568.0, 74.0, min(ylagst, 300.0)
        wi_ = projicera(komp, *ISO)
        wi, hi = wi_[1] - wi_[0], wi_[3] - wi_[2]
        if ix1 - ix0 > 40 and iy1 - iy0 > 30:
            ni = next((k for k in SKALOR if (ns or n) <= k and wi / k <= ix1 - ix0 and hi / k <= iy1 - iy0 - 12), None)
        if ni:
            iso = Vy(doc, page, "Isometri", list(ds), ISO[0], ISO[1], ni, (ix0 + ix1) / 2, (iy0 + iy1) / 2 + 6)
        else:
            iso = None
            logg("OBS: ingen plats för isometrin")
        doc.recompute()
        for vy in [vd["vy"] for vd in vdef] + ([iso] if iso else []):
            vy.klar()
            vo = vy.v.ViewObject
            vo.LineWidth, vo.HiddenWidth, vo.FaceColor = 0.25, 0.13, (1.0, 1.0, 1.0)
        page.ViewObject.show()
        pump(0.5)
        logg("Vyer klara: %s" % ", ".join(vd["namn"] for vd in vdef) + (", Isometri %s" % skaltext(ni) if ni else ""))

        # ---- måttkedjor och totalmått
        nm = 0

        def lagen(seg, mitt):
            """Måttexternas lägen längs en kedja: mitt i segmentet, eller utanför det (mot kedjans närmaste ände)
            när texten inte ryms mellan förlängningslinjerna. Utflyttade texter skjuts så att de inte överlappar."""
            ut, upptaget = {}, []
            for i, (pa, pb, tw) in enumerate(seg):
                if pb - pa >= tw + 0.5:
                    ut[i] = (pa + pb) / 2
                    upptaget.append((ut[i] - tw / 2, ut[i] + tw / 2))
            for sida in (1, -1):
                ordn = [i for i in range(len(seg)) if i not in ut and ((seg[i][0] + seg[i][1]) / 2 >= mitt) == (sida > 0)]
                ordn.sort(key=lambda i: sida * seg[i][0])
                for i in ordn:
                    pa, pb, tw = seg[i]
                    c = pb + tw / 2 + 1.2 if sida > 0 else pa - tw / 2 - 1.2
                    for _ in range(50):
                        krock = [u for u in upptaget if u[0] - 0.8 < c + tw / 2 and c - tw / 2 < u[1] + 0.8]
                        if not krock:
                            break
                        c = max(u[1] for u in krock) + tw / 2 + 0.8 if sida > 0 else min(u[0] for u in krock) - tw / 2 - 0.8
                    ut[i] = c
                    upptaget.append((c - tw / 2, c + tw / 2))
            return [ut[i] for i in range(len(seg))]

        for vd in vdef:
            vy = vd["vy"]
            X, Y = vy.v.X.Value, vy.v.Y.Value
            w, h_ = vd["w"] * vy.s, vd["h"] * vy.s
            ext = vd["ext"]
            for axel, kedjor_ in (("x", vd["kedja_x"]), ("y", vd["kedja_y"])):
                for niva, ked in enumerate(kedjor_):
                    par = [(p, q) for p, q in zip(ked, ked[1:]) if q - p >= 0.5]
                    if axel == "x":
                        pts = [(vy.punkt(p, ext[3]), vy.punkt(q, ext[3])) for p, q in par]
                        seg = [(vy.papper(A_)[0], vy.papper(B_)[0]) for A_, B_ in pts]
                    else:
                        pts = [(vy.punkt(ext[0], p), vy.punkt(ext[0], q)) for p, q in par]
                        seg = [(vy.papper(A_)[1], vy.papper(B_)[1]) for A_, B_ in pts]
                    seg = [(min(u, v), max(u, v), textbredd(fmt(q - p), 3.0)) for (u, v), (p, q) in zip(seg, par)]
                    for (A_, B_), c in zip(pts, lagen(seg, X if axel == "x" else Y)):
                        if axel == "x":
                            vy.matt("DistanceX", A_, B_, (c, Y + h_ / 2 + FORST + vd["extra"] + STEG * niva), "Matt%s" % vd["namn"])
                        else:
                            vy.matt("DistanceY", A_, B_, (X - w / 2 - FORST - STEG * niva, c), "Matt%s" % vd["namn"])
                        nm += 1
        logg("Mått: %d" % nm)

        # ---- positionsbubblor: varje positionsnummer en gång, i vyn där delen syns störst på papperet
        bast = {}
        for vd in vdef:
            kvar = vd["shapes"]
            for o, sh in zip(vd["delar"], kvar):
                r = synlig_yta(sh, kvar, vd["d"], vd["snitt"])
                if r is None:
                    continue
                poang = r[0] / vd["n"] ** 2
                if o.Pos not in bast or poang > bast[o.Pos][0]:
                    bast[o.Pos] = (poang, vd, r[1], o)
        saknas = sorted({o.Pos for o in ds} - set(bast))
        if saknas:
            logg("OBS: positioner som inte syns i någon vy (ingen bubbla): %s" % ", ".join(saknas))
        # ---- hålangivelser 4*Ø14 - M12x44: grupper i vyns övre halva ovanför måtten, i nedre halvan i raden
        # med positionsbubblor under vyn. Varje hålgrupp en gång (i första vyn där hålen syns som cirklar).
        nb = nh = 0
        gjorda = set()
        for vd in vdef:
            vy = vd["vy"]
            X, Y, h_ = vy.v.X.Value, vy.v.Y.Value, vd["h"] * vy.s
            ytop = Y + h_ / 2 + FORST - 3 + vd["extra"] + STEG * len(vd["kedja_x"]) + 5
            ybub = Y - h_ / 2 - 8.5 - vd["extra"]
            uppe, nere = [], []                       # (text, ankare, bredd, form, hålradie på papperet)
            for pos, (_, v_, p, o) in bast.items():
                if v_ is vd:
                    txt = "%s %s %s" % (marke, pos, o.Profil) if huvud is not None and o.Pos == huvud.Pos else pos
                    nere.append((txt, vy.papper(p), textbredd(txt, 3.0) + 7, "Inspection", 0.0))
            for gi in vd["hal"]:
                if gi in gjorda:
                    continue
                gjorda.add(gi)
                h = hg[gi]
                pts = vd["halpts"][gi]
                txt = stal.haltext(len(h["punkter"]), h["d"], h["bult"])
                pp = [vy.papper(q) for q in pts]
                cy = sum(q[1] for q in pp) / len(pp)
                if cy >= Y:
                    uppe.append((txt, max(pp, key=lambda q: (q[1], q[0])), textbredd(txt, 3.0) + 4, "Line", h["d"] / 2 * vy.s))
                else:
                    nere.append((txt, min(pp, key=lambda q: (q[1], -q[0])), textbredd(txt, 3.0) + 4, "Line", h["d"] / 2 * vy.s))
            for rad, yr, forskj in ((uppe, ytop, 8.0), (nere, ybub, 0.0)):
                if not rad:
                    continue
                xs = sprid([(ank[0] + forskj, b) for _, ank, b, _, _ in rad], 44, 570, 3.0)
                for (txt, ank, b, form, r), xb in zip(rad, xs):
                    dx, dy = xb - ank[0], yr - ank[1]
                    L = math.hypot(dx, dy) or 1.0
                    vy.ballong(txt, (ank[0] + dx / L * r, ank[1] + dy / L * r), (xb, yr), form=form)
                    if form == "Line":
                        nh += 1
                    else:
                        nb += 1
            if uppe or nere:
                logg("%s: %s" % (vd["namn"], ", ".join(t[0] for t in nere + uppe)))
        skymda = {gi for vd in vdef for gi in vd["skymda"]}
        ejvisade = [stal.haltext(len(h["punkter"]), h["d"], h["bult"]) for i, h in enumerate(hg) if i not in gjorda and i not in skymda]
        logg("Positionsbubblor: %d, hålangivelser: %d (%d grupper bakom andra med samma hålbild)%s" % (
            nb, nh, len(skymda - gjorda), ("  OBS: syns inte som cirklar i någon vy: %s" % ", ".join(ejvisade)) if ejvisade else ""))

        # ---- snittrubriker, isometrins skala
        for vd in vdef:
            if vd["snitt"]:
                vy = vd["vy"]
                sv, w_, h_ = rubrik_svg("%s - %s" % (vd["snitt"]["namn"], vd["snitt"]["namn"]), skaltext(vd["n"]))
                symbol(doc, page, "Rubrik" + vd["namn"], sv, vy.v.X.Value - w_ / 2, vy.v.Y.Value - vd["h"] * vy.s / 2 - BUBBEL - 1, w_, h_)
        if iso:
            sv, w_, h_ = rubrik_svg("-", skaltext(ni))
            symbol(doc, page, "RubrikIsometri", sv, iso.v.X.Value - w_ / 2, iso.v.Y.Value - hi / ni / 2 - 2, w_, h_)

        # ---- materiallista, noter, titelblock
        symbol(doc, page, "Materiallista", ml, 404 - mw, 20 + mh, mw, mh)
        if noter:
            symbol(doc, page, "Noter", nsvg, X0, 26.0 + nh_, nw, nh_)
        skalor = sorted({n} | ({ns} if ns else set()))          # som Tekla: huvudvyer och snitt (inte isometrin)
        rev = [s.strip() for s in a["rev"].split("|")] if a.get("rev") else []
        if len(rev) == 4:
            rev = [rev[0], ""] + rev[1:]
        rev = (rev + [""] * 5)[:5]
        obj = (a.get("objekt") or []) + ["", "", ""]
        adr = list(a.get("adress") or []) + ["", "", ""]
        falt = dict(Foretag=a.get("foretag") or "", Adress1=adr[0], Adress2=adr[1], Adress3=adr[2],
                    Uppdrag=a["uppdrag"], RitadAv=a["ritad_av"], Datum=a.get("datum") or time.strftime("%Y-%m-%d"),
                    Handlaggare=a["handlaggare"], Ansvarig=a["ansvarig"], Objekt1=obj[0], Objekt2=obj[1], Objekt3=obj[2],
                    Skala="  ".join(skaltext(k) for k in skalor), Nummer=marke, Bet=a["bet"],
                    RevBet=rev[0], RevAnt=rev[1], RevText=rev[2], RevDatum=rev[3], RevSign=rev[4],
                    StomnatNummer=marke, Systemlinje=a.get("stomnat") or cfg.get("stomnat", ""),
                    Etapp=a["etapp"], Antal=a["antal"])
        et = tpl.EditableTexts
        et.update(falt)
        tpl.EditableTexts = et
        doc.recompute()
        pump(1.0)

        # ---- kontroll och export
        fel = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
        if fel:
            logg("OBS: objekt med fel:", fel)
        with open(bas + "_materiallista.csv", "w", encoding="utf-8-sig") as f:
            f.write("STYCKLIT.;PROFIL;MATERIAL;ANT.;LÄNGD;AREA/st;VIKT/st\n")
            for r in rader:
                f.write("%s;%s;%s;%d;%s;%s;%s\n" % (r["pos"], r["profil"], r["material"], r["antal"], fmt(r["langd"]),
                                                  ("%.2f" % r["area"]).replace(".", ","), ("%.1f" % r["vikt"]).replace(".", ",")))
            f.write(";;;;TOTALT;%s;%s\n" % (("%.1f" % ta).replace(".", ","), ("%.1f" % tv).replace(".", ",")))
            for s_ in kallrader:
                f.write("KÄLLA;%s\n" % s_)
        doc.saveAs(bas + ".FCStd")
        logg("Sparat:", bas + ".FCStd")
        page.ViewObject.show()
        pump(1.0)
        import TechDrawGui
        tmp = bas + "_tmp.pdf"
        TechDrawGui.exportPageAsPdf(page, tmp)
        return dict(sidor=[tmp], bas=bas, skala=n, skala_snitt=ns, skala_iso=ni, matt=nm, bubblor=nb, hal=nh, vikt=tv)

    fcapi.kor_jobb(lambda a: bygg(a) if a["lage"] == "bygg" else ritning(a))


def _efterbehandla(r):
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    bas = r["bas"]
    pdf = bas + ".pdf"
    with pymupdf.open(r["sidor"][0]) as d:
        try:
            if os.path.exists(pdf):
                os.remove(pdf)
        except PermissionError:
            pdf = bas + "_" + time.strftime("%H%M%S") + ".pdf"
            print("OBS: PDF:en är öppen i ett annat program - sparar som %s" % os.path.basename(pdf))
        d.save(pdf)
        d[0].get_pixmap(dpi=110).save(bas + ".png")
    os.remove(r["sidor"][0])
    print("PDF: %s  PNG: %s  CSV: %s" % (pdf, os.path.basename(bas + ".png"), os.path.basename(bas + "_materiallista.csv")))


if __name__ == "__fcjobb__":
    _jobb()
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    a = args()
    a.fil = os.path.abspath(a.fil)
    if not os.path.exists(a.fil):
        raise SystemExit("Filen finns inte: " + a.fil)
    if a.ut_fil:
        a.ut_fil = os.path.abspath(a.ut_fil)
    r = fcapi.kor(__file__, vars(a))
    if a.lage == "ritning":
        _efterbehandla(r)
