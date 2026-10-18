"""Efterbehandling av en sammanställningsritning från skillens sammanstallning.py ritning:

1. Positionsbubblorna flyttas intill delen de pekar på (kort hänvisningslinje med pil) i stället för en rad
   under vyn med långa linjer. Bubblorna läggs där de inte krockar med andra bubblor, mått eller noter.
2. Finns egenskapen Detaljer i gruppen Sammanstallning (räckena, se egna/racke_bas.py) läggs ett blad 2
   "Detaljer" i samma FCStd: TechDraw-detaljvyer (DrawViewDetail) i skala 1:2 av snitt A och framvyn, med
   mått på profilerna och en beskrivning under varje detalj. Detaljernas cirklar och D1, D2 ... syns i
   blad 1. Titelblocket kopieras (nummer <märke>.1 och <märke>.2).
3. PDF:en görs om med båda bladen, PNG per blad (<modell>.png och <modell>_detaljer.png).

python3 egna/ritning_detaljer.py ut/R1_Racke_ovre_lopp.FCStd
"""
import os, sys, re, json, math, argparse

SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".claude", "skills", "freecad-styrning", "scripts")
SKALA_DETALJ = 2.0
FONT = "osifont"


def _kant(v, i):
    """Kantens punkter (oskalade, relativt vyns mitt); StopIteration när kanterna är slut."""
    try:
        return v.getEdgeByIndex(i).discretize(6)
    except Exception:
        raise StopIteration


def num(q):
    return float(getattr(q, "Value", q))


