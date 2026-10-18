"""Hållfasthet som överslag: balkformler för en del i en sammanställning, och FEM (CalculiX) för en enskild del.
Resultaten är kontroller för konstruktören, inte en dimensionering: lasterna och lastfaktorn ges av den som
beställer beräkningen, och en konstruktion som bär last eller skyddar mot fall (räcken, bjälklag, infästningar)
ska dimensioneras och signeras av en konstruktör.

  python3 hallfasthet.py balk <modell.FCStd> --pos hl/1 --fall fritt|konsol|fast --q 0.5 | --p 1.0
                         [--spann 1300] [--riktning upp|sida] [--gamma 1.5] [--grans 200]
  python3 hallfasthet.py fem <del.FCStd> --fast=-z --last "+x=1000" [--last "+y=500@-z"] [--pos pl/1]
                         [--natstorlek 4] [--e-modul 210000] [--fy 235]

**balk**: tvärsnittet tas ur delen (snitt mitt på delen, vinkelrätt mot dess längd, med rotradier och hål) och ger
I och W kring den axel som lasten böjer (`--riktning upp` = tvärsnittets höjdriktning, `sida` = bredden).
Fall (L = spannet, standard delens längd; q i kN/m, P i kN):
  fritt   fritt upplagd:      M = qL²/8   δ = 5qL⁴/384EI    |  M = PL/4  δ = PL³/48EI   (P mitt på)
  konsol  inspänd i ena änden: M = qL²/2   δ = qL⁴/8EI       |  M = PL    δ = PL³/3EI    (P i änden)
  fast    inspänd i båda:      M = qL²/12  δ = qL⁴/384EI     |  M = PL/8  δ = PL³/192EI  (P mitt på)
Spänningen σ = γ·M/W jämförs med fy (materialets nominella sträckgräns, kallor.py), nedböjningen (utan γ) med
L/`--grans`. E = 210 000 MPa för stål (EN 1993-1-1 3.2.6), 200 000 för austenitiskt rostfritt (EN 1993-1-4),
70 000 för aluminium (EN 1999-1-1); andra material kräver `--e-modul` och `--fy`.

**fem**: delen nätas med Gmsh (tetraedrar, `--natstorlek` mm), CalculiX räknar linjärelastiskt. `--fast=-z` låser
de plana ytor som har normalen -z och ligger längst ner (t.ex. en fotplattas undersida); flera med komma;
`+z:8` = ytorna med normalen +z i z = 8. `--last "+x=1000"` lägger 1000 N på ytorna längst ut åt +x, riktad in mot
delen (tryck); `@-z` anger en annan riktning. Ger största von Mises-spänning, största förskjutning och utnyttjandet σ/fy (utan lastfaktor om den inte
ingår i lasten). Spänningstoppar i skarpa inre hörn är nätberoende: bedöm dem med förstånd.
"""
import os, sys, math, argparse

E_MODUL = {"stal": 210000.0, "rostfritt": 200000.0, "aluminium": 70000.0}


def e_modul(material, angiven=None):
    if angiven:
        return float(angiven)
    import stal
    d = stal.densitet(material)
    for k, rho in (("aluminium", 2700.0), ("rostfritt", 8000.0), ("stal", 7850.0)):
        if d == rho:
            return E_MODUL[k]
    raise RuntimeError("Ingen E-modul för materialet %s: ange --e-modul (MPa) ur materialets datablad" % material)


def flytgrans(material, t, angiven=None):
    if angiven:
        return float(angiven), "angiven"
    import kallor
    info = kallor.material(material, t)
    if info is None or not info.get("fy"):
        raise RuntimeError("Ingen sträckgräns för %s: ange --fy (MPa) ur materialets standard eller datablad" % material)
    return float(info["fy"]), info["kalla"].get("kort", "")


def _hitta(doc, pos):
    import stal
    g = doc.getObject("Sammanstallning")
    if g is not None:
        ds = [o for o in g.Group if hasattr(o, "Pos") and (pos is None or o.Pos == pos)]
    else:
        ds = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    if not ds:
        raise RuntimeError("Hittar ingen del %s" % (pos or ""))
    return ds[0]


