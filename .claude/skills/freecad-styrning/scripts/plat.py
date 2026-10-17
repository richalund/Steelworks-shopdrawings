"""Plåtverktyg som körs inne i FreeCAD: utbredning med bockdata, DXF-export och plåtdata.

Utbredningen använder SheetMetal-tilläggets nya unfolder (SheetMetalNewUnfolder, LGPL, Shai Seger m.fl.).
`utbred()` är en kopia av dess `unfold()` + `getUnfold()` som dessutom sparar vinkel, riktning och
radie för varje bock, så att bocknoter kan skrivas på ritningen och i DXF:en.
"""
import math
from functools import reduce
from operator import mul
import FreeCAD as App
import Part
from FreeCAD import Vector as V, Matrix

STAL_DENSITET = 7850.0      # kg/m3, S235/S355


def rotyta(shape, normal=V(0, 0, -1)):
    """Index (0-baserat) för den största plana ytan med given normal. Används som fast yta i utbredningen
    (dataställ: bottenplattans undersida), annars hamnar utbredningen i en lutande ytas plan."""
    bast = None
    for i, f in enumerate(shape.Faces):
        if f.Surface.TypeId != "Part::GeomPlane":
            continue
        if f.normalAt(0, 0).dot(normal) < 0.9999:
            continue
        if bast is None or f.Area > bast[1]:
            bast = (i, f.Area)
    if bast is None:
        raise RuntimeError("Ingen plan yta med normal %s hittades för utbredningen" % normal)
    return bast[0]


