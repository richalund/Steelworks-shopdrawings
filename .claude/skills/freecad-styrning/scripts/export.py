"""Export av modellen till andra program: glTF (webbläsare, mobil, WeChat), IFC (arkitekter, BIM), STEP, STL.

  python3 export.py <modell.FCStd> [--format glb,ifc,step,stl] [--utan-omgivning] [--ut <mapp>]

- glb (glTF binär): en fil som öppnas direkt i webbläsaren (t.ex. gltf-viewer.donmccurdy.com, Windows 3D Viewer,
  macOS Förhandsvisning) och går att skicka till en kund, med delarnas färger och utseende (k.utseende).
- ifc (IFC4): varje del som ett byggelement (IfcMember/IfcPlate/IfcBuildingElementProxy) med positionsnummer,
  profil och material som egenskaper, för arkitektens samordningsmodell. Kräver ifcopenshell
  (installera_linux.sh installerar det i /opt/freecad-extra).
- step: hela sammanställningen som en STEP-fil (AP214) med en kropp per del.
- stl: för 3D-utskrift av en modell i skala.
Standard är glb och step. Referenskropparna (Omgivning) följer med i glb, inte i ifc/step; --utan-omgivning tar
bort dem ur glb också. Filerna heter <modell>.glb, .ifc, .step och .stl.
"""
import os, sys, argparse

EXTRA = "/opt/freecad-extra"


def _jobb(a):
    import FreeCAD as App, FreeCADGui as Gui
    from fcapi import logg, pump
    doc = App.openDocument(a["fil"])
    doc.recompute()
    pump(0.3)
    grp = doc.getObject("Sammanstallning")
    delar = [o for o in (grp.Group if grp else []) if hasattr(o, "Pos")]
    if not delar:
        delar = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    omg = doc.getObject("Omgivning")
    omgivning = [o for o in (omg.Group if omg else [])] if not a.get("utan_omgivning") else []
    utmapp = os.path.abspath(a["ut"]) if a.get("ut") else os.path.dirname(a["fil"])
    os.makedirs(utmapp, exist_ok=True)
    bas = os.path.join(utmapp, os.path.splitext(os.path.basename(a["fil"]))[0])
    format_ = [f.strip().lower() for f in a["format"].split(",") if f.strip()]
    ut = {}
    if "glb" in format_ or "gltf" in format_:
        import ImportGui
        try:                                           # utseendet som i 3D-bilderna (rendera.py)
            import rendera, json
            val = json.loads(getattr(grp, "Utseende", "") or "{}") if grp else {}
            for o in delar:
                namn = next((v for k, v in sorted(val.items(), key=lambda kv: -len(kv[0])) if k != "alla" and o.Pos.startswith(k)),
                            val.get("alla")) if hasattr(o, "Pos") else None
                namn = namn or rendera.auto_utseende(getattr(o, "Material", ""))
                if namn:
                    farg, _, genom = rendera.UTSEENDE[namn]
                    o.ViewObject.ShapeColor, o.ViewObject.Transparency = farg, genom
        except Exception as e:
            logg("Obs: utseende i glb:", e)
        fil = bas + ".glb"
        ImportGui.export(delar + omgivning, fil)
        ut["glb"] = fil
        logg("glTF: %s (%d delar%s, %.0f kB)" % (fil, len(delar), " + %d referenskroppar" % len(omgivning) if omgivning else "",
                                              os.path.getsize(fil) / 1024))
    if "step" in format_:
        import ImportGui
        fil = bas + ".step"
        ImportGui.export(delar, fil)
        ut["step"] = fil
        logg("STEP:", fil)
    if "stl" in format_:
        import Mesh, Part
        fil = bas + ".stl"
        Mesh.export(delar, fil)
        ut["stl"] = fil
        logg("STL:", fil)
    if "ifc" in format_:
        if os.path.isdir(EXTRA) and EXTRA not in sys.path:
            sys.path.append(EXTRA)
        try:
            import ifcopenshell  # noqa: F401
        except ImportError:
            raise RuntimeError("IFC kräver ifcopenshell: kör installera_linux.sh (lägger det i %s)" % EXTRA)
        ut["ifc"] = ifc(doc, delar, bas + ".ifc", logg)
    return dict(filer=ut)


