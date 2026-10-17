"""Tillverkningsritning + DXF-utbredning för en plåtdel i FreeCAD (TechDraw, titelblock med företagsuppgifter).

  python ritning.py "<del.FCStd>" --namn "Dataställ" --nummer "DS-01" [--skala 2] [--skala-utbredning 2]
                    [--material "Stål S235, obehandlad"] [--foretag "Firma AB"] [--ritad-av AB] [--ut <mapp>]

Titelblockets företagsnamn och signatur kan också sättas med miljövariablerna FC_FORETAG och FC_RITAD_AV.

Delen ska ha en SheetMetal-utbredning (objektet "Utbredning", som datastall.py skapar) och gärna en
profilskiss "Profil" med namngivna mått; de namngivna måtten och vinklarna sätts ut i profilvyn
(motsvarar SolidWorks modellmått). Skalan väljs automatiskt om den inte anges.

Skapar bredvid delen (eller i --ut):
  <del>.FCStd               delen med ritningsbladen Blad1 (vyer + mått + noter) och Blad2 (utbredning)
  <del>.pdf                 båda bladen
  <del>_blad1.png/_blad2.png  för granskning
  <del>_utbredning.dxf      kontur + bocklinjer + bocknoter (egna lager)  -> bockning
  <del>_kontur.dxf          enbart kontur                                 -> laser
  <del>_granskning.txt      tillverkningsgranskning (dfm.py): fläns, radie, hål mot bock, avlastning, format
"""
import os, sys, math, time, argparse

SKALOR = [1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10, 15, 20, 25, 50]
GRA = (0.5, 0.5, 0.5)
MORK = (0.2, 0.2, 0.2)


def args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("del_")
    ap.add_argument("--namn", required=True)
    ap.add_argument("--nummer", required=True)
    ap.add_argument("--skala", type=float, default=None, help="1:N på blad 1 (standard: automatiskt)")
    ap.add_argument("--skala-utbredning", dest="skala_ut", type=float, default=None, help="1:N på blad 2 (standard: automatiskt)")
    ap.add_argument("--ut", default=None)
    ap.add_argument("--material", default="Stål S235, obehandlad")
    ap.add_argument("--ritad-av", dest="ritad_av", default=os.environ.get("FC_RITAD_AV", ""), help="signatur i titelblocket (standard: miljövariabeln FC_RITAD_AV)")
    ap.add_argument("--foretag", default=os.environ.get("FC_FORETAG", ""), help="företagsnamn i titelblocket (standard: miljövariabeln FC_FORETAG)")
    ap.add_argument("--ytbehandling", default="Ytbehandling enligt beställning.")
    ap.add_argument("--utan-kallor", dest="utan_kallor", action="store_true",
                    help="ingen not om var materialkvaliteten är verifierad (kallor.py)")
    ap.add_argument("--v-oppning", dest="v_oppning", type=float, default=None, help="kantpressens V-öppning för granskningen (standard: minsta V >= 8 t)")
    return ap.parse_args(argv)


def skaltext(n):
    """1:2 för förminskning, 2:1 för förstoring."""
    return "1:%s" % fmt(n) if n >= 1 else "%s:1" % fmt(1.0 / n)


def fmt(x, dec=1):
    s = ("%." + str(dec) + "f") % x
    s = s.rstrip("0").rstrip(".") if "." in s else s
    return s.replace(".", ",")


