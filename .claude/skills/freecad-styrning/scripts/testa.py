"""Testar skillen: bygger och ritar alla exempel, kör verktygen på dem och jämför ritningarna med referensbilder.
Kör före varje bidrag (PR).

  python3 testa.py [--snabb] [--ut <mapp>] [--bara balkongram,grind] [--uppdatera-referens] [--strikt]

Varje exempel byggs med sitt kommando (partdesign.py, datastall.py, sammanstallning.py), ritas (ritning.py,
sammanstallning.py ritning) och kontrolleras: skisserna fullt bestämda, inga features med fel, inga krockar,
regelkontrollen utan FEL, PDF och PNG skapade. Sammanställningarna får dessutom 3D-bild (rendera.py),
mängdunderlag (mangder.py) och DXF (dxf.py); exempel med k.rorelse rörelsekontroll (rorelse.py); grinden även
export (export.py), beställningspaket, leveransmail och filerna till chatten (paket.py skapa/kontrollera/skicka/samla); trappräcket balkkontroll och konsolen FEM
(hallfasthet.py), noteringarna på eget blad och projektets noteringsritning (sammanstallning.py noteringar);
balkongramens PDF läses av underlag.py. --snabb hoppar över allt utom bygget.

Bildjämförelse: ritningens PNG (för enstaka delar blad 1) jämförs med `tester/referens/<exempel>.png` (gråskala, 1000 px bred). Skiljer sig
mer än 0,5 % av pixlarna står det ÄNDRAD x % i tabellen och `<exempel>_diff.png` (ändringarna i rött) läggs i
ut-mappen: titta på den och avgör om ändringen är avsedd. Är den det: kör med --uppdatera-referens och lägg de
nya referensbilderna i samma PR. --strikt gör en ändrad bild till FEL. Datum, företagsuppgifter, källnoter och
skillversion låses i testerna (FC_DATUM, FC_FORETAG_FIL, --utan-kallor, FC_SKILLVERSION) så att bilderna blir
lika från dag till dag.

Ger en tabell med OK/ÄNDRAD/FEL per exempel och avslutas med kod 1 om något gick fel. Loggar och bilder i
ut-mappen (standard ut/test i arbetsmappen).
"""
import os, sys, re, json, time, shutil, argparse, subprocess

HIT = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HIT)
REFERENS = os.path.join(SKILL, "tester", "referens")
PY = sys.executable
GRANS = 0.005                      # andel ändrade pixlar som räknas som ändrad bild