def ifc(doc, delar, fil, logg):
    """IFC4 med ifcopenshell direkt: projekt, plats, byggnad, våning och en produkt per del med triangulerad
    geometri (IfcTriangulatedFaceSet) och egenskaperna Pos, Profil, Material i en egen egenskapsuppsättning."""
    import ifcopenshell, ifcopenshell.guid
    import stal
    f = ifcopenshell.file(schema="IFC4")
    ny = lambda typ, **kw: f.create_entity(typ, GlobalId=ifcopenshell.guid.new(), **kw)
    enh = f.createIfcUnitAssignment([f.createIfcSIUnit(None, "LENGTHUNIT", "MILLI", "METRE")])
    ctx = f.createIfcGeometricRepresentationContext(None, "Model", 3, 1.0e-5,
                                                    f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0))), None)
    sub = f.createIfcGeometricRepresentationSubContext("Body", "Model", None, None, None, None, ctx, None, "MODEL_VIEW", None)
    proj = ny("IfcProject", Name=doc.Label, UnitsInContext=enh, RepresentationContexts=[ctx])
    origo = f.createIfcLocalPlacement(None, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0))))
    plats = ny("IfcSite", Name="Plats", ObjectPlacement=origo)
    hus = ny("IfcBuilding", Name="Byggnad", ObjectPlacement=origo)
    plan = ny("IfcBuildingStorey", Name="Plan", ObjectPlacement=origo)
    for a_, b_ in ((proj, plats), (plats, hus), (hus, plan)):
        ny("IfcRelAggregates", RelatingObject=a_, RelatedObjects=[b_])
    produkter = []
    for o in delar:
        s = o.Shape.copy()
        pts, tri = s.tessellate(0.3)
        if not tri:
            continue
        lista = f.createIfcCartesianPointList3D([tuple(float(c) for c in p) for p in pts])
        yta = f.createIfcTriangulatedFaceSet(lista, None, None, [tuple(i + 1 for i in t) for t in tri], None)
        rep = f.createIfcProductDefinitionShape(None, None, [f.createIfcShapeRepresentation(sub, "Body", "Tessellation", [yta])])
        profil = getattr(o, "Profil", "")
        try:
            typ = stal.tolka(profil, kallor=False)["typ"]
        except Exception:
            typ = None
        klass = "IfcPlate" if typ == "PL" or "BOCKAD" in profil.upper() or profil.upper().startswith("GLAS") else \
            ("IfcMember" if typ else "IfcBuildingElementProxy")
        p = ny(klass, Name="%s %s" % (getattr(o, "Pos", ""), profil), ObjectPlacement=origo, Representation=rep,
               Tag=getattr(o, "Pos", ""))
        egen = [f.createIfcPropertySingleValue(n, None, f.createIfcLabel(str(getattr(o, n, ""))), None) for n in ("Pos", "Profil", "Material")]
        ps = ny("IfcPropertySet", Name="FreeCAD-styrning", HasProperties=egen)
        ny("IfcRelDefinesByProperties", RelatedObjects=[p], RelatingPropertyDefinition=ps)
        mat = f.createIfcMaterial(str(getattr(o, "Material", "") or "Stål"), None, None)
        f.createIfcRelAssociatesMaterial(ifcopenshell.guid.new(), None, None, None, [p], mat)
        produkter.append(p)
    ny("IfcRelContainedInSpatialStructure", RelatedElements=produkter, RelatingStructure=plan)
    f.write(fil)
    logg("IFC: %s (%d delar, IFC4)" % (fil, len(produkter)))
    return fil


if __name__ == "__fcjobb__":
    import fcapi
    fcapi.kor_jobb(_jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("fil")
    ap.add_argument("--format", default="glb,step")
    ap.add_argument("--utan-omgivning", dest="utan_omgivning", action="store_true")
    ap.add_argument("--ut", default=None)
    a = vars(ap.parse_args())
    a["fil"] = os.path.abspath(a["fil"])
    fcapi.kor(__file__, a)
