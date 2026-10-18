"""Gemensam hjälpare för FreeCAD-skripten. Används från två håll:

1. Vanlig Python (startaren): `kor(skript, args)` startar FreeCAD 1.x med GUI, kör `skript` som ett
   jobb inne i FreeCAD och skriver ut jobbets logg medan det kör. Returnerar jobbets resultat (dict).
2. Inne i FreeCAD (jobbet): `jobb()` ger argumenten, `logg()` skriver till loggen, `pump()` låter Qt
   arbeta (TechDraw räknar vyer i bakgrunden), `start_vakt()` stänger modala dialoger, `avsluta()`
   stänger dokumenten och avslutar FreeCAD.

Bara standardbiblioteket på toppnivå: filen importeras av både system-Python och FreeCADs Python.
"""
import os, sys, json, time, glob, shutil, tempfile, subprocess

MILJO = "FCJOBB"


# ---------------------------------------------------------------- startaren (vanlig Python)
def hitta_freecad():
    """bin-mappen för senaste FreeCAD 1.x. Miljövariabeln FREECAD_BIN går före."""
    if os.environ.get("FREECAD_BIN"):
        return os.environ["FREECAD_BIN"]
    if os.name != "nt":
        # Linux/macOS (t.ex. molnsession med FreeCAD från conda-forge i /opt/freecad).
        kand = ["/opt/freecad/bin/freecad", os.path.expanduser("~/.local/opt/freecad/bin/freecad")]   # installera_linux.sh
        exe = shutil.which("freecad") or next((k for k in kand if os.path.exists(k)), None)
        if not exe:
            raise SystemExit("FreeCAD hittades inte. Installera FreeCAD 1.x eller sätt FREECAD_BIN till bin-mappen.")
        return os.path.dirname(exe)
    kandidater = []
    for rot in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.path.expandvars(r"%LOCALAPPDATA%\Programs")):
        kandidater += glob.glob(os.path.join(rot, "FreeCAD*", "bin", "freecad.exe"))
    if not kandidater:
        raise SystemExit("FreeCAD hittades inte. Installera FreeCAD 1.x eller sätt FREECAD_BIN till bin-mappen.")
    kandidater.sort(key=lambda p: [int(x) if x.isdigit() else 0 for x in os.path.basename(os.path.dirname(os.path.dirname(p))).replace("FreeCAD", "").strip().split(".")])
    return os.path.dirname(kandidater[-1])


def kor(skript, args, timeout=None, gui=True):
    """Kör `skript` som jobb i FreeCAD med argumenten `args` (dict). Skriver ut loggen löpande."""
    tmp = tempfile.mkdtemp(prefix="fcjobb_")
    jobbfil = os.path.join(tmp, "jobb.json")
    logg_ = os.path.join(tmp, "logg.txt")
    res = os.path.join(tmp, "resultat.json")
    with open(jobbfil, "w", encoding="utf-8") as f:
        json.dump({"skript": os.path.abspath(skript), "skriptmapp": os.path.dirname(os.path.abspath(skript)),
                   "logg": logg_, "resultat": res, "args": args}, f, ensure_ascii=False)
    # Startfilen ligger i %TEMP% (ASCII-sökväg) så att FreeCAD inte behöver tolka å/ä/ö på kommandoraden.
    start = os.path.join(tmp, "start_jobb.py")
    with open(start, "w", encoding="utf-8") as f:
        f.write("import os, sys, json, runpy\n"
                "j = json.load(open(os.environ['%s'], encoding='utf-8'))\n"
                "sys.path.insert(0, j['skriptmapp'])\n"
                "runpy.run_path(j['skript'], run_name='__fcjobb__')\n" % MILJO)
    timeout = timeout or float(os.environ.get("FC_TIMEOUT", 600))
    ext = ".exe" if os.name == "nt" else ""
    exe = os.path.join(hitta_freecad(), ("freecad" if gui else "freecadcmd") + ext)
    env = dict(os.environ, **{MILJO: jobbfil})
    cmd = [exe, start]
    if gui and os.name != "nt" and sys.platform != "darwin" and not os.environ.get("DISPLAY"):
        # Ingen skärm (molnsession): TechDraw kräver GUI, så kör FreeCAD i en virtuell X-skärm.
        if not shutil.which("xvfb-run"):
            raise SystemExit("Ingen skärm och xvfb-run saknas (apt install xvfb).")
        cmd = ["xvfb-run", "-a"] + cmd
    t0 = time.time()
    p = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    las = 0
    while True:
        klar = p.poll() is not None
        if os.path.exists(logg_):
            with open(logg_, encoding="utf-8", errors="replace") as f:
                f.seek(las)
                ny = f.read()
                las = f.tell()
            if ny:
                # FreeCAD 1.0.1 (PySide2/shiboken + Python 3.11) skriver "SystemError: unknown opcode" i
                # bakgrunden under TechDraw-jobb utan att något går fel - filtreras bort.
                ny = "".join(r for r in ny.splitlines(True) if "SystemError: unknown opcode" not in r)
                sys.stdout.write(ny)
                sys.stdout.flush()
        if klar:
            break
        if time.time() - t0 > timeout:
            p.kill()
            raise SystemExit("FreeCAD svarade inte inom %d s och avbröts. Loggen: %s" % (timeout, logg_))
        time.sleep(0.3)
    if not os.path.exists(res):
        raise SystemExit("FreeCAD avslutades utan resultat (kod %s). Loggen: %s" % (p.returncode, logg_))
    with open(res, encoding="utf-8") as f:
        r = json.load(f)
    if not r.get("ok"):
        raise SystemExit("Jobbet misslyckades: %s" % r.get("fel", "okänt fel"))
    return r