def fall(ut):
    d, k = os.path.join(SKILL, "delar"), os.path.join(SKILL, "konstruktioner")
    s = lambda n: os.path.join(HIT, n)
    f = lambda n: os.path.join(ut, n)
    ut_ = []
    for namn in ("fotplatta", "konsol", "hylsa", "hprofil"):
        extra = []
        if namn == "konsol":
            extra = [[s("hallfasthet.py"), "fem", f("konsol.FCStd"), "--fast=-y", "--last", "+z:8=2000", "--natstorlek", "6"]]
        ut_.append((namn, [[s("partdesign.py"), "bygg", os.path.join(d, namn + ".py"), f(namn + ".FCStd"), "--png"]],
                    [[s("ritning.py"), f(namn + ".FCStd"), "--namn", namn.upper(), "--nummer", "TEST-" + namn, "--utan-kallor"],
                     [s("mangder.py"), f(namn + ".FCStd")]] + extra))
    ut_.append(("datastall", [[s("datastall.py"), "bygg", f("datastall.FCStd"), "--png"]],
                [[s("ritning.py"), f("datastall.FCStd"), "--namn", "DATASTÄLL", "--nummer", "TEST-DS", "--utan-kallor"],
                 [s("mangder.py"), f("datastall.FCStd")]]))
    for namn in sorted(n[:-3] for n in os.listdir(k) if n.endswith(".py")):
        skript = os.path.join(k, namn + ".py")
        text = open(skript, encoding="utf-8").read()
        m = f(namn + ".FCStd")
        rita = [[s("sammanstallning.py"), "ritning", m, "--uppdrag", "TEST", "--utan-kallor"],
                [s("rendera.py"), m, "--vyer", "iso"],
                [s("mangder.py"), m],
                [s("dxf.py"), m]]
        if "k.rorelse" in text:
            rita.append([s("rorelse.py"), m, "--oppen", "-60", "--ut", f(namn + "_oppen.FCStd")])
        if namn == "grind":
            rita += [[s("export.py"), m, "--format", "glb,ifc,step"],
                     [s("paket.py"), "skapa", m, "--skript", skript],
                     [s("paket.py"), "kontrollera", f(namn + "_bestallning.zip"), "--ut", f("paketkontroll")],
                     [s("paket.py"), "skicka", f(namn + "_bestallning.zip"), "--avsandare", "Test"],
                     [s("paket.py"), "samla", f(namn + ".pdf"), m, f(namn + ".step"), f(namn + "_3d_iso.png"),
                      f(namn + "_mangder.csv"), "--namn", namn, "--skript", skript, "--ut", f("samlat")]]
        if namn == "trappracke":
            rita.append([s("hallfasthet.py"), "balk", m, "--pos", "hl/1", "--q", "0.5", "--spann", "860", "--riktning", "sida"])
            # noteringarna på eget blad (kopia, så att bladet som jämförs med referensen är det vanliga) och
            # projektets gemensamma noteringsritning
            rita += [[s("sammanstallning.py"), "ritning", m, "--uppdrag", "TEST", "--utan-kallor", "--noter-blad",
                      "--noter-ref", "N-01", "--ut", f("noterblad")],
                     [s("sammanstallning.py"), "noteringar", os.path.join(SKILL, "mallar", "noter_projekt.py"),
                      f("N-01.FCStd"), "--nummer", "N-01", "--uppdrag", "TEST"]]
        if namn == "balkongram":
            rita.append([s("underlag.py"), "las", f("balkongram.pdf"), "--ut", f("underlag")])
        ut_.append((namn, [[s("sammanstallning.py"), "bygg", skript, m]], rita))
    return ut_


def kontroll(text):
    """Fel i utskriften: undantag, ej bestämda skisser, features med fel, krockar, regelfel, misslyckad kontroll."""
    fel = []
    if "Traceback" in text or "Jobbet misslyckades" in text or "avslutades utan resultat" in text:
        fel.append("körningen misslyckades")
    m = re.search(r"fullt bestämda: (.*?); features med fel: (.*)", text)
    if m and m.group(1).strip() != "alla":
        fel.append("skisser " + m.group(1).strip())
    if m and m.group(2).strip() != "inga":
        fel.append("features med fel: " + m.group(2).strip())
    m = re.search(r"Krockar \(överlappande delar\): (.*)", text)
    if m and m.group(1).strip() != "inga":
        fel.append("krockar: " + m.group(1).strip())
    m = re.search(r"Regelkontroll: (\d+) FEL", text)
    if m and int(m.group(1)):
        fel.append("regelkontroll: " + "; ".join(re.findall(r"  FEL: (.*)", text)))
    if "AVVIKER:" in text:
        fel.append("beställningspaketet avviker")
    m = re.search(r"Rörelse (.*?): krock vid (.*)", text)
    if m:
        fel.append("rörelse %s: krock vid %s" % (m.group(1), m.group(2)))
    return fel


