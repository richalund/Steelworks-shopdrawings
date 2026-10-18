"""Prisunderlag ur modellen: mängder per del och totalt, och ett pris om verkstadens priser finns.

  python3 kalkyl.py <modell.FCStd> [--priser egna/priser.json] [--yta pulverlack] [--antal 1] [--ut <mapp>]

Mängderna räknas ur geometrin (FreeCAD), för en sammanställning (delar med positionsnummer) eller en enstaka
del (Part Design, SheetMetal):
  - vikt per material (densitet efter materialet: stål, rostfritt, aluminium, mässing, glas, trä)
  - yta (m2) för ytbehandling: lack, förzinkning, patinering
  - kap: raka kap (två per stång/profil) och geringar (sneda kap, Pocket "Gering")
  - hål per diameter (hålgrupperna), borrade i profiler och skurna i plåt
  - laser: skärlängd (m) och antal håltagningar (insticksställen) för plåtar (PL med bredd >= 100) och
    bockade delar
  - bockningar i bockade delar (SheetMetal)
  - svets: uppskattad längd (m) = kontaktkanterna mellan delar som rör varandra (yttre konturen av varje
    kontaktyta). Uppskattning: verkligt svetsomfång bestäms av konstruktören.
Ger `<modell>_kalkyl.csv` (öppnas i Excel) och `<modell>_kalkyl.json` (till beställningspaketet, paket.py).

**Priser** läses från `--priser`, FC_PRISER_FIL, `egna/priser.json` eller `~/.config/freecad-styrning/priser.json`
(mall: `mallar/priser.json`, alla priser 0 tills verkstaden fyllt i dem). Priserna hör till verkstaden och ligger
aldrig i skillen. Utan priser blir det bara mängder.
"""
import os, sys, json, argparse

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def prisfil(fil=None):
    for f in (fil, os.environ.get("FC_PRISER_FIL"), os.path.join(os.getcwd(), "egna", "priser.json"),
              os.path.join(os.path.expanduser("~"), ".config", "freecad-styrning", "priser.json")):
        if f and os.path.exists(f):
            return f
    return None


def _materialpris(priser, material):
    tab = priser.get("material_kr_per_kg", {})
    m = (material or "").upper().replace(" ", "")
    bast = max((k for k in tab if not k.startswith("_") and k != "standard" and m.startswith(k.upper().replace(" ", ""))),
               key=len, default=None)
    return float(tab[bast] if bast else tab.get("standard", 0) or 0)


def pris(mangder, priser, yta=None, antal=1):
    """Pris ur mängderna och prislistan: rader (text, mängd, enhet, á-pris, summa) och totalsumma."""
    rader = []

    def rad(text, mangd, enhet, apris):
        if mangd and apris:
            rader.append((text, mangd, enhet, apris, mangd * apris))
    for mat, kg in sorted(mangder["vikt_per_material"].items()):
        rad("Material %s" % mat, kg * antal, "kg", _materialpris(priser, mat))
    ytor = priser.get("yta_kr_per_m2", {})
    ytnamn = yta or priser.get("yta_standard")
    if ytnamn:
        rad("Ytbehandling %s" % ytnamn, mangder["yta_m2"] * antal, "m2", float(ytor.get(ytnamn, 0) or 0))
    for nyckel, text, enhet in (("kap", "Kap", "st"), ("geringar", "Geringskap", "st"), ("hal", "Hål", "st"),
                                ("laser_m", "Laserskärning", "m"), ("instick", "Håltagningar laser", "st"),
                                ("bockningar", "Bockningar", "st"), ("svets_m", "Svets (uppskattad)", "m"),
                                ("delar", "Hantering per del", "st")):
        rad(text, mangder[nyckel] * antal, enhet, float(priser.get({"kap": "kap_kr_st", "geringar": "gering_kr_st", "hal": "hal_kr_st",
                                                                     "laser_m": "laser_kr_per_m", "instick": "instick_kr_st",
                                                                     "bockningar": "bock_kr_st", "svets_m": "svets_kr_per_m",
                                                                     "delar": "del_kr_st"}[nyckel], 0) or 0))
    if priser.get("start_kr"):
        rader.append(("Startkostnad per order", 1, "st", float(priser["start_kr"]), float(priser["start_kr"])))
    summa = sum(r[4] for r in rader)
    pa = float(priser.get("paslag_procent", 0) or 0)
    if pa:
        rader.append(("Påslag %g %%" % pa, summa, "kr", pa / 100.0, summa * pa / 100.0))
        summa *= 1 + pa / 100.0
    return rader, summa


