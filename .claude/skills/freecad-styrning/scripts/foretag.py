"""Företagsuppgifter till titelblocket: sparas en gång och används sedan av ritning.py och sammanstallning.py.

  python3 foretag.py visa
  python3 foretag.py satt --foretag "Firma AB" --adress "Gatan 1" "123 45 Staden" "firma.se 08-123 45 67" \\
                          --ritad-av AB --handlaggare AB --ansvarig "A. Bson" [--logga logga.png] [--fil foretag.json]
  python3 foretag.py ta-bort

Ordning när ritningen görs: kommandoradsargument > miljövariabler FC_FORETAG, FC_ADRESS (rader åtskilda med |),
FC_RITAD_AV, FC_HANDLAGGARE, FC_ANSVARIG, FC_LOGGA > foretag.json. Filen söks i FC_FORETAG_FIL, i egna/foretag.json och
foretag.json i arbetsmappen och i användarens konfigmapp (~/.config/freecad-styrning/foretag.json, på Windows
%APPDATA%\\freecad-styrning\\foretag.json). `satt` skriver till den fil som hittas, annars till egna/foretag.json om mappen egna finns,
annars till konfigmappen; `--fil` väljer. Loggan (PNG eller JPEG) läggs in i titelblocket i stället för
företagsnamnet, i rutan som mallen anger i sin kommentar.
"""
import os, re, sys, json, base64, argparse

FALT = ("foretag", "adress", "ritad_av", "handlaggare", "ansvarig", "logga")
MILJO = dict(foretag="FC_FORETAG", adress="FC_ADRESS", ritad_av="FC_RITAD_AV", handlaggare="FC_HANDLAGGARE",
             ansvarig="FC_ANSVARIG", logga="FC_LOGGA")


def konfigfil():
    if os.name == "nt":
        rot = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        rot = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(rot, "freecad-styrning", "foretag.json")


def hitta_fil():
    """Första foretag.json som finns: FC_FORETAG_FIL, arbetsmappen, konfigmappen. None om ingen."""
    for f in (os.environ.get("FC_FORETAG_FIL"), os.path.join(os.getcwd(), "egna", "foretag.json"),
              os.path.join(os.getcwd(), "foretag.json"), konfigfil()):
        if f and os.path.exists(f):
            return f
    return None


def _tom():
    return dict(foretag="", adress=[], ritad_av="", handlaggare="", ansvarig="", logga="")


def las():
    """Uppgifterna: fil < miljövariabler. Returnerar dict med fälten samt 'fil' (sökväg eller None) och
    'kalla' (per fält: 'fil', 'miljö' eller '')."""
    u, kalla = _tom(), {k: "" for k in FALT}
    fil = hitta_fil()
    if fil:
        try:
            with open(fil, encoding="utf-8") as f:
                d = json.load(f)
            for k in FALT:
                if d.get(k):
                    u[k] = d[k]
                    kalla[k] = "fil"
            if u["logga"] and not os.path.isabs(u["logga"]):
                u["logga"] = os.path.join(os.path.dirname(fil), u["logga"])
        except (ValueError, OSError) as e:
            print("foretag.py: kunde inte läsa %s: %s" % (fil, e), file=sys.stderr)
    for k, m in MILJO.items():
        v = os.environ.get(m)
        if v:
            u[k] = [r.strip() for r in v.split("|") if r.strip()] if k == "adress" else v
            kalla[k] = "miljö"
    u["adress"] = list(u["adress"] or [])
    u["fil"], u["kalla"] = fil, kalla
    return u


def saknas(u=None):
    """De fält som behövs för ett komplett titelblock men saknas (företag och signatur)."""
    u = u or las()
    return [k for k in ("foretag", "ritad_av") if not u.get(k)]


