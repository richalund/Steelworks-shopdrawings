"""Pall av rör med bockad sittram – exempel på bockade rör (k.rorbage), gering mellan ett bockat rör och ett ben
(k.kap och k.gera), fiskmun mot ett rörs mantel (k.fiskmun) och ett liggande plattstål att skruva sitsen i.

  python3 scripts/sammanstallning.py bygg konstruktioner/pall.py ut/P1.FCStd --var Bredd=420 --png
  python3 scripts/sammanstallning.py ritning ut/P1.FCStd --uppdrag 2026-001

Sittramen ra/1 är ett rör bockat till en U-bage (halvcirkel bak, raka sidor fram). Frambenen b/1 står lodrätt
under framhörnen och geras 45° mot sittramens sidor; bakbenen b/2 lutar utåt och fiskmunskapas mot bågen. Ett
liggande plattstål fl/1 mellan sidorna, indraget från framkanten, bär sitsens framkant och sitsen skruvas i det.
Sitsen pl/1 är en D-formad plåt med samma form som ramen.

Koordinater: X = bredd (mitt x = 0), Y = djup (sitsens framkant y = 0, bakåt +Y), Z uppåt (golv z = 0).
Måtten är exempelmått; ramens mått räknas ur Variabler vid bygget.
"""
import math

NAMN = "Pall"
MARKE = "P/1"
VARIABLER = [
    ("Hojd", 450, "mm, golv till sitsens ovansida"),
    ("Bredd", 400, "mm, sitsens bredd = bågens ytterdiameter"),
    ("Djup", 380, "mm, sitsens djup"),
    ("Regel", 20, "mm, framregelns framkant bakom sitsens framkant"),
]
REGLER = [dict(villkor="Djup > Bredd / 2 + 60", text="raka sidor minst 60 mm i sittramen")]

ROR, D = "RÖR21.3*2", 21.3
R = D / 2
PT = 3.0                       # sitsplåt
VINKEL = 50                    # bakbenens läge på bågen, grader från bakåt
UT = 1.15                      # bakbenens fot = toppens läge * UT (lutning utåt)
NOTER = ["EXEMPEL – PALL AV RÖR MED BOCKAD SITTRAM, EJ FÖR TILLVERKNING",
         "UTFÖRANDE: ra/1 BOCKAS AV ETT RÖR, LÄNGDEN I MATERIALLISTAN ÄR UTDRAGEN LÄNGD",
         "UTFÖRANDE: b/1 GERAS 45° MOT ra/1, b/2 OCH fl/1 FISKMUNSKAPAS MOT ra/1",
         "MONTAGE: SITSEN SKRUVAS I fl/1 MED 2 SKRUV M5x12 FÖRSÄNKT + MUTTER, NITAS I ra/1",
         "SVETS: MIG RUNT OM",
         "YTBEHANDLING: PULVERLACK"]


