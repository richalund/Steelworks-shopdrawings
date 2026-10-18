"""Beställningspaket: allt som behövs för att prissätta och tillverka en ritning, i en zip, och kontrollen av ett
paket som kommer in.

  python3 paket.py skapa <modell.FCStd> [--skript egna/konstruktioner/x.py] [--antal 1] [--ut <mapp>]
  python3 paket.py kontrollera <paket.zip> [--ut <mapp>]

`skapa` samlar modellens filer i samma mapp (FCStd, PDF, PNG, DXF, STEP, materiallista, prisunderlag), skriptet
modellen byggdes från och de egna moduler det importerar (med sina sökvägar), kör prisunderlaget (kalkyl.py) om
det saknas och skriver `manifest.json`: skillens version, datum, variabler, vikt, mått, regelkontrollen och en
kontrollsumma (SHA-256) per fil. Ger `<modell>_bestallning.zip`. Det är paketet kunden eller återförsäljaren
skickar in.

`kontrollera` packar upp paketet, jämför kontrollsummorna, bygger om modellen från skriptet och variablerna med
den här versionen av skillen och jämför vikt, mått, antal delar och regelkontroll med manifestet. Ger OK eller en
lista över avvikelser (ändrad fil, annan vikt, regelfel). Ritningen som prissätts är den ombyggda, inte den
inskickade.
"""
import os, re, sys, json, time, shutil, hashlib, zipfile, argparse, tempfile, subprocess
import xml.etree.ElementTree as ET

HIT = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HIT)
TYPER = (".fcstd", ".pdf", ".png", ".dxf", ".step", ".stp", ".csv", ".json", ".txt", ".glb", ".ifc", ".svg")