# ---------------------------------------------------------------- jobbet (inne i FreeCAD)
_J = None
_LOGG = None
STANGDA = []


def jobb():
    """Jobbets inställningar: {'args': ..., 'logg': ..., 'resultat': ..., 'skriptmapp': ...}."""
    global _J, _LOGG
    if _J is None:
        with open(os.environ[MILJO], encoding="utf-8") as f:
            _J = json.load(f)
        _LOGG = open(_J["logg"], "w", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = _LOGG
        if os.environ.get("FC_FELSOK"):
            import faulthandler
            faulthandler.enable(file=_LOGG, all_threads=True)
            faulthandler.dump_traceback_later(float(os.environ["FC_FELSOK"]), repeat=True, file=_LOGG)
    return _J


def logg(*a):
    print(*a, flush=True)


def har_gui():
    try:
        import FreeCADGui
        return FreeCADGui.getMainWindow() is not None
    except Exception:
        return False


def pump(sek=0.2):
    """Låt Qt bearbeta händelser i `sek` sekunder (TechDraw räknar vyer i en tråd)."""
    from PySide import QtGui
    slut = time.time() + sek
    while time.time() < slut:
        QtGui.QApplication.processEvents()
        time.sleep(0.02)


def start_vakt():
    """Stänger modala dialoger (återställning, varningar) som annars blockerar jobbet. Rapporteras i STANGDA."""
    if not har_gui() or os.environ.get("FC_INGEN_VAKT"):
        return None
    from PySide import QtCore, QtGui

    def kolla():
        w = QtGui.QApplication.activeModalWidget()
        if w is not None:
            text = w.windowTitle()
            if hasattr(w, "text"):
                try:
                    text += ": " + w.text()
                except Exception:
                    pass
            STANGDA.append(time.strftime("%H:%M:%S ") + text)
            logg("Obs: dialog stängd automatiskt:", text)
            w.reject() if hasattr(w, "reject") else w.close()
    t = QtCore.QTimer()
    t.timeout.connect(kolla)
    t.start(500)
    return t


def avsluta(ok=True, **data):
    """Skriv resultatet, stäng alla dokument utan att spara och avsluta FreeCAD."""
    j = jobb()
    data["ok"] = ok
    data["dialoger"] = STANGDA
    with open(j["resultat"], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
    try:
        import FreeCAD
        for n in list(FreeCAD.listDocuments()):
            FreeCAD.closeDocument(n)
    except Exception:
        pass
    try:
        _LOGG.flush()
    except Exception:
        pass
    os._exit(0 if ok else 1)


def kor_jobb(funktion):
    """Kör `funktion(args)` inne i FreeCAD med felhantering; funktionen returnerar en dict med resultat."""
    import traceback
    j = jobb()
    vakt = start_vakt()
    t0 = time.time()
    try:
        if har_gui():
            import FreeCADGui
            FreeCADGui.getMainWindow().showMinimized()
        r = funktion(j["args"]) or {}
        logg("Klart på %.0f s" % (time.time() - t0))
        avsluta(True, **r)
    except SystemExit:
        raise
    except Exception as e:
        logg(traceback.format_exc())
        avsluta(False, fel="%s: %s" % (type(e).__name__, e))