# =====================================================================================================
# Jobbet: körs inne i FreeCAD med GUI (PDF-exporten och mallen kräver TechDrawGui)
# =====================================================================================================
def _jobb():
    import FreeCAD as App, FreeCADGui as Gui, Part
    from FreeCAD import Vector as V
    import TechDrawGui
    from PySide import QtGui
    import fcapi, plat, dfm
    import pd as pdm
    from fcapi import logg, pump

    mall = os.path.join(os.path.dirname(fcapi.jobb()["skriptmapp"]), "mallar", "A3.svg")

    def textbredd(s, h):
        f = QtGui.QFont("Century Gothic")
        f.setPixelSize(100)
        return QtGui.QFontMetricsF(f).horizontalAdvance(s) / 100.0 * h * 1.371   # TechDraw ritar 3,5 som 4,8 mm (uppmätt i PDF)

    def utsträckning(shape, d, x):
        """Bredd och höjd på papperet (oskalat) för en vy med riktning d och x-riktning x."""
        d, x = V(d).normalize(), V(x).normalize()
        y = d.cross(x)
        bb = shape.optimalBoundingBox(False, False)
        hörn = [V(a, b, c) for a in (bb.XMin, bb.XMax) for b in (bb.YMin, bb.YMax) for c in (bb.ZMin, bb.ZMax)]
        xs, ys = [p.dot(x) for p in hörn], [p.dot(y) for p in hörn]
        return max(xs) - min(xs), max(ys) - min(ys)

    def antal_kanter(v):
        n = 0
        while True:
            try:
                if v.getEdgeByIndex(n) is None:
                    return n
            except Exception:
                return n
            n += 1

    class Vy:
        def __init__(self, doc, page, namn, kalla, d, x, skala, px, py):
            v = doc.addObject("TechDraw::DrawViewPart", namn)
            page.addView(v)
            v.Source = kalla
            v.Direction, v.XDirection = V(*d), V(*x)
            v.ScaleType, v.Scale = "Custom", 1.0 / skala
            v.X, v.Y = px, py
            self.v, self.doc, self.page, self.s = v, doc, page, 1.0 / skala

        def klar(self):
            for _ in range(300):
                pump(0.05)
                if self.v.getVisibleEdges():
                    break
            else:
                raise RuntimeError("Vyn %s räknades aldrig klart" % self.v.Name)
            self.c = None
            return True

        def _kalibrera(self, p):
            """Vyns mitt: kosmetiska linjer lagras oskalade relativt vyns mitt med Y uppåt, projectPoint ger
            oskalad projektion utan centrering - mitten är skillnaden. (Kosmetiska PUNKTER visas Y-speglade i
            vyer med negativ X-riktning i FreeCAD 1.0.1 och används därför inte.)"""
            tag = self.v.makeCosmeticLine3D(p, p + V(self.v.XDirection).normalize() * 0.01)
            ce = self.v.getCosmeticEdge(tag)
            st = ce.Start
            f = ce.Format
            f["visible"] = False
            ce.Format = f                       # lämnas kvar osynlig: att ta bort kosmetik när bladet visas kraschar
            pp = self.v.projectPoint(p)
            self.c = (pp.x - st.x, pp.y - st.y)

        def papper(self, p):
            if self.c is None:
                self._kalibrera(p)
            pp = self.v.projectPoint(p)
            return (self.v.X.Value + self.s * (pp.x - self.c[0]), self.v.Y.Value + self.s * (pp.y - self.c[1]))

        def linje(self, a, b, stil=1, bredd=0.18, farg=GRA, synlig=True):
            """Kosmetisk linje mellan modellpunkterna a och b. Returnerar kantnamnet (för mått)."""
            tag = self.v.makeCosmeticLine3D(a, b)
            ce = self.v.getCosmeticEdge(tag)
            ce.Format = {"style": stil if synlig else 0, "weight": bredd, "color": farg + (1.0,), "visible": synlig}
            self.v.recompute()
            return "Edge%d" % (antal_kanter(self.v) - 1)

        def matt(self, typ, a, b, etikett, namn="Matt"):
            """Mått mellan modellpunkterna a och b (typ Distance, DistanceX eller DistanceY), mätt på en osynlig
            kosmetisk linje a-b; etikett = pappersläge för måttexten. (Mått mellan kosmetiska punkter ritades
            spegelvända eller med förlängningslinjer åt fel håll i FreeCAD 1.0.1.)"""
            d = self.doc.addObject("TechDraw::DrawViewDimension", namn)
            d.Type, d.MeasureType = typ, "Projected"
            d.References2D = [(self.v, self.linje(a, b, synlig=False))]
            self.page.addView(d)
            d.X, d.Y = etikett[0] - self.v.X.Value, etikett[1] - self.v.Y.Value
            return stil(d)

        def vinkel(self, spets, a, b, etikett, namn="Vinkel"):
            """Vinkel mellan riktningarna spets->a och spets->b, mätt på två tunna kosmetiska linjer
            (Angle3Pt mellan kosmetiska punkter ritade bågen fel i FreeCAD 1.0.1)."""
            k1 = self.linje(spets, a, 1, 0.13)
            k2 = self.linje(spets, b, 1, 0.13)
            d = self.doc.addObject("TechDraw::DrawViewDimension", namn)
            d.Type, d.MeasureType = "Angle", "Projected"
            d.References2D = [(self.v, k1), (self.v, k2)]
            self.page.addView(d)
            d.X, d.Y = etikett[0] - self.v.X.Value, etikett[1] - self.v.Y.Value
            return stil(d)

    def stil(d):
        d.FormatSpec = "%.1w"
        vo = d.ViewObject
        vo.Font, vo.Fontsize, vo.Arrowsize, vo.LineWidth, vo.Color = "Century Gothic", 3.5, 2.5, 0.18, MORK
        return d

    def text(doc, page, s, x, y, h=3.5, rot=0.0, farg=GRA, vanster=True):
        """Text med vänsterkant (eller mitt) i x och baslinjen ungefär i y."""
        a = doc.addObject("TechDraw::DrawViewAnnotation", "Not")
        page.addView(a)
        a.Text, a.TextSize, a.Font, a.TextColor = [s], h, "Century Gothic", farg
        w = textbredd(s, h)
        a.X = x + (w / 2 if vanster else 0.0)
        a.Y = y + h * 0.35
        a.Rotation = rot
        return a

    def materialrader(a, tjocklek=None):
        """Material-raden i noterna och, om inte --utan-kallor, var kvaliteten är verifierad (kallor.py)."""
        rader = ["Material: %s" % a["material"]]
        if a.get("utan_kallor"):
            return rader
        import kallor
        info = kallor.material(a["material"], tjocklek)
        rader += kallor.bryt(kallor.text_material(info, a["material"], kort=True), 64)
        for s_ in kallor.notiser():
            logg("Källor OBS:", s_)
        for s_ in kallor.fel():
            logg("Källor FEL:", s_)
        return rader

    def textblock(doc, page, rader, x, y, h=3.5, farg=GRA, radavstand=6.0):
        """Flerradig not med vänsterkanten i x och SISTA radens baslinje ungefär i y; blocket växer uppåt så att
        fler rader (t.ex. källorna för materialet) inte hamnar under ramen. En annotation per block, så att
        raderna vänsterjusteras mot varandra (TechDraw placerar annotationens mitt)."""
        a = doc.addObject("TechDraw::DrawViewAnnotation", "Noter")
        page.addView(a)
        a.Text, a.TextSize, a.Font, a.TextColor = list(rader), h, "Century Gothic", farg
        a.LineSpace = int(round(radavstand / (h * 1.69) * 100))   # uppmätt: LineSpace 100 = 1,69 x textstorleken
        w = max(textbredd(r, h) for r in rader)
        a.X = x + w / 2
        a.Y = y + h * 0.35 + (len(rader) - 1) * radavstand / 2
        return a

    def nytt_blad(doc, namn, f):
        page = doc.addObject("TechDraw::DrawPage", namn)
        tpl = doc.addObject("TechDraw::DrawSVGTemplate", namn + "_mall")
        tpl.Template = mall
        page.Template = tpl
        et = tpl.EditableTexts
        et.update(f)
        tpl.EditableTexts = et
        return page

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

    def valj_skala(behov, onskad):
        if onskad:
            return onskad
        for n in SKALOR:
            if all(b / n <= m for b, m in behov):
                return n
        return SKALOR[-1]

    def profilmatt(doc, vy, kropp):
        """Namngivna längd- och vinkelmått i skissen Profil -> mått i profilvyn (som SolidWorks modellmått)."""
        sk = doc.getObject("Profil")
        if sk is None:
            return 0
        G = [sk.Placement.multVec(g.StartPoint) for g in sk.Geometry], [sk.Placement.multVec(g.EndPoint) for g in sk.Geometry]
        mitt = kropp.Shape.optimalBoundingBox(False, False).Center
        cpap = vy.papper(mitt)
        n = 0
        for c in sk.Constraints:
            if not c.Name:
                continue
            if c.Type == "Distance" and c.Second < 0:
                a, b = G[0][c.First], G[1][c.First]
                pa, pb = vy.papper(a), vy.papper(b)
                dx, dy = pb[0] - pa[0], pb[1] - pa[1]
                L = math.hypot(dx, dy)
                if abs(dy) < 1e-6 * L:
                    typ, nrm = "DistanceX", (0.0, 1.0)
                elif abs(dx) < 1e-6 * L:
                    typ, nrm = "DistanceY", (1.0, 0.0)
                else:
                    typ, nrm = "Distance", (-dy / L, dx / L)
                m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                if (m[0] - cpap[0]) * nrm[0] + (m[1] - cpap[1]) * nrm[1] < 0:
                    nrm = (-nrm[0], -nrm[1])
                avst = 9.0
                vy.matt(typ, a, b, (m[0] + nrm[0] * avst, m[1] + nrm[1] * avst), c.Name)
                n += 1
            elif c.Type == "Angle" and c.Second >= 0:
                i, j = c.First, c.Second
                gem = None
                for pi in (G[0][i], G[1][i]):
                    for pj in (G[0][j], G[1][j]):
                        if (pi - pj).Length < 1e-6:
                            gem = pi
                if gem is None:
                    continue
                di = (G[1][i] - G[0][i]).normalize()
                dj = (G[1][j] - G[0][j]).normalize()
                L = 18.0 / vy.s                                  # 18 mm på papperet
                qa, qb = gem + di * L, gem + dj * L
                ps, pa, pb = vy.papper(gem), vy.papper(qa), vy.papper(qb)
                bis = (pa[0] + pb[0] - 2 * ps[0], pa[1] + pb[1] - 2 * ps[1])
                bl = math.hypot(*bis) or 1.0
                vy.vinkel(gem, qa, qb, (ps[0] + bis[0] / bl * 13, ps[1] + bis[1] / bl * 13), c.Name)
                n += 1
        return n

    def plat_ritning(doc, a, bas, u, falt):
        """Plåtdel med SheetMetal-utbredning: blad 1 (planvy, profil, isometri) och blad 2 (utbredning)."""
        kropp = u.baseObject[0]
        rot = int(u.baseObject[1][0].replace("Face", "")) - 1
        doc.recompute()
        utb = plat.utbred(kropp.Shape, rot, kfaktor=u.KFactor)
        pd = plat.platdata(kropp, utb)
        bf = doc.getObject("Basflans")
        radie = bf.Radius.Value if bf is not None else (utb["bockar2d"][0]["radie"] if utb["bockar2d"] else 0)
        hornr = float(doc.Variabler.get("Hornradie")) if doc.getObject("Variabler") and doc.Variabler.getCellFromAlias("Hornradie") else 0.0
        logg("Plåt: t=%s r=%s massa=%.2f kg utbredning=%.1f x %.1f, bockar: %s" % (fmt(pd["tjocklek"]), fmt(radie), pd["massa"], pd["utbredning"][0], pd["utbredning"][1], ", ".join(pd["bockar"])))
        for f, n in plat.exportera_dxf(utb, bas).items():
            logg("DXF:", os.path.basename(f), n, "entiteter")
        am, sam = dfm.granska(utb, a["material"], a.get("v_oppning"), kfaktor=u.KFactor)
        gtext = dfm.rapport(am, sam, "Tillverkningsgranskning %s (%s)" % (os.path.basename(bas), a["material"]))
        with open(bas + "_granskning.txt", "w", encoding="utf-8") as f:
            f.write(gtext + "\n")
        logg(gtext)

        # ---------------- blad 1: planvy, profil, isometri
        sk = doc.getObject("Profil")
        nprof = sk.Placement.Rotation.multVec(V(0, 0, 1)) if sk else V(1, 0, 0)
        xprof = sk.Placement.Rotation.multVec(V(1, 0, 0)) if sk else V(0, 1, 0)
        PLAN = ((0, 0, 1), (1, 0, 0))
        PROF = (tuple(nprof), tuple(xprof))
        ISO = ((1, -1, 1), (1, 1, 0))
        wp, hp = utsträckning(kropp.Shape, *PLAN)
        wr, hr = utsträckning(kropp.Shape, *PROF)
        # planvy + profil bredvid varandra ovanför noterna; utrymme för mått runt om
        n = valj_skala([(wp + wr, 330.0), (hp, 150.0), (hr, 120.0)], a.get("skala"))
        logg("Skala blad 1: 1:%s" % fmt(n))
        page1 = nytt_blad(doc, "Blad1", falt)
        logg("Blad1 skapat")
        px = 30 + wp / n / 2
        plan = Vy(doc, page1, "Planvy", [kropp], *PLAN, n, px, 278 - 12 - hp / n / 2)
        rx = max(px + wp / n / 2 + 40 + wr / n / 2, 300)
        rx = min(rx, 405 - 18 - wr / n / 2)
        prof = Vy(doc, page1, "Profil", [kropp], *PROF, n, rx, 278 - 20 - hr / n / 2)
        wi, hi = utsträckning(kropp.Shape, *ISO)
        x0, x1 = px + wp / n / 2 + 12, 405.0                    # till höger om planvyn
        y0, y1 = 62.0, prof.v.Y.Value - hr / n / 2 - 16          # ovanför titelblocket, under profilens mått
        ni = next((k for k in SKALOR if k >= n and wi / k <= x1 - x0 and hi / k <= y1 - y0), 2 * n)
        iso = Vy(doc, page1, "Isometri", [kropp], *ISO, ni, (x0 + x1) / 2, (y0 + y1) / 2)
        logg("Vyer skapade, räknar")
        doc.recompute()
        for vy in (plan, prof, iso):
            vy.klar()
            vo = vy.v.ViewObject
            vo.LineWidth, vo.FaceColor = 0.35, (1.0, 1.0, 1.0)
        logg("Vyer klara")
        page1.ViewObject.show()
        pump(0.5)
        # mått: profilskissens namngivna mått + bredd och djup i planvyn
        nm = profilmatt(doc, prof, kropp)
        bb = kropp.Shape.optimalBoundingBox(False, False)
        y_bak = bb.YMax
        a_, b_ = V(bb.XMin, y_bak, bb.ZMax), V(bb.XMax, y_bak, bb.ZMax)
        pa = plan.papper(a_)
        plan.matt("DistanceX", a_, b_, ((pa[0] + plan.papper(b_)[0]) / 2, pa[1] + 9), "Bredd")
        djup = float(doc.Variabler.get("Djup")) if doc.getObject("Variabler") and doc.Variabler.getCellFromAlias("Djup") else bb.YLength
        c_, d_ = V(bb.XMin, y_bak - djup, bb.ZMax), V(bb.XMin, y_bak, bb.ZMax)
        pc, pdd = plan.papper(c_), plan.papper(d_)
        plan.matt("DistanceY", c_, d_, (pc[0] - 9, (pc[1] + pdd[1]) / 2), "Djup")
        logg("Mått blad 1: %d ur profilskissen + 2 i planvyn" % nm)
        # noter (skalan på blad 2 behövs i texten)
        L, W = pd["utbredning"]
        n2 = valj_skala([(L, 375.0), (W, 180.0)], a.get("skala_ut"))
        rader = materialrader(a, pd["tjocklek"]) + [
                 "Plåttjocklek %s mm, bockradie (inre) %s mm" % (fmt(pd["tjocklek"]), fmt(radie)),
                 "Utbredd plåt ca %.0f x %.0f mm, se blad 2" % pd["utbredning"],
                 "Vikt ca %s kg" % ("%.1f" % pd["massa"]).replace(".", ","),
                 "Mått i mm. Skala 1:%s (isometri 1:%s), blad 2 1:%s." % (fmt(n), fmt(ni), fmt(n2)),
                 a["ytbehandling"]]
        if hornr > 0:
            rader.insert(next(i for i, r in enumerate(rader) if r.startswith("Plåttjocklek")) + 1, "Hörnradier R%s (4 st)" % fmt(hornr))
        textblock(doc, page1, rader, 20, 14)
        doc.recompute()

        # ---------------- blad 2: utbredning
        falt2 = dict(falt, Ritningsnummer=a["nummer"] + " blad 2")
        page2 = nytt_blad(doc, "Blad2", falt2)
        rn = utb["rotnormal"]
        d_ut = (-rn).normalize()
        fb = utb["solid3d"].optimalBoundingBox(False, False)
        ax = [V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)]
        ax = [x for x in ax if abs(x.dot(d_ut)) < 0.5]
        lang = max(ax, key=lambda x: abs(V(fb.XLength, fb.YLength, fb.ZLength).dot(x)))
        rc = kropp.Shape.Faces[rot].CenterOfMass
        if (rc - fb.Center).dot(lang) < 0:          # rotytan (bottenplattan) till höger, som i SolidWorks
            lang = -lang
        hf = W / n2
        # Bocklinjerna som riktig geometri strax ovanför plåtens ovansida (annars döljs de i HLR, och kosmetiska
        # linjer ritas alltid streckade i FreeCAD 1.0.1 oavsett stil). Formateras per kant nedan.
        topp = max(p.Point.dot(d_ut) for p in utb["solid3d"].Vertexes)
        bl = []
        for b in utb["bockar3d"]:
            e = b["linje"]
            e = e.translated(d_ut * (topp + 0.05 - e.Vertexes[0].Point.dot(d_ut)))
            if b["riktning"] == "UPP":
                bl.append(e)
            else:                                   # NED: streckad, 5 mm streck och 2,5 mm mellanrum på papperet
                p1, p2 = e.Vertexes[0].Point, e.Vertexes[-1].Point
                rikt, Lb = (p2 - p1).normalize(), e.Length
                st, gap, t = 5.0 * n2, 2.5 * n2, 0.0
                while t < Lb - 1e-6:
                    bl.append(Part.makeLine(p1 + rikt * t, p1 + rikt * min(t + st, Lb)))
                    t += st + gap
        bobj = doc.getObject("Bocklinjer") or doc.addObject("Part::Feature", "Bocklinjer")
        bobj.Shape = Part.makeCompound(bl)
        logg("Bocklinjer som geometri: %d kanter" % len(bl))
        bobj.ViewObject.Visibility = False
        flat = Vy(doc, page2, "Utbredningsvy", [u, bobj], tuple(d_ut), tuple(lang), n2, 20 + L / n2 / 2, 278 - 14 - hf / 2)
        doc.recompute()
        flat.klar()
        flat.v.ViewObject.LineWidth, flat.v.ViewObject.FaceColor = 0.35, (1.0, 1.0, 1.0)
        page2.ViewObject.show()
        pump(0.5)
        # bocklinjer (UPP heldragen, NED streckad som i SolidWorks) och bocknoter längs linjerna
        kanter = []
        k = 0
        while True:
            try:
                e = flat.v.getEdgeByIndex(k)
            except Exception:
                break
            if e is None:
                break
            kanter.append((k, e))
            k += 1
        for b in utb["bockar3d"]:
            e = b["linje"]
            p1, p2 = e.Vertexes[0].Point, e.Vertexes[-1].Point
            q1, q2 = flat.papper(p1), flat.papper(p2)
            mx = ((q1[0] + q2[0]) / 2 - flat.v.X.Value) / flat.s        # vyns kantkoordinater är oskalade
            my = ((q1[1] + q2[1]) / 2 - flat.v.Y.Value) / flat.s
            # bocklinjens kanter i vyn: raka, parallella med linjen och på samma ställe (NED = flera streck)
            ux_, uy_ = (q2[0] - q1[0]), (q2[1] - q1[1])
            ul = math.hypot(ux_, uy_) or 1.0
            ux_, uy_ = ux_ / ul, uy_ / ul
            trf = []
            for k, ve in kanter:
                if ve.Curve.TypeId != "Part::GeomLine" or ve.Length > e.Length + 0.1:
                    continue
                c = ve.CenterOfMass
                for sy in (1, -1):                       # vyns Y-led kan vara speglad mot papperet
                    dx, dy = c.x - mx, sy * c.y - my
                    if abs(dx * uy_ - dy * ux_) < 0.3 and (b["riktning"] != "UPP" or abs(ve.Length - e.Length) < 0.1):
                        trf.append(k)
                        break
            for k in trf:
                flat.v.formatGeometricEdge(k, 1, 0.18, GRA, True)
            logg("Bocklinje %s: %d kant(er) i vyn" % (plat.bocknot(b), len(trf)))
            if not trf:
                logg("Obs: bocklinjen vid %.1f hittades inte i vyn - ritas utan format" % mx)
            vk = math.degrees(math.atan2(q2[1] - q1[1], q2[0] - q1[0]))
            if vk > 90.0 or vk <= -90.0:
                vk += 180.0
                q1, q2 = q2, q1
            ux, uy = math.cos(math.radians(vk)), math.sin(math.radians(vk))
            m = ((q1[0] + q2[0]) / 2 - uy * 3.0, (q1[1] + q2[1]) / 2 + ux * 3.0)
            t = text(doc, page2, plat.bocknot(b), m[0], m[1], 3.5, vk, MORK, vanster=False)
            t.Y = m[1]
        # totalmått och bocklinjernas lägen (kedja längs underkanten)
        sida = d_ut.cross(lang)                       # papperets y-riktning i modellen
        lo = [fb.XMin, fb.YMin, fb.ZMin]
        hi = [fb.XMax, fb.YMax, fb.ZMax]

        def hörn(sx, sy):
            p = V(*[(lo[k] + hi[k]) / 2 for k in range(3)])
            hl = V(fb.XLength / 2, fb.YLength / 2, fb.ZLength / 2)
            return p + V(lang.x * hl.x, lang.y * hl.y, lang.z * hl.z) * sx + V(sida.x * hl.x, sida.y * hl.y, sida.z * hl.z) * sy
        vu, hu, vo_, ho = hörn(-1, -1), hörn(1, -1), hörn(-1, 1), hörn(1, 1)
        q_vo, q_ho, q_hu = flat.papper(vo_), flat.papper(ho), flat.papper(hu)
        flat.matt("DistanceX", vo_, ho, ((q_vo[0] + q_ho[0]) / 2, q_vo[1] + 9), "Langd")
        flat.matt("DistanceY", hu, ho, (q_hu[0] + 9, (q_hu[1] + q_ho[1]) / 2), "Bredd")
        kedja = [vu]
        for b in utb["bockar3d"]:
            e = b["linje"]
            p = min((e.Vertexes[0].Point, e.Vertexes[-1].Point), key=lambda p: p.dot(sida))
            kedja.append(p)
        kedja.append(hu)
        kedja.sort(key=lambda p: flat.papper(p)[0])
        yk = flat.papper(vu)[1] - 9
        for i, (p, q) in enumerate(zip(kedja, kedja[1:])):
            flat.matt("DistanceX", p, q, ((flat.papper(p)[0] + flat.papper(q)[0]) / 2, yk), "Bocklage%d" % (i + 1))
        # hörnradie
        if hornr > 0:
            cir = []
            k = 0
            while True:
                try:
                    e = flat.v.getEdgeByIndex(k)
                except Exception:
                    break
                if e is None:
                    break
                if e.Curve.TypeId == "Part::GeomCircle" and abs(e.Curve.Radius - hornr) < 0.01:   # vyns kanter är oskalade
                    cir.append((k, e))
                k += 1
            if cir:
                k, e = max(cir, key=lambda t: t[1].Curve.Center.x + t[1].Curve.Center.y)    # uppe till höger
                r = doc.addObject("TechDraw::DrawViewDimension", "Hornradie")
                r.Type, r.MeasureType = "Radius", "Projected"
                r.References2D = [(flat.v, "Edge%d" % k)]
                page2.addView(r)
                c = e.Curve.Center
                stil(r)
                r.FormatSpec = "R%.1w"
                r.X, r.Y = c.x * flat.s + 6, c.y * flat.s + 9
                logg("Hörnradie R%s satt på Edge%d i utbredningen" % (fmt(hornr), k))
            else:
                logg("Obs: hörnradiens båge hittades inte i utbredningsvyn")
        textblock(doc, page2, ["Utbredning %s, plåt %s mm. Utbredd storlek ca %.0f x %.0f mm." % (a["namn"], fmt(pd["tjocklek"]), L, W),
                               "Bockradie inre %s mm. Bocknoter: riktning och vinkel vid varje bocklinje (NED streckad)." % fmt(radie),
                               "DXF för laser: %s, för bockning: %s" % (os.path.basename(bas + "_kontur.dxf"), os.path.basename(bas + "_utbredning.dxf")),
                               "Tillverkningsgranskning: %s, se %s" % (sam, os.path.basename(bas + "_granskning.txt"))],
                  20, min(flat.papper(vu)[1] - 24, 70) - 18)          # sista radens baslinje (fyra rader)
        doc.recompute()
        pump(1.0)
        return [page1, page2], dict(skala=n, skala_ut=n2, utbredning=pd["utbredning"], bockar=pd["bockar"], massa=pd["massa"], granskning=sam)

    # ------------------------------------------------------------------ Part Design-del (ingen utbredning)
    # Vyer enligt E-metoden (SS-ISO 128): framvy, ovanvy under, sidovy (sedd från vänster) till höger.
    VYER = {"Framvy": ((0, -1, 0), (1, 0, 0)), "Ovanvy": ((0, 0, 1), (1, 0, 0)), "Sidovy": ((-1, 0, 0), (0, -1, 0))}
    STEG, FORST = 8.0, 9.0                     # avstånd mellan måttnivåer och från vyn till första nivån (mm)

    def skisspunkt(sk, geo, pos):
        pl = sk.getGlobalPlacement()
        if geo == -1 and pos in (0, 1):
            return pl.multVec(V(0, 0, 0))
        if geo < 0:
            return None
        g = sk.Geometry[geo]
        if isinstance(g, Part.Point):
            q = V(g.X, g.Y, g.Z)
        elif pos == 1:
            q = g.StartPoint
        elif pos == 2:
            q = g.EndPoint
        elif pos == 3:
            q = g.Center
        else:
            return None
        return pl.multVec(q)

    def axel_av(v):
        """Global axel ('x', 'y', 'z') som v är parallell med, annars None."""
        for k, e in (("x", V(1, 0, 0)), ("y", V(0, 1, 0)), ("z", V(0, 0, 1))):
            if v.Length > 1e-9 and abs(abs(V(v).normalize().dot(e)) - 1) < 1e-6:
                return k
        return None

    def platta(shape):
        """(axel, tjocklek, underyta) om kroppen är en platta: två lika plana ändytor, alla andra ytor parallella
        med axeln och tjockleken mindre än halva minsta sidan. Annars None."""
        bb = shape.optimalBoundingBox(False, False)
        for ax in (V(0, 0, 1), V(0, 1, 0), V(1, 0, 0)):
            ok, andar = True, []
            for f in shape.Faces:
                yt = f.Surface
                if yt.TypeId == "Part::GeomPlane":
                    k = abs(f.normalAt(0, 0).dot(ax))
                    if abs(k - 1) < 1e-6:
                        andar.append(f)
                    elif k > 1e-6:
                        ok = False
                elif yt.TypeId == "Part::GeomCylinder":
                    ok = ok and abs(abs(yt.Axis.dot(ax)) - 1) < 1e-6
                else:
                    ok = False
            if ok and len(andar) == 2 and abs(andar[0].Area - andar[1].Area) < 1e-3:
                t = abs((andar[0].CenterOfMass - andar[1].CenterOfMass).dot(ax))
                sidor = [l for l, e in zip((bb.XLength, bb.YLength, bb.ZLength), (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1))) if abs(e.dot(ax)) < 0.5]
                if t < 0.5 * min(sidor):
                    return ax, t, min(andar, key=lambda f: f.CenterOfMass.dot(ax))
        return None

    def kontur_dxf(yta, ax, fil):
        """Plattans kontur (underytan sedd ovanifrån) i XY-planet med nedre vänstra hörnet i origo."""
        f = yta.copy()
        f.transformShape(App.Placement(V(0, 0, 0), App.Rotation(ax, V(0, 0, 1))).toMatrix())
        b = f.optimalBoundingBox(False, False)
        f.translate(V(-b.XMin, -b.YMin, -b.ZMin))
        return plat.skriv_dxf(fil, [("KONTUR", 7, list(f.Edges))]), (b.XLength, b.YLength)

    def del_matt(body, bb):
        """Måttkandidater: kroppens totalmått och skissernas namngivna mått (namn som börjar med _ hoppas
        över), i den vy som tittar längs skissens normal. Totalmått som en skiss redan ger tas bort."""
        lin, vinklar, diam, radier = [], [], {}, {}
        for sk in body.Group:
            if sk.TypeId != "Sketcher::SketchObject":
                continue
            rot = sk.getGlobalPlacement().Rotation
            nrm, sx, sy = rot.multVec(V(0, 0, 1)), rot.multVec(V(1, 0, 0)), rot.multVec(V(0, 1, 0))
            vy = next((k for k, (d, x) in VYER.items() if abs(abs(nrm.dot(V(*d))) - 1) < 1e-6), None)
            if vy is None:
                logg("Obs: skissen %s ligger inte i ett vyplan - måtten sätts inte ut" % sk.Name)
                continue
            for c in sk.Constraints:
                if not c.Name or c.Name.startswith("_"):
                    continue
                if c.Type in ("Distance", "DistanceX", "DistanceY"):
                    if c.Second < -1000 and c.FirstPos == 0:
                        a, b = skisspunkt(sk, c.First, 1), skisspunkt(sk, c.First, 2)
                    elif c.Second < -1000:
                        a, b = skisspunkt(sk, -1, 1), skisspunkt(sk, c.First, c.FirstPos)
                    elif c.SecondPos == 0:
                        continue                                      # punkt till linje: sätts inte ut
                    else:
                        a, b = skisspunkt(sk, c.First, c.FirstPos), skisspunkt(sk, c.Second, c.SecondPos)
                    if a is None or b is None:
                        continue
                    rikt = {"DistanceX": sx, "DistanceY": sy}.get(c.Type, b - a)
                    lin.append(dict(vy=vy, a=a, b=b, rikt=V(rikt), namn=c.Name, total=False))
                elif c.Type in ("Diameter", "Radius"):
                    r = c.Value / 2 if c.Type == "Diameter" else c.Value
                    (diam if c.Type == "Diameter" else radier).setdefault(round(r, 3), "⌀%.1w" if c.Type == "Diameter" else "R%.1w")
                elif c.Type == "Angle" and c.Second >= 0:
                    G = [(skisspunkt(sk, i, 1), skisspunkt(sk, i, 2)) for i in (c.First, c.Second)]
                    gem = next((p for p in G[0] for q in G[1] if (p - q).Length < 1e-6), None)
                    if gem is not None:
                        vinklar.append(dict(vy=vy, spets=gem, di=(G[0][1] - G[0][0]).normalize(), dj=(G[1][1] - G[1][0]).normalize(), namn=c.Name))
        for f in body.Group:
            if f.TypeId in ("PartDesign::Revolution", "PartDesign::Groove"):
                # rotationsprofilens avstånd till axeln = diametrar (syns som cirklar i vyn längs axeln)
                sk, ref = f.Profile[0], f.ReferenceAxis
                pl = sk.getGlobalPlacement()
                if ref[0] == sk:
                    p0, ax = pl.Base, pl.Rotation.multVec(V(0, 1, 0) if ref[1][0] == "V_Axis" else V(1, 0, 0))
                else:
                    p0, ax = V(0, 0, 0), {"X": V(1, 0, 0), "Y": V(0, 1, 0), "Z": V(0, 0, 1)}[ref[0].Role[0]]
                for g in sk.Geometry:
                    for q in (getattr(g, "StartPoint", None), getattr(g, "EndPoint", None)):
                        if q is None:
                            continue
                        w = pl.multVec(q) - p0
                        r = (w - ax * w.dot(ax)).Length
                        if r > 0.01:
                            diam.setdefault(round(r, 3), "⌀%.1w")
            elif f.TypeId == "PartDesign::Hole":
                r = round(f.Diameter.Value / 2, 3)
                diam[r] = f.ThreadSize if f.Threaded else "⌀%.1w"
            elif f.TypeId == "PartDesign::Fillet":
                radier.setdefault(round(f.Radius.Value, 3), "R%.1w")
        # totalmått
        tot = [dict(vy="Framvy", a=V(bb.XMin, bb.YMin, bb.ZMax), b=V(bb.XMax, bb.YMin, bb.ZMax), rikt=V(1, 0, 0), namn="TotX", sida="T"),
               dict(vy="Framvy", a=V(bb.XMin, bb.YMin, bb.ZMin), b=V(bb.XMin, bb.YMin, bb.ZMax), rikt=V(0, 0, 1), namn="TotZ", sida="L"),
               dict(vy="Ovanvy", a=V(bb.XMin, bb.YMin, bb.ZMax), b=V(bb.XMin, bb.YMax, bb.ZMax), rikt=V(0, 1, 0), namn="TotY", sida="L")]

        def nyckel(m):
            k = axel_av(m["rikt"])
            if k is None:
                return None
            return (k, round(min(getattr(m["a"], k), getattr(m["b"], k)), 2), round(max(getattr(m["a"], k), getattr(m["b"], k)), 2))
        finns = {nyckel(m) for m in lin}
        for t in tot:
            langd = abs((t["b"] - t["a"]).dot(t["rikt"]))
            if any(abs(2 * r - langd) < 0.01 for r in diam):          # rund del: diametern räcker
                continue
            if nyckel(t) not in finns:
                t["total"] = True
                lin.append(t)
        # dubbletter i samma vy (samma axel och samma ändlägen)
        ut, sett = [], set()
        for m in lin:
            m["varde"] = abs((m["b"] - m["a"]).dot(V(m["rikt"]).normalize()))
            k = (m["vy"], nyckel(m)) if nyckel(m) else None
            if k is not None and k in sett:
                continue
            sett.add(k)
            ut.append(m)
        return ut, vinklar, diam, radier

    def del_ritning(doc, a, bas, body, falt):
        """Part Design-kropp: ett blad med framvy, ovanvy, sidovy och isometri, totalmått, skissernas namngivna
        mått, hål- och radiemått med antal. En platta får också _kontur.dxf (laser)."""
        s = body.Shape
        bb = s.optimalBoundingBox(False, False)
        mitt = bb.Center
        storlek = {k: utsträckning(s, d, x) for k, (d, x) in VYER.items()}
        lin, vinklar, diam, radier = del_matt(body, bb)

        def rel(vy, p):
            """Oskalat pappersläge relativt vyns mitt (axelparallella vyer: projektionen av lådans mitt)."""
            d, x = VYER[vy]
            d, x = V(*d), V(*x)
            q = p - mitt
            return q.dot(x), q.dot(d.cross(x))

        for m in lin:                                   # vågrät eller lodrät på papperet, eller snett
            d, x = VYER[m["vy"]]
            r = m["rikt"]
            px, py = r.dot(V(*x)), r.dot(V(*d).cross(V(*x)))
            L = math.hypot(px, py) or 1.0
            m["typ"] = "DistanceX" if abs(py) < 1e-6 * L else ("DistanceY" if abs(px) < 1e-6 * L else "Distance")
            (ax, ay), (bx, by) = rel(m["vy"], m["a"]), rel(m["vy"], m["b"])
            if "sida" not in m:
                if m["typ"] == "DistanceX":
                    m["sida"] = "T" if (ay + by) / 2 >= -1e-6 else "B"
                elif m["typ"] == "DistanceY":
                    m["sida"] = "R" if (ax + bx) / 2 > 1e-6 else "L"

        def packa(n):
            """Måttnivåer per vy och sida (kortaste måttet närmast vyn, inga överlappande texter på en nivå).
            Returnerar marginalen (mm) som måtten tar på varje sida."""
            niv = {(k, sd): [] for k in VYER for sd in "TBLR"}
            for m in sorted([m for m in lin if m["typ"] != "Distance"], key=lambda m: m["varde"]):
                (ax, ay), (bx, by) = rel(m["vy"], m["a"]), rel(m["vy"], m["b"])
                if m["typ"] == "DistanceX":
                    lo, hi = min(ax, bx) / n, max(ax, bx) / n
                else:
                    lo, hi = min(ay, by) / n, max(ay, by) / n
                tw = textbredd(fmt(m["varde"]), 3.5) + 3
                mid = (lo + hi) / 2
                lo, hi = min(lo, mid - tw / 2), max(hi, mid + tw / 2)
                nivaer = niv[(m["vy"], m["sida"])]
                for i, upptaget in enumerate(nivaer):
                    if all(hi < u0 or lo > u1 for u0, u1 in upptaget):
                        upptaget.append((lo, hi))
                        m["niva"] = i
                        break
                else:
                    nivaer.append([(lo, hi)])
                    m["niva"] = len(nivaer) - 1
            return {k: (0.0 if not v else FORST - 3 + STEG * len(v)) for k, v in niv.items()}

        def placera(n):
            mg = packa(n)
            st = {k: (w / n, h / n) for k, (w, h) in storlek.items()}
            M = lambda vy, sd: mg[(vy, sd)]
            xl = 14 + max(M("Framvy", "L"), M("Ovanvy", "L"))
            fx = xl + st["Framvy"][0] / 2
            topp = 285 - max(M("Framvy", "T"), M("Sidovy", "T"))
            fy = topp - st["Framvy"][1] / 2
            oy = fy - st["Framvy"][1] / 2 - max(M("Framvy", "B"), M("Ovanvy", "T")) - 10 - st["Ovanvy"][1] / 2
            sx = fx + st["Framvy"][0] / 2 + M("Framvy", "R") + M("Sidovy", "L") + 16 + st["Sidovy"][0] / 2
            pos = {"Framvy": (fx, fy), "Ovanvy": (fx, oy), "Sidovy": (sx, fy)}
            ok = (oy - st["Ovanvy"][1] / 2 - M("Ovanvy", "B") >= 60 and sx + st["Sidovy"][0] / 2 + M("Sidovy", "R") <= 408
                  and fy - st["Sidovy"][1] / 2 - M("Sidovy", "B") >= 60)
            # isometrin: under sidovyn och till höger om ovanvyn, annars till höger om sidovyn
            ytor = [(fx + st["Ovanvy"][0] / 2 + M("Ovanvy", "R") + 12, 408, 60, fy - st["Sidovy"][1] / 2 - M("Sidovy", "B") - 10),
                    (sx + st["Sidovy"][0] / 2 + M("Sidovy", "R") + 12, 408, 60, 285)]
            return ok, pos, st, ytor

        if a.get("skala"):
            n = a["skala"]
            ok, pos, st, ytor = placera(n)
            if not ok:
                logg("Obs: vyerna får inte plats på A3 i skala %s" % skaltext(n))
        else:
            for n in [0.2, 0.5] + SKALOR:              # små delar i förstoring (5:1, 2:1) om vyerna ryms
                ok, pos, st, ytor = placera(n)
                if ok:
                    break
        logg("Skala: %s" % skaltext(n))
        page = nytt_blad(doc, "Blad1", falt)
        vyer = {k: Vy(doc, page, k, [body], *VYER[k], n, *pos[k]) for k in VYER}
        ISO = ((1, -1, 1), (1, 1, 0))
        wi, hi_ = utsträckning(s, *ISO)
        ni = None
        for x0, x1, y0, y1 in ytor:
            ni = next((k for k in [0.2, 0.5] + SKALOR if k >= n and wi / k <= x1 - x0 and hi_ / k <= y1 - y0), None)
            if ni and x1 - x0 >= 40 and y1 - y0 >= 30:
                vyer["Isometri"] = Vy(doc, page, "Isometri", [body], *ISO, ni, (x0 + x1) / 2, (y0 + y1) / 2)
                break
            ni = None
        if ni is None:
            logg("Obs: ingen plats för isometrin")
        doc.recompute()
        for vy in vyer.values():
            vy.klar()
            vy.v.ViewObject.LineWidth, vy.v.ViewObject.FaceColor = 0.35, (1.0, 1.0, 1.0)
        page.ViewObject.show()
        pump(0.5)
        # linjära mått på sina nivåer
        for m in lin:
            vy = vyer[m["vy"]]
            w, h = st[m["vy"]]
            X, Y = vy.v.X.Value, vy.v.Y.Value
            pa, pb = vy.papper(m["a"]), vy.papper(m["b"])
            if m["typ"] == "DistanceX":
                y = Y + h / 2 + FORST + STEG * m["niva"] if m["sida"] == "T" else Y - h / 2 - FORST - STEG * m["niva"]
                vy.matt("DistanceX", m["a"], m["b"], ((pa[0] + pb[0]) / 2, y), m["namn"])
            elif m["typ"] == "DistanceY":
                x = X + w / 2 + FORST + STEG * m["niva"] if m["sida"] == "R" else X - w / 2 - FORST - STEG * m["niva"]
                vy.matt("DistanceY", m["a"], m["b"], (x, (pa[1] + pb[1]) / 2), m["namn"])
            else:
                dx, dy = pb[0] - pa[0], pb[1] - pa[1]
                L = math.hypot(dx, dy) or 1.0
                nrm = (-dy / L, dx / L)
                mp = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                if (mp[0] - X) * nrm[0] + (mp[1] - Y) * nrm[1] < 0:
                    nrm = (-nrm[0], -nrm[1])
                vy.matt("Distance", m["a"], m["b"], (mp[0] + nrm[0] * FORST, mp[1] + nrm[1] * FORST), m["namn"])
        for v in vinklar:
            vy = vyer[v["vy"]]
            L = 18.0 / vy.s
            qa, qb = v["spets"] + v["di"] * L, v["spets"] + v["dj"] * L
            ps, pa, pb = vy.papper(v["spets"]), vy.papper(qa), vy.papper(qb)
            bis = (pa[0] + pb[0] - 2 * ps[0], pa[1] + pb[1] - 2 * ps[1])
            bl = math.hypot(*bis) or 1.0
            vy.vinkel(v["spets"], qa, qb, (ps[0] + bis[0] / bl * 13, ps[1] + bis[1] / bl * 13), v["namn"])
        # hål och radier: cirklar/bågar i varje vy med en känd radie, ett mått per radie och vy med antal
        nr, anvanda = 0, {}
        for namn, vy in vyer.items():
            if namn == "Isometri":
                continue
            grupper = {}
            k = 0
            while True:
                try:
                    e = vy.v.getEdgeByIndex(k)
                except Exception:
                    break
                if e is None:
                    break
                if e.Curve.TypeId == "Part::GeomCircle":
                    hel = e.isClosed()
                    for r, spec in (diam if hel else radier).items():
                        if abs(e.Curve.Radius - r) < 0.01:
                            g = grupper.setdefault((hel, r, spec), [])
                            c = e.Curve.Center
                            if all((c - q[1].Curve.Center).Length > 0.01 for q in g):
                                g.append((k, e))
                k += 1
            for (hel, r, spec), g in grupper.items():
                # radier vid bågen uppe till höger med texten strax utanför bågen, hål vid hålet nere till höger
                # med texten inåt mot vyns mitt (så att texterna inte krockar med varandra eller totalmåtten)
                k, e = max(g, key=lambda t: t[1].Curve.Center.x + (-1 if hel else 1) * t[1].Curve.Center.y)
                c = e.Curve.Center
                L = math.hypot(c.x, c.y)
                ux, uy = (c.x / L, c.y / L) if L > 1e-6 else (0.7071, 0.7071)
                inat = hel and L > r                      # cirkel runt vyns mitt (ytterkontur, centrumhål): texten utåt
                if inat:
                    ux, uy = -ux, -uy
                # koncentriska cirklar (hylsa, fläns): vrid varje nytt mått 35° så att texterna inte hamnar i rad
                rund = (round(c.x, 1), round(c.y, 1))
                vrid = math.radians(-35.0 * anvanda.get((namn, rund), 0))
                anvanda[(namn, rund)] = anvanda.get((namn, rund), 0) + 1
                ux, uy = ux * math.cos(vrid) - uy * math.sin(vrid), ux * math.sin(vrid) + uy * math.cos(vrid)
                nr += 1
                d = doc.addObject("TechDraw::DrawViewDimension", ("Diameter%d" if hel else "Radie%d") % nr)
                d.Type, d.MeasureType = ("Diameter" if hel else "Radius"), "Projected"
                d.References2D = [(vy.v, "Edge%d" % k)]
                page.addView(d)
                stil(d)
                d.FormatSpec = ("%d×" % len(g) if len(g) > 1 else "") + spec
                if "%" not in spec:                       # gänga (M10): texten som den är, annars visas inget
                    d.Arbitrary = True
                if hel:
                    try:
                        d.ViewObject.RenderingExtent = "Reduced"   # en pil mot cirkeln, ingen linje genom mitten
                    except Exception as ex:
                        logg("Obs: RenderingExtent:", ex)
                rp = r * vy.s + (8.0 if inat or not hel else 6.0)
                d.X, d.Y = c.x * vy.s + ux * rp, c.y * vy.s + uy * rp
        # DXF för platta, noter
        pl = platta(s)
        rader = materialrader(a, pl[1] if pl else None)
        if pl:
            antal, (lx, ly) = kontur_dxf(pl[2], pl[0], bas + "_kontur.dxf")
            logg("DXF: %s %d entiteter, %.1f x %.1f mm" % (os.path.basename(bas + "_kontur.dxf"), antal, lx, ly))
            rader.append("Plåttjocklek %s mm. Kontur för laser: %s" % (fmt(pl[1]), os.path.basename(bas + "_kontur.dxf")))
        fasar = sorted({f.Size.Value for f in body.Group if f.TypeId == "PartDesign::Chamfer"})
        if fasar:
            rader.append("Fasade kanter %s mm" % ", ".join(fmt(x) for x in fasar))
        gangor = sorted({f.ThreadSize for f in body.Group if f.TypeId == "PartDesign::Hole" and f.Threaded})
        if gangor:
            rader.append("Gängade hål %s (gängan inte ritad)" % ", ".join(gangor))
        massa = s.Volume * 1e-9 * pdm.STAL_DENSITET
        rader += ["Vikt ca %s kg (stål)" % ("%.1f" % massa).replace(".", ","),
                  "Mått i mm. Skala %s%s. Projektionsmetod E." % (skaltext(n), " (isometri %s)" % skaltext(ni) if ni else ""),
                  a["ytbehandling"]]
        textblock(doc, page, rader, 20, 14)
        return [page], dict(skala=n, massa=massa, platta=bool(pl))

    def huvud(a):
        fil = os.path.abspath(a["del_"])
        utmapp = os.path.abspath(a["ut"]) if a.get("ut") else os.path.dirname(fil)
        os.makedirs(utmapp, exist_ok=True)
        bas = os.path.join(utmapp, os.path.splitext(os.path.basename(fil))[0])
        doc = App.openDocument(fil)
        logg("Rensade gamla ritningsobjekt:", rensa(doc))
        falt = dict(Namn=a["namn"], Ritningsnummer=a["nummer"], Datum=time.strftime("%Y-%m-%d"), RitadAv=a["ritad_av"],
                    Filnamn=os.path.basename(bas), Foretag=a.get("foretag") or "")
        u = doc.getObject("Utbredning")
        if u is not None:
            blad, info = plat_ritning(doc, a, bas, u, falt)
        else:
            blad, info = del_ritning(doc, a, bas, pdm.hitta_kropp(doc), falt)
        doc.recompute()
        pump(1.0)
        # ---------------- kontroll och export
        for page in blad:
            for o in page.Views:
                if o.TypeId == "TechDraw::DrawViewDimension":
                    logg("  %-8s %-14s %-10s = %-8s %s" % (page.Name, o.Name, o.Type, fmt(o.getRawValue(), 2), o.FormatSpec))
            logg("%s: %d mått" % (page.Name, sum(1 for o in page.Views if o.TypeId == "TechDraw::DrawViewDimension")))
        fel = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
        if fel:
            logg("Obs: objekt med fel:", fel)
        ut_fcstd = bas + ".FCStd"
        doc.saveAs(ut_fcstd)
        logg("Sparat:", ut_fcstd)
        sidor = []
        for i, page in enumerate(blad, start=1):
            page.ViewObject.show()
            pump(0.8)
            p = bas + "_blad%d_tmp.pdf" % i
            TechDrawGui.exportPageAsPdf(page, p)
            sidor.append(p)
        return dict(sidor=sidor, bas=bas, **info)

    fcapi.kor_jobb(huvud)


