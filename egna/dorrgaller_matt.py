"""Tilläggsmått till sammanställningsritningen för solgallret (egna/konstruktioner/dorrgaller.py).

sammanstallning.py sätter bara ut totalmått och hålgrupper. Det här skriptet öppnar den färdiga ritningen och
lägger till: måttkedja längs underkanten (bockpunkterna 117-233-233-117 och öppningen 700), kedja längs höger
sida (105-210-210-210-210-105 och öppningen 1050), ringens Ø160, samt en detalj B (skala 1:1) av den bockade
foten ur snitt A-A med lyft, bock, fot, godstjocklek och skruvhål. Snitt A-A flyttas åt höger för att ge
plats åt kedjan, bubblorna sänks under kedjan. Exporterar PDF och PNG på nytt.

    python3 egna/dorrgaller_matt.py ut/G1_solgaller.FCStd
"""
import os, sys, math

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".claude", "skills", "freecad-styrning", "scripts")
sys.path.insert(0, SKILL)
import fcapi

FONT = "Arial Narrow"
SVART = (0.0, 0.0, 0.0)


def _jobb():
    import FreeCAD as App
    import FreeCADGui as Gui
    from FreeCAD import Vector as V
    from fcapi import logg, pump

    def stall_in():
        for grp, typ, k, val in [("Dimensions", "Int", "ArrowStyle", 2), ("Dimensions", "Float", "FontSize", 3.4),
                                 ("Dimensions", "String", "FontName", FONT), ("Labels", "String", "LabelFont", FONT),
                                 ("Labels", "Float", "LabelSize", 3.0)]:
            getattr(App.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/" + grp), "Set" + typ)(k, val)
        pg = App.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/Colors")
        for k in ("PageColor", "FaceColor"):
            pg.SetUnsigned(k, 0xFFFFFFFF)
        for k in ("NormalColor", "HiddenColor", "SectionColor", "CenterColor", "VertexColor"):
            pg.SetUnsigned(k, 0x000000FF)

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
        """Pappersberäkning och mått på en befintlig TechDraw-vy (samma kalibrering som i sammanstallning.py)."""

        def __init__(self, doc, page, v):
            self.doc, self.page, self.v, self.s, self.c = doc, page, v, float(v.Scale), None

        def klar(self):
            for _ in range(600):
                pump(0.05)
                if self.v.getVisibleEdges():
                    return True
            raise RuntimeError("Vyn %s räknades aldrig klart" % self.v.Name)

        def _kalibrera(self, p):
            tag = self.v.makeCosmeticLine3D(p, p + V(0.01, 0.01, 0.01))
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

        def linje(self, a, b):
            tag = self.v.makeCosmeticLine3D(a, b)
            ce = self.v.getCosmeticEdge(tag)
            ce.Format = {"style": 0, "weight": 0.1, "color": SVART + (1.0,), "visible": False}
            self.v.recompute()
            return "Edge%d" % (antal_kanter(self.v) - 1)

        def matt(self, typ, a, b, etikett, namn="Matt", fmt=None):
            d = self.doc.addObject("TechDraw::DrawViewDimension", namn)
            d.Type, d.MeasureType = typ, "Projected"
            d.References2D = [(self.v, self.linje(V(*a), V(*b)))]
            self.page.addView(d)
            d.X, d.Y = etikett[0] - self.v.X.Value, etikett[1] - self.v.Y.Value
            stil(d)
            if fmt:
                d.FormatSpec = fmt
            return d

        def kedja(self, typ, punkter, lage, namn):
            """Kedja av mått mellan punkterna i tur och ordning; lage = pappersläget tvärs kedjan."""
            ut = []
            for a, b in zip(punkter, punkter[1:]):
                pa, pb = self.papper(V(*a)), self.papper(V(*b))
                if typ == "DistanceX":
                    et = ((pa[0] + pb[0]) / 2, lage)
                else:
                    et = (lage, (pa[1] + pb[1]) / 2)
                ut.append(self.matt(typ, a, b, et, namn))
            return ut

    def symbol(doc, page, namn, svgtext, x0, y0, w, h):
        s = doc.addObject("TechDraw::DrawViewSymbol", namn)
        s.Symbol = svgtext
        page.addView(s)
        s.Scale = 96.0 / 90.0
        s.X, s.Y = x0 + w / 2, y0 - h / 2
        return s

    def rubrik_svg(text, skala):
        w, h = 24.0, 11.0
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" viewBox="0 0 %g %g">'
                '<text x="%g" y="4.2" font-family="%s" font-size="4.2" text-anchor="middle" fill="#000">%s</text>'
                '<line x1="%g" y1="5.4" x2="%g" y2="5.4" stroke="#000" stroke-width="0.35"/>'
                '<text x="%g" y="9.6" font-family="%s" font-size="3.0" text-anchor="middle" fill="#000">%s</text></svg>'
                % (w, h, w, h, w / 2, FONT, text, w / 2 - 6, w / 2 + 6, w / 2, FONT, skala)), w, h

    def kor(a):
        stall_in()
        fil = a["fil"]
        doc = App.openDocument(fil)
        Gui.getDocument(doc.Name)
        page = next(o for o in doc.Objects if o.TypeId == "TechDraw::DrawPage")
        fram_v = doc.getObject("Framvy")
        snitt_v = doc.getObject("SnittA")
        sh = doc.getObject("Variabler")
        W, H, lyft, fot, bock, hd = (float(sh.get(k)) for k in ("Bredd", "Hojd", "Lyft", "Fot", "Bock", "HalD"))
        T, RING = 5.0, 160.0
        yc = -(lyft + T / 2)
        # ta bort mått/vyer från en tidigare körning av det här skriptet
        gamla = [o.Name for o in doc.Objects if o.Name.startswith(("Tm", "DetaljB", "RubrikDetaljB"))]
        for n in gamla:
            if doc.getObject(n) is not None:
                doc.removeObject(n)
        logg("Rensade tidigare tilläggsobjekt:", len(gamla))
        doc.recompute()
        page.ViewObject.show()
        pump(1.0)
        fram, snitt = Vy(doc, page, fram_v), Vy(doc, page, snitt_v)
        fram.klar(); snitt.klar()
        s = fram.s
        logg("Framvy skala 1:%g vid (%.1f, %.1f); snitt 1:%g" % (1 / s, fram_v.X.Value, fram_v.Y.Value, 1 / snitt.s))

        # ---- snitt A-A åt höger, så att kedjan längs gallrets högra sida får plats
        dx_snitt = 275.0 - snitt_v.X.Value
        snitt_v.X = 275.0
        rub = doc.getObject("RubrikSnittA")
        if rub is not None:
            rub.X = rub.X.Value + dx_snitt
        # ---- positionsbubblorna 30 mm nedåt (under måttkedjan)
        for o in doc.Objects:
            if o.TypeId == "TechDraw::DrawViewBalloon" and o.SourceView == fram_v:
                o.Y = o.Y.Value - 30.0 / s
        doc.recompute()
        pump(0.5)

        # ---- framvyn: lådan i papper
        x0, x1 = fram.papper(V(-W / 2 - bock - fot, yc, 0))[0], fram.papper(V(W / 2 + bock + fot, yc, 0))[0]
        y0, y1 = fram.papper(V(0, yc, -H / 2 - bock - fot))[1], fram.papper(V(0, yc, H / 2 + bock + fot))[1]
        # kedja längs underkanten: bockpunkterna (öppningens kant) 117-233-233-117 och öppningen 700
        zb = -H / 2
        dxb = round(W / 3)
        pk = [(-W / 2, yc, zb), (-dxb, yc, zb), (0, yc, zb), (dxb, yc, zb), (W / 2, yc, zb)]
        fram.kedja("DistanceX", pk, y0 - 8.0, "TmBock")
        fram.matt("DistanceX", pk[0], pk[-1], ((x0 + x1) / 2, y0 - 15.0), "TmBredd")
        # kedja längs höger sida: 105-210-210-210-210-105 och öppningen 1050
        xb = W / 2
        dzb = round(H / 5)
        pz = [(xb, yc, -H / 2), (xb, yc, -2 * dzb), (xb, yc, -dzb), (xb, yc, 0), (xb, yc, dzb), (xb, yc, 2 * dzb), (xb, yc, H / 2)]
        fram.kedja("DistanceY", pz, x1 + 7.0, "TmSida")
        fram.matt("DistanceY", pz[0], pz[-1], (x1 + 14.0, (y0 + y1) / 2), "TmHojd")
        # ringens diameter
        ring_edge = None
        for i in range(antal_kanter(fram_v)):
            e = fram_v.getEdgeByIndex(i)
            if e is not None and e.Curve.TypeId == "Part::GeomCircle" and abs(e.Curve.Radius - RING / 2) < 0.5:
                ring_edge = "Edge%d" % i
                break
        if ring_edge:
            d = doc.addObject("TechDraw::DrawViewDimension", "TmRing")
            d.Type, d.MeasureType = "Diameter", "Projected"
            d.References2D = [(fram_v, ring_edge)]
            page.addView(d)
            stil(d)
            d.FormatSpec = "Ø%.1w"
            d.ViewObject.RenderingExtent = "Reduced"
            px, py = fram.papper(V(RING * 0.9, yc, RING * 0.9))
            d.X, d.Y = px - fram_v.X.Value, py - fram_v.Y.Value
        else:
            logg("OBS: ringens cirkel hittades inte i framvyn - inget Ø-mått")
        nm = 4 + 1 + 6 + 1 + (1 if ring_edge else 0)

        # ---- detalj B av den översta foten ur snitt A-A, skala 1:1. Kosmetiska linjer hamnar fel i en detaljvy
        # (uppmätt 2026-10-17), så måtten sätts mellan vyns egna hörnpunkter (VertexN). Detaljens lokala
        # koordinater = snittets lokala - ankaret: x = modell-y + lyft + t/2, y = modell-z - ankarets z.
        zf = H / 2                                    # bockpunkten (öppningens överkant)
        za = zf + (bock + fot) / 2                    # ankarets z (detaljens mitt)
        mitt = V(0, yc, za)
        pm = snitt.papper(mitt)
        detalj_ok = False
        try:
            dv = doc.addObject("TechDraw::DrawViewDetail", "DetaljB")
            page.addView(dv)
            dv.BaseView = snitt_v
            dv.Source = snitt_v.Source
            dv.AnchorPoint = V((pm[0] - snitt_v.X.Value) / snitt.s, (pm[1] - snitt_v.Y.Value) / snitt.s, 0)
            dv.Radius = 48.0
            dv.Reference = "B"
            dv.ScaleType, dv.Scale = "Custom", 1.0
            dv.X, dv.Y = 335.0, 190.0
            doc.recompute()
            Vy(doc, page, dv).klar()
            dxp, dyp = dv.X.Value, dv.Y.Value
            verts = []
            while True:
                try:
                    vx = dv.getVertexByIndex(len(verts))
                except Exception:
                    break
                if vx is None:
                    break
                verts.append((vx.Point.x, vx.Point.y))
            lok = lambda y, z: (y - yc, z - za)       # modell (y, z) -> detaljens lokala koordinater

            def vertex(y, z):
                px, py = lok(y, z)
                for i, (vx, vy) in enumerate(verts):
                    if abs(vx - px) < 0.05 and abs(vy - py) < 0.05:
                        return "Vertex%d" % i
                raise RuntimeError("ingen hörnpunkt vid modell (y=%g, z=%g) = lokalt (%.2f, %.2f)" % (y, z, px, py))

            def dmatt(typ, p1, p2, lage, namn, fmt=None):
                d = doc.addObject("TechDraw::DrawViewDimension", namn)
                d.Type, d.MeasureType = typ, "Projected"
                d.References2D = [(dv, vertex(*p1)), (dv, vertex(*p2))]
                page.addView(d)
                d.X, d.Y = lage
                stil(d)
                if fmt:
                    d.FormatSpec = fmt
                return d
            yfram, ybak = -lyft - T, -lyft              # stångens framsida (mot betraktaren) / baksida (mot karmen)
            zh = zf + bock + fot / 2                    # skruvhålets mitt
            dmatt("DistanceY", (0, zf + bock), (0, zf + bock + fot), (30.0, 10.0), "TmFot")           # fot 40
            dmatt("DistanceY", (ybak, zf), (0, zf + bock), (21.0, -20.0), "TmBockL")                 # bock 20
            dmatt("DistanceX", (ybak, zf), (0, zf + bock), (2.5, -38.0), "TmLyft")                  # lyft 15
            dmatt("DistanceX", (yfram, zf), (ybak, zf), (-7.5, -38.0), "TmT")                       # t 5
            dmatt("DistanceY", (0, zh - hd / 2), (0, zh + hd / 2), (25.0, lok(0, zh)[1]), "TmHalD", fmt="Ø%.1w")
            sv, w_, h_ = rubrik_svg("B", "1:1")
            symbol(doc, page, "RubrikDetaljB", sv, dxp - w_ / 2, dyp - 52.0, w_, h_)
            nm += 5
            detalj_ok = True
        except Exception as e:
            logg("OBS: detalj B gick inte att göra (%s) - måtten läggs i snitt A-A i stället" % e)
            for n in [o.Name for o in doc.Objects if o.Name.startswith(("DetaljB", "RubrikDetaljB", "TmLyft", "TmT", "TmBockL", "TmFot", "TmHal"))]:
                if doc.getObject(n) is not None:
                    doc.removeObject(n)
            sx, sy = snitt_v.X.Value, snitt_v.Y.Value
            snitt.matt("DistanceX", (0, 0, zf + bock + fot * 0.75), (0, -lyft, zf - 30), (sx - 14, snitt.papper(V(0, 0, zf))[1]), "TmLyft")
            snitt.matt("DistanceY", (0, 0, zf + bock), (0, 0, zf + bock + fot), (sx + 12, snitt.papper(V(0, 0, zf + bock + fot / 2))[1]), "TmFot")
            snitt.matt("DistanceY", (0, -lyft, zf), (0, 0, zf + bock), (sx + 12, snitt.papper(V(0, 0, zf + bock / 2))[1] - 6), "TmBockL")
            nm += 3
        doc.recompute()
        pump(1.0)
        fel = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
        if fel:
            logg("OBS: objekt med fel:", fel)
        logg("Tilläggsmått: %d, detalj B: %s" % (nm, "ja (1:1)" if detalj_ok else "nej"))
        doc.save()
        logg("Sparat:", fil)
        page.ViewObject.show()
        pump(1.0)
        import TechDrawGui
        bas = os.path.splitext(fil)[0]
        tmp = bas + "_tmp.pdf"
        TechDrawGui.exportPageAsPdf(page, tmp)
        return dict(sidor=[tmp], bas=bas)

    fcapi.kor_jobb(kor)


def _efterbehandla(r):
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    bas = r["bas"]
    with pymupdf.open(r["sidor"][0]) as d:
        d.save(bas + ".pdf")
        d[0].get_pixmap(dpi=110).save(bas + ".png")
    os.remove(r["sidor"][0])
    print("PDF: %s  PNG: %s" % (bas + ".pdf", bas + ".png"))


if __name__ == "__fcjobb__":
    _jobb()
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    fil = os.path.abspath(sys.argv[1])
    if not os.path.exists(fil):
        raise SystemExit("Filen finns inte: " + fil)
    _efterbehandla(fcapi.kor(__file__, {"fil": fil}))
