"""Parametriskt dataställ i FreeCAD 1.x (SheetMetal-tillägget), styrt från vanlig Python.

  python datastall.py bygg <ut.FCStd> [--bredd 350 --djup 280 --rygg 150 --hylla 290 --kant 20 --lutning 5
                                       --tjocklek 3 --bockradie 3 --hornradie 10] [--png] [--step]
  python datastall.py satt <fil.FCStd> --bredd 400 ...      # ändrar variablerna i befintlig fil och bygger om
  python datastall.py las  <fil.FCStd>                       # läser variabler, mått, låda, massa och utbredning

Alla mått i mm. Måtten är yttermått som i SolidWorks-versionen: undersida botten, baksida rygg, ovansida
hylla och kantens insida (stoppet mot datorn). Hyllan lutar nedåt framåt (Lutning i grader) och kanten är
uppvikt vinkelrätt mot hyllan. Koordinater: X = bredd, Y = djup bakåt, Z = höjd (Z uppåt som i FreeCAD).
Variablerna ligger i kalkylbladet "Variabler" (motsvarar SolidWorks globala variabler) och skissmåtten,
plåttjockleken, bockradien och bredden är uttryck mot bladet, så de går också att ändra direkt i FreeCAD.
"""
import os, sys, math, argparse

VARS = ["Bredd", "Djup", "Rygg", "Hylla", "Kant", "Lutning", "Tjocklek", "Bockradie", "Hornradie"]
DEFAULT = dict(Bredd=350, Djup=280, Rygg=150, Hylla=290, Kant=20, Lutning=5, Tjocklek=3, Bockradie=3, Hornradie=10)
BESKR = dict(Bredd="mm, plåtens bredd", Djup="mm, bottenplatta (undersida)", Rygg="mm, höjd (baksida)",
             Hylla="mm, hyllans längd (ovansida)", Kant="mm, uppvikt framkant (insida)", Lutning="grader, hyllan nedåt framåt",
             Tjocklek="mm, plåt", Bockradie="mm, inre", Hornradie="mm, fria hörn (0 = inga)")


def args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("lage", choices=["bygg", "satt", "las"])
    ap.add_argument("fil")
    for v in VARS:
        ap.add_argument("--" + v.lower(), type=float)
    ap.add_argument("--step", action="store_true", help="exportera STEP bredvid filen")
    ap.add_argument("--png", action="store_true", help="spara isometrisk bild bredvid filen")
    return ap.parse_args(argv)


