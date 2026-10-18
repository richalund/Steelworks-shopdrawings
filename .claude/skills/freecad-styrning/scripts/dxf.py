"""DXF till laser och kantpress för plåtdelarna i en sammanställning: en fil per positionsnummer.

  python3 dxf.py <modell.FCStd> [--ut <mapp>] [--bara pl/1,pl/2] [--kfaktor 0.5]

Plåtar (PL med bredd >= 100 mm, och egna kroppar som är skurna plattor) får `<modell>_<pos>_kontur.dxf` med
konturen och hålen sedda rakt på den största ytan (lager KONTUR) och en märkning (pos, profil, material, antal)
på lagret MARKNING, som inte skärs. Bockade delar (k.bockad, k.trag, SheetMetal) bredas ut som i ritning.py:
`_kontur.dxf` (laser) och `_utbredning.dxf` (KONTUR + BOCKLINJER + BOCKNOTER). Utskriften ger storlek och antal
per fil, och en rad per del som inte kunde bredas ut.
"""
import os, re, sys, argparse


def _jobb(a):
    import FreeCAD as App
    from FreeCAD import Vector as V
    import stal, plat
    from fcapi import logg
    doc = App.openDocument(a["fil"])
    doc.recompute()
    g, ds, _ = stal.delar(doc)
    utmapp = os.path.abspath(a["ut"]) if a.get("ut") else os.path.dirname(a["fil"])
    os.makedirs(utmapp, exist_ok=True)
    bas = os.path.join(utmapp, os.path.splitext(os.path.basename(a["fil"]))[0])
    bara = {x.strip() for x in (a.get("bara") or "").split(",") if x.strip()}
    per_pos = {}
    for o in ds:
        per_pos.setdefault(o.Pos, []).append(o)
    import kalkyl
    filer = []
    for pos, lst in sorted(per_pos.items()):
        if bara and pos not in bara:
            continue
        o, n = lst[0], len(lst)
        if hasattr(o, "Vikt"):                          # inköpt detalj (k.inkop): ingen egen tillverkning
            continue
        s = o.Shape
        profil = stal.profilnamn(o)
        info = None
        try:
            info = stal.tolka(o.Profil, kallor=False)
        except Exception:
            pass
        bockad = not hasattr(o, "Group")
        platta = bockad or (info is not None and info["typ"] == "PL" and o.Profil.upper().startswith("PL") and info["b"] >= 100) \
            or (info is None and kalkyl._platta(s))
        if not platta:
            continue
        namn = "%s_%s" % (bas, re.sub(r"[^A-Za-z0-9]+", "", pos))
        markning = "%s  %s  %s  %d ST" % (pos, profil, o.Material, n)
        plan = [f for f in s.Faces if f.Surface.TypeId == "Part::GeomPlane"]
        storst = max(plan, key=lambda f: f.Area)
        if bockad:
            try:
                utb = plat.utbred(s, plat.rotyta(s, storst.normalAt(0, 0)), kfaktor=a.get("kfaktor", 0.5))
            except Exception as e:
                logg("OBS: %s kunde inte bredas ut (%s: %s)" % (pos, type(e).__name__, e))
                continue
            ut = plat.exportera_dxf(utb, namn)
            fb = utb["face2d"].BoundBox
            logg("DXF %s: utbredd %.1f x %.1f mm, %d bockar (%s), %d st" % (pos, fb.XLength, fb.YLength, len(utb["bockar2d"]),
                                                                            ", ".join(plat.bocknot(b) for b in utb["bockar2d"]), n))
            filer += list(ut)
            continue
        f = storst.copy()
        f.transformShape(App.Placement(V(0, 0, 0), App.Rotation(f.normalAt(0, 0), V(0, 0, 1))).toMatrix())
        bb = f.BoundBox
        f.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
        fil = namn + "_kontur.dxf"
        plat.skriv_dxf(fil, [("KONTUR", 7, list(f.Edges))], [("MARKNING", markning, 2.0, -6.0, 3.5, 0.0)])
        hal = len(f.Wires) - 1
        logg("DXF %s: %.1f x %.1f mm, %d hål, %d st" % (pos, bb.XLength, bb.YLength, hal, n))
        filer.append(fil)
    logg("DXF-filer: %d i %s" % (len(filer), utmapp))
    return dict(filer=filer)


if __name__ == "__fcjobb__":
    import fcapi
    fcapi.kor_jobb(_jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("fil")
    ap.add_argument("--ut", default=None)
    ap.add_argument("--bara", default="", help="kommaseparerade positionsnummer")
    ap.add_argument("--kfaktor", type=float, default=0.5)
    a = vars(ap.parse_args())
    a["fil"] = os.path.abspath(a["fil"])
    fcapi.kor(__file__, a)