def _jobb(a):
    import FreeCAD as App
    from FreeCAD import Vector as V
    import fcapi
    from fcapi import logg, pump
    # samma TechDraw-inställningar som sammanstallning.py (gäller bara jobbet)
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
    sidor = [o for o in doc.Objects if o.TypeId == "TechDraw::DrawPage"]
    blad1 = next(p for p in sidor if p.Name.startswith("Sammanstallningsritning"))
    grupp = doc.getObject("Sammanstallning")
    marke = grupp.Marke
    for p in sidor:
        p.ViewObject.show()
    pump(1.0)

    # ---- rensa ett tidigare blad 2
    gamla = [o for o in doc.Objects if o.Name.startswith(("Detaljblad", "MallDetaljer", "Detalj", "SnittE"))]
    ordning = {"TechDraw::DrawPage": 1, "TechDraw::DrawSVGTemplate": 2}         # vyer först, sedan blad och mall
    namn = [o.Name for o in sorted(gamla, key=lambda o: ordning.get(o.TypeId, 0))]
    if namn:
        pump(1.0)
    for n in namn:
        if doc.getObject(n) is not None:
            doc.removeObject(n)
    doc.recompute()

    def symbolruta(s):
        m = re.search(r'width="([\d.]+)mm"\s+height="([\d.]+)mm"', s.Symbol)
        if not m:
            return None
        w, h = float(m.group(1)), float(m.group(2))
        return (s.X.Value - w / 2, s.Y.Value - h / 2, s.X.Value + w / 2, s.Y.Value + h / 2)

    def overlapp(r, q, marg=1.0):
        return not (r[2] + marg <= q[0] or q[2] + marg <= r[0] or r[3] + marg <= q[1] or q[3] + marg <= r[1])

    # ---- 1. positionsbubblor intill delen
    hinder = []
    for v in blad1.Views:
        if v.TypeId == "TechDraw::DrawViewSymbol":
            r = symbolruta(v)
            if r:
                hinder.append(r)
        elif v.TypeId == "TechDraw::DrawViewDimension":
            bas = v.References2D[0][0] if v.References2D else None
            if bas is not None:
                cx, cy = bas.X.Value + num(v.X), bas.Y.Value + num(v.Y)
                hinder.append((cx - 8, cy - 3, cx + 8, cy + 3))
    hinder.append((360, 0, 594, 75))                                     # titelblocket
    # snittlinjernas pilar och bokstäver ovanför och under basvyn
    for sv_ in [v for v in blad1.Views if v.TypeId == "TechDraw::DrawViewSection"]:
        bas_ = sv_.BaseView
        try:
            s_ = num(bas_.Scale)
            p_ = V(sv_.SectionOrigin)
            tag = bas_.makeCosmeticLine3D(p_, p_ + V(bas_.XDirection).normalize() * 0.01)
            ce = bas_.getCosmeticEdge(tag)
            f_ = ce.Format
            f_["visible"] = False
            ce.Format = f_
            px = bas_.X.Value + s_ * ce.Start.x
            ys, i = [], 0
            while True:
                try:
                    ys += [q.y for q in _kant(bas_, i)]
                except StopIteration:
                    break
                i += 1
        except Exception as e:
            logg("OBS: snittmarkering %s: %s" % (sv_.Name, e))
            continue
        ytop, ybot = bas_.Y.Value + s_ * max(ys), bas_.Y.Value + s_ * min(ys)
        hinder += [(px - 4, ytop - 2, px + 18, ytop + 16), (px - 4, ybot - 16, px + 18, ybot + 2)]
    ballonger = [v for v in blad1.Views if v.TypeId == "TechDraw::DrawViewBalloon"]
    pil = None
    for b in ballonger:
        typer = b.getEnumerationsOfProperty("EndType")
        pil = next((t for t in typer if "arrow" in t.lower() and "fill" in t.lower()), None) or next((t for t in typer if "arrow" in t.lower()), b.EndType)
        break
    placerade = 0
    for b in ballonger:
        sv = b.SourceView
        s = num(sv.Scale)
        ox, oy = sv.X.Value + s * num(b.OriginX), sv.Y.Value + s * num(b.OriginY)
        w, h = 1.85 * len(b.Text) + 7.0, 6.0
        kand = [(w / 2 + 7, 8), (-w / 2 - 7, 8), (w / 2 + 7, -8), (-w / 2 - 7, -8), (0, 11), (0, -11),
                (w / 2 + 10, 0), (-w / 2 - 10, 0), (w / 2 + 9, 14), (-w / 2 - 9, 14), (w / 2 + 9, -14), (-w / 2 - 9, -14)]
        val = None
        for dx, dy in kand:
            cx, cy = ox + dx, oy + dy
            r = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            if r[0] < 32 or r[2] > 584 or r[1] < 12 or r[3] > 410:
                continue
            if any(overlapp(r, q) for q in hinder):
                continue
            val = (cx, cy, r)
            break
        if val is None:
            dx, dy = kand[0]
            val = (ox + dx, oy + dy, (ox + dx - w / 2, oy + dy - h / 2, ox + dx + w / 2, oy + dy + h / 2))
        cx, cy, r = val
        hinder.append(r)
        b.X, b.Y = (cx - sv.X.Value) / s, (cy - sv.Y.Value) / s
        b.EndType = pil
        if hasattr(b, "EndTypeScale"):
            b.EndTypeScale = 0.6
        placerade += 1
    logg("Positionsbubblor flyttade intill delen: %d (pil: %s)" % (placerade, pil))
    doc.recompute()
    pump(1.0)

    # ---- 2. blad 2 med detaljer
    det = json.loads(getattr(grupp, "Detaljer", "") or "[]")
    snitt_e = None
    if isinstance(det, dict):
        snitt_e, det = det.get("snitt"), det.get("detaljer", [])
    blad = [blad1]
    if det:
        tpl1 = blad1.Template
        tpl2 = doc.addObject("TechDraw::DrawSVGTemplate", "MallDetaljer")
        tpl2.Template = tpl1.Template
        blad2 = doc.addObject("TechDraw::DrawPage", "Detaljblad")
        blad2.Label = "Detaljer"
        blad2.Template = tpl2
        et1 = dict(tpl1.EditableTexts)
        et2 = dict(et1)
        et1["Nummer"], et2["Nummer"] = marke + ".1", marke + ".2"
        et2["Skala"] = "1:%g" % SKALA_DETALJ
        tpl1.EditableTexts = et1
        tpl2.EditableTexts = et2
        doc.recompute()
        blad2.ViewObject.show()
        pump(0.5)
        blad.append(blad2)

        def stil(d, fs=3.0):
            d.FormatSpec = "%.1w"
            vo = d.ViewObject
            vo.Font, vo.Fontsize, vo.Arrowsize, vo.LineWidth = FONT, fs, 2.0, 0.13
            return d

        def ankare(bas, p):
            """Modellpunktens läge i basvyn: oskalat, relativt vyns mitt (via en osynlig kosmetisk linje)."""
            p = V(*p)
            tag = bas.makeCosmeticLine3D(p, p + V(bas.XDirection).normalize() * 0.01)
            ce = bas.getCosmeticEdge(tag)
            f = ce.Format
            f["visible"] = False
            ce.Format = f
            return V(ce.Start.x, ce.Start.y, 0)

        def kanter(v):
            ut, i = [], 0
            while True:
                try:
                    e = v.getEdgeByIndex(i)
                except Exception:
                    break
                ut.append(e)
                i += 1
            return ut

        def matt(v, typ, ref, lage, namn):
            d = doc.addObject("TechDraw::DrawViewDimension", namn)
            d.Type, d.MeasureType = typ, "Projected"
            d.References2D = ref
            blad2.addView(d)
            d.X, d.Y = lage
            return stil(d)

        def detaljmatt(v, nr, slag):
            """Mått på profilerna i en detalj av snitt A: letar kanter efter längd och riktning."""
            s = num(v.Scale)
            ek = kanter(v)
            rak = []
            for i, e in enumerate(ek):
                if len(e.Vertexes) != 2 or e.Curve.__class__.__name__ not in ("Line", "LineSegment"):
                    continue
                p, q = e.Vertexes[0].Point, e.Vertexes[1].Point
                rak.append((i, p, q, abs(q.x - p.x), abs(q.y - p.y)))
            bagar = [(i, e) for i, e in enumerate(ek) if e.Curve.__class__.__name__ == "Circle" and abs(e.Curve.Radius - 52) < 1]
            gjorda, n = set(), 0

            def forsta(villkor, nyckel=None):
                kand = [r for r in rak if villkor(r)]
                if nyckel:
                    kand.sort(key=nyckel)
                return kand[0] if kand else None

            def sattut(r, typ, dx, dy, etikett):
                nonlocal n
                if r is None or r[0] in gjorda:
                    return
                gjorda.add(r[0])
                i, p, q = r[0], r[1], r[2]
                mx, my = (p.x + q.x) / 2 * s, (p.y + q.y) / 2 * s
                matt(v, typ, [(v, "Edge%d" % i)], (mx + dx, my + dy), "DetaljMatt%d_%d" % (nr, n))
                n += 1

            if slag == "handledare":
                hl = forsta(lambda r: abs(r[3] - 40) < 0.5 and r[4] < 0.1, nyckel=lambda r: -r[1].y)
                sattut(hl, "DistanceX", 0, -6, "40")
                if bagar:
                    d = doc.addObject("TechDraw::DrawViewDimension", "DetaljMatt%d_R" % nr)
                    d.Type, d.MeasureType = "Radius", "Projected"
                    d.References2D = [(v, "Edge%d" % bagar[0][0])]
                    blad2.addView(d)
                    d.X, d.Y = 14, 18
                    stil(d).FormatSpec = "R%.1w"
                    n += 1
                ft = forsta(lambda r: abs(r[3] - 5) < 0.3 and r[4] < 0.1, nyckel=lambda r: (-r[1].y, r[1].x))
                sattut(ft, "DistanceX", 0, 5, "5")
                sp = forsta(lambda r: abs(r[3] - 12) < 0.3 and r[4] < 0.1, nyckel=lambda r: -r[1].y)
                sattut(sp, "DistanceX", 0, 5, "12")
            elif slag == "underliggare":
                ft = forsta(lambda r: abs(r[3] - 5) < 0.3 and r[4] < 0.1, nyckel=lambda r: (r[1].y, r[1].x))
                sattut(ft, "DistanceX", 0, -5, "5")
                sp = forsta(lambda r: abs(r[3] - 12) < 0.3 and r[4] < 0.1, nyckel=lambda r: r[1].y)
                sattut(sp, "DistanceX", 0, -5, "12")
            return n

        # snitt E vinkelrätt mot handledaren (bara första fackets handledare, följare och spjälor, så att det
        # som ligger bakom snittet är parallellt med det och inte skymmer tvärsnitten)
        fram = doc.getObject("Framvy")
        if snitt_e and fram is not None:
            x0, x1 = snitt_e["x_omr"]
            delar = []
            for o in grupp.Group:
                if not hasattr(o, "Pos"):
                    continue
                bb = o.Shape.BoundBox
                p_ = o.Pos.split()[-1]
                if p_.startswith(("l/", "sp/")) and bb.XMin >= x0 - 1 and bb.XMax <= x1 + 1:
                    delar.append(o)
                elif p_.startswith("hl/") and bb.XMin < x1 and bb.XMax > x0:
                    # handledarens Pad utan snäckan (snäckan ligger i blickriktningen och skymmer profilen)
                    delar.append(next((f for f in o.Group if f.TypeId == "PartDesign::Pad"), o))
            # vy längs handledaren (TechDraws snitt med fri normal gav fel geometri i FreeCAD 1.1.3): allt i
            # facket ligger parallellt med blicken, så vyn visar profilernas tvärsnitt
            se = doc.addObject("TechDraw::DrawViewPart", "SnittE")
            blad2.addView(se)
            se.Source = delar
            n = V(*snitt_e["normal"])
            se.Direction = n
            se.XDirection = V(0, 0, 1).cross(n).normalize() if abs(n.z) < 0.9 else V(1, 0, 0)
            se.ScaleType, se.Scale = "Custom", 1.0 / 5
            se.X, se.Y = 70, 225
            doc.recompute()
            for _ in range(300):
                pump(0.05)
                if se.getVisibleEdges():
                    break
            vo = se.ViewObject
            for k_, v_ in (("LineWidth", 0.35), ("HiddenWidth", 0.13), ("FaceColor", (1.0, 1.0, 1.0))):
                if hasattr(vo, k_):
                    setattr(vo, k_, v_)
            pts = [q for e in kanter(se) for q in e.discretize(8)]
            h_e = (max(q.y for q in pts) - min(q.y for q in pts)) / 5 if pts else 150
            t = doc.addObject("TechDraw::DrawViewAnnotation", "DetaljTextE")
            blad2.addView(t)
            t.Text = ["VY %s  1:5" % snitt_e["namn"], snitt_e.get("text", "")]
            t.TextSize = 2.6
            t.X, t.Y = se.X.Value, se.Y.Value - h_e / 2 - 12
            logg("Snitt E-E: %d delar, %d kanter" % (len(delar), len(kanter(se))))
        kol = [175, 300, 425, 535]
        rad = [318, 165]
        nm = 0
        for i, d in enumerate(det[:8]):
            bas = doc.getObject(d["vy"])
            if bas is None:
                logg("OBS: vyn %s saknas, detalj D%d hoppas över" % (d["vy"], i + 1))
                continue
            dv = doc.addObject("TechDraw::DrawViewDetail", "Detalj%d" % (i + 1))
            blad2.addView(dv)
            dv.BaseView = bas
            dv.Source = bas.Source
            dv.Direction, dv.XDirection = bas.Direction, bas.XDirection
            dv.AnchorPoint = ankare(bas, d["punkt"])
            dv.Radius = d["radie"]
            dv.Reference = "D%d" % (i + 1)
            dv.ScaleType, dv.Scale = "Custom", 1.0 / SKALA_DETALJ
            dv.X, dv.Y = kol[i % 4], rad[i // 4]
            vo = dv.ViewObject
            for k_, v_ in (("LineWidth", 0.35), ("HiddenWidth", 0.13), ("FaceColor", (1.0, 1.0, 1.0))):
                if hasattr(vo, k_):
                    setattr(vo, k_, v_)
            doc.recompute()
            for _ in range(200):
                pump(0.05)
                if dv.getVisibleEdges():
                    break
            else:
                logg("OBS: detalj D%d räknades inte" % (i + 1))
            if d.get("matt"):
                try:
                    nm += detaljmatt(dv, i + 1, d["matt"])
                except Exception as e:
                    logg("OBS: mått i D%d: %s" % (i + 1, e))
            t = doc.addObject("TechDraw::DrawViewAnnotation", "DetaljText%d" % (i + 1))
            blad2.addView(t)
            t.Text = ["DETALJ D%d  1:%g" % (i + 1, SKALA_DETALJ), d["rubrik"]] + list(d.get("text", []))
            t.TextSize = 2.6
            t.X, t.Y = dv.X.Value, dv.Y.Value - d["radie"] / SKALA_DETALJ - 8 - 2.2 * len(t.Text)
            if hasattr(t, "Font"):
                t.Font = FONT
        rub = doc.addObject("TechDraw::DrawViewAnnotation", "DetaljRubrik")
        blad2.addView(rub)
        rub.Text = ["DETALJER %s – SKALA 1:%g, DETALJERNAS LÄGEN D1 ... VISAS I BLAD %s.1" % (marke, SKALA_DETALJ, marke)]
        rub.TextSize = 3.5
        rub.X, rub.Y = 200, 402
        doc.recompute()
        pump(1.5)
        logg("Blad 2: %d detaljer i 1:%g, %d mått" % (min(len(det), 8), SKALA_DETALJ, nm))

    # ---- 3. export
    doc.save()
    import TechDrawGui
    bas = os.path.splitext(a["fil"])[0]
    ut = []
    for j, p in enumerate(blad):
        p.ViewObject.show()
        pump(1.0)
        tmp = "%s_tmp%d.pdf" % (bas, j + 1)
        TechDrawGui.exportPageAsPdf(p, tmp)
        ut.append(tmp)
    fel = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
    if fel:
        logg("OBS: objekt med fel:", fel)
    return dict(sidor=ut, bas=bas)


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
    a = ap.parse_args()
    r = fcapi.kor(__file__, {"fil": os.path.abspath(a.fil)})
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    bas = r["bas"]
    ny = pymupdf.open()
    for i, s in enumerate(r["sidor"]):
        with pymupdf.open(s) as d:
            ny.insert_pdf(d)
            d[0].get_pixmap(dpi=110).save(bas + (".png" if i == 0 else "_detaljer.png"))
        os.remove(s)
    ny.save(bas + ".pdf")
    print("PDF: %s (%d blad)  PNG: %s%s" % (bas + ".pdf", len(r["sidor"]), os.path.basename(bas) + ".png",
                                           (", " + os.path.basename(bas) + "_detaljer.png") if len(r["sidor"]) > 1 else ""))