def balk(a):
    import FreeCAD as App
    from FreeCAD import Vector as V
    import Part
    import stal
    from fcapi import logg
    doc = App.openDocument(a["fil"])
    doc.recompute()
    o = _hitta(doc, a.get("pos"))
    rot = o.Placement.Rotation
    w, upp, sida = rot.multVec(V(0, 0, 1)), rot.multVec(V(0, 1, 0)), rot.multVec(V(1, 0, 0))
    L_del = stal.langd(o) if hasattr(o, "Group") else o.Shape.BoundBox.DiagonalLength
    L = float(a.get("spann") or L_del)
    # tvärsnittet mitt på delen
    c = o.Shape.BoundBox.Center
    snitt = o.Shape.slice(w, c.dot(w))
    if not snitt:
        raise RuntimeError("Snittet genom %s blev tomt" % o.Label)
    ytor = sorted((Part.Face(wi) for wi in snitt), key=lambda f: -f.Area)
    yta = ytor[0]
    for inre in ytor[1:]:
        yta = yta.cut(inre)
    A = yta.Area
    cg = yta.CenterOfMass
    bojning = upp if a.get("riktning", "upp") == "upp" else sida       # lastens riktning
    axel = w.cross(bojning)                                            # böjningsaxeln
    I = 0.0
    # I kring axeln genom tyngdpunkten: ∫ d² dA, d = avstånd längs lastriktningen
    m = yta.MatrixOfInertia
    n = bojning
    T = [[m.A11, m.A12, m.A13], [m.A21, m.A22, m.A23], [m.A31, m.A32, m.A33]]
    ax = [axel.x, axel.y, axel.z]
    I = sum(ax[i] * T[i][j] * ax[j] for i in range(3) for j in range(3))   # tröghetsmoment kring axeln
    cmax = max(abs((v.Point - cg).dot(n)) for v in yta.Vertexes) if yta.Vertexes else 0
    for e in yta.Edges:                                                # rundade hörn: kolla även kanternas punkter
        for p in e.discretize(12):
            cmax = max(cmax, abs((p - cg).dot(n)))
    W = I / cmax
    E = e_modul(o.Material, a.get("e_modul"))
    try:
        info = stal.tolka(o.Profil, kallor=False)
        t = info.get("t") or info.get("tf") or info.get("d")
    except Exception:
        t = None
    fy, fy_kalla = flytgrans(o.Material, t, a.get("fy"))
    q, P = a.get("q"), a.get("p")
    fall = a["fall"]
    if (q is None) == (P is None):
        raise RuntimeError("Ange antingen --q (kN/m) eller --p (kN)")
    if q is not None:
        qq = float(q)                          # kN/m = N/mm
        M, d = {"fritt": (qq * L ** 2 / 8, 5 * qq * L ** 4 / 384), "konsol": (qq * L ** 2 / 2, qq * L ** 4 / 8),
                "fast": (qq * L ** 2 / 12, qq * L ** 4 / 384)}[fall]
        last = "q = %g kN/m" % qq
    else:
        PP = float(P) * 1000.0                 # N
        M, d = {"fritt": (PP * L / 4, PP * L ** 3 / 48), "konsol": (PP * L, PP * L ** 3 / 3),
                "fast": (PP * L / 8, PP * L ** 3 / 192)}[fall]
        last = "P = %g kN" % float(P)
    d = d / (E * I)
    gamma = float(a.get("gamma") or 1.5)
    sigma = gamma * M / W
    grans = float(a.get("grans") or 200)
    logg("Del %s (%s, %s), %s, spann %.0f mm, last %s åt %s" % (o.Pos if hasattr(o, "Pos") else o.Label, getattr(o, "Profil", ""),
                                                            o.Material, {"fritt": "fritt upplagd", "konsol": "konsol", "fast": "inspänd i båda ändar"}[fall],
                                                            L, last, a.get("riktning", "upp")))
    logg("Tvärsnitt ur modellen: A = %.0f mm², I = %.4g mm⁴, W = %.4g mm³ (avstånd till yttersta fiber %.1f mm)" % (A, I, W, cmax))
    logg("M = %.3g kNm, σ = γ·M/W = %.1f · %.3g / %.4g = %.0f MPa mot fy %.0f MPa (%s): utnyttjande %.0f %%" % (
        M / 1e6, gamma, M, W, sigma, fy, fy_kalla, 100 * sigma / fy))
    logg("Nedböjning δ = %.1f mm (utan lastfaktor) mot L/%g = %.1f mm: %s" % (d, grans, L / grans, "OK" if d <= L / grans else "FÖR STOR"))
    logg("Bedömning: %s (överslag – ersätter inte konstruktörens beräkning)" % ("OK" if sigma <= fy and d <= L / grans else "INTE OK"))
    return dict(A=A, I=I, W=W, M=M, sigma=sigma, fy=fy, utnyttjande=sigma / fy, nedbojning=d, godkand=sigma <= fy and d <= L / grans)


