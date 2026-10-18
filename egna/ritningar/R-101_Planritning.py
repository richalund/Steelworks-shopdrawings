"""Planritning R-101 för P. Hellstones entrétrappa (ritskript till skillens scripts/oversikt.py): fasad sett från
gången och plan i 1:20 av översikten T/1 (trappa + räcken R/1–R/3), måttkedjor för trappan och räckenas stolpar,
märkning R/1, R/2, R/3, nivåer och noter.

python3 .claude/skills/freecad-styrning/scripts/oversikt.py ut/T1_Trappa_oversikt.FCStd egna/ritningar/R-101_Planritning.py --uppdrag OFFERT
"""
import os, sys, importlib.util

HIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, HIT)
import trappa_hellstone as T

NUMMER = "R-101"
SKALA = 20
OBJEKT = ["PLAN ENTRÉTRAPPA MED RÄCKEN, VILLA", "Patrik Hellstone, 0733 41 42 21", "Adress enligt beställare"]


def parametrar(modul):
    spec = importlib.util.spec_from_file_location(modul, os.path.join(HIT, "konstruktioner", modul + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.parametrar()


def rita(r):
    # fasad sett från gången (dörren till vänster som på fotot) och plan under (E-metoden)
    fasad = r.vy("FASAD MOT INNERGÅRDEN", riktning=(0, 1, 0), x=(-1, 0, 0), lage=(175, 324), rubrik=False)
    plan = r.vy("PLAN", riktning=(0, 0, 1), x=(-1, 0, 0), lage=(175, 142), rubrik=False)
    Zv, Zp, B, Yf = T.Z_VILPLAN, T.Z_PODEST, T.BREDD, T.Y_FRAM
    xv, x0, xp, xw = T.X_VILPLAN, 0.0, T.X_PODEST, T.X_VAGG
    # ---- trappans mått: längs fasaden (ovanför, vid fasaden), ut från fasaden (till höger om vilplanet)
    plan.kedja([(xw, 0, Zp), (xp, 0, Zp), (x0, 0, Zp), (xv, 0, Zp)], "x", 7, fran=(xw, 0, 0))
    plan.matt((xw, 0, Zp), (xv, 0, Zp), "x", 14, fran=(xw, 0, 0))
    plan.kedja([(xv, 0, Zv), (xv, B, Zv), (xv, Yf, 0)], "y", 20, fran=(xv, 0, 0))
    plan.matt((xv, 0, Zv), (xv, Yf, 0), "y", 28, fran=(xv, 0, 0))
    plan.matt((x0, Yf, 0), (xv, Yf, 0), "x", -7, fran=(0, Yf, 0))
    # ---- räckenas stolpar (c/c), samma lägen som i R/1–R/3
    y1, xr2, xr3 = B - T.KANT, -T.KANT, xv + T.KANT
    st1 = [(x, y1, Zp) for x in parametrar("racke_r1_ovre")["stolpar"]]
    st2 = sorted([(xr2, Yf - x, Zv) for x in parametrar("racke_r2_nedre_vanster")["stolpar"]], key=lambda p: p[1])
    st3 = sorted([(xr3, Yf - x, Zv) for x in parametrar("racke_r3_nedre_hoger")["stolpar"]], key=lambda p: p[1])
    plan.kedja(st1, "x", -8, fran=(0, y1, 0))                  # under R/1, i innergården
    plan.kedja(st2, "y", -9, fran=(xr2, 0, 0))                 # mot innergården
    plan.kedja(st3, "y", 10, fran=(xv, 0, 0))                  # utanför R/3
    # ---- märkning, nivåer, rubriker
    plan.bubbla("R/1", (xp + 600, y1, Zp), -6, -24)
    plan.bubbla("R/2", (xr2, Yf - 900, Zv), -12, -6)
    plan.bubbla("R/3", (xr3, 450, Zv), -14, -8)
    fasad.bubbla("R/1", (xp - 300, y1, Zp + 900 - 400), 10, 16)
    fasad.bubbla("R/2", (xr2, Yf - 900, 600), -14, 4)
    fasad.bubbla("R/3", (xr3, Yf - 1800, 1400), -14, 12)
    for p, txt in (((xv / 2, B / 2, 0), "VILPLAN +%g" % Zv), (((xp + xw) / 2, B / 2, 0), "DÖRRPODEST +%g" % Zp),
                   ((xp / 2, B / 2, 0), "UPP 4 STEG"), ((xv / 2, B + 900, 0), "UPP 5 STEG"), ((xv / 2, Yf + 250, 0), "GÅNG ±0"),
                   (((x0 + xw) / 2, B + 1000, 0), "INNERGÅRD ±0"), ((xw + 450, 150, 0), "FASAD")):
        plan.text(txt, p)
    for z, txt in ((0, "±0 GÅNG"), (Zv, "+%g VILPLAN" % Zv), (Zp, "+%g DÖRRPODEST" % Zp)):
        fasad.niva(txt, (xv - 150, Yf, z), dx=26)
    r.text("FASAD MOT INNERGÅRDEN  1:%g" % SKALA, (175, fasad.papper((0, Yf, 0))[1] - 8), 3.5)
    r.text("PLAN  1:%g" % SKALA, (175, plan.papper((0, Yf, 0))[1] - 22), 3.5)
    r.noter(["PLANRITNING – ENTRÉTRAPPA MED RÄCKEN R/1, R/2, R/3 (OFFERTUNDERLAG, EJ FÖR TILLVERKNING)",
             "UNDERLAG: FOTON OCH MÅTT I MAIL FRÅN P. HELLSTONE 2026-10-17",
             "TRAPPANS MÅTT ÄR ANTAGNA UR FOTON – KONTROLLMÄTS PÅ PLATS",
             "STEG %g/%g (ÖVRE LOPP) OCH %g/%g (NEDRE LOPP), RÄCKENA %g IN FRÅN STENKANT" % (T.R, T.G_OVRE, T.R, T.G_NEDRE, T.KANT),
             "STOLPAR FS20 NEDGJUTNA 100 I KÄRNBORRADE HÅL Ø40, c/c MAX 1300, MÅTT c/c STOLPE",
             "R/1 OCH R/2 HAR GEMENSAM HÖRNSTOLPE PÅ VILPLANET",
             "RÄCKESHÖJD 900 ÖVER STEGFRAMKANT, KNÄCKEN MITT ÖVER STOLPE 60 IN PÅ PODEST/VILPLAN",
             "TILLVERKNINGSRITNINGAR: R/1, R/2, R/3 (BLAD .1 OCH .2), GRIND G/1",
             "GRIND G/1 SITTER MELLAN GRANITSTOLPARNA VID GATAN (EJ I PLANEN)",
             "YTBEHANDLING: VARMFÖRZINKAD OCH PULVERLACKAD SVART RAL 9005 (ANTAGET)"])
