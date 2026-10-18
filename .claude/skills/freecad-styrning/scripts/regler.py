"""Regelkontroll: produktens regler (vad en kund eller återförsäljare får ändra) och verkstadens gränser.

  python3 regler.py <modell.FCStd> [--verkstad egna/verkstad.json] [--regler egna/regler.json]

Körs automatiskt av `sammanstallning.py bygg` och skriver en rad "Regelkontroll: OK (12 regler)" eller
"Regelkontroll: 2 FEL, 1 VARNING" med en rad per anmärkning. Resultatet sparas i modellen (gruppen
Sammanstallning, egenskapen Regelkontroll) och står som not på ritningen, så att den som tar emot ritningen ser
att den är kontrollerad och med vilken version av skillen.

**Produktregler** står i konstruktionsskriptet (eller en JSON-fil med samma lista) och gör att en kund kan
ändra produkten inom ramar som verkstaden vet går att bygga:

  REGLER = [
      dict(villkor="600 <= Bredd <= 1400", text="dörrbladets bredd 600-1400"),
      dict(villkor="Hojd / Bredd <= 3.2", text="höga smala blad slår sig", niva="VARNING"),
      dict(villkor="VIKT <= 180", text="gångjärnen klarar 180 kg"),
  ]

`villkor` är ett Python-uttryck med variablerna i Variabler och de härledda storheterna VIKT (kg, alla delar),
LANGD, BREDD, HOJD (sammanställningens låda i x, y, z, mm), DELAR (antal delar) och POSITIONER; dessutom
min, max, abs, round och math. `niva` är FEL (standard) eller VARNING.

**Verkstadens gränser** läses från `verkstad.json` (FC_VERKSTAD_FIL, `egna/verkstad.json`, arbetsmappen,
~/.config/freecad-styrning/; annars `mallar/verkstad.json` i skillen med tumregler). Ett tal som är null
kontrolleras inte. Kontrollerna:
  - stång/profil längre än lagerlängden (lagerlangd_mm: VARNING, max_langd_mm: FEL); FL, FS och PL under 100 mm
    bredd räknas som stång
  - plåt (PL, bredd minst 100 mm) större än plåtformatet (platformat_mm, båda orienteringarna)
  - del tyngre än vad som lyfts för hand (max_vikt_hand_kg: VARNING) eller med verkstadens lyft (max_vikt_kg: FEL)
  - sammanställningen större än förzinkningsbadet (forzinkning_mm) eller transporten (transport_mm)
  - hål med mindre diameter än godstjockleken (min_hal_mot_tjocklek, laser och stans)
Ställ in gränserna mot den egna verkstaden en gång (kopiera mallen till egna/verkstad.json).
"""
import os, sys, json, math, argparse

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def verkstadsfil():
    for f in (os.environ.get("FC_VERKSTAD_FIL"), os.path.join(os.getcwd(), "egna", "verkstad.json"),
              os.path.join(os.getcwd(), "verkstad.json"),
              os.path.join(os.path.expanduser("~"), ".config", "freecad-styrning", "verkstad.json"),
              os.path.join(SKILL, "mallar", "verkstad.json")):
        if f and os.path.exists(f):
            return f
    return None


def las_verkstad(fil=None):
    fil = fil or verkstadsfil()
    if not fil:
        return {}, None
    with open(fil, encoding="utf-8") as f:
        d = json.load(f)
    return {k: v for k, v in d.items() if not k.startswith("_")}, fil