def utbred(shape, rot_index, kfaktor=0.5, standard="ansi"):
    """Utbred en plåtkropp. Returnerar dict med
       face2d      utbredd kontur som yta i XY-planet (för DXF)
       bockar2d    [{linje, vinkel, riktning, radie}] i samma plan
       solid3d     utbredd kropp på plats vid rotytan (för ritningsvyn)
       bockar3d    samma bockar som linjer på plats
       tjocklek, rotnormal"""
    import networkx as nx
    import SheetMetalNewUnfolder as U
    bac = U.BendAllowanceCalculator.from_single_value(kfaktor, standard)
    g = U.build_graph_of_tangent_faces(shape, rot_index)
    t = U.EstimateThickness.using_best_method(shape, rot_index)
    seam = set(shape.Edges[ed["label"]].hashCode() for _, _, ed in g.edges(data=True))
    st = nx.minimum_spanning_tree(g, weight="label")
    dg = nx.DiGraph()
    for n in st:
        dg.add_node(n)
    avst = {k: kv for k, kv in nx.all_pairs_shortest_path_length(st)}[rot_index]
    for f1, f2, ed in st.edges(data=True):
        if avst[f1] <= avst[f2]:
            dg.add_edge(f1, f2, label=ed["label"])
        else:
            dg.add_edge(f2, f1, label=ed["label"])
    for e in [e for e in dg.edges if shape.Faces[e[1]].Surface.TypeId == "Part::GeomCylinder"]:
        bock = shape.Faces[e[1]]
        kant = shape.Edges[dg.get_edge_data(e[0], e[1])["label"]]
        if kant.Curve.TypeId != "Part::GeomLine":
            raise RuntimeError("Bock över en kant som inte är rak (Edge%d) går inte att breda ut" % (dg.get_edge_data(e[0], e[1])["label"] + 1))
        align, total, uvref = U.compute_unbend_transform(bock, kant, t, bac)
        dg.nodes[e[1]]["unbend_transform"] = total
        flat, linje = U.unroll_cylinder(bock, uvref, bac, t, seam)
        umin, umax, vmin, vmax = bock.ParameterRange
        r = bock.Surface.Radius
        # Rotsidans bockyta är konvex (ytteryta) när bocken går bort från rotytans normal, dvs. mot den som
        # tittar på utbredningen från andra sidan: UPP. Konkav (inneryta) = NED. Bestäms på geometrin, inte
        # med SheetMetals BendDirection (som gav omvänt resultat för dataställen 2026-10-10).
        um, vm = (umin + umax) / 2, (vmin + vmax) / 2
        p, n = bock.valueAt(um, vm), bock.normalAt(um, vm)
        ax, c = bock.Surface.Axis, bock.Surface.Center
        radiell = (p - c) - ax * (p - c).dot(ax)
        konvex = n.dot(radiell) > 0
        dg.nodes[e[1]]["bend_line"] = linje.transformed(align)
        dg.nodes[e[1]]["sketch_lines"] = [x.transformed(align) for x in flat]
        dg.nodes[e[1]]["bock"] = dict(vinkel=math.degrees(umax - umin), riktning="UPP" if konvex else "NED",
                                      radie=(r - t) if konvex else r)
    linjer, bockar = [], []
    nd = dg.nodes.data()
    for fid, vag in nx.shortest_path(dg, source=rot_index).items():
        mats = [nd[f]["unbend_transform"] for f in vag[:-1] if "unbend_transform" in nd[f]]
        m = reduce(mul, mats, Matrix())
        if "sketch_lines" in nd[fid]:
            linjer += [x.transformed(m) for x in nd[fid]["sketch_lines"]]
        else:
            linjer += [x.transformed(m) for x in shape.Faces[fid].Edges if x.hashCode() not in seam]
        if "bend_line" in nd[fid]:
            bockar.append(dict(nd[fid]["bock"], linje=nd[fid]["bend_line"].transformed(m)))
    rot = shape.Faces[rot_index]
    a = U.SketchExtraction.move_to_origin(Part.makeCompound(linjer), rot)
    linjer = [x.transformed(a) for x in linjer]
    face = Part.makeFace(U.Edge2DCleanup.clean_and_structure_geometry(linjer), "Part::FaceMakerBullseye")
    platt = face.extrude(V(0, 0, -t)).translated(V(0, 0, 0.5 * t))
    rn = rot.normalAt(0, 0)
    ut = dict(face2d=face, solid3d=face.transformed(a.inverse()).extrude(rn.normalize() * -t), tjocklek=t, rotnormal=rn,
              bockar2d=[], bockar3d=[])
    for b in bockar:
        l2 = b["linje"].transformed(a).common(platt)
        if not l2.Edges:
            continue
        e2 = l2.Edges[0]
        info = {k: b[k] for k in ("vinkel", "riktning", "radie")}
        ut["bockar2d"].append(dict(info, linje=e2))
        ut["bockar3d"].append(dict(info, linje=e2.transformed(a.inverse())))
    # sortera bockarna längs utbredningen (vänster till höger i DXF:en)
    ordning = sorted(range(len(ut["bockar2d"])), key=lambda i: (round(ut["bockar2d"][i]["linje"].CenterOfMass.x, 3), ut["bockar2d"][i]["linje"].CenterOfMass.y))
    ut["bockar2d"] = [ut["bockar2d"][i] for i in ordning]
    ut["bockar3d"] = [ut["bockar3d"][i] for i in ordning]
    return ut


def bocknot(b):
    return "%s %g° R%g" % (b["riktning"], round(b["vinkel"], 1), round(b["radie"], 1))


