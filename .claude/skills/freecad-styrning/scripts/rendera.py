"""3D-bilder (PNG) av en modell från flera håll, för offerter och kundgenomgångar.

  python3 rendera.py <modell.FCStd> [--vyer iso,fram,plan] [--vy namn:dx,dy,dz ...] [--utan-omgivning]
                     [--storlek 2000x1400] [--ut <mapp>]

Färdiga vyer (blickriktning från kameran mot modellen, z uppåt):
  iso      snett framifrån höger, ovanifrån (-1, 1, -0.8), som FreeCADs isometri
  iso2     snett framifrån vänster (1, 1, -0.8)
  bak      snett bakifrån höger (-1, -1, -0.8)
  fram     rakt framifrån (0, 1, 0), lätt ovanifrån
  sida     rakt från vänster (1, 0, 0)
  plan     rakt uppifrån, +y uppåt i bilden
Egna vyer med --vy namn:dx,dy,dz (blickriktningen), t.ex. --vy innergard:-0.4,-0.82,-0.42.

Bilderna heter <modell>_3d_<vy>.png. Alla kroppar visas (delar och referenskroppar i gruppen Omgivning, med
sina färger); skisser, ritningsblad och origo döljs. --utan-omgivning döljer referenskropparna.
"""
import os, sys, argparse

VYER = {"iso": (-1.0, 1.0, -0.8), "iso2": (1.0, 1.0, -0.8), "bak": (-1.0, -1.0, -0.8), "fram": (0.0, 1.0, -0.12),
        "sida": (1.0, 0.0, -0.12), "plan": (0.0, 0.0, -1.0)}


def args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("fil")
    ap.add_argument("--vyer", default="iso,fram,plan", help="färdiga vyer, kommaseparerade: " + ", ".join(VYER))
    ap.add_argument("--vy", action="append", default=[], metavar="NAMN:DX,DY,DZ", help="egen blickriktning")
    ap.add_argument("--utan-omgivning", dest="utan_omgivning", action="store_true", help="dölj referenskropparna (Omgivning)")
    ap.add_argument("--storlek", default="2000x1400")
    ap.add_argument("--ut", default=None)
    return ap.parse_args(argv)


def vylista(a):
    ut = []
    for n in [x.strip() for x in a["vyer"].split(",") if x.strip()]:
        if n not in VYER:
            raise SystemExit("Okänd vy %s. Finns: %s (eller --vy namn:dx,dy,dz)" % (n, ", ".join(VYER)))
        ut.append((n, VYER[n]))
    for s in a["vy"]:
        namn, r = s.split(":", 1)
        ut.append((namn, tuple(float(q) for q in r.split(","))))
    return ut


def _jobb(a):
    import FreeCAD as App, FreeCADGui as Gui
    from fcapi import logg, pump
    doc = App.openDocument(a["fil"])
    doc.recompute()
    pump(0.5)
    gd = Gui.getDocument(doc.Name)
    vyer3d = gd.mdiViewsOfType("Gui::View3DInventor")        # aktiv vy kan vara ett ritningsblad
    if not vyer3d:
        Gui.runCommand("Std_ViewCreate")
        pump(0.5)
        vyer3d = gd.mdiViewsOfType("Gui::View3DInventor")
    vy = vyer3d[0]
    try:
        vy.setAnimationEnabled(False)         # annars sparas bilden mitt i kamerans övergång
    except Exception:
        pass
    omg = doc.getObject("Omgivning")
    omgivning = {o.Name for o in (omg.Group if omg else [])}
    for o in doc.Objects:                     # bara kroppar synliga (skisser, ritningsblad m.m. dolda)
        vo = getattr(o, "ViewObject", None)
        if vo is None:
            continue
        if o.TypeId == "PartDesign::Body":
            vo.Visibility = not (a.get("utan_omgivning") and o.Name in omgivning)
        elif o.TypeId.startswith(("TechDraw::", "Sketcher::", "App::Origin", "App::Line", "App::Plane", "Spreadsheet::")):
            vo.Visibility = False
    utmapp = os.path.abspath(a["ut"]) if a.get("ut") else os.path.dirname(a["fil"])
    os.makedirs(utmapp, exist_ok=True)
    bas = os.path.join(utmapp, os.path.splitext(os.path.basename(a["fil"]))[0])
    w, h = (int(q) for q in a["storlek"].lower().split("x"))
    ut = []
    for namn, d in vylista(a):
        # kameran tittar längs -z_kam med y_kam uppåt: rotationen byggs ur blickriktningen och lodlinjen
        # (setViewDirection fungerar inte pålitligt i FreeCAD 1.1, se references/fallor.md)
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
        vy.saveImage(fil, w, h, "White")
        logg("PNG:", fil)
        ut.append(fil)
    return dict(bilder=ut)


if __name__ == "__fcjobb__":
    import fcapi
    fcapi.kor_jobb(_jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    a = vars(args())
    a["fil"] = os.path.abspath(a["fil"])
    vylista(a)                                # fel i vynamnen före FreeCAD startar
    fcapi.kor(__file__, a)