def _ytor(shape, spec):
    """'-z' -> namnen på de plana ytor vars normal är -z och som ligger längst ut åt -z (inom 0,5 mm);
    '+z:8' -> ytorna med normalen +z i z = 8 (t.ex. hyllbenets ovansida i en konsol)."""
    from FreeCAD import Vector as V
    spec, _, lage = spec.strip().partition(":")
    tecken, axel = (-1 if spec[0] == "-" else 1), spec.lstrip("+-").lower()
    n = V(*[tecken * (1.0 if axel == k else 0.0) for k in "xyz"])
    kand = [(i, f) for i, f in enumerate(shape.Faces) if f.Surface.TypeId == "Part::GeomPlane" and f.normalAt(0, 0).dot(n) > 0.999]
    if not kand:
        raise RuntimeError("Ingen plan yta med normalen %s" % spec)
    if lage:
        k = "xyz".index(axel)
        valda = ["Face%d" % (i + 1) for i, f in kand if abs(f.CenterOfMass[k] - float(lage)) < 0.5]
        if not valda:
            raise RuntimeError("Ingen yta med normalen %s i %s = %s" % (spec, axel, lage))
        return valda, n
    ytterst = max(f.CenterOfMass.dot(n) for _, f in kand)
    return ["Face%d" % (i + 1) for i, f in kand if f.CenterOfMass.dot(n) > ytterst - 0.5], n


