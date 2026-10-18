"""Rörelsekontroll för dörrar, grindar och luckor: krockar genom hela öppningen, tyngdpunkt och gångjärnslast.

  python3 rorelse.py <modell.FCStd> [--steg 5] [--oppen 90 --ut <modell>_oppen.FCStd]

Den rörliga delen beskrivs i konstruktionsskriptet med `k.rorelse(namn, delar, axel=((x, y, z), (0, 0, 1)),
fran=0, till=100, gangjarn=[(x, y, z1), (x, y, z2)])` (stal.py). För varje rörelse vrids delarna kring axeln i steg
om `--steg` grader från `fran` till `till`, och för varje läge kontrolleras överlapp (volym > 1 mm3) mot alla
andra delar och referenskropparna i Omgivning (vägg, mark, trappsteg). Utskriften:
  Rörelse GRIND: fri 0–100° | krock vid 85° med Omgivning/Trappsteg 3 (fritt till 80°)
  Tyngdpunkt 412 mm från axeln, 38.2 kg; gångjärn c/c 1200: horisontell last 128 N per gångjärn, lodrätt 375 N
Gångjärnslasten: horisontalkraften H = G·e/h (kraftpar mellan övre och undre gångjärnet, e = tyngdpunktens
avstånd från axeln, h = gångjärnsavståndet) och hela tyngden G lodrätt (på ett gångjärn, som säkert antagande).
Jämför med gångjärnets eller beslagstillverkarens tillåtna last.

`--oppen 90 --ut fil.FCStd` sparar en kopia med de rörliga delarna öppnade 90° (för 3D-bilder av öppen grind
eller dörr: `rendera.py fil.FCStd`). Originalfilen ändras inte.
"""
import os, sys, json, argparse


def _jobb(a):
    import FreeCAD as App
    from FreeCAD import Vector as V
    import Part
    import stal
    from fcapi import logg
    doc = App.openDocument(a["fil"])
    doc.recompute()
    g, ds, _ = stal.delar(doc)
    rorelser = json.loads(getattr(g, "Rorelser", "") or "[]")
    if not rorelser:
        raise RuntimeError("Modellen har inga rörliga delar: lägg till k.rorelse(...) i konstruktionsskriptet")
    omg = doc.getObject("Omgivning")
    referens = [o for o in (omg.Group if omg else []) if getattr(o, "Shape", None) is not None and o.Shape.Solids]
    resultat = []
    for r in rorelser:
        sel = r["delar"]
        rorliga = [o for o in ds if (o.Pos in sel if isinstance(sel, list) else o.Pos.startswith(sel))]
        if not rorliga:
            raise RuntimeError("Rörelse %s: inga delar matchar %s" % (r["namn"], sel))
        fasta = [o for o in ds if o not in rorliga] + referens
        p0, rikt = V(*r["axel"][0]), V(*r["axel"][1]).normalize()
        rorlig = Part.makeCompound([o.Shape for o in rorliga])
        steg = abs(float(a.get("steg") or 5)) * (1 if r["till"] >= r["fran"] else -1)   # negativ till = medurs
        n = int(abs(r["till"] - r["fran"]) / abs(steg) + 1e-9)
        vinklar = [r["fran"] + i * steg for i in range(n + 1)]
        if abs(vinklar[-1] - r["till"]) > 1e-9:
            vinklar.append(float(r["till"]))
        krock, fritt = None, None
        for vk in vinklar:
            s = rorlig.copy()
            s.rotate(p0, rikt, vk - r["fran"])
            bb = s.BoundBox
            traff = []
            for o in fasta:
                if not bb.intersect(o.Shape.BoundBox):
                    continue
                c = s.common(o.Shape)
                if c.Volume > 1.0:
                    traff.append(o.Label if o not in referens else "Omgivning/" + o.Label)
            if traff:
                krock = (vk, traff)
                break
            fritt = vk
        # tyngdpunkt och gångjärnslast
        massa, moment = 0.0, V(0, 0, 0)
        for o in rorliga:
            m = float(getattr(o, "Vikt", 0) or 0) or o.Shape.Volume * 1e-9 * stal.densitet(getattr(o, "Material", ""))
            massa += m
            for sol in o.Shape.Solids:                   # SheetMetal-delar är compounds: tyngdpunkt per solid
                moment += sol.CenterOfMass * (m * sol.Volume / o.Shape.Volume)
        tp = moment * (1.0 / massa)
        d = tp - p0
        e = (d - rikt * d.dot(rikt)).Length
        G = massa * 9.81
        last = ""
        gj = [V(*p) for p in r.get("gangjarn") or []]
        if len(gj) >= 2:
            pos = sorted((q - p0).dot(rikt) for q in gj)
            h = pos[-1] - pos[0]
            H = G * e / h if h > 0 else float("nan")
            last = "; gångjärn c/c %.0f: horisontell last %.0f N per gångjärn (övre drar, undre trycker), lodrätt %.0f N" % (h, H, G)
        if krock:
            txt = "krock vid %g° med %s (fritt till %s°)" % (krock[0], ", ".join(krock[1]), "%g" % fritt if fritt is not None else "-")
        else:
            txt = "fri %g–%g°" % (r["fran"], r["till"])
        logg("Rörelse %s (%d delar): %s" % (r["namn"], len(rorliga), txt))
        logg("  Tyngdpunkt %.0f mm från axeln, %.1f kg%s" % (e, massa, last))
        resultat.append(dict(namn=r["namn"], fri=not krock, krock_vid=krock[0] if krock else None, med=krock[1] if krock else [],
                             fritt_till=fritt, massa=massa, avstand_mm=e))
        if a.get("oppen") is not None and a.get("ut"):
            for o in rorliga:
                for k in ("x", "y", "z"):
                    try:
                        o.setExpression(".Placement.Base." + k, None)
                    except Exception:
                        pass
                rot = App.Placement(V(0, 0, 0), App.Rotation(rikt, float(a["oppen"]) - r["fran"]), p0)
                o.Placement = rot.multiply(o.Placement)
    if a.get("oppen") is not None and a.get("ut"):
        doc.recompute()
        doc.saveAs(os.path.abspath(a["ut"]))
        logg("Sparat med rörliga delar öppnade %g°: %s" % (float(a["oppen"]), os.path.abspath(a["ut"])))
    return dict(rorelser=resultat)


if __name__ == "__fcjobb__":
    import fcapi
    fcapi.kor_jobb(_jobb)
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("fil")
    ap.add_argument("--steg", type=float, default=5)
    ap.add_argument("--oppen", type=float, default=None, help="vinkel (grader) att spara öppen kopia i")
    ap.add_argument("--ut", default=None)
    a = vars(ap.parse_args())
    a["fil"] = os.path.abspath(a["fil"])
    if (a["oppen"] is None) != (a["ut"] is None):
        ap.error("--oppen och --ut anges tillsammans")
    r = fcapi.kor(__file__, a)
    sys.exit(0 if all(x["fri"] for x in r["rorelser"]) else 1)