def platdata(kropp, utb=None, densitet=STAL_DENSITET):
    """Massa, låda och utbredd storlek."""
    s = kropp.Shape
    bb = s.optimalBoundingBox(False, False)
    d = dict(massa=s.Volume * 1e-9 * densitet, volym_cm3=s.Volume / 1000.0,
             lada=(bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    if utb is not None:
        fb = utb["face2d"].optimalBoundingBox(False, False)
        d["utbredning"] = tuple(sorted((fb.XLength, fb.YLength), reverse=True))
        d["bockar"] = [bocknot(b) for b in utb["bockar2d"]]
        d["tjocklek"] = utb["tjocklek"]
    return d


# ---------------------------------------------------------------- DXF (R12, lager per innehåll)
def _p(x):
    return "%.6f" % x


def _arc_vinklar(e):
    c = e.Curve
    p1, p2 = e.valueAt(e.FirstParameter), e.valueAt(e.LastParameter)
    a1 = math.degrees(math.atan2(p1.y - c.Center.y, p1.x - c.Center.x))
    a2 = math.degrees(math.atan2(p2.y - c.Center.y, p2.x - c.Center.x))
    if c.Axis.z < 0:            # kurvan går medurs i XY: DXF-bågen (moturs) går från slut till start
        a1, a2 = a2, a1
    return a1 % 360.0, a2 % 360.0


def _entiteter(e, lager):
    ut = []
    typ = e.Curve.TypeId
    if typ == "Part::GeomLine":
        a, b = e.Vertexes[0].Point, e.Vertexes[-1].Point
        ut.append(["0", "LINE", "8", lager, "10", _p(a.x), "20", _p(a.y), "30", "0.0", "11", _p(b.x), "21", _p(b.y), "31", "0.0"])
    elif typ == "Part::GeomCircle" and abs(e.Curve.Axis.z) > 0.9999:
        c = e.Curve
        if e.isClosed():
            ut.append(["0", "CIRCLE", "8", lager, "10", _p(c.Center.x), "20", _p(c.Center.y), "30", "0.0", "40", _p(c.Radius)])
        else:
            a1, a2 = _arc_vinklar(e)
            ut.append(["0", "ARC", "8", lager, "10", _p(c.Center.x), "20", _p(c.Center.y), "30", "0.0", "40", _p(c.Radius),
                       "50", _p(a1), "51", _p(a2)])
    else:
        pts = e.discretize(Deflection=0.01)
        for a, b in zip(pts, pts[1:]):
            ut.append(["0", "LINE", "8", lager, "10", _p(a.x), "20", _p(a.y), "30", "0.0", "11", _p(b.x), "21", _p(b.y), "31", "0.0"])
    return ut


def skriv_dxf(fil, lager, texter=()):
    """lager: [(namn, färg (ACI), [kanter])], texter: [(lager, text, x, y, höjd, vinkel)]. Koordinater i mm, Z = 0."""
    rad = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
           "0", "SECTION", "2", "TABLES",
           "0", "TABLE", "2", "LTYPE", "70", "1", "0", "LTYPE", "2", "CONTINUOUS", "70", "0", "3", "Solid line", "72", "65", "73", "0", "40", "0.0", "0", "ENDTAB",
           "0", "TABLE", "2", "LAYER", "70", str(len(lager) + len({t[0] for t in texter}))]
    namn = [l[0] for l in lager] + sorted({t[0] for t in texter} - {l[0] for l in lager})
    farg = {l[0]: l[1] for l in lager}
    for n in namn:
        rad += ["0", "LAYER", "2", n, "70", "0", "62", str(farg.get(n, 3)), "6", "CONTINUOUS"]
    rad += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    antal = 0
    for n, _, kanter in lager:
        for e in kanter:
            for ent in _entiteter(e, n):
                rad += ent
                antal += 1
    for n, s, x, y, h, vinkel in texter:
        rad += ["0", "TEXT", "8", n, "10", _p(x), "20", _p(y), "30", "0.0", "40", _p(h), "1", s.replace("°", "%%d"), "50", _p(vinkel)]
        antal += 1
    rad += ["0", "ENDSEC", "0", "EOF"]
    with open(fil, "w", encoding="ascii", errors="replace", newline="\r\n") as f:
        f.write("\n".join(rad) + "\n")
    return antal


def exportera_dxf(utb, bas):
    """Två filer som i SolidWorks-skillen: _kontur.dxf (laser) och _utbredning.dxf (kontur + bocklinjer + bocknoter)."""
    kontur = list(utb["face2d"].Edges)
    bl = [b["linje"] for b in utb["bockar2d"]]
    noter = []
    for b in utb["bockar2d"]:
        e = b["linje"]
        m = e.CenterOfMass
        d = e.Vertexes[-1].Point - e.Vertexes[0].Point
        vinkel = math.degrees(math.atan2(d.y, d.x))
        if vinkel > 90.0 or vinkel <= -90.0:
            vinkel += 180.0
        noter.append(("BOCKNOTER", bocknot(b), m.x + 2.0, m.y + 2.0, 3.5, vinkel % 360.0))
    n1 = skriv_dxf(bas + "_kontur.dxf", [("KONTUR", 7, kontur)])
    n2 = skriv_dxf(bas + "_utbredning.dxf", [("KONTUR", 7, kontur), ("BOCKLINJER", 1, bl)], noter)
    return {bas + "_kontur.dxf": n1, bas + "_utbredning.dxf": n2}