def sha(fil):
    h = hashlib.sha256()
    with open(fil, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fcstd_egenskaper(fil):
    """Comment, gruppens Regelkontroll/Marke och kalkylbladets variabler (alias -> värde) ur Document.xml,
    utan FreeCAD. Variablerna är bladets nuvarande värden, även de som ändrats för hand i FreeCAD."""
    with zipfile.ZipFile(fil) as z:
        rot = ET.fromstring(z.read("Document.xml"))
    ut = {"variabler": {}}
    for p in rot.iter("Property"):
        if p.get("name") in ("Comment", "Regelkontroll", "Marke", "Namn") and p.get("name") not in ut:
            s = p.find("String")
            if s is not None:
                ut[p.get("name")] = s.get("value", "")
    for c in rot.iter("Cell"):
        if c.get("alias"):
            try:
                ut["variabler"][c.get("alias")] = float(c.get("content", "").lstrip("="))
            except ValueError:
                pass
    return ut


def variabler_ur(comment):
    m = re.search(r"variabler (\{.*?\})", comment or "")
    try:
        return json.loads(m.group(1)) if m else {}
    except ValueError:
        return {}


def hitta_skript(comment, modell):
    m = re.search(r"från (\S+\.py)", comment or "")
    if not m:
        return None
    namn = m.group(1).rstrip(",")
    for mapp in (os.path.join(os.getcwd(), "egna", "konstruktioner"), os.path.join(os.getcwd(), "egna", "delar"),
                 os.path.join(SKILL, "konstruktioner"), os.path.join(SKILL, "delar"), os.path.dirname(modell), os.getcwd()):
        f = os.path.join(mapp, namn)
        if os.path.exists(f):
            return f
    return None


def moduler(skript):
    """Egna moduler som skriptet importerar (rekursivt), sökta i skriptets mapp, mappen ovanför och egna/.
    Skillens egna moduler (scripts/) räknas inte: de kommer från den skill som bygger om."""
    hittade, kö = [], [skript]
    while kö:
        f = kö.pop()
        try:
            text = open(f, encoding="utf-8").read()
        except OSError:
            continue
        namn = set(re.findall(r"^\s*import\s+([\w, ]+)", text, re.M))
        namn = {n.strip().split(" as ")[0] for rad in namn for n in rad.split(",")}
        namn |= set(re.findall(r"^\s*from\s+(\w+)\s+import", text, re.M))
        for n in namn:
            if os.path.exists(os.path.join(HIT, n + ".py")):
                continue
            for mapp in (os.path.dirname(f), os.path.dirname(os.path.dirname(f)), os.path.join(os.getcwd(), "egna")):
                k = os.path.join(mapp, n + ".py")
                if os.path.exists(k) and os.path.abspath(k) not in hittade and os.path.abspath(k) != os.path.abspath(skript):
                    hittade.append(os.path.abspath(k))
                    kö.append(k)
                    break
    return hittade


def relativ(f):
    """Sökväg i paketet: relativt arbetsmappen (repots rot) om filen ligger där, annars bara filnamnet."""
    r = os.path.relpath(os.path.abspath(f), os.getcwd())
    return r.replace(os.sep, "/") if not r.startswith("..") else os.path.basename(f)


def skapa(a):
    import regler
    modell = os.path.abspath(a.fil)
    mapp, bas = os.path.dirname(modell), os.path.splitext(os.path.basename(modell))[0]
    eg = fcstd_egenskaper(modell)
    kalkylfil = os.path.join(mapp, bas + "_kalkyl.json")
    if not os.path.exists(kalkylfil) or os.path.getmtime(kalkylfil) < os.path.getmtime(modell):
        print("Prisunderlag saknas eller är äldre än modellen: kör kalkyl.py")
        subprocess.run([sys.executable, os.path.join(HIT, "kalkyl.py"), modell, "--antal", str(a.antal)], check=True)
    with open(kalkylfil, encoding="utf-8") as f:
        kalkyl = json.load(f)
    filer = sorted(os.path.join(mapp, n) for n in os.listdir(mapp)
                   if (n == bas + os.path.splitext(n)[1] or n.startswith(bas + "_") or n.startswith(bas + "."))
                   and n.lower().endswith(TYPER) and not n.endswith("_bestallning.zip") and "_zoom_" not in n)
    skript = os.path.abspath(a.skript) if a.skript else hitta_skript(eg.get("Comment"), modell)
    underlag = ([skript] + moduler(skript)) if skript else []
    if not skript:
        print("OBS: hittade inte skriptet modellen byggdes från (%s); paketet kan inte byggas om vid kontrollen. Ange --skript."
              % eg.get("Comment", "ingen kommentar"))
    rk = json.loads(eg["Regelkontroll"]) if eg.get("Regelkontroll") else None
    t = kalkyl["totalt"]
    manifest = dict(
        typ="freecad-styrning beställningspaket", skapat=time.strftime("%Y-%m-%d %H:%M"), skill=regler.skillversion(),
        modell=os.path.basename(modell), marke=eg.get("Marke", ""), namn=eg.get("Namn", ""), antal=a.antal,
        skript=relativ(skript) if skript else None, byggare="partdesign" if "partdesign.py" in eg.get("Comment", "") else "sammanstallning",
        variabler=eg["variabler"] or variabler_ur(eg.get("Comment")),
        vikt_kg=round(t["vikt"] + sum(x["vikt"] for x in kalkyl.get("inkop", [])), 2), delar=t["delar"] + t.get("inkopta", 0), yta_m2=round(t["yta_m2"], 3), regelkontroll=rk,
        filer={})
    zipnamn = os.path.join(os.path.abspath(a.ut) if a.ut else mapp, bas + "_bestallning.zip")
    os.makedirs(os.path.dirname(zipnamn), exist_ok=True)
    with zipfile.ZipFile(zipnamn, "w", zipfile.ZIP_DEFLATED) as z:
        for f in filer:
            namn = "ritning/" + os.path.basename(f)
            z.write(f, namn)
            manifest["filer"][namn] = dict(sha256=sha(f), byte=os.path.getsize(f))
        for f in underlag:
            namn = "underlag/" + relativ(f)
            z.write(f, namn)
            manifest["filer"][namn] = dict(sha256=sha(f), byte=os.path.getsize(f))
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
        z.writestr("LASMIG.txt", LASMIG % dict(modell=manifest["modell"], skill=manifest["skill"], vikt=manifest["vikt_kg"],
                                               rk=("OK" if rk and rk["ok"] else "SE MANIFEST") if rk else "ej körd"))
    print("Beställningspaket: %s (%d filer, skill %s, vikt %.1f kg, regelkontroll %s)" % (
        zipnamn, len(manifest["filer"]), manifest["skill"], manifest["vikt_kg"],
        "OK" if rk and rk["ok"] and not rk["varningar"] else ("%d FEL, %d VARNING" % (len(rk["fel"]), len(rk["varningar"])) if rk else "ej körd")))
    return zipnamn


LASMIG = """Beställningspaket från freecad-styrning (skill %(skill)s)

Modell: %(modell)s, vikt %(vikt)s kg, regelkontroll %(rk)s.
ritning/   ritningar (PDF, PNG), modell (FCStd), DXF, STEP, materiallista och prisunderlag
underlag/  skriptet modellen byggdes från och dess egna moduler
manifest.json  variabler, vikt, regelkontroll och kontrollsumma (SHA-256) för varje fil

Kontroll hos tillverkaren: python3 .claude/skills/freecad-styrning/scripts/paket.py kontrollera <paket.zip>
(bygger om modellen med samma variabler och jämför).

Order package from freecad-styrning: drawings in ritning/, source script in underlag/, checksums and parameters in
manifest.json. The manufacturer rebuilds the model from the script and compares before pricing.
"""


def kontrollera(a):
    zipfil = os.path.abspath(a.fil)
    ut = os.path.abspath(a.ut) if a.ut else tempfile.mkdtemp(prefix="paket_")
    with zipfile.ZipFile(zipfil) as z:
        namn_i_zip = z.namelist()
        for n in namn_i_zip:                         # inga sökvägar utanför utmappen
            if n.startswith("/") or ".." in n.split("/"):
                raise SystemExit("Otillåten sökväg i paketet: %s" % n)
        z.extractall(ut)
    with open(os.path.join(ut, "manifest.json"), encoding="utf-8") as f:
        m = json.load(f)
    avvik, info = [], []
    for namn, d in m["filer"].items():
        f = os.path.join(ut, namn)
        if not os.path.exists(f):
            avvik.append("saknas: %s" % namn)
        elif sha(f) != d["sha256"]:
            avvik.append("ändrad efter att paketet skapades: %s" % namn)
    for n in sorted(namn_i_zip):
        if n not in m["filer"] and n not in ("manifest.json", "LASMIG.txt") and not n.endswith("/"):
            avvik.append("fil som inte står i manifestet: %s" % n)
    info.append("Paketet skapat %s med skill %s; kontrolleras med skill %s" % (m["skapat"], m["skill"], __import__("regler").skillversion()))
    if m.get("skript"):
        skript = os.path.join(ut, "underlag", m["skript"])
        modell = os.path.join(ut, "ombyggd", m["modell"])
        shutil.rmtree(os.path.dirname(modell), ignore_errors=True)        # ombyggnaden från en tidigare kontroll
        os.makedirs(os.path.dirname(modell), exist_ok=True)
        byggare = m.get("byggare", "sammanstallning")
        kmd = [sys.executable, os.path.join(HIT, byggare + ".py"), "bygg", skript, modell]
        for k, v in (m.get("variabler") or {}).items():
            kmd += ["--var", "%s=%s" % (k, v)]
        print("Bygger om från %s med %d variabler ..." % (m["skript"], len(m.get("variabler") or {})))
        miljo = dict(os.environ)
        egen = os.path.join(os.getcwd(), "egna", "verkstad.json")      # mottagarens verkstadsgränser, inte avsändarens
        if os.path.exists(egen) and not miljo.get("FC_VERKSTAD_FIL"):
            miljo["FC_VERKSTAD_FIL"] = egen
        r = subprocess.run(kmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=os.path.join(ut, "underlag"), env=miljo)
        logg = r.stdout + r.stderr
        with open(os.path.join(ut, "ombyggd", "bygg.log"), "w", encoding="utf-8") as f:
            f.write(logg)
        mv = re.search(r"Delar (\d+), positioner \d+, hålgrupper \d+, vikt ([\d.]+) kg", logg)
        mp = re.search(r"Massa: ([\d.]+) kg", logg)                   # partdesign.py
        if r.returncode != 0 or not (mv or mp):
            avvik.append("ombyggnaden misslyckades (se ombyggd/bygg.log)")
        else:
            delar, vikt = (int(mv.group(1)), float(mv.group(2))) if mv else (1, float(mp.group(1)))
            info.append("Ombyggd: %d delar, %.1f kg (paketet: %d delar, %.1f kg)" % (delar, vikt, m["delar"], m["vikt_kg"]))
            if delar != m["delar"]:
                avvik.append("antal delar %d i stället för %d" % (delar, m["delar"]))
            if abs(vikt - m["vikt_kg"]) > max(0.1, 0.005 * m["vikt_kg"]):
                avvik.append("vikt %.1f kg i stället för %.1f kg" % (vikt, m["vikt_kg"]))
            rk = re.search(r"Regelkontroll: (.*)", logg)
            if rk:
                info.append("Regelkontroll vid ombyggnaden: " + rk.group(1))
                if "FEL" in rk.group(1).split("(")[0]:
                    avvik.append("regelkontrollen ger fel: " + "; ".join(re.findall(r"  FEL: (.*)", logg)))
            for k in ("Krockar (överlappande delar): ", "fullt bestämda: "):
                rad = re.search(re.escape(k) + r"(.*)", logg)
                if rad and rad.group(1).split(";")[0].strip() not in ("inga", "alla"):
                    avvik.append(k + rad.group(1))
    else:
        avvik.append("paketet har inget skript: kan inte byggas om, ritningen måste granskas för hand")
    for s in info:
        print(s)
    if avvik:
        print("AVVIKER:")
        for s in avvik:
            print("  - " + s)
    else:
        print("OK: paketet är oförändrat och ombyggnaden stämmer. Ombyggd modell: %s" % os.path.join(ut, "ombyggd"))
    return not avvik


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lage", choices=["skapa", "kontrollera"])
    ap.add_argument("fil")
    ap.add_argument("--skript", default=None)
    ap.add_argument("--antal", type=int, default=1)
    ap.add_argument("--ut", default=None)
    a = ap.parse_args(argv)
    sys.path.insert(0, HIT)
    if a.lage == "skapa":
        skapa(a)
    else:
        sys.exit(0 if kontrollera(a) else 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