def skillversion():
    """Skillens version (filen VERSION) och git-commit om repot finns. FC_SKILLVERSION går före (testa.py)."""
    if os.environ.get("FC_SKILLVERSION"):
        return os.environ["FC_SKILLVERSION"]
    v = ""
    try:
        with open(os.path.join(SKILL, "VERSION"), encoding="utf-8") as f:
            v = f.read().strip()
    except OSError:
        pass
    try:
        import subprocess
        c = subprocess.run(["git", "-C", SKILL, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5)
        if c.returncode == 0 and c.stdout.strip():
            v += " (%s)" % c.stdout.strip()
    except Exception:
        pass
    return v or "okänd"


# ---------------------------------------------------------------- inne i FreeCAD
def kontrollera(doc, regler=(), variabler=None, delar=None, verkstad=None, logg=print):
    """Kör produktreglerna och verkstadsgränserna på modellen. Returnerar dict(ok, fel, varningar, antal, version)
    och sparar den som JSON i Sammanstallning.Regelkontroll (om gruppen finns)."""
    import Part
    import stal
    g = doc.getObject("Sammanstallning")
    ds = list(delar) if delar is not None else ([o for o in g.Group if hasattr(o, "Pos")] if g else
                                                  [o for o in doc.Objects if o.TypeId == "PartDesign::Body"])
    if variabler is None:
        variabler = {}
        sh = doc.getObject("Variabler")
        if sh:
            import pd
            for a in pd.alias_lista(sh):
                try:
                    variabler[a] = float(sh.get(a))
                except Exception:
                    pass
    if verkstad is None:
        verkstad, _ = las_verkstad()
    fel, varn, antal = [], [], 0
    rader = stal.materiallista(ds) if ds and all(hasattr(o, "Pos") for o in ds) else []
    vikt = sum(r["antal"] * r["vikt"] for r in rader) if rader else sum(o.Shape.Volume * 1e-9 * 7850 for o in ds)
    bb = Part.makeCompound([o.Shape for o in ds]).BoundBox if ds else None
    namn = dict(variabler, VIKT=vikt, LANGD=bb.XLength if bb else 0, BREDD=bb.YLength if bb else 0,
                HOJD=bb.ZLength if bb else 0, DELAR=len(ds), POSITIONER=len(rader),
                min=min, max=max, abs=abs, round=round, math=math)
    # produktregler
    for r in regler or ():
        antal += 1
        txt = r.get("text") or r["villkor"]
        try:
            ok = bool(eval(r["villkor"], {"__builtins__": {}}, namn))
        except Exception as e:
            fel.append("regeln '%s' går inte att räkna (%s: %s)" % (r["villkor"], type(e).__name__, e))
            continue
        if not ok:
            (varn if r.get("niva", "FEL").upper().startswith("VARN") else fel).append("%s (%s)" % (txt, r["villkor"]))
    # verkstadens gränser
    V = verkstad or {}

    def vk(nyckel):
        x = V.get(nyckel)
        return None if x in (None, "", 0) else x
    for o in ds:
        info = None
        try:
            info = stal.tolka(o.Profil, kallor=False) if hasattr(o, "Profil") else None
        except Exception:
            info = None
        L = stal.langd(o) if hasattr(o, "Group") else 0.0
        etik = o.Label
        plat = bool(info) and info["typ"] == "PL" and o.Profil.upper().startswith("PL") and info["b"] >= 100   # annars stång (FL, FS, smal PL)
        if info and not plat and L:
            antal += 1
            if vk("max_langd_mm") and L > vk("max_langd_mm"):
                fel.append("%s är %.0f mm, längre än %s mm (max_langd_mm)" % (etik, L, vk("max_langd_mm")))
            elif vk("lagerlangd_mm") and L > vk("lagerlangd_mm"):
                varn.append("%s är %.0f mm, längre än lagerlängden %s mm: skarv eller specialbeställning" % (etik, L, vk("lagerlangd_mm")))
        if plat and vk("platformat_mm"):
            antal += 1
            ob = o.Shape.optimalBoundingBox(False, False) if hasattr(o.Shape, "optimalBoundingBox") else o.Shape.BoundBox
            matt = sorted((ob.XLength, ob.YLength, ob.ZLength))[1:]
            a_, b_ = sorted(vk("platformat_mm"))
            if matt[0] > a_ + 0.5 or matt[1] > b_ + 0.5:
                fel.append("%s är %.0f x %.0f mm, större än plåtformatet %s x %s mm" % (etik, matt[1], matt[0], b_, a_))
        if hasattr(o, "Material"):
            m = o.Shape.Volume * 1e-9 * stal.densitet(o.Material)
            if vk("max_vikt_kg") and m > vk("max_vikt_kg"):
                antal += 1
                fel.append("%s väger %.0f kg, mer än verkstadens lyft %s kg" % (etik, m, vk("max_vikt_kg")))
            elif vk("max_vikt_hand_kg") and m > vk("max_vikt_hand_kg"):
                antal += 1
                varn.append("%s väger %.0f kg: lyfts inte för hand (gräns %s kg)" % (etik, m, vk("max_vikt_hand_kg")))
        if vk("min_hal_mot_tjocklek") and info:
            t = info.get("t") or info.get("tf")
            for f in getattr(o, "Group", []):
                if f.TypeId == "PartDesign::Pocket" and hasattr(f, "Halgrupp"):
                    sk = f.Profile[0] if isinstance(f.Profile, (list, tuple)) else f.Profile
                    for geo in sk.Geometry:
                        if isinstance(geo, Part.Circle) and t and 2 * geo.Radius < vk("min_hal_mot_tjocklek") * t:
                            antal += 1
                            varn.append("%s: hål Ø%g mindre än godstjockleken %g mm (laser/stans)" % (etik, 2 * geo.Radius, t))
                            break
    if bb is not None:
        lada = sorted((bb.XLength, bb.YLength, bb.ZLength), reverse=True)
        for nyckel, beskr in (("forzinkning_mm", "förzinkningsbadet"), ("transport_mm", "transporten")):
            if vk(nyckel):
                antal += 1
                gr = sorted(vk(nyckel), reverse=True)
                if any(x > y + 0.5 for x, y in zip(lada, gr)):
                    (fel if nyckel == "forzinkning_mm" else varn).append(
                        "sammanställningen %.0f x %.0f x %.0f mm ryms inte i %s %s" % (*lada, beskr, " x ".join("%g" % y for y in gr)))
    res = dict(ok=not fel, fel=fel, varningar=varn, antal=antal, version=skillversion(), datum=os.environ.get("FC_DATUM") or __import__("time").strftime("%Y-%m-%d"))
    if g is not None:
        if not hasattr(g, "Regelkontroll"):
            g.addProperty("App::PropertyString", "Regelkontroll", "Stal", "resultatet av regelkontrollen (JSON)")
        g.Regelkontroll = json.dumps(res, ensure_ascii=False)
    logg("Regelkontroll: %s (%d regler och gränser, skill %s)" % (
        "OK" if not fel and not varn else "%d FEL, %d VARNING" % (len(fel), len(varn)), antal, res["version"]))
    for s in fel:
        logg("  FEL: " + s)
    for s in varn:
        logg("  VARNING: " + s)
    return res


def not_text(res, T=None):
    """Ritningens not om regelkontrollen, t.ex. 'REGELKONTROLL 2026-10-18: OK (14 REGLER), SKILL 2026.10.18 (abc123)'."""
    if not res:
        return None
    if T is None:
        import sprak
        T = sprak.oversattare("sv")
    status = "OK" if res["ok"] and not res["varningar"] else ("%d FEL, %d VARNING" % (len(res["fel"]), len(res["varningar"])))
    return T("REGELKONTROLL %s: %s", res.get("datum", ""), "%s (%d), FREECAD-STYRNING %s" % (status, res["antal"], res["version"]))


# ---------------------------------------------------------------- kommandot
def _jobb(a):
    import FreeCAD as App
    from fcapi import logg
    doc = App.openDocument(a["fil"])
    doc.recompute()
    regler = []
    if a.get("regler"):
        with open(a["regler"], encoding="utf-8") as f:
            regler = json.load(f)
    else:
        g = doc.getObject("Sammanstallning")
        regler = json.loads(getattr(g, "Regler", "") or "[]") if g else []
    verkstad, fil = las_verkstad(a.get("verkstad"))
    logg("Verkstadens gränser: %s" % (fil or "inga"))
    res = kontrollera(doc, regler, verkstad=verkstad, logg=logg)
    doc.save()
    return dict(regelkontroll=res)


if __name__ == "__fcjobb__":
    import fcapi
    fcapi.kor_jobb(_jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("fil")
    ap.add_argument("--verkstad", default=None, help="verkstad.json (standard: se ovan)")
    ap.add_argument("--regler", default=None, help="JSON-lista med regler (standard: modellens, från konstruktionsskriptets REGLER)")
    a = vars(ap.parse_args())
    a["fil"] = os.path.abspath(a["fil"])
    r = fcapi.kor(__file__, a)
    sys.exit(0 if r["regelkontroll"]["ok"] else 1)