def fem(a):
    import FreeCAD as App
    from FreeCAD import Vector as V
    import ObjectsFem
    from femmesh.gmshtools import GmshTools
    from femtools import ccxtools
    from fcapi import logg
    import stal
    doc = App.openDocument(a["fil"])
    doc.recompute()
    o = _hitta(doc, a.get("pos"))
    s = o.Shape
    E = e_modul(getattr(o, "Material", "Stål"), a.get("e_modul"))
    try:
        try:                                     # godstjockleken för fy: ur profilen, annars okänd (tunnaste området)
            info = stal.tolka(o.Profil, kallor=False)
            t = info.get("t") or info.get("tf") or info.get("d")
        except Exception:
            t = None
        fy, kalla = flytgrans(getattr(o, "Material", "S235JR"), t, a.get("fy"))
    except RuntimeError:
        if not a.get("fy"):
            raise
        fy, kalla = float(a["fy"]), "angiven"
    an = ObjectsFem.makeAnalysis(doc, "Analys")
    sol = ObjectsFem.makeSolverCalculiXCcxTools(doc, "CalculiX")
    an.addObject(sol)
    mat = ObjectsFem.makeMaterialSolid(doc, "Material")
    m = dict(mat.Material)
    m.update(Name=getattr(o, "Material", "Stål"), YoungsModulus="%g MPa" % E, PoissonRatio="0.30",
             Density="%g kg/m^3" % stal.densitet(getattr(o, "Material", "")))
    mat.Material = m
    an.addObject(mat)
    for spec in [x for x in a["fast"].split(",") if x.strip()]:
        ytor, _ = _ytor(s, spec)
        fx = ObjectsFem.makeConstraintFixed(doc, "Fast")
        fx.References = [(o, tuple(ytor))]
        an.addObject(fx)
        logg("Fast: %s (%s)" % (spec, ", ".join(ytor)))
    total = 0.0
    for spec in a["last"]:
        yt, kraft = spec.split("=")
        riktn = None
        if "@" in kraft:
            kraft, riktn = kraft.split("@")
        ytor, n = _ytor(s, yt)
        F = ObjectsFem.makeConstraintForce(doc, "Last")
        F.References = [(o, tuple(ytor))]
        F.Force = "%g N" % float(kraft)
        d = n * -1 if riktn is None else V(*[(-1 if riktn.strip()[0] == "-" else 1) * (1.0 if riktn.strip().lstrip("+-").lower() == k else 0.0) for k in "xyz"])
        # riktningen ges av en kant eller yta i FreeCAD; här: en yta vars normal är lastriktningen, eller Reversed
        F.Direction = (o, [ytor[0]])
        F.Reversed = d.dot(n) < 0
        if riktn is not None and abs(abs(d.dot(n)) - 1) > 1e-6:
            dir_ytor, _ = _ytor(s, riktn)
            F.Direction = (o, [dir_ytor[0]])
            F.Reversed = False
        an.addObject(F)
        total += float(kraft)
        mot = ("-" if yt.strip()[0] == "+" else "+") + yt.strip().lstrip("+-").split(":")[0]
        logg("Last: %s N på %s (%s), riktning %s" % (kraft, yt, ", ".join(ytor), riktn or "in mot delen (%s)" % mot))
    mesh = ObjectsFem.makeMeshGmsh(doc, "Nat")
    mesh.Shape = o
    mesh.CharacteristicLengthMax = "%g mm" % float(a.get("natstorlek") or 4)
    mesh.ElementOrder = "2nd"
    an.addObject(mesh)
    doc.recompute()
    fel = GmshTools(mesh).create_mesh()
    if fel:
        raise RuntimeError("Gmsh: %s" % fel)
    logg("Nät: %d noder, %d element" % (mesh.FemMesh.NodeCount, mesh.FemMesh.VolumeCount))
    doc.recompute()
    ft = ccxtools.FemToolsCcx(an, sol)
    ft.update_objects()
    ft.setup_working_dir()
    ft.setup_ccx()
    msg = ft.check_prerequisites()
    if msg:
        raise RuntimeError("CalculiX: %s" % msg)
    ft.write_inp_file()
    ft.ccx_run()
    ft.load_results()
    res = next((x for x in an.Group if x.TypeId == "Fem::FemResultObjectPython"), None)
    if res is None:
        raise RuntimeError("CalculiX gav inga resultat (se %s)" % ft.working_dir)
    vm = max(res.vonMises)
    u = max(res.DisplacementLengths)
    logg("von Mises max %.0f MPa mot fy %.0f MPa (%s): utnyttjande %.0f %%; största förskjutning %.3f mm; total last %.0f N" % (
        vm, fy, kalla, 100 * vm / fy, u, total))
    logg("Bedömning: %s (linjärelastisk FEM, lasten utan faktor om den inte ingår; ersätter inte konstruktörens beräkning)" % (
        "OK" if vm <= fy else "INTE OK"))
    ut = os.path.splitext(a["fil"])[0] + "_fem.FCStd"
    doc.saveAs(ut)
    logg("Sparat med analysen (öppna i FreeCAD för att se spänningarna): %s" % ut)
    return dict(von_mises=vm, forskjutning=u, fy=fy, utnyttjande=vm / fy, godkand=vm <= fy)


if __name__ == "__fcjobb__":
    import fcapi
    fcapi.kor_jobb(lambda a: balk(a) if a["lage"] == "balk" else fem(a))
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lage", choices=["balk", "fem"])
    ap.add_argument("fil")
    ap.add_argument("--pos", default=None)
    ap.add_argument("--fall", choices=["fritt", "konsol", "fast"], default="fritt")
    ap.add_argument("--q", type=float, default=None, help="jämnt fördelad last kN/m")
    ap.add_argument("--p", type=float, default=None, help="punktlast kN")
    ap.add_argument("--spann", type=float, default=None)
    ap.add_argument("--riktning", choices=["upp", "sida"], default="upp")
    ap.add_argument("--gamma", type=float, default=1.5, help="lastfaktor på spänningen (standard 1,5 för variabel last)")
    ap.add_argument("--grans", type=float, default=200, help="nedböjningsgräns L/n")
    ap.add_argument("--fast", default="-z")
    ap.add_argument("--last", action="append", default=[])
    ap.add_argument("--natstorlek", type=float, default=4)
    ap.add_argument("--e-modul", dest="e_modul", type=float, default=None)
    ap.add_argument("--fy", type=float, default=None)
    a = vars(ap.parse_args())
    a["fil"] = os.path.abspath(a["fil"])
    if a["lage"] == "fem" and not a["last"]:
        ap.error("fem kräver minst en --last")
    r = fcapi.kor(__file__, a)
    sys.exit(0 if r.get("godkand") else 2)