# ---------------------------------------------------------------- inne i FreeCAD
def _platta(s):
    """Skuren platta: prismatisk kropp (plana ytor parallella eller vinkelräta mot den största ytan, cylindrar
    vinkelräta) med tjockleken under halva minsta sidan."""
    plan = [f for f in s.Faces if f.Surface.TypeId == "Part::GeomPlane"]
    if not plan:
        return False
    n = max(plan, key=lambda f: f.Area).normalAt(0, 0)
    for f in s.Faces:
        if f.Surface.TypeId == "Part::GeomPlane":
            k = abs(f.normalAt(0, 0).dot(n))
            if 1e-6 < k < 1 - 1e-6:
                return False
        elif f.Surface.TypeId == "Part::GeomCylinder":
            if abs(abs(f.Surface.Axis.dot(n)) - 1) > 1e-6:
                return False
        else:
            return False
    proj = [v.Point.dot(n) for v in s.Vertexes]
    t = max(proj) - min(proj)
    bb = s.BoundBox
    sidor = sorted((bb.XLength, bb.YLength, bb.ZLength))[1:]
    return t < 0.5 * min(sidor)


def mangder(doc, logg=print):
    import Part
    import stal
    g = doc.getObject("Sammanstallning")
    if g is not None:
        ds = [o for o in g.Group if hasattr(o, "Pos")]
    else:                                        # enstaka del: slutliga solider (Body, SheetMetal), inte utbredningen
        kand = [o for o in doc.Objects if o.Name != "Utbredning" and getattr(o, "Shape", None) is not None and
                not o.TypeId.startswith(("TechDraw::", "Sketcher::", "Spreadsheet::", "App::", "PartDesign::Feature", "PartDesign::Pad",
                                         "PartDesign::Pocket", "PartDesign::Hole", "PartDesign::Fillet", "PartDesign::Chamfer",
                                         "PartDesign::Revolution", "PartDesign::Additive", "PartDesign::Subtractive", "PartDesign::Linear",
                                         "PartDesign::Polar", "PartDesign::Mirrored", "PartDesign::MultiTransform", "PartDesign::Groove",
                                         "PartDesign::Thickness", "PartDesign::Draft", "PartDesign::Boolean"))
                and o.Shape.Solids and (o.TypeId == "PartDesign::Body" or o.getParentGeoFeatureGroup() is None)]
        ds = [o for o in kand if not any(p in kand for p in o.InList)]
    per_del, vikt_mat = [], {}
    tot = dict(kap=0, geringar=0, hal=0, laser_m=0.0, instick=0, bockningar=0, yta_m2=0.0, vikt=0.0, delar=len(ds))
    halper, inkop = {}, []
    for o in ds:
        if hasattr(o, "Vikt") and getattr(o, "Material", "") == "INKÖP":     # inköpt detalj (k.inkop)
            inkop.append(dict(pos=o.Pos, text=o.Profil, vikt=float(o.Vikt or 0)))
            tot["delar"] -= 1
            continue
        mat = getattr(o, "Material", "") or "Stål"
        profil = getattr(o, "Profil", "") or o.Label
        s = o.Shape
        vikt = float(getattr(o, "Vikt", 0) or 0) or s.Volume * 1e-9 * stal.densitet(mat)
        info = None
        try:
            info = stal.tolka(profil, kallor=False)
        except Exception:
            pass
        feat = getattr(o, "Group", [])
        geringar = sum(1 for f in feat if f.TypeId == "PartDesign::Pocket" and f.Name.startswith("Gering"))
        hal = 0
        for f in feat:
            if f.TypeId == "PartDesign::Pocket" and hasattr(f, "Halgrupp"):
                sk = f.Profile[0] if isinstance(f.Profile, (list, tuple)) else f.Profile
                for geo in sk.Geometry:
                    if isinstance(geo, Part.Circle):
                        hal += 1
                        d = round(geo.Radius * 2, 1)
                        halper[d] = halper.get(d, 0) + 1
        bockad = o.TypeId != "PartDesign::Body"
        plat = bockad or (info is not None and info["typ"] == "PL" and profil.upper().startswith("PL") and info["b"] >= 100) or (
            not hasattr(o, "Profil") and _platta(s))
        laser, instick, bock = 0.0, 0, 0
        if plat:
            plan = [f for f in s.Faces if f.Surface.TypeId == "Part::GeomPlane"]
            f = max(plan, key=lambda f: f.Area) if plan else None
            if bockad:                                   # bockad plåt: utbredningens kontur och bockarna
                try:
                    import plat as P
                    utb = P.utbred(s, P.rotyta(s, f.normalAt(0, 0)))
                    f, bock = utb["face2d"], len(utb["bockar2d"])
                except Exception as e:
                    logg("OBS: %s kunde inte bredas ut för prisunderlaget (%s)" % (o.Label, e))
                    bock = sum(1 for f_ in s.Faces if f_.Surface.TypeId == "Part::GeomCylinder") // 2
            if f is not None:
                laser = sum(w.Length for w in f.Wires) / 1000.0
                instick = len(f.Wires)
        kap = 0 if plat else (2 if info is not None and info["typ"] != "PL" or profil.upper().startswith(("FL", "FS", "PL")) else 0)
        kap = max(kap - min(geringar, 2), 0)
        yta = s.Area / 1e6
        per_del.append(dict(namn=o.Label, pos=getattr(o, "Pos", ""), profil=profil, material=mat, vikt=vikt, yta_m2=yta,
                            langd=stal.langd(o) if o.TypeId == "PartDesign::Body" else 0.0, kap=kap, geringar=geringar,
                            hal=hal, laser_m=laser, instick=instick, bockningar=bock))
        vikt_mat[mat] = vikt_mat.get(mat, 0.0) + vikt
        for k, v in (("kap", kap), ("geringar", geringar), ("hal", hal), ("laser_m", laser), ("instick", instick),
                     ("bockningar", bock), ("yta_m2", yta), ("vikt", vikt)):
            tot[k] += v
    # svets: kontaktkanter mellan delar som rör varandra (yttre slingan av varje kontaktyta)
    svets, fogar = 0.0, 0
    for i, o1 in enumerate(ds):
        b1 = o1.Shape.BoundBox
        b1.enlarge(0.2)
        for o2 in ds[i + 1:]:
            if not b1.intersect(o2.Shape.BoundBox):
                continue
            try:
                if o1.Shape.distToShape(o2.Shape)[0] > 0.05:
                    continue
                kanter = o1.Shape.section(o2.Shape).Edges
            except Exception:
                continue
            if not kanter:
                continue
            slingor = [Part.Wire(w) for w in Part.__sortEdges__(kanter) if w] if len(kanter) > 1 else [Part.Wire(kanter)]
            yttre = []
            for w in slingor:                               # släpp slingor som ligger inuti en annan (rörets insida)
                bw = w.BoundBox
                if any(w2 is not w and w2.BoundBox.isInside(bw.getPoint(0)) and w2.BoundBox.isInside(bw.getPoint(6))
                       and w2.BoundBox.DiagonalLength > bw.DiagonalLength + 0.1 for w2 in slingor):
                    continue
                yttre.append(w)
            L = sum(w.Length for w in yttre)
            if L > 1.0:
                svets += L
                fogar += 1
    tot["svets_m"] = svets / 1000.0
    tot["fogar"] = fogar
    tot["inkopta"] = len(inkop)
    return dict(per_del=per_del, inkop=inkop, totalt=tot, vikt_per_material=vikt_mat, hal_per_diameter={str(k): v for k, v in sorted(halper.items())},
                **{k: tot[k] for k in tot})