# =====================================================================================================
# Jobbet: körs inne i FreeCAD (fcapi.kor startar FreeCAD med den här filen som jobb)
# =====================================================================================================
def _jobb():
    import FreeCAD as App, Part, Sketcher
    from FreeCAD import Vector as V, Placement, Rotation
    import fcapi, plat
    from fcapi import logg
    import SheetMetalTools
    if not fcapi.har_gui():                                   # SheetMetal definierar detta bara med GUI
        SheetMetalTools.taskRestoreDefaults = lambda *a, **k: None
    import SheetMetalBaseCmd, SheetMetalUnfoldCmd
    GUI = fcapi.har_gui()

    def varde(doc, namn):
        return float(doc.Variabler.get(namn))

    def till_global(sk, x, y):
        return sk.Placement.multVec(V(x, y, 0))

    def hornkanter(doc, kropp):
        """Kanterna (1-baserade index) i kroppen där hörnradierna ska sitta: bottenplattans två framhörn och
        kantens två övre hörn. Letas på geometrin: raka kanter med längd = tjockleken på rätt ställe."""
        sk = doc.Profil
        T, B = varde(doc, "Tjocklek"), varde(doc, "Bredd")
        g0, g3 = sk.Geometry[0], sk.Geometry[3]
        d = (g3.EndPoint - g3.StartPoint).normalize()
        n = V(-d.y, d.x, 0)                                    # materialet ligger till vänster om profilen
        kant_mitt = g3.EndPoint + n * (T / 2)
        bott_mitt = g0.StartPoint + V(0, T / 2, 0)
        mal = []
        for x in (0.0, B):
            for q in (kant_mitt, bott_mitt):
                p = till_global(sk, q.x, q.y)
                mal.append(V(x, p.y, p.z))
        ut = []
        for i, e in enumerate(kropp.Shape.Edges, start=1):
            if abs(e.Length - T) < 0.01:
                m = e.valueAt((e.FirstParameter + e.LastParameter) / 2)
                if any((m - q).Length < 0.5 for q in mal):
                    ut.append(i)
        return ut

    def uppdatera_kedja(doc):
        """Hörnradier och utbredningens fasta yta efter en måttändring."""
        doc.recompute()
        bf, R = doc.Basflans, varde(doc, "Hornradie")
        f = doc.getObject("Hornradie")
        if R > 0:
            if f is None:
                f = doc.addObject("Part::Fillet", "Hornradie")
                f.Base = bf
            kanter = hornkanter(doc, bf)
            if len(kanter) != 4:
                raise RuntimeError("Hittade %d hörnkanter, väntade 4" % len(kanter))
            f.Edges = [(i, R, R) for i in kanter]
            bf.Visibility = False
            kropp = f
        else:
            if f is not None:
                doc.removeObject(f.Name)
            bf.Visibility = True
            kropp = bf
        doc.recompute()
        rot = plat.rotyta(kropp.Shape)
        u = doc.getObject("Utbredning")
        if u is None:
            u = doc.addObject("Part::FeaturePython", "Utbredning")
            SheetMetalUnfoldCmd.SMUnfold(u, kropp, ["Face%d" % (rot + 1)])
            if GUI:
                SheetMetalUnfoldCmd.SMUnfoldViewProvider(u.ViewObject)
        u.baseObject = (kropp, ["Face%d" % (rot + 1)])
        u.KFactor = 0.5                                      # samma som SolidWorks-dataställen
        u.KFactorStandard = "ansi"
        u.GenerateSketch = False
        u.touch()
        doc.recompute()
        if GUI:
            u.ViewObject.Visibility = False
            kropp.ViewObject.Visibility = True
        return kropp, rot

    def bygg_profil(doc, p):
        sk = doc.addObject("Sketcher::SketchObject", "Profil")
        # Skissen i YZ-planet: skissens x = globalt Y (djup bakåt), skissens y = globalt Z (höjd). Normal = +X.
        sk.Placement = Placement(V(0, 0, 0), Rotation(V(1, 1, 1), 120))
        D, H, HY, K = p["Djup"], p["Rygg"], p["Hylla"], p["Kant"]
        v = math.radians(p["Lutning"])
        P = [(0, 0), (D, 0), (D, H)]
        P.append((D - HY * math.cos(v), H - HY * math.sin(v)))          # hyllans framkant, lägre än bakkanten
        P.append((P[3][0] - K * math.sin(v), P[3][1] + K * math.cos(v)))  # kanten uppåt, vinkelrät mot hyllan
        for a, b in zip(P, P[1:]):
            sk.addGeometry(Part.LineSegment(V(a[0], a[1], 0), V(b[0], b[1], 0)))
        C = Sketcher.Constraint
        for c in (C("Coincident", 0, 1, -1, 1), C("Coincident", 0, 2, 1, 1), C("Coincident", 1, 2, 2, 1),
                  C("Coincident", 2, 2, 3, 1), C("Horizontal", 0), C("Vertical", 1), C("Perpendicular", 2, 3)):
            sk.addConstraint(c)
        for geo, namn in ((0, "Djup"), (1, "Rygg"), (2, "Hylla"), (3, "Kant")):
            i = sk.addConstraint(C("Distance", geo, p[namn]))
            sk.renameConstraint(i, namn)
            sk.setExpression("Constraints." + namn, "Variabler." + namn)
        # vinkeln mellan ryggens riktning (uppåt) och hyllans (framåt-nedåt) = 90 + lutningen
        i = sk.addConstraint(C("Angle", 1, 2, math.radians(90 + p["Lutning"])))
        sk.renameConstraint(i, "Vinkel")
        sk.setExpression("Constraints.Vinkel", "(90 + Variabler.Lutning) * 1 deg")
        return sk

    def kontroll(doc):
        doc.recompute()
        sk = doc.Profil
        logg("Variabler:")
        for v in VARS:
            logg("    %-10s %s" % (v, doc.Variabler.get(v)))
        logg("Skiss Profil: solve=%s, fullt bestämd=%s, frihetsgrader=%s" % (sk.solve(), sk.FullyConstrained, sk.DoF if hasattr(sk, "DoF") else "?"))
        logg("Mått i skissen:", ", ".join("%s %s" % (n, sk.getDatum(n).UserString) for n in ("Djup", "Rygg", "Hylla", "Kant", "Vinkel")))
        fel = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
        if fel:
            raise RuntimeError("Objekt med fel efter omräkning: %s" % fel)
        kropp = doc.getObject("Hornradie") or doc.Basflans
        rot = plat.rotyta(kropp.Shape)
        utb = plat.utbred(kropp.Shape, rot, kfaktor=doc.Utbredning.KFactor)
        d = plat.platdata(kropp, utb)
        b = d["lada"]
        logg("Kropp: %s, giltig=%s, plåt %.2f mm, bockradie %.2f mm" % (kropp.Name, kropp.Shape.isValid(), utb["tjocklek"], doc.Basflans.Radius.Value))
        logg("Låda mm: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f" % b)
        logg("Massa: %.3f kg (stål %g kg/m3)   volym %.1f cm3" % (d["massa"], plat.STAL_DENSITET, d["volym_cm3"]))
        logg("Utbredning: %.1f x %.1f mm, fast yta Face%d, %d bockar: %s" % (d["utbredning"][0], d["utbredning"][1], rot + 1, len(d["bockar"]), ", ".join(d["bockar"])))
        import dfm
        am, sam = dfm.granska(utb, "S235", kfaktor=doc.Utbredning.KFactor)
        logg("Tillverkningsgranskning (S235): %s%s" % (sam, "".join("\n    %s %s: %s (krav %s)" % (x["niva"], x["regel"], x["varde"], x["krav"]) for x in am if x["niva"] in ("FEL", "VARNING"))))
        ub = doc.Utbredning.Shape.optimalBoundingBox(False, False)
        logg("Utbredningsfeature låda mm: X %.1f  Y %.1f  Z %.1f" % (ub.XLength, ub.YLength, ub.ZLength))
        return dict(lada=b, massa=d["massa"], utbredning=d["utbredning"], bockar=d["bockar"], fullt_bestamd=bool(sk.FullyConstrained))

    def spara(doc, fil, a, kropp):
        doc.saveAs(fil)
        logg("Sparat:", fil)
        bas = os.path.splitext(fil)[0]
        if a.get("step"):
            kropp.Shape.exportStep(bas + ".step")
            logg("STEP:", bas + ".step")
        if a.get("png"):
            if not GUI:
                logg("PNG kräver GUI - hoppas över")
            else:
                import FreeCADGui as Gui
                gd = Gui.getDocument(doc.Name)
                for o in doc.Objects:
                    if hasattr(o, "ViewObject") and o.ViewObject is not None and o.TypeId.startswith(("Part::", "Sketcher::")):
                        o.ViewObject.Visibility = (o == kropp)
                kropp.ViewObject.ShapeColor = (0.62, 0.64, 0.67)
                fcapi.pump(0.3)
                vy = gd.ActiveView
                vy.viewIsometric()
                vy.fitAll()
                fcapi.pump(0.3)
                vy.saveImage(bas + ".png", 1600, 1200, "White")
                logg("PNG:", bas + ".png")

    def bygg(a):
        p = {v: (a.get(v.lower()) if a.get(v.lower()) is not None else DEFAULT[v]) for v in VARS}
        doc = App.newDocument("Datastall")
        sh = doc.addObject("Spreadsheet::Sheet", "Variabler")
        sh.set("A1", "Variabel"); sh.set("B1", "Värde"); sh.set("C1", "Beskrivning")
        for i, v in enumerate(VARS, start=2):
            sh.set("A%d" % i, v); sh.set("B%d" % i, "%g" % p[v]); sh.setAlias("B%d" % i, v); sh.set("C%d" % i, BESKR[v])
        sh.setStyle("A1:C1", "bold")
        doc.recompute()
        sk = bygg_profil(doc, p)
        doc.recompute()
        logg("Skiss: fullt bestämd=%s" % sk.FullyConstrained)
        if not sk.FullyConstrained:
            raise RuntimeError("Profilskissen är inte fullt bestämd")
        bf = doc.addObject("Part::FeaturePython", "Basflans")
        SheetMetalBaseCmd.SMBaseBend(bf, sk)
        if GUI:
            SheetMetalBaseCmd.SMBaseViewProvider(bf.ViewObject)
        bf.BendSide = "Inside"       # materialet på vänster sida om profilen = yttermåtten ovan (uppmätt 2026-10-10)
        for prop, var in (("Thickness", "Tjocklek"), ("Radius", "Bockradie"), ("Length", "Bredd")):
            bf.setExpression(prop, "Variabler." + var)
        doc.recompute()
        bb = bf.Shape.BoundBox
        if bb.ZMin < -0.5 or bb.YMax > p["Djup"] + 0.5:
            raise RuntimeError("Plåten hamnade utanför profilen (Z min %.1f, Y max %.1f)" % (bb.ZMin, bb.YMax))
        kropp, _ = uppdatera_kedja(doc)
        r = kontroll(doc)
        spara(doc, os.path.abspath(a["fil"]), a, kropp)
        return r

    def oppna(fil):
        doc = App.openDocument(os.path.abspath(fil))
        if doc.getObject("Variabler") is None or doc.getObject("Profil") is None:
            raise RuntimeError("Filen saknar kalkylbladet Variabler eller skissen Profil - är det ett dataställ från bygg?")
        return doc

    def satt(a):
        doc = oppna(a["fil"])
        for v in VARS:
            nytt = a.get(v.lower())
            if nytt is None:
                continue
            doc.Variabler.set(doc.Variabler.getCellFromAlias(v), "%g" % nytt)
            logg("Ändrade", v, "->", nytt)
        kropp, _ = uppdatera_kedja(doc)
        r = kontroll(doc)
        spara(doc, os.path.abspath(a["fil"]), a, kropp)
        return r

    def las(a):
        doc = oppna(a["fil"])
        return kontroll(doc)

    fcapi.kor_jobb(lambda a: {"bygg": bygg, "satt": satt, "las": las}[a["lage"]](a))


if __name__ == "__fcjobb__":
    _jobb()
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    a = args()
    a.fil = os.path.abspath(a.fil)
    if a.lage != "bygg" and not os.path.exists(a.fil):
        raise SystemExit("Filen finns inte: " + a.fil)
    fcapi.kor(__file__, vars(a))
