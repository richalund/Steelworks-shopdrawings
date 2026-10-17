r"""H-/I-profil (HEA, HEB, IPE …) som Part Design: en skiss med tvärsnittet och en Pad längs balken.
Standardmåtten är HEA 260 (EN 10365): h 250, b 260, tw 7,5, tf 12,5, r 24.
  python scripts/partdesign.py bygg delar/hprofil.py "<mapp>\HEA260.FCStd" --var Langd=2500 --png --step
Koordinater: X = balkens längd (0..Langd), Y = flänsbredd (centrerad), Z = höjd (underfläns underkant i Z = 0).
Tvärsnittet ritas i YZ-planet med tangerande bågar i livets hörn, så att radien är ett skissmått.
"""
import math
import Part
from FreeCAD import Vector as V

NAMN = "HEA260"
VARIABLER = [
    ("Hojd", 250, "mm, profilhöjd h"),
    ("Bredd", 260, "mm, flänsbredd b"),
    ("Liv", 7.5, "mm, livtjocklek tw"),
    ("Flans", 12.5, "mm, flänstjocklek tf"),
    ("Radie", 24, "mm, radie liv/fläns r"),
    ("Langd", 2500, "mm, balklängd L"),
]

START, SLUT = 1, 2


def bygg(d):
    sk = d.skiss("Tvarsnitt", "YZ")                    # skissens x = Y, y = Z, normal +X
    h, b, tw, tf, r = (sk._v(v) for v in ("Hojd", "Bredd", "Liv", "Flans", "Radie"))
    x1, x2 = tw / 2, tw / 2 + r                        # livets yta, bågens slut på flänsen

    def linje(a, c):
        return sk.geo(Part.LineSegment(V(a[0], a[1], 0), V(c[0], c[1], 0)))

    def bage(mx, my, v0, v1):
        return sk.geo(Part.ArcOfCircle(Part.Circle(V(mx, my, 0), V(0, 0, 1), r), v0, v1))

    pi = math.pi
    L0 = linje((-b / 2, 0), (b / 2, 0))                # underflänsens underkant
    L1 = linje((b / 2, 0), (b / 2, tf))
    L2 = linje((b / 2, tf), (x2, tf))
    A0 = bage(x2, tf + r, pi, 1.5 * pi)                # nedre högra roten: start på livet, slut på flänsen
    L3 = linje((x1, tf + r), (x1, h - tf - r))         # livets högra sida
    A1 = bage(x2, h - tf - r, 0.5 * pi, pi)            # övre högra roten: start på flänsen, slut på livet
    L4 = linje((x2, h - tf), (b / 2, h - tf))
    L5 = linje((b / 2, h - tf), (b / 2, h))
    L6 = linje((b / 2, h), (-b / 2, h))                # överflänsens överkant
    L7 = linje((-b / 2, h), (-b / 2, h - tf))
    L8 = linje((-b / 2, h - tf), (-x2, h - tf))
    A2 = bage(-x2, h - tf - r, 0, 0.5 * pi)            # övre vänstra roten: start på livet, slut på flänsen
    L9 = linje((-x1, h - tf - r), (-x1, tf + r))       # livets vänstra sida
    A3 = bage(-x2, tf + r, 1.5 * pi, 2 * pi)           # nedre vänstra roten: start på flänsen, slut på livet
    L10 = linje((-x2, tf), (-b / 2, tf))
    L11 = linje((-b / 2, tf), (-b / 2, 0))

    # slutna konturen: hörn där två linjer möts, tangent där linje och båge möts
    for g1, g2 in ((L0, L1), (L1, L2), (L4, L5), (L5, L6), (L6, L7), (L7, L8), (L10, L11), (L11, L0)):
        sk.begr("Coincident", g1, SLUT, g2, START)
    for g1, p1, g2, p2 in ((L2, SLUT, A0, SLUT), (A0, START, L3, START), (L3, SLUT, A1, SLUT),
                           (A1, START, L4, START), (L8, SLUT, A2, SLUT), (A2, START, L9, START),
                           (L9, SLUT, A3, SLUT), (A3, START, L10, START)):
        sk.begr("Tangent", g1, p1, g2, p2)
    for g in (L0, L2, L4, L6, L8, L10):
        sk.begr("Horizontal", g)
    for g in (L1, L3, L5, L7, L9, L11):
        sk.begr("Vertical", g)

    # läge: underflänsen centrerad kring origo (underkant i Z = 0)
    sk.begr("Symmetric", L0, START, L0, SLUT, -1, 1)
    # symmetri: lika radier, lika flänstjocklekar, lika flänsbredder, överflänsen rakt över, livet i mitten
    for a in (A1, A2, A3):
        sk.begr("Equal", A0, a)
    for g in (L11, L5, L7):
        sk.begr("Equal", L1, g)
    sk.begr("Equal", L0, L6)
    sk.begr("PointOnObject", L5, START, L1)
    sk.begr("Equal", L2, L10)

    # namngivna mått mot Variabler
    sk.matt("DistanceX", L0, START, L0, SLUT, varde="Bredd")
    sk.matt("DistanceY", L0, START, L7, START, varde="Hojd")
    sk.matt("DistanceY", L1, START, L1, SLUT, varde="Flans")
    sk.matt("DistanceX", L9, SLUT, L3, START, varde="Liv")
    sk.matt("Radius", A0, varde="Radie")

    d.kloss(sk, "Langd", "Balk")
