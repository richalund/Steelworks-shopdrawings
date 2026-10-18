"""Register över inköpta komponenter (gångjärn, lås, handtag, dörrstängare, glas, motorer, bultar) med mått ur
leverantörens datablad. Skillen innehåller inga komponentdata: de söks upp på nätet hos leverantörer i landet där
skillen används (`land` i foretag.json) och sparas här med källa, så att samma komponent kan ritas igen.

  python3 komponenter.py visa [--typ gångjärn]
  python3 komponenter.py lagg-till --id gj-120-rf --typ gångjärn --benamning "GÅNGJÄRN 120 ROSTFRITT" \\
          --tillverkare "Leverantör AB" --artikel 12345 --cylinder 20x120 | --lada 100x30x150 --vikt 0.5 \\
          --kalla https://leverantor.se/produkt/12345 [--last "80 kg/par"] [--land SE] [--anteckning "..."]
  python3 komponenter.py ta-bort --id gj-120-rf

Registret är `egna/komponenter.json` (eller FC_KOMPONENT_FIL, eller ~/.config/freecad-styrning/komponenter.json).
I konstruktionsskriptet: `k.inkop("gj/1", komponent="gj-120-rf", mitt=(...), rot=(...))` ritar komponenten som
utrymmesmodell med databladets mått och vikt, skriver benämning, tillverkare och artikelnummer i materiallistan och
källan i noterna. Måtten i registret ska vara de som står i databladet (ytterkontur, montagemått); hittas de inte:
fråga användaren, gissa inte.
"""
import os, sys, json, time, argparse


def fil():
    if os.environ.get("FC_KOMPONENT_FIL"):
        return os.environ["FC_KOMPONENT_FIL"]
    for f in (os.path.join(os.getcwd(), "egna", "komponenter.json"),
              os.path.join(os.path.expanduser("~"), ".config", "freecad-styrning", "komponenter.json")):
        if f and os.path.exists(f):
            return f
    if os.path.isdir(os.path.join(os.getcwd(), "egna")):
        return os.path.join(os.getcwd(), "egna", "komponenter.json")
    return os.path.join(os.path.expanduser("~"), ".config", "freecad-styrning", "komponenter.json")


def las(sokvag=None):
    f = sokvag or fil()
    if not os.path.exists(f):
        return {}
    with open(f, encoding="utf-8") as fh:
        return {k: v for k, v in json.load(fh).items() if not k.startswith("_")}


def hamta(kid, sokvag=None):
    """Komponenten med id `kid`, eller RuntimeError med vad som ska göras."""
    reg = las(sokvag)
    if kid not in reg:
        raise RuntimeError("Komponenten %s finns inte i registret %s. Sök upp leverantörens datablad i användarens land "
                           "(SKILL.md, 'Komponenter') och lägg in den med komponenter.py lagg-till." % (kid, sokvag or fil()))
    return reg[kid]


def land():
    """Landet där skillen används: FC_LAND, foretag.json eller tomt (fråga användaren)."""
    try:
        import foretag
        return (foretag.las().get("land") or "").upper()
    except Exception:
        return (os.environ.get("FC_LAND") or "").upper()


def _matt(s):
    return [float(x.replace(",", ".")) for x in s.lower().replace("×", "x").split("x")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lage", choices=["visa", "lagg-till", "ta-bort"])
    ap.add_argument("--id")
    ap.add_argument("--typ", default="")
    ap.add_argument("--benamning", default="")
    ap.add_argument("--tillverkare", default="")
    ap.add_argument("--artikel", default="")
    ap.add_argument("--lada", help="x x y x z (mm), t.ex. 100x30x150")
    ap.add_argument("--cylinder", help="d x l (mm), t.ex. 20x120")
    ap.add_argument("--vikt", type=float, default=0.0, help="kg per styck enligt databladet")
    ap.add_argument("--last", default="", help="tillåten last enligt databladet, t.ex. '80 kg/par'")
    ap.add_argument("--kalla", default="", help="URL till databladet eller produktsidan")
    ap.add_argument("--land", default=None, help="landet leverantören valdes för (standard: foretag.json)")
    ap.add_argument("--anteckning", default="")
    ap.add_argument("--fil", default=None)
    a = ap.parse_args(argv)
    f = a.fil or fil()
    reg = las(f)
    if a.lage == "visa":
        print("Komponentregister: %s (%d komponenter), land: %s" % (f, len(reg), land() or "okänt (fråga användaren)"))
        for k, v in sorted(reg.items()):
            if a.typ and v.get("typ", "").lower() != a.typ.lower():
                continue
            m = v.get("matt", {})
            mt = ("låda %gx%gx%g" % tuple(m["lada"])) if "lada" in m else ("cylinder Ø%g x %g" % tuple(m["cylinder"])) if "cylinder" in m else "-"
            print("  %-16s %-12s %-30s %s %s, %s, %g kg, %s [%s %s]" % (k, v.get("typ", ""), v.get("benamning", ""), v.get("tillverkare", ""),
                                                                    v.get("artikel", ""), mt, v.get("vikt_kg", 0), v.get("last", ""),
                                                                    v.get("kalla", ""), v.get("hamtad", "")))
        return
    if not a.id:
        ap.error("ange --id")
    if a.lage == "ta-bort":
        reg.pop(a.id, None)
    else:
        if (a.lada is None) == (a.cylinder is None):
            ap.error("ange --lada eller --cylinder med databladets mått")
        if not a.kalla:
            ap.error("ange --kalla (databladet): mått utan källa läggs inte in")
        reg[a.id] = dict(typ=a.typ, benamning=a.benamning or a.typ.upper(), tillverkare=a.tillverkare, artikel=a.artikel,
                         matt={"lada": _matt(a.lada)} if a.lada else {"cylinder": _matt(a.cylinder)}, vikt_kg=a.vikt,
                         last=a.last, kalla=a.kalla, land=(a.land or land() or "").upper(), hamtad=time.strftime("%Y-%m-%d"),
                         anteckning=a.anteckning)
    os.makedirs(os.path.dirname(f) or ".", exist_ok=True)
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)
    print("Sparat i %s: %s %s" % (f, a.id, "borttagen" if a.lage == "ta-bort" else reg[a.id]["benamning"]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