def _jobb(a):
    import FreeCAD as App
    from fcapi import logg
    doc = App.openDocument(a["fil"])
    doc.recompute()
    m = mangder(doc, logg)
    t = m["totalt"]
    logg("Delar %d (+ %d inköpta), vikt %.1f kg (%s)" % (t["delar"], t["inkopta"], t["vikt"], ", ".join("%s %.1f kg" % kv for kv in sorted(m["vikt_per_material"].items()))))
    logg("Yta %.2f m2, kap %d, geringar %d, hål %d (%s), laser %.2f m / %d håltagningar, bockningar %d, svets ca %.1f m i %d fogar" % (
        t["yta_m2"], t["kap"], t["geringar"], t["hal"], ", ".join("Ø%s: %d" % kv for kv in m["hal_per_diameter"].items()) or "-",
        t["laser_m"], t["instick"], t["bockningar"], t["svets_m"], t["fogar"]))
    return m


def _efterbehandla(m, a):
    utmapp = os.path.abspath(a["ut"]) if a.get("ut") else os.path.dirname(a["fil"])
    os.makedirs(utmapp, exist_ok=True)
    bas = os.path.join(utmapp, os.path.splitext(os.path.basename(a["fil"]))[0])
    fil = prisfil(a.get("priser"))
    priser = {}
    if fil:
        with open(fil, encoding="utf-8") as f:
            priser = json.load(f)
    antal = int(a.get("antal") or 1)
    prisrader, summa = pris(m, priser, a.get("yta"), antal) if priser else ([], 0.0)
    m.update(antal=antal, prisfil=fil, prisrader=prisrader, summa_kr=summa)
    for k in ("ok", "dialoger"):
        m.pop(k, None)
    with open(bas + "_kalkyl.json", "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    tal = lambda x, d=2: ("%.*f" % (d, x)).replace(".", ",")
    with open(bas + "_kalkyl.csv", "w", encoding="utf-8-sig") as f:
        f.write("PRISUNDERLAG;%s;antal %d\n\n" % (os.path.basename(a["fil"]), antal))
        f.write("DEL;POS;PROFIL;MATERIAL;LÄNGD mm;VIKT kg;YTA m2;KAP;GERINGAR;HÅL;LASER m;HÅLTAGNINGAR;BOCKNINGAR\n")
        for d in m["per_del"]:
            f.write("%s;%s;%s;%s;%s;%s;%s;%d;%d;%d;%s;%d;%d\n" % (d["namn"], d["pos"], d["profil"], d["material"], tal(d["langd"], 0),
                                                              tal(d["vikt"]), tal(d["yta_m2"], 3), d["kap"], d["geringar"], d["hal"],
                                                              tal(d["laser_m"]), d["instick"], d["bockningar"]))
        t = m["totalt"]
        f.write("\nTOTALT PER ST;;;;;%s;%s;%d;%d;%d;%s;%d;%d\n" % (tal(t["vikt"]), tal(t["yta_m2"], 3), t["kap"], t["geringar"], t["hal"],
                                                            tal(t["laser_m"]), t["instick"], t["bockningar"]))
        f.write("SVETS (UPPSKATTAD);%s m;%d fogar\n" % (tal(t["svets_m"]), t["fogar"]))
        for mat, kg in sorted(m["vikt_per_material"].items()):
            f.write("VIKT %s;%s kg\n" % (mat, tal(kg)))
        for d, n in m["hal_per_diameter"].items():
            f.write("HÅL Ø%s;%d st\n" % (d, n))
        if m.get("inkop"):
            f.write("\nINKÖP;POS;ANTAL\n")
            per = {}
            for x in m["inkop"]:
                per.setdefault((x["text"], x["pos"]), 0)
                per[(x["text"], x["pos"])] += 1
            for (text, pos), n in sorted(per.items()):
                f.write("%s;%s;%d\n" % (text, pos, n * antal))
        if prisrader:
            f.write("\nPRIS (%s);MÄNGD;ENHET;Á-PRIS;SUMMA kr\n" % os.path.basename(fil))
            for text, mangd, enhet, apris, s in prisrader:
                f.write("%s;%s;%s;%s;%s\n" % (text, tal(mangd), enhet, tal(apris), tal(s, 0)))
            f.write("SUMMA;;;;%s\n" % tal(summa, 0))
    print("Prisunderlag: %s, %s%s" % (bas + "_kalkyl.csv", os.path.basename(bas + "_kalkyl.json"),
                                      "; pris %s kr för %d st (%s)" % (tal(summa, 0), antal, os.path.basename(fil)) if prisrader
                                      else "; inga priser (fyll i egna/priser.json efter mallar/priser.json)"))
    return m


if __name__ == "__fcjobb__":
    import fcapi
    fcapi.kor_jobb(_jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("fil")
    ap.add_argument("--priser", default=None)
    ap.add_argument("--yta", default=None, help="ytbehandling (nyckel i priser.json yta_kr_per_m2), t.ex. pulverlack")
    ap.add_argument("--antal", type=int, default=1)
    ap.add_argument("--ut", default=None)
    a = vars(ap.parse_args())
    a["fil"] = os.path.abspath(a["fil"])
    _efterbehandla(fcapi.kor(__file__, a), a)
