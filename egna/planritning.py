"""Planritning R-101 för P. Hellstones entrétrappa: A2-blad med fasad (sett från gången) och plan i 1:20 av
översikten T/1 (trappa + räcken R/1–R/3), måttkedjor för trappan och räckenas stolpar, märkning R/1, R/2, R/3,
nivåer och noter. Ritas med TechDraw i T/1:s FCStd (bladet Planritning) och exporteras som PDF och PNG.

python3 egna/planritning.py ut/T1_Trappa_oversikt.FCStd      (efter sammanstallning.py bygg av trappa_oversikt.py)
"""
import os, sys, json, time, argparse

HIT = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HIT, "..", ".claude", "skills", "freecad-styrning", "scripts")
FONT = "osifont"
SKALA = 20.0


def _jobb(a):
    import FreeCAD as App
    from FreeCAD import Vector as V
    import fcapi, foretag
    from fcapi import logg, pump
    sys.path.insert(0, HIT)
    import trappa_hellstone as T
    import importlib.util

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

    doc = App.openDocument(a["fil"])
    gamla = [o for o in doc.Objects if o.TypeId.startswith("TechDraw::")]
    ordning = {"TechDraw::DrawPage": 1, "TechDraw::DrawSVGTemplate": 2}
    for n in [o.Name for o in sorted(gamla, key=lambda o: ordning.get(o.TypeId, 0))]:
        if doc.getObject(n) is not None:
            doc.removeObject(n)
    doc.recompute()

    u = foretag.las()
    mall = os.path.join(SKILL, "..", "mallar", "A2_tekla.svg")
    mall = foretag.mall_med_logga(mall, u.get("logga"), os.path.dirname(a["fil"])) if u.get("logga") else mall
    tpl = doc.addObject("TechDraw::DrawSVGTemplate", "MallPlan")
    tpl.Template = mall
    page = doc.addObject("TechDraw::DrawPage", "Planritning")
    page.Template = tpl
    doc.recompute()
    page.ViewObject.show()
    pump(0.5)

    kroppar = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]

    class Vy:
        def __init__(self, namn, d, x, px, py):
            v = doc.addObject("TechDraw::DrawViewPart", namn)
            page.addView(v)
            v.Source = kroppar
            v.Direction, v.XDirection = V(*d), V(*x)
            v.ScaleType, v.Scale = "Custom", 1.0 / SKALA
            v.X, v.Y = px, py
            self.v, self.s = v, 1.0 / SKALA
            self.c = None

        def klar(self):
            for _ in range(600):
                pump(0.05)
                if self.v.getVisibleEdges():
                    break
            vo = self.v.ViewObject
            vo.LineWidth, vo.HiddenWidth, vo.FaceColor = 0.25, 0.13, (1.0, 1.0, 1.0)

        def _start(self, p):
            tag = self.v.makeCosmeticLine3D(p, p + V(self.v.XDirection).normalize() * 0.01)
            ce = self.v.getCosmeticEdge(tag)
            f = ce.Format
            f["visible"] = False
            ce.Format = f
            return ce.Start

        def centrerad(self, p):
            """Modellpunktens läge i vyn: oskalat, relativt vyns mitt (kalibrerat en gång)."""
            p = V(*p)
            if self.c is None:
                st = self._start(p)
                pp = self.v.projectPoint(p)
                self.c = (pp.x - st.x, pp.y - st.y)
            pp = self.v.projectPoint(p)
            return (pp.x - self.c[0], pp.y - self.c[1])

        def papper(self, p):
            cx, cy = self.centrerad(p)
            return (self.v.X.Value + self.s * cx, self.v.Y.Value + self.s * cy)

        def matt(self, typ, a_, b_, etikett):
            """Mått mellan två modellpunkter (på en osynlig kosmetisk linje), etikett i bladmillimeter."""
            tag = self.v.makeCosmeticLine3D(V(*a_), V(*b_))
            ce = self.v.getCosmeticEdge(tag)
            ce.Format = {"style": 0, "weight": 0.1, "color": (0, 0, 0, 1.0), "visible": False}
            self.v.recompute()
            n, i = 0, 0
            while True:
                try:
                    self.v.getEdgeByIndex(i)
                except Exception:
                    break
                i += 1
            d = doc.addObject("TechDraw::DrawViewDimension", "MattPlan")
            d.Type, d.MeasureType = typ, "Projected"
            d.References2D = [(self.v, "Edge%d" % (i - 1))]
            page.addView(d)
            d.X, d.Y = etikett[0] - self.v.X.Value, etikett[1] - self.v.Y.Value
            d.FormatSpec = "%.1w"
            vo = d.ViewObject
            vo.Font, vo.Fontsize, vo.Arrowsize, vo.LineWidth = FONT, 3.0, 2.0, 0.13
            return d

        def kedja(self, typ, pts, fast, avst):
            """Måttkedja längs x (typ DistanceX) eller y (DistanceY) i vyns papper; pts = modellpunkter i ordning,
            etiketterna `avst` mm från linjen genom punkterna (vinkelrätt på papperet)."""
            for p, q in zip(pts, pts[1:]):
                pp, qq = self.papper(p), self.papper(q)
                if typ == "DistanceX":
                    lage = ((pp[0] + qq[0]) / 2, fast + avst)
                else:
                    lage = (fast + avst, (pp[1] + qq[1]) / 2)
                self.matt(typ, p, q, lage)

        def text(self, namn, rader, px, py, storlek=3.0):
            t = doc.addObject("TechDraw::DrawViewAnnotation", namn)
            page.addView(t)
            t.Text = rader
            t.TextSize = storlek
            t.X, t.Y = px, py
            if hasattr(t, "Font"):
                t.Font = FONT
            return t

        def bubbla(self, txt, p, dx, dy):
            b = doc.addObject("TechDraw::DrawViewBalloon", "Bubbla")
            b.SourceView = self.v
            page.addView(b)
            ox, oy = self.centrerad(p)
            b.Text, b.BubbleShape = txt, "Circular"
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

    # ---- vyer: fasad sett från gången (dörren till vänster som på fotot) och plan under (E-metoden)
    fasad = Vy("Fasad", (0, 1, 0), (-1, 0, 0), 175, 324)
    plan = Vy("Plan", (0, 0, 1), (-1, 0, 0), 175, 142)
    doc.recompute()
    fasad.klar()
    plan.klar()

    Zv, Zp, B, Yf = T.Z_VILPLAN, T.Z_PODEST, T.BREDD, T.Y_FRAM
    xv, x0, xp, xw = T.X_VILPLAN, 0.0, T.X_PODEST, T.X_VAGG
    # ---- planens mått: längs fasaden (ovanför, vid fasaden) och ut från fasaden (till höger om vilplanet)
    topp = plan.papper((xw, 0, 0))[1]
    plan.kedja("DistanceX", [(xw, 0, Zp), (xp, 0, Zp), (x0, 0, Zp), (xv, 0, Zp)], topp, 7)
    plan.matt("DistanceX", (xw, 0, Zp), (xv, 0, Zp), (plan.papper(((xw + xv) / 2, 0, 0))[0], topp + 14))
    hoger = plan.papper((xv, 0, 0))[0]
    plan.kedja("DistanceY", [(xv, 0, Zv), (xv, B, Zv), (xv, Yf, 0)], hoger, 20)
    plan.matt("DistanceY", (xv, 0, Zv), (xv, Yf, 0), (hoger + 28, plan.papper((xv, Yf / 2, 0))[1]))
    botten = plan.papper((0, Yf, 0))[1]
    plan.matt("DistanceX", (x0, Yf, 0), (xv, Yf, 0), (plan.papper((xv / 2, Yf, 0))[0], botten - 7))
    # ---- räckenas stolpar (c/c) – samma lägen som i R/1–R/3
    def par(modul):
        spec = importlib.util.spec_from_file_location(modul, os.path.join(HIT, "konstruktioner", modul + ".py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.parametrar()
    y1, xr2, xr3 = B - T.KANT, -T.KANT, xv + T.KANT
    st1 = [(x, y1, Zp) for x in par("racke_r1_ovre")["stolpar"]]
    st2 = [(xr2, Yf - x, Zv) for x in par("racke_r2_nedre_vanster")["stolpar"]]
    st3 = [(xr3, Yf - x, Zv) for x in par("racke_r3_nedre_hoger")["stolpar"]]
    yl = plan.papper((0, y1, 0))[1]
    plan.kedja("DistanceX", st1, yl, -8)                                    # under R/1, i innergården
    plan.kedja("DistanceY", sorted(st2, key=lambda p: p[1]), plan.papper((xr2, 0, 0))[0], -9)  # mot innergården
    plan.kedja("DistanceY", sorted(st3, key=lambda p: p[1]), plan.papper((xv, 0, 0))[0], 10)   # utanför R/3
    # ---- märkning och nivåer
    plan.bubbla("R/1", (xp + 600, y1, Zp), -6, -24)          # under stolpkedjan, fritt från måtten
    plan.bubbla("R/2", (xr2, Yf - 900, Zv), -12, -6)
    plan.bubbla("R/3", (xr3, 450, Zv), -14, -8)
    fasad.bubbla("R/1", (xp - 300, y1, Zp + 900 - 400), 10, 16)
    fasad.bubbla("R/2", (xr2, Yf - 900, 600), -14, 4)
    fasad.bubbla("R/3", (xr3, Yf - 1800, 1400), -14, 12)
    for (px, py), txt in ((plan.papper((xv / 2, B / 2, 0)), "VILPLAN +%g" % Zv), (plan.papper(((xp + xw) / 2, B / 2, 0)), "DÖRRPODEST +%g" % Zp),
                          (plan.papper((xp / 2, B / 2, 0)), "UPP 4 STEG"), (plan.papper((xv / 2, B + 900, 0)), "UPP 5 STEG"),
                          (plan.papper((xv / 2, Yf + 250, 0)), "GÅNG ±0"), (plan.papper(((x0 + xw) / 2, B + 1000, 0)), "INNERGÅRD ±0"),
                          (plan.papper((xw + 450, 150, 0)), "FASAD")):
        plan.text("Niva", [txt], px, py, 2.6)
    for z, txt in ((0, "±0 GÅNG"), (Zv, "+%g VILPLAN" % Zv), (Zp, "+%g DÖRRPODEST" % Zp)):
        px, py = fasad.papper((xv - 150, Yf, z))
        fasad.text("NivaFasad", ["▽ " + txt], px + 26, py + 1.5, 2.6)
    fasad.text("Rubrik", ["FASAD MOT INNERGÅRDEN  1:%g" % SKALA], 175, fasad.papper((0, Yf, 0))[1] - 8, 3.5)
    plan.text("Rubrik", ["PLAN  1:%g" % SKALA], 175, plan.papper((0, Yf, 0))[1] - 22, 3.5)
    noter = ["PLANRITNING – ENTRÉTRAPPA MED RÄCKEN R/1, R/2, R/3 (OFFERTUNDERLAG, EJ FÖR TILLVERKNING)",
             "UNDERLAG: FOTON OCH MÅTT I MAIL FRÅN P. HELLSTONE 2026-10-17",
             "TRAPPANS MÅTT ÄR ANTAGNA UR FOTON – KONTROLLMÄTS PÅ PLATS",
             "STEG %g/%g (ÖVRE LOPP) OCH %g/%g (NEDRE LOPP), RÄCKENA %g IN FRÅN STENKANT" % (T.R, T.G_OVRE, T.R, T.G_NEDRE, T.KANT),
             "STOLPAR FS20 NEDGJUTNA 100 I KÄRNBORRADE HÅL Ø40, c/c MAX 1300, MÅTT c/c STOLPE",
             "R/1 OCH R/2 HAR GEMENSAM HÖRNSTOLPE PÅ VILPLANET",
             "RÄCKESHÖJD 900 ÖVER STEGFRAMKANT, KNÄCKEN MITT ÖVER STOLPE 60 IN PÅ PODEST/VILPLAN",
             "TILLVERKNINGSRITNINGAR: R/1, R/2, R/3 (BLAD .1 OCH .2), GRIND G/1",
             "GRIND G/1 SITTER MELLAN GRANITSTOLPARNA VID GATAN (EJ I PLANEN)",
             "YTBEHANDLING: VARMFÖRZINKAD OCH PULVERLACKAD SVART RAL 9005 (ANTAGET)"]
    nt = plan.text("Noter", noter, 470, 210, 2.6)
    # ---- titelblock
    adr = list(u.get("adress") or []) + ["", "", ""]
    et = dict(tpl.EditableTexts)
    et.update(dict(Foretag=u.get("foretag") or "", Adress1=adr[0], Adress2=adr[1], Adress3=adr[2], Uppdrag="OFFERT",
                   RitadAv=u.get("ritad_av", ""), Datum=time.strftime("%Y-%m-%d"), Handlaggare=u.get("handlaggare", ""),
                   Ansvarig=u.get("ansvarig", ""), Objekt1="PLAN ENTRÉTRAPPA MED RÄCKEN, VILLA",
                   Objekt2="Patrik Hellstone, 0733 41 42 21", Objekt3="Adress enligt beställare", Skala="1:%g" % SKALA,
                   Nummer="R-101", Bet="", StomnatNummer="R-101", Systemlinje="", Etapp="1", Antal="1"))
    tpl.EditableTexts = et
    doc.recompute()
    pump(1.5)
    doc.save()
    import TechDrawGui
    bas = os.path.splitext(a["fil"])[0].replace("T1_Trappa_oversikt", "R-101_Planritning")
    page.ViewObject.show()
    pump(1.0)
    tmp = bas + "_tmp.pdf"
    TechDrawGui.exportPageAsPdf(page, tmp)
    fel = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
    if fel:
        logg("OBS: objekt med fel:", fel)
    logg("Planritning: %d mått" % len([v for v in page.Views if v.TypeId == "TechDraw::DrawViewDimension"]))
    return dict(tmp=tmp, bas=bas)


if __name__ == "__fcjobb__":
    sys.path.insert(0, SKILL)
    import fcapi
    fcapi.kor_jobb(_jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, SKILL)
    import fcapi
    ap = argparse.ArgumentParser()
    ap.add_argument("fil")
    r = fcapi.kor(__file__, {"fil": os.path.abspath(ap.parse_args().fil)})
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    with pymupdf.open(r["tmp"]) as d:
        d.save(r["bas"] + ".pdf")
        d[0].get_pixmap(dpi=110).save(r["bas"] + ".png")
    os.remove(r["tmp"])
    print("PDF: %s.pdf  PNG: %s.png" % (r["bas"], r["bas"]))