def bygg(k, v):
    H, B, Dj = v["Hojd"], v["Bredd"], v["Djup"]
    Rut = B / 2                        # bågens ytterradie = sitsens kant
    Rs = Rut - R                       # rörets axel
    yc = Dj - Rut                      # bågens mitt
    zs = H - PT - R                    # ramens axel
    # sittram: U-bage med raka ben fram till framkanten, gerade 45° mot frambenen (hörnets axelpunkt y = R)
    ra = k.rorbage("ra/1", ROR, Rs, yc + 5, mitt=(0, yc, zs), material="S235JRH", huvuddel=True)
    k.kap(ra, (Rs, 0, zs + R), (Rs, 2 * R, zs - R), (1, 0, 0))
    # framben: lodräta under hörnen, gerade mot ramen och kapade plant mot golvet
    for s in (-1, 1):
        b = k.balk("b/1", ROR, (s * Rs, R, -5), (s * Rs, R, zs + 2 * R), upp=(1, 0, 0), material="S235JRH")
        k.gera(b, (s * Rs, 0, zs + R), (s * Rs, 2 * R, zs - R))
        k.gera(b, (s * Rs - 30, R, 0), (s * Rs + 30, R, 0))
    # bakben: från golvet (utåt) till bågens axel, fiskmun mot bågens tangent
    a = math.radians(VINKEL)
    for s in (-1, 1):
        topp = (s * Rs * math.sin(a), yc + Rs * math.cos(a), zs)
        fot = (topp[0] * UT, yc + (topp[1] - yc) * UT, 0)
        w = [t - f for t, f in zip(topp, fot)]
        L = math.sqrt(sum(c * c for c in w))
        w = [c / L for c in w]
        hor = math.hypot(w[0], w[1])
        ut = (w[0] / hor, w[1] / hor, 0)
        b = k.balk("b/2", ROR, tuple(f - c * 6 for f, c in zip(fot, w)), topp, upp=(-ut[1], ut[0], 0), material="S235JRH")
        k.gera(b, (fot[0] + ut[0] * 30, fot[1] + ut[1] * 30, 0), (fot[0] - ut[0] * 30, fot[1] - ut[1] * 30, 0))
        k.fiskmun(b, topp, (math.cos(a), -s * math.sin(a), 0), D)
    # framregel: liggande plattstål, ovansidan mot sitsen, fiskmunskapad mot ramens sidor
    yr = v["Regel"] + 15
    fl = k.balk("fl/1", "FL30*5", (-Rs, yr, zs + R - 2.5), (Rs, yr, zs + R - 2.5), upp=(0, 0, 1), material="S235JR")
    for s in (-1, 1):
        k.fiskmun(fl, (s * Rs, 0, zs), (0, 1, 0), D)

    # sits: D-formad plåt
    def sits(d):
        import Part
        import pd
        from FreeCAD import Vector as V
        sk = d.skiss("Kontur", "XY")
        fram = sk.geo(Part.LineSegment(V(-Rut, -yc, 0), V(Rut, -yc, 0)))
        hoger = sk.geo(Part.LineSegment(V(Rut, -yc, 0), V(Rut, 0, 0)))
        bage = sk.geo(Part.ArcOfCircle(Part.Circle(V(0, 0, 0), V(0, 0, 1), Rut), 0.0, math.pi))
        vanster = sk.geo(Part.LineSegment(V(-Rut, 0, 0), V(-Rut, -yc, 0)))
        sk.begr("Horizontal", fram)
        sk.begr("Vertical", hoger)
        sk.begr("Vertical", vanster)
        sk.begr("Coincident", fram, pd.SLUT, hoger, pd.START)
        sk.begr("Coincident", vanster, pd.SLUT, fram, pd.START)
        sk.begr("Tangent", hoger, pd.SLUT, bage, pd.START)
        sk.begr("Tangent", bage, pd.SLUT, vanster, pd.START)
        sk.begr("Coincident", bage, pd.MITT, pd.ROT, 1)
        sk.matt("Radius", bage, varde=Rut, namn="Radie")
        sk.matt("DistanceY", fram, pd.START, pd.ROT, 1, varde=yc, namn="Rak")
        d.kloss(sk, PT, "Tjocklek")
    pl = k.egen("pl/1", "PL%g*%g" % (PT, B), sits, mitt=(0, yc, H - PT), material="S235JR")
    k.hal([pl, fl], [(-120, yr, H - PT), (120, yr, H - PT)], (0, 0, 1), d=5.5, bult="M5x12", langd=16)
    k.hal([pl, ra], [(-Rs, yc * 0.6, H - PT), (Rs, yc * 0.6, H - PT), (0, yc + Rs, H - PT)], (0, 0, 1), d=4.9,
          bult="BLINDNIT 4.8", langd=8)
    k.ritning(vyer=["fram", "plan"], snitt=[dict(namn="A", axel="x", varde=0, mot="-")], noter=NOTER)
