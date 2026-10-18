"""Testar skillen: bygger och ritar alla exempel och kontrollerar utskrifterna. Kör före varje bidrag (PR).

  python3 testa.py [--snabb] [--ut <mapp>] [--bara balkongram,trappracke]

Varje exempel byggs med sitt kommando (partdesign.py, datastall.py, sammanstallning.py), ritas (ritning.py,
sammanstallning.py ritning) och kontrolleras: skisserna fullt bestämda, inga features med fel, inga krockar,
PDF och PNG skapade. --snabb hoppar över ritningarna (bara bygg). Ger en tabell med OK/FEL per exempel och
avslutas med kod 1 om något gick fel. Bilderna hamnar i ut-mappen (standard: ut/test i arbetsmappen) så att de
kan granskas med ögonen: titta alltid på PNG:erna för exemplen som berörs av en ändring.
"""
import os, sys, re, time, argparse, subprocess

HIT = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HIT)
PY = sys.executable


def fall(ut):
    d, k = os.path.join(SKILL, "delar"), os.path.join(SKILL, "konstruktioner")
    s = lambda n: os.path.join(HIT, n)
    f = lambda n: os.path.join(ut, n)
    ut_ = []
    for namn in ("fotplatta", "konsol", "hylsa", "hprofil"):
        ut_.append((namn, [[s("partdesign.py"), "bygg", os.path.join(d, namn + ".py"), f(namn + ".FCStd"), "--png"]],
                    [[s("ritning.py"), f(namn + ".FCStd"), "--namn", namn.upper(), "--nummer", "TEST-" + namn]]))
    ut_.append(("datastall", [[s("datastall.py"), "bygg", f("datastall.FCStd"), "--png"]],
                [[s("ritning.py"), f("datastall.FCStd"), "--namn", "DATASTÄLL", "--nummer", "TEST-DS"]]))
    for namn in sorted(n[:-3] for n in os.listdir(k) if n.endswith(".py")):
        ut_.append((namn, [[s("sammanstallning.py"), "bygg", os.path.join(k, namn + ".py"), f(namn + ".FCStd")]],
                    [[s("sammanstallning.py"), "ritning", f(namn + ".FCStd"), "--uppdrag", "TEST"],
                     [s("rendera.py"), f(namn + ".FCStd"), "--vyer", "iso"]]))
    return ut_


def kontroll(text):
    """Fel i utskriften: undantag, ej bestämda skisser, features med fel, krockar."""
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
    return fel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snabb", action="store_true", help="bara bygg, inga ritningar")
    ap.add_argument("--ut", default=os.path.join(os.getcwd(), "ut", "test"))
    ap.add_argument("--bara", default="", help="kommaseparerade exempelnamn")
    a = ap.parse_args()
    os.makedirs(a.ut, exist_ok=True)
    bara = {x.strip() for x in a.bara.split(",") if x.strip()}
    rader, alla_ok = [], True
    for namn, bygg, rita in fall(a.ut):
        if bara and namn not in bara:
            continue
        t0, fel, logg = time.time(), [], []
        for cmd in bygg + ([] if a.snabb else rita):
            r = subprocess.run([PY] + cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            logg.append(r.stdout + r.stderr)
            fel += kontroll(r.stdout + r.stderr)
            if r.returncode != 0 and "körningen misslyckades" not in fel:
                fel.append("kod %d" % r.returncode)
            if fel:
                break
        if not a.snabb and not fel:
            for slut in (".pdf", ".png"):
                if not os.path.exists(os.path.join(a.ut, namn + slut)):
                    fel.append("saknar %s%s" % (namn, slut))
        with open(os.path.join(a.ut, namn + "_test.log"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(logg))
        alla_ok &= not fel
        rader.append((namn, "OK" if not fel else "FEL", "%.0f s" % (time.time() - t0), "; ".join(fel)))
        print("%-14s %-4s %6s  %s" % rader[-1], flush=True)
    print("\n%d exempel, %d fel. Loggar och bilder i %s" % (len(rader), sum(r[1] == "FEL" for r in rader), a.ut))
    sys.exit(0 if alla_ok else 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
