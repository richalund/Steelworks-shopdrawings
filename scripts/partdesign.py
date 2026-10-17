"""Parametriska delar i FreeCADs Part Design (PartDesign::Body), styrt från vanlig Python.

  python partdesign.py bygg <delskript.py> <ut.FCStd> [--var Bredd=300 --var HalD=22] [--png] [--step]
  python partdesign.py satt <fil.FCStd> --var Bredd=300 [--var ...] [--png] [--step]
  python partdesign.py las  <fil.FCStd>

Ett delskript (se ../delar/) beskriver delen:
  NAMN = "Fotplatta"
  VARIABLER = [("Bredd", 250, "mm, plattans bredd (X)"), ...]     # blir kalkylbladet Variabler
  def bygg(d):                                                    # d = pd.Del (kropp + hjälpare)
      sk = d.skiss("Platta", "XY")
      sk.rundad_rektangel("Bredd", "Langd", "Hornradie")
      d.kloss(sk, "Tjocklek")
      ...
Måtten i skisserna och features är uttryck mot Variabler, så `satt` (eller användaren i FreeCAD) ändrar
variablerna och modellen räknas om. Fillet/Chamfer-kanter letas om efter varje ändring (pd.uppdatera).
"""
import os, sys, argparse


def args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("lage", choices=["bygg", "satt", "las"])
    ap.add_argument("fil", help="bygg: delskriptet; satt/las: .FCStd-filen")
    ap.add_argument("ut", nargs="?", help="bygg: .FCStd att skapa")
    ap.add_argument("--var", action="append", default=[], metavar="NAMN=VÄRDE")
    ap.add_argument("--densitet", type=float, default=7850.0, help="kg/m3 (standard stål 7850)")
    ap.add_argument("--step", action="store_true", help="exportera STEP bredvid filen")
    ap.add_argument("--png", action="store_true", help="spara isometrisk bild bredvid filen")
    a = ap.parse_args(argv)
    if a.lage == "bygg" and not a.ut:
        ap.error("bygg kräver delskript och ut-fil")
    return a


def tolka_var(lista):
    ut = {}
    for s in lista:
        if "=" not in s:
            raise SystemExit("--var ska vara NAMN=VÄRDE, fick: %s" % s)
        k, v = s.split("=", 1)
        ut[k.strip()] = v.strip().replace(",", ".")
    return ut


# =====================================================================================================
# Jobbet: körs inne i FreeCAD
# =====================================================================================================
def _jobb():
    import runpy
    import FreeCAD as App
    import fcapi, pd
    from fcapi import logg

    def spara(doc, fil, a):
        body = pd.hitta_kropp(doc)
        doc.saveAs(fil)
        logg("Sparat:", fil)
        bas = os.path.splitext(fil)[0]
        if a.get("step"):
            body.Shape.exportStep(bas + ".step")
            logg("STEP:", bas + ".step")
        if a.get("png"):
            if fcapi.har_gui():
                pd.bild(doc, body, bas + ".png", fcapi.pump)
                logg("PNG:", bas + ".png")
            else:
                logg("PNG kräver GUI - hoppas över")

    def bygg(a):
        mod = runpy.run_path(a["fil"])
        namn = mod.get("NAMN", os.path.splitext(os.path.basename(a["fil"]))[0])
        nya = tolka_var(a["var"])
        kanda = [v[0] for v in mod["VARIABLER"]]
        okanda = set(nya) - set(kanda)
        if okanda:
            raise RuntimeError("Okända variabler %s. Delskriptet har: %s" % (sorted(okanda), ", ".join(kanda)))
        doc = App.newDocument("".join(c for c in namn if c.isalnum()) or "Del")
        sh = doc.addObject("Spreadsheet::Sheet", "Variabler")
        sh.set("A1", "Variabel"); sh.set("B1", "Värde"); sh.set("C1", "Beskrivning")
        for i, (v, std, beskr) in enumerate(mod["VARIABLER"], start=2):
            sh.set("A%d" % i, v)
            sh.set("B%d" % i, str(nya.get(v, std)))
            sh.setAlias("B%d" % i, v)
            sh.set("C%d" % i, beskr)
        sh.setStyle("A1:C1", "bold")
        doc.recompute()
        d = pd.Del(doc)
        d.body.Label = namn
        mod["bygg"](d)
        d.stada()
        doc.Comment = "Byggd med partdesign.py från %s" % os.path.basename(a["fil"])
        pd.uppdatera(doc)
        r = pd.kontroll(doc, logg, a["densitet"])
        spara(doc, os.path.abspath(a["ut"]), a)
        return r

    def oppna(fil):
        doc = App.openDocument(os.path.abspath(fil))
        pd.hitta_kropp(doc)
        return doc

    def satt(a):
        doc = oppna(a["fil"])
        sh = doc.getObject("Variabler")
        if sh is None:
            raise RuntimeError("Filen saknar kalkylbladet Variabler")
        kanda = pd.alias_lista(sh)
        for k, v in tolka_var(a["var"]).items():
            if k not in kanda:
                raise RuntimeError("Variabeln %s finns inte. Filen har: %s" % (k, ", ".join(kanda)))
            sh.set(sh.getCellFromAlias(k), v)
            logg("Ändrade", k, "->", v)
        pd.uppdatera(doc)
        r = pd.kontroll(doc, logg, a["densitet"])
        spara(doc, os.path.abspath(a["fil"]), a)
        return r

    def las(a):
        return pd.kontroll(oppna(a["fil"]), logg, a["densitet"])

    fcapi.kor_jobb(lambda a: {"bygg": bygg, "satt": satt, "las": las}[a["lage"]](a))


if __name__ == "__fcjobb__":
    _jobb()
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    a = args()
    a.fil = os.path.abspath(a.fil)
    if not os.path.exists(a.fil):
        raise SystemExit("Filen finns inte: " + a.fil)
    if a.ut:
        a.ut = os.path.abspath(a.ut)
    tolka_var(a.var)
    fcapi.kor(__file__, vars(a))
