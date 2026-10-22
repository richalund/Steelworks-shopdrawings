"""Översiktsritning (plan, fasad, montage- eller offertritning) på A2 av en hel modell: delar och referenskroppar
(omgivningen) med måttkedjor, bubblor, nivåer, texter och noter som ett ritskript bestämmer.

  python3 oversikt.py <modell.FCStd> <ritskript.py> [--uppdrag OFFERT] [--objekt rad1 rad2 rad3] [--datum ...]
                      [--ut <mapp>]

Modellen är vilken FCStd som helst med kroppar, t.ex. byggd med `sammanstallning.py bygg` där omgivningen
(trappa, vägg, mark) ritats med `k.referens(...)`. Ritskriptet beskriver bladet:

  NUMMER = "R-101"                        # ritningsnummer i titelblocket
  OBJEKT = ["PLAN ENTRÉTRAPPA, VILLA", "Kund", "Adress"]       # titelblockets tre objektrader (valfritt)
  SKALA = 20                              # standardskala för vyerna
  SPRAK = "sv"                            # titelblockets språk: sv, en, zh (valfritt, --sprak går före)
  def rita(r):
      plan = r.vy("PLAN", riktning=(0, 0, 1), x=(1, 0, 0), lage=(175, 150))
      fasad = r.vy("FASAD", riktning=(0, -1, 0), x=(1, 0, 0), lage=(175, 330))
      plan.kedja([(0, 0, 0), (1100, 0, 0), (2380, 0, 0)], "x", avstand=8)   # måttkedja, 8 mm från punkterna
      plan.matt((0, 0, 0), (2380, 0, 0), "x", avstand=16)                    # totalmått
      plan.bubbla("R/1", (600, 1440, 1430), dx=-6, dy=-14)                    # märkning med kort pil
      plan.text("VILPLAN +780", (-800, 750, 780))                             # text på papperet vid punkten
      fasad.niva("+780 VILPLAN", (-1600, 0, 780), dx=26)                       # nivåtext med ▽
      plan.stomnat(x={"1": 0, "2": 2380}, y={"A": 0}, marginal=800)                # stomlinjer med cirklar
      r.noter(["PLANRITNING ...", "..."])                                       # noterna till höger

Vyernas riktning pekar mot betraktaren (som TechDraw): plan (0, 0, 1), framifrån (0, -1, 0). `x` är vyns
riktning åt höger. `lage` är vyns mitt på bladet (mm, origo nere till vänster); utelämnas den staplas vyerna
uppifrån i vänsterkolumnen. `kallor="delar"` visar bara sammanställningens delar, `"alla"` (standard) även
omgivningen. Avstånd och dx/dy är millimeter på papperet; positiva värden åt höger/uppåt.
Ger <ritskript>.pdf och .png i modellens mapp och bladet Oversikt<NUMMER> i modellens FCStd.
"""
import os, sys, re, time, argparse, runpy

FONT = "Arial Narrow"


def args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("fil", help="modellens .FCStd")
    ap.add_argument("ritskript", help="python-fil med rita(r)")
    ap.add_argument("--uppdrag", default="")
    ap.add_argument("--objekt", nargs="*", default=None, help="upp till tre rader (annars ritskriptets OBJEKT)")
    ap.add_argument("--datum", default=None)
    ap.add_argument("--sprak", choices=["sv", "en", "zh"], default=None, help="titelblockets språk (annars ritskriptets SPRAK eller sv)")
    ap.add_argument("--ut", default=None)
    return ap.parse_args(argv)


