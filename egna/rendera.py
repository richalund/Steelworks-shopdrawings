"""3D-bilder av en FCStd från flera håll (översikter, modeller): python3 egna/rendera.py <fil.FCStd> [--ut mapp]
Bilder: <fil>_3d_gard.png (snett från gården, nedifrån trappan), _3d_trappa.png (snett från gården mot plattan, trappräcket närmast),
_3d_fram.png (rakt från gården), _3d_plan.png (uppifrån). Kör FreeCAD med GUI via skillens fcapi."""
import os, sys, argparse

SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".claude", "skills", "freecad-styrning", "scripts")
VYER = [("gard", (0.55, 0.70, -0.45)), ("trappa", (-0.60, 0.65, -0.35)), ("fram", (0.0, 1.0, -0.15)), ("plan", (0.0, 0.0, -1.0))]

if __name__ == "__fcjobb__":
    sys.path.insert(0, SKILL)
    import fcapi

    def jobb(a):
        import FreeCAD as App, FreeCADGui as Gui
        from fcapi import logg, pump
        doc = App.openDocument(a["fil"])
        doc.recompute()
        pump(0.5)
        gd = Gui.getDocument(doc.Name)
        vy = gd.ActiveView
        try:
            vy.setAnimationEnabled(False)         # annars sparas bilden mitt i kamerans övergång
        except Exception:
            pass
        for o in doc.Objects:                     # bara kroppar synliga (skisser, ritningssidor m.m. dolda)
            vo = getattr(o, "ViewObject", None)
            if vo is None:
                continue
            if o.TypeId == "PartDesign::Body":
                vo.Visibility = True
            elif o.TypeId.startswith(("TechDraw::", "Sketcher::", "App::Origin", "App::Line", "App::Plane", "Spreadsheet::")):
                vo.Visibility = False
        bas = os.path.splitext(a["fil"])[0]
        ut = []
        for namn, d in VYER:
            # kameran tittar längs -z_kam med y_kam uppåt: bygg rotationen ur blickriktningen och lodlinjen
            f = App.Vector(*d).normalize()
            upp = App.Vector(0, 1, 0) if abs(f.z) > 0.99 else App.Vector(0, 0, 1)
            hoger = f.cross(upp).normalize()
            upp2 = hoger.cross(f).normalize()
            zk = f.negative()
            m = App.Matrix(hoger.x, upp2.x, zk.x, 0, hoger.y, upp2.y, zk.y, 0, hoger.z, upp2.z, zk.z, 0, 0, 0, 0, 1)
            vy.setCameraOrientation(App.Rotation(m))
            vy.fitAll()
            pump(1.5)
            fil = "%s_3d_%s.png" % (bas, namn)
            vy.saveImage(fil, 2000, 1400, "White")
            logg("PNG:", fil)
            ut.append(fil)
        return dict(bilder=ut)

    fcapi.kor_jobb(jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, SKILL)
    import fcapi
    ap = argparse.ArgumentParser()
    ap.add_argument("fil")
    a = ap.parse_args()
    fcapi.kor(__file__, {"fil": os.path.abspath(a.fil)})