def satt(fil=None, **varden):
    """Sparar (slår ihop med det som redan finns i filen). Returnerar sökvägen."""
    fil = fil or os.environ.get("FC_FORETAG_FIL") or hitta_fil() or (
        os.path.join(os.getcwd(), "egna", "foretag.json") if os.path.isdir(os.path.join(os.getcwd(), "egna")) else konfigfil())
    d = {}
    if os.path.exists(fil):
        with open(fil, encoding="utf-8") as f:
            d = json.load(f)
    for k, v in varden.items():
        if k in FALT and v is not None:
            d[k] = v
    if d.get("logga"):
        d["logga"] = os.path.abspath(d["logga"])
        if not os.path.exists(d["logga"]):
            raise FileNotFoundError("loggan finns inte: %s" % d["logga"])
    os.makedirs(os.path.dirname(fil) or ".", exist_ok=True)
    with open(fil, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return fil


def mall_med_logga(mall, logga, ut_mapp):
    """Kopia av TechDraw-mallen där Foretag-texten är utbytt mot loggan (inbäddad som data-URI) i rutan som
    mallens kommentar anger ("rutan x A-B, y C-D"). Returnerar kopians sökväg, eller mallen själv om ingen logga."""
    if not logga:
        return mall
    if not os.path.exists(logga):
        raise FileNotFoundError("loggan finns inte: %s" % logga)
    with open(mall, encoding="utf-8") as f:
        svg = f.read()
    m = re.search(r"rutan x ([\d.]+)-([\d.]+), y ([\d.]+)-([\d.]+)", svg)
    if not m:
        raise ValueError("mallen %s anger ingen ruta för loggan i sin kommentar" % os.path.basename(mall))
    x1, x2, y1, y2 = (float(v) for v in m.groups())
    typ = "image/jpeg" if logga.lower().endswith((".jpg", ".jpeg")) else "image/png"
    with open(logga, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    bild = ('<image x="%g" y="%g" width="%g" height="%g" preserveAspectRatio="xMinYMid meet" '
            'xlink:href="data:%s;base64,%s"/>' % (x1, y1, x2 - x1, y2 - y1, typ, data))
    ny, n = re.subn(r'<text[^>]*freecad:editable="Foretag"[^>]*>.*?</text>', bild, svg, count=1, flags=re.S)
    if n != 1:
        raise ValueError("hittade inte Foretag-fältet i %s" % os.path.basename(mall))
    os.makedirs(ut_mapp, exist_ok=True)
    ut = os.path.join(ut_mapp, "_" + os.path.splitext(os.path.basename(mall))[0] + "_logga.svg")
    with open(ut, "w", encoding="utf-8") as f:
        f.write(ny)
    return ut


def visa(u=None):
    u = u or las()
    print("Företagsuppgifter (%s):" % (u["fil"] or "ingen fil, bara miljövariabler"))
    for k in FALT:
        v = u[k]
        print("  %-12s %-40s %s" % (k, " | ".join(v) if isinstance(v, list) else (v or "-"), u["kalla"][k]))
    s = saknas(u)
    if s:
        print("SAKNAS: %s. Spara med: python3 foretag.py satt --foretag \"Firma AB\" --adress \"Gatan 1\" \"123 45 Staden\" "
              "--ritad-av AB [--handlaggare AB --ansvarig \"A. Bson\" --logga logga.png]" % ", ".join(s))
    else:
        print("Komplett.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Företagsuppgifter till titelblocket")
    ap.add_argument("lage", choices=["visa", "satt", "ta-bort"])
    ap.add_argument("--foretag")
    ap.add_argument("--adress", nargs="*", help="upp till tre rader")
    ap.add_argument("--ritad-av", dest="ritad_av")
    ap.add_argument("--handlaggare")
    ap.add_argument("--ansvarig")
    ap.add_argument("--logga", help="PNG/JPEG som ersätter företagsnamnet i titelblocket")
    ap.add_argument("--fil", help="foretag.json att skriva/ta bort (standard: se modulens docstring)")
    a = ap.parse_args(argv)
    if a.lage == "visa":
        return visa()
    if a.lage == "ta-bort":
        f = a.fil or hitta_fil()
        if f and os.path.exists(f):
            os.remove(f)
            print("Tog bort", f)
        else:
            print("Ingen fil att ta bort.")
        return
    v = {k: getattr(a, k) for k in FALT}
    if all(x is None for x in v.values()):
        ap.error("ange minst ett fält att spara")
    f = satt(a.fil, **v)
    print("Sparat i", f)
    os.environ["FC_FORETAG_FIL"] = f
    visa()


if __name__ == "__main__":
    main()