def _jobb(a):
    import FreeCAD as App
    from FreeCAD import Vector as V
    import fcapi, foretag
    from fcapi import logg, pump
    skript = runpy.run_path(a["ritskript"])
    nummer = str(skript.get("NUMMER", "X-1"))
    skala0 = float(skript.get("SKALA", 20))
    slug = re.sub(r"[^A-Za-z0-9]", "", nummer) or "1"
    pref = "Ovs%s_" % slug

    for grp, typ, k, val in [("Dimensions", "Int", "ArrowStyle", 2), ("Dimensions", "Float", "FontSize", 3.4),
                             ("Dimensions", "String", "FontName", FONT), ("Labels", "String", "LabelFont", FONT),
                             ("Labels", "Float", "LabelSize", 3.0)]:
        pg = App.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/" + grp)
        getattr(pg, "Set" + typ)(k, val)
    pg = App.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/Colors")
    for k in ("PageColor", "FaceColor"):
        pg.SetUnsigned(k, 0xFFFFFFFF)
    for k in ("NormalColor", "HiddenColor", "SectionColor", "CenterColor", "VertexColor"):
        pg.SetUnsigned(k, 0x000000FF)

    doc = fcapi.mm_enheter(App.openDocument(a["fil"]))
    # ta bort bladet från en tidigare körning: vyer först, sedan blad och mall (annars kraschar FreeCAD)
    gamla = [o for o in doc.Objects if o.Name.startswith(pref)]
    ordning = {"TechDraw::DrawViewPart": 1, "TechDraw::DrawPage": 2, "TechDraw::DrawSVGTemplate": 3}
    if gamla:
        pump(1.0)
    for n in [o.Name for o in sorted(gamla, key=lambda o: ordning.get(o.TypeId, 0))]:
        if doc.getObject(n) is not None:
            doc.removeObject(n)
    doc.recompute()

    u = foretag.las()
    utmapp = os.path.abspath(a["ut"]) if a.get("ut") else os.path.dirname(a["fil"])
    os.makedirs(utmapp, exist_ok=True)
    mall = os.path.join(os.path.dirname(os.path.abspath(fcapi.__file__)), "..", "mallar", "A2.svg")
    mall = foretag.mall_med_logga(mall, u.get("logga"), utmapp)
    import sprak
    mall = sprak.mallfil(mall, a.get("sprak") or skript.get("SPRAK") or "sv", utmapp)
    tpl = doc.addObject("TechDraw::DrawSVGTemplate", pref + "Mall")
    tpl.Template = mall
    page = doc.addObject("TechDraw::DrawPage", pref + "Blad")
    page.Label = "Oversikt %s" % nummer
    page.Template = tpl
    doc.recompute()
    page.ViewObject.show()
    pump(0.5)

    allt = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    grupp = doc.getObject("Sammanstallning")
    delar = [o for o in (grupp.Group if grupp else []) if hasattr(o, "Pos")] or allt
    raknare = [0]

    def nytt(typ, namn):
        raknare[0] += 1
        return doc.addObject(typ, "%s%s%d" % (pref, namn, raknare[0]))

    def kanter(v):
        i = 0
        while True:
            try:
                if v.getEdgeByIndex(i) is None:
                    return i
            except Exception:
                return i
            i += 1

    def lada(kroppar, d, x):
        d, x = V(*d).normalize(), V(*x).normalize()
        y = d.cross(x)
        xs, ys = [], []
        for o in kroppar:
            bb = o.Shape.BoundBox
            if not bb.isValid():
                continue
            for p in (V(p_, q_, r_) for p_ in (bb.XMin, bb.XMax) for q_ in (bb.YMin, bb.YMax) for r_ in (bb.ZMin, bb.ZMax)):
                xs.append(p.dot(x))
                ys.append(p.dot(y))
        return (max(xs) - min(xs), max(ys) - min(ys)) if xs else (100.0, 100.0)

    class Vy:
        def __init__(self, namn, riktning, x, lage, skala, kallor):
            self.namn, self.n = namn, skala
            kroppar = delar if kallor == "delar" else (kallor if isinstance(kallor, list) else allt)
            self.w, self.h = (q / skala for q in lada(kroppar, riktning, x))
            v = nytt("TechDraw::DrawViewPart", "Vy")
            page.addView(v)
            v.Source = kroppar
            v.Direction, v.XDirection = V(*riktning), V(*x)
            v.ScaleType, v.Scale = "Custom", 1.0 / skala
            v.X, v.Y = lage
            self.v, self.s, self.c = v, 1.0 / skala, None
            doc.recompute()
            for _ in range(600):
                pump(0.05)
                if v.getVisibleEdges():
                    break
            vo = v.ViewObject
            vo.LineWidth, vo.HiddenWidth, vo.FaceColor = 0.25, 0.13, (1.0, 1.0, 1.0)

        def centrerad(self, p):
            """Modellpunktens läge i vyn: oskalat, relativt vyns mitt (kalibrerat med en osynlig kosmetisk linje)."""
            p = V(*p)
            if self.c is None:
                tag = self.v.makeCosmeticLine3D(p, p + V(self.v.XDirection).normalize() * 0.01)
                ce = self.v.getCosmeticEdge(tag)
                f = ce.Format
                f["visible"] = False
                ce.Format = f
                pp = self.v.projectPoint(p)
                self.c = (pp.x - ce.Start.x, pp.y - ce.Start.y)
            pp = self.v.projectPoint(p)
            return (pp.x - self.c[0], pp.y - self.c[1])

        def papper(self, p):
            cx, cy = self.centrerad(p)
            return (self.v.X.Value + self.s * cx, self.v.Y.Value + self.s * cy)

        def _matt(self, a_, b_, typ, etikett):
            tag = self.v.makeCosmeticLine3D(V(*a_), V(*b_))
            ce = self.v.getCosmeticEdge(tag)
            ce.Format = {"style": 0, "weight": 0.1, "color": (0, 0, 0, 1.0), "visible": False}
            self.v.recompute()
            d = nytt("TechDraw::DrawViewDimension", "Matt")
            d.Type, d.MeasureType = typ, "Projected"
            d.References2D = [(self.v, "Edge%d" % (kanter(self.v) - 1))]
            page.addView(d)
            d.X, d.Y = etikett[0] - self.v.X.Value, etikett[1] - self.v.Y.Value
            d.FormatSpec = "%.1w"
            vo = d.ViewObject
            vo.Font, vo.Fontsize, vo.Arrowsize, vo.LineWidth = FONT, 3.0, 2.0, 0.13
            return d

        def matt(self, a_, b_, axel="x", avstand=8.0, fran=None):
            """Mått mellan två modellpunkter längs vyns x eller y; texten `avstand` mm från linjen genom `fran`
            (standard: första punkten), vinkelrätt på papperet."""
            pa, pb = self.papper(a_), self.papper(b_)
            f = self.papper(fran if fran is not None else a_)
            if axel == "x":
                return self._matt(a_, b_, "DistanceX", ((pa[0] + pb[0]) / 2, f[1] + avstand))
            return self._matt(a_, b_, "DistanceY", (f[0] + avstand, (pa[1] + pb[1]) / 2))

        def kedja(self, pts, axel="x", avstand=8.0, fran=None):
            """Måttkedja genom punkterna i ordning (t.ex. stolpar c/c, trappans delar)."""
            for p, q in zip(pts, pts[1:]):
                self.matt(p, q, axel, avstand, fran if fran is not None else pts[0])

        def bubbla(self, txt, p, dx=-10.0, dy=-10.0, form="Circular"):
            """Märkning (t.ex. R/1) med kort fylld pil mot punkten; bubblan dx, dy mm från punkten."""
            b = nytt("TechDraw::DrawViewBalloon", "Bubbla")
            b.SourceView = self.v
            page.addView(b)
            ox, oy = self.centrerad(p)
            b.Text, b.BubbleShape = txt, form
            typer = b.getEnumerationsOfProperty("EndType")
            b.EndType = next((t for t in typer if "arrow" in t.lower() and "fill" in t.lower()), b.EndType)
            if hasattr(b, "EndTypeScale"):
                b.EndTypeScale = 0.6
            b.OriginX, b.OriginY = ox, oy
            b.X, b.Y = ox + dx / self.s, oy + dy / self.s
            b.KinkLength = 0.0
            vo = b.ViewObject
            vo.Font, vo.Fontsize, vo.LineWidth = FONT, 3.5, 0.13
            return b

        def stomlinje(self, namn, a_, b_, bubbla="a", avstand=6.0):
            """Stomlinje (streckad, tunn) mellan två modellpunkter med namnet i en cirkel `avstand` mm utanför
            ändpunkten: bubbla "a", "b" eller "bada"."""
            tag = self.v.makeCosmeticLine3D(V(*a_), V(*b_))
            ce = self.v.getCosmeticEdge(tag)
            ce.Format = {"style": 4, "weight": 0.13, "color": (0.35, 0.35, 0.35, 1.0), "visible": True}
            pa, pb = self.papper(a_), self.papper(b_)
            L = max(((pb[0] - pa[0]) ** 2 + (pb[1] - pa[1]) ** 2) ** 0.5, 1e-9)
            ux, uy = (pb[0] - pa[0]) / L, (pb[1] - pa[1]) / L
            for slut, p_, sg in (("a", pa, -1), ("b", pb, 1)):
                if bubbla in (slut, "bada"):
                    c = (p_[0] + sg * ux * avstand, p_[1] + sg * uy * avstand)
                    b = nytt("TechDraw::DrawViewBalloon", "Stom")
                    b.SourceView = self.v
                    page.addView(b)
                    ox, oy = (c[0] - self.v.X.Value) / self.s, (c[1] - self.v.Y.Value) / self.s
                    b.Text, b.BubbleShape = namn, "Circular"
                    b.OriginX, b.OriginY, b.X, b.Y = ox, oy, ox, oy        # ingen ledare: cirkeln står vid linjen
                    b.KinkLength = 0.0
                    typer = b.getEnumerationsOfProperty("EndType")
                    b.EndType = next((x for x in typer if "none" in x.lower() or "no " in x.lower()), b.EndType)
                    vo = b.ViewObject
                    vo.Font, vo.Fontsize, vo.LineWidth = FONT, 3.2, 0.18
            return tag

        def stomnat(self, x=None, y=None, z=0.0, marginal=1500.0, bubbla="a", avstand=6.0):
            """Stomnät i ett vågrätt plan: `x` = {namn: x-koordinat} (linjer längs y), `y` = {namn: y} (linjer längs
            x), över hela nätets utsträckning plus `marginal` mm. Bubblorna i början (lägsta koordinaten) med "a",
            i slutet med "b". Exempel: plan.stomnat(x={"1": 0, "2": 6000}, y={"A": 0, "B": 4800}, z=0)."""
            x, y = x or {}, y or {}
            xs, ys = list(x.values()) or [0.0], list(y.values()) or [0.0]
            x0, x1, y0, y1 = min(xs) - marginal, max(xs) + marginal, min(ys) - marginal, max(ys) + marginal
            for n, xv in x.items():
                self.stomlinje(n, (xv, y0, z), (xv, y1, z), bubbla, avstand)
            for n, yv in y.items():
                self.stomlinje(n, (x0, yv, z), (x1, yv, z), bubbla, avstand)

        def text(self, txt, p, dx=0.0, dy=0.0, storlek=2.6):
            px, py = self.papper(p)
            return r.text(txt, (px + dx, py + dy), storlek)

        def niva(self, txt, p, dx=20.0, storlek=2.6):
            """Nivåtext med ▽ vid punktens höjd i en fasad eller ett snitt."""
            px, py = self.papper(p)
            return r.text("▽ " + txt, (px + dx, py + 1.5), storlek)

    class Ritning:
        def __init__(self):
            self.vyer, self.noterna = [], []
            self.nasta_y = 395.0

        def vy(self, namn, riktning, x, lage=None, skala=None, kallor="alla", rubrik=True):
            skala = float(skala or skala0)
            if lage is None:                                   # staplas uppifrån i vänsterkolumnen
                w, h = (q / skala for q in lada(delar if kallor == "delar" else allt, riktning, x))
                lage = (45 + w / 2, self.nasta_y - h / 2)
                self.nasta_y -= h + 30
            vy = Vy(namn, riktning, x, lage, skala, kallor)
            if rubrik:
                self.text("%s  1:%g" % (namn, skala), (vy.v.X.Value, vy.v.Y.Value - vy.h / 2 - 12), 3.5)
            self.vyer.append(vy)
            return vy

        def text(self, txt, lage, storlek=2.6):
            t = nytt("TechDraw::DrawViewAnnotation", "Text")
            page.addView(t)
            t.Text = txt if isinstance(txt, list) else [txt]
            t.TextSize = storlek
            t.X, t.Y = lage
            if hasattr(t, "Font"):
                t.Font = FONT
            return t

        def noter(self, rader, lage=(470, 210), storlek=2.6):
            self.noterna = list(rader)
            return self.text(self.noterna, lage, storlek)

    r = Ritning()
    skript["rita"](r)
    # ---- titelblock
    adr = list(u.get("adress") or []) + ["", "", ""]
    obj = list(a.get("objekt") or skript.get("OBJEKT", [])) + ["", "", ""]
    skalor = sorted({vy.n for vy in r.vyer})
    et = dict(tpl.EditableTexts)
    et.update(dict(Foretag=u.get("foretag") or "", Adress1=adr[0], Adress2=adr[1], Adress3=adr[2], Uppdrag=a.get("uppdrag", ""),
                   RitadAv=u.get("ritad_av", ""), Datum=a.get("datum") or os.environ.get("FC_DATUM") or time.strftime("%Y-%m-%d"), Handlaggare=u.get("handlaggare", ""),
                   Ansvarig=u.get("ansvarig", ""), Objekt1=obj[0], Objekt2=obj[1], Objekt3=obj[2],
                   Skala="  ".join("1:%g" % k for k in skalor), Nummer=nummer, Bet="", StomnatNummer=nummer, Systemlinje="",
                   Etapp="1", Antal="1"))
    tpl.EditableTexts = et
    doc.recompute()
    pump(1.5)
    doc.save()
    import TechDrawGui
    bas = os.path.join(utmapp, os.path.splitext(os.path.basename(a["ritskript"]))[0])
    page.ViewObject.show()
    pump(1.0)
    tmp = bas + "_tmp.pdf"
    TechDrawGui.exportPageAsPdf(page, tmp)
    fel = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
    if fel:
        logg("OBS: objekt med fel:", fel)
    logg("Översikt %s: %d vyer, %d mått, %d bubblor" % (nummer, len(r.vyer),
         len([v for v in page.Views if v.TypeId == "TechDraw::DrawViewDimension"]),
         len([v for v in page.Views if v.TypeId == "TechDraw::DrawViewBalloon"])))
    return dict(tmp=tmp, bas=bas)


if __name__ == "__fcjobb__":
    import fcapi
    fcapi.kor_jobb(_jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    a = vars(args())
    a["fil"], a["ritskript"] = os.path.abspath(a["fil"]), os.path.abspath(a["ritskript"])
    for f in (a["fil"], a["ritskript"]):
        if not os.path.exists(f):
            raise SystemExit("Filen finns inte: " + f)
    r = fcapi.kor(__file__, a)
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    with pymupdf.open(r["tmp"]) as d:
        d.save(r["bas"] + ".pdf")
        d[0].get_pixmap(dpi=110).save(r["bas"] + ".png")
    os.remove(r["tmp"])
    print("PDF: %s.pdf  PNG: %s.png" % (r["bas"], r["bas"]))