def _efterbehandla(r):
    """Slå ihop bladen till en PDF och rendera PNG per blad (system-Python med PyMuPDF)."""
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    bas = r["bas"]
    ut = pymupdf.open()
    for p in r["sidor"]:
        with pymupdf.open(p) as d:
            ut.insert_pdf(d)
    pdf = bas + ".pdf"
    try:
        if os.path.exists(pdf):
            os.remove(pdf)
    except PermissionError:
        pdf = bas + "_" + time.strftime("%H%M%S") + ".pdf"
        print("OBS: %s är öppen i ett annat program och kan inte skrivas över - sparar som %s" % (os.path.basename(bas + ".pdf"), os.path.basename(pdf)))
    ut.save(pdf)
    for i, sida in enumerate(ut, start=1):
        sida.get_pixmap(dpi=110).save(bas + "_blad%d.png" % i)
    print("PDF:", pdf, "(%d blad)" % len(ut), "  PNG:", ", ".join(os.path.basename(bas + "_blad%d.png" % i) for i in range(1, len(ut) + 1)))
    ut.close()
    for p in r["sidor"]:
        try:
            os.remove(p)
        except OSError:
            pass
    # DXF-kontroll med ezdxf om det finns
    try:
        import ezdxf
        for suf in ("_kontur.dxf", "_utbredning.dxf"):
            if not os.path.exists(bas + suf):
                continue
            d = ezdxf.readfile(bas + suf)
            msp = d.modelspace()
            lager = {}
            sneda = 0
            for e in msp:
                lager[e.dxf.layer] = lager.get(e.dxf.layer, 0) + 1
                if e.dxftype() == "LINE":
                    v = math.degrees(math.atan2(e.dxf.end.y - e.dxf.start.y, e.dxf.end.x - e.dxf.start.x)) % 90.0
                    if 0.01 < v < 89.99:
                        sneda += 1
            from ezdxf import bbox
            b = bbox.extents(msp)
            print("DXF %s: %s, låda %.1f x %.1f mm, sneda linjer: %d" % (suf, lager, b.size.x, b.size.y, sneda))
    except ImportError:
        print("(ezdxf saknas - DXF:en kontrolleras inte automatiskt)")


if __name__ == "__fcjobb__":
    _jobb()
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    a = args()
    a.del_ = os.path.abspath(a.del_)
    if not os.path.exists(a.del_):
        raise SystemExit("Filen finns inte: " + a.del_)
    r = fcapi.kor(__file__, vars(a))
    _efterbehandla(r)
