"""Tillverkningsgranskning (DFM) av en plåtdel i FreeCAD: bockning i kantpress och laserskärning.

  python granska.py "<del.FCStd>" [--material S235] [--v-oppning 24] [--kantpress 3000] [--fil]

Delen ska ha SheetMetal-utbredningen "Utbredning" (som datastall.py skapar). Reglerna och gränsvärdena står i
scripts/dfm.py. --fil sparar rapporten som <del>_granskning.txt bredvid delen.
Material styr minsta bockradie: S235 1 t, S355 1,5 t, rostfritt 1 t, aluminium 6082-T6 3 t osv.
"""
import os, sys, argparse


def args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("del_")
    ap.add_argument("--material", default="S235")
    ap.add_argument("--v-oppning", dest="v_oppning", type=float, default=None, help="V-öppning i mm (standard: minsta V >= 8 t)")
    ap.add_argument("--kantpress", type=float, default=3000.0, help="kantpressens längd i mm")
    ap.add_argument("--fil", action="store_true", help="spara rapporten som <del>_granskning.txt")
    return ap.parse_args(argv)


def _jobb():
    import FreeCAD as App
    import fcapi, plat, dfm
    from fcapi import logg

    def huvud(a):
        doc = App.openDocument(os.path.abspath(a["del_"]))
        u = doc.getObject("Utbredning")
        if u is None:
            raise RuntimeError("Delen saknar utbredningen 'Utbredning' (SheetMetal Unfold)")
        doc.recompute()
        kropp = u.baseObject[0]
        rot = int(u.baseObject[1][0].replace("Face", "")) - 1
        utb = plat.utbred(kropp.Shape, rot, kfaktor=u.KFactor)
        am, sam = dfm.granska(utb, a["material"], a["v_oppning"], a["kantpress"], kfaktor=u.KFactor)
        text = dfm.rapport(am, sam, "Tillverkningsgranskning %s (%s)" % (os.path.basename(a["del_"]), a["material"]))
        logg(text)
        if a["fil"]:
            ut = os.path.splitext(os.path.abspath(a["del_"]))[0] + "_granskning.txt"
            with open(ut, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            logg("Sparat:", ut)
        return dict(sammanfattning=sam, fel=sum(x["niva"] == "FEL" for x in am))

    fcapi.kor_jobb(huvud)


if __name__ == "__fcjobb__":
    _jobb()
elif __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fcapi
    a = args()
    a.del_ = os.path.abspath(a.del_)
    if not os.path.exists(a.del_):
        raise SystemExit("Filen finns inte: " + a.del_)
    fcapi.kor(__file__, vars(a))