def jamfor(png, ref, diff):
    """Andel pixlar som skiljer (gråskala, 1000 px bred, tröskel 48 av 255) och en diffbild i rött."""
    from PIL import Image, ImageChops
    a = Image.open(png).convert("L")
    a = a.resize((1000, round(1000 * a.height / a.width)))
    b = Image.open(ref).convert("L")
    if b.size != a.size:
        b = b.resize(a.size)
    d = ImageChops.difference(a, b).point(lambda v: 255 if v > 48 else 0)
    andel = sum(d.histogram()[255:]) / float(a.width * a.height)
    if andel > GRANS:
        rod = Image.merge("RGB", (a.point(lambda v: 128 + v // 2), a.point(lambda v: v // 2), a.point(lambda v: v // 2)))
        Image.composite(rod, a.convert("RGB"), d).save(diff)
    return andel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snabb", action="store_true", help="bara bygg, inga ritningar eller verktyg")
    ap.add_argument("--ut", default=os.path.join(os.getcwd(), "ut", "test"))
    ap.add_argument("--bara", default="", help="kommaseparerade exempelnamn")
    ap.add_argument("--uppdatera-referens", dest="uppdatera", action="store_true", help="spara ritningarna som nya referensbilder")
    ap.add_argument("--strikt", action="store_true", help="ändrad bild = FEL")
    a = ap.parse_args()
    a.ut = os.path.abspath(a.ut)
    os.makedirs(a.ut, exist_ok=True)
    fore = os.path.join(a.ut, "_foretag.json")
    with open(fore, "w", encoding="utf-8") as fh:
        json.dump(dict(foretag="Testföretag AB", adress=["Testgatan 1", "123 45 Teststad"], ritad_av="TT",
                       handlaggare="TT", ansvarig="T. Test", logga=""), fh, ensure_ascii=False)
    miljo = dict(os.environ, FC_DATUM="2026-01-01", FC_FORETAG_FIL=fore, FC_SKILLVERSION="TEST")
    for k in ("FC_FORETAG", "FC_ADRESS", "FC_RITAD_AV", "FC_HANDLAGGARE", "FC_ANSVARIG", "FC_LOGGA", "FC_VERKSTAD_FIL", "FC_KOMPONENT_FIL"):
        miljo.pop(k, None)
    bara = {x.strip() for x in a.bara.split(",") if x.strip()}
    rader, alla_ok = [], True
    for namn, bygg, rita in fall(a.ut):
        if bara and namn not in bara:
            continue
        t0, fel, logg, status = time.time(), [], [], ""
        for cmd in bygg + ([] if a.snabb else rita):
            # verktygen körs från skillens mapp så att egna/ i arbetsmappen (verkstad, komponenter) inte påverkar
            r = subprocess.run([PY] + cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=miljo, cwd=a.ut)
            logg.append("$ " + " ".join(os.path.basename(c) if os.path.isabs(c) else c for c in cmd) + "\n" + r.stdout + r.stderr)
            fel += kontroll(r.stdout + r.stderr)
            if r.returncode != 0 and "körningen misslyckades" not in fel and not fel:
                fel.append("%s gav kod %d" % (os.path.basename(cmd[0]), r.returncode))
            if fel:
                break
        if not a.snabb and not fel:
            for slut in (".pdf", ".png"):
                if not os.path.exists(os.path.join(a.ut, namn + slut)):
                    fel.append("saknar %s%s" % (namn, slut))
        if not a.snabb and not fel:
            # enstaka delar: ritningens blad 1 (ritning.py); <namn>.png är där 3D-bilden, vars utsnitt varierar
            png = os.path.join(a.ut, namn + "_blad1.png")
            if not os.path.exists(png):
                png = os.path.join(a.ut, namn + ".png")
            ref = os.path.join(REFERENS, namn + ".png")
            if a.uppdatera or not os.path.exists(ref):
                from PIL import Image
                os.makedirs(REFERENS, exist_ok=True)
                b = Image.open(png).convert("L")
                b.resize((1000, round(1000 * b.height / b.width))).save(ref, optimize=True)
                status = "ny referens" if not a.uppdatera else "referens uppdaterad"
            else:
                andel = jamfor(png, ref, os.path.join(a.ut, namn + "_diff.png"))
                if andel > GRANS:
                    status = "ÄNDRAD %.1f %% (se %s_diff.png)" % (100 * andel, namn)
                    if a.strikt:
                        fel.append("bilden ändrad %.1f %%" % (100 * andel))
        with open(os.path.join(a.ut, namn + "_test.log"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(logg))
        alla_ok &= not fel
        res = "FEL" if fel else ("ÄNDRAD" if status.startswith("ÄNDRAD") else "OK")
        rader.append((namn, res, "%.0f s" % (time.time() - t0), "; ".join(fel) or status))
        print("%-14s %-6s %6s  %s" % rader[-1], flush=True)
    andrade = sum(r[1] == "ÄNDRAD" for r in rader)
    print("\n%d exempel, %d fel, %d ändrade bilder. Loggar och bilder i %s" % (
        len(rader), sum(r[1] == "FEL" for r in rader), andrade, a.ut))
    sys.exit(0 if alla_ok else 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
