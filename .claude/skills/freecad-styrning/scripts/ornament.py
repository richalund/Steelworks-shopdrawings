"""Ornament i Part Design-skisser: mönster ur SVG, text och monogram, och genererade motiv (solfjäder, sicksack,
trappsteg, bågar). Används inne i ett delskript eller i `bygg(d)` till `k.egen`:

  import ornament
  def fris(d):
      sk = d.skiss("Ornament", "XY")
      ornament.svg(sk, "egna/ornament/blad.svg", bredd=400)        # konturerna ur en SVG (Inkscape, Illustrator)
      d.kloss(sk, 3, "Relief")                                     # relief 3 mm (eller d.ficka för gravyr)
      t = d.skiss("Text", "XY", forskjutning=3)
      ornament.text(t, "NO 12", hojd=60, font="egna/ornament/art_deco.ttf")
      d.ficka(t, 1.5, "Gravyr")
  k.egen("or/1", "PL3*400", fris, mitt=(...), material="CuZn37")

Geometrin läggs som linjer, bågar och B-splines i skissen och låses med Block-villkor, så att skissen är fullt
bestämd (måtten ändras genom att köra skriptet med nya värden, inte genom att dra i skissen). Slutna konturer blir
öar, konturer inuti andra blir hål när skissen används till en Pad eller Pocket. Upprepa ett motiv med
`d.monster(...)` eller `d.polart(...)` (pd.py) i stället för att rita det många gånger.

Motiven (alla mått i mm, mitt = motivets mittpunkt i skissen):
  solfjader(sk, r_inre, r_yttre, antal, fran=0, till=180, andel=0.5, mitt=(0, 0))   strålar som ringsektorer
  sicksack(sk, langd, hojd, antal, bredd, mitt=(0, 0))                             sicksackband
  trappsteg(sk, bredd, hojd, steg, mitt=(0, 0))                                   trappstegsmotiv (sluten kontur)
  bagar(sk, r, bredd, antal, avstand, mitt=(0, 0))                                rad av halvcirkelbågar (fjäll)
  ring(sk, d_yttre, d_inre, mitt=(0, 0))                                          ring
Text: `text(sk, "TEXT", hojd, font=None, mitt=(0, 0), sparning=0)`; utan font används osifont (följer med
FreeCAD). Egna typsnitt (.ttf/.otf) läggs i egna/ och anges med sökväg; kontrollera att licensen tillåter det.
SVG: `svg(sk, fil, bredd=None, hojd=None, mitt=(0, 0))` skalar så att bredden (eller höjden) blir den angivna och
centrerar i `mitt` (SVG:ns y nedåt blir uppåt i skissen).
"""
import os, math


def _font():
    import FreeCAD as App
    for f in (os.path.join(App.getResourceDir(), "Mod", "TechDraw", "Resources", "fonts", "osifont-lgpl3fe.ttf"),
              os.path.join(App.getResourceDir(), "examples", "osifont-lgpl3fe.ttf"),
              os.path.join(os.path.dirname(App.getResourceDir().rstrip("/")), "examples", "osifont-lgpl3fe.ttf"),
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(f):
            return f
    raise RuntimeError("Hittar inget typsnitt: ange font='sökväg/till/typsnitt.ttf'")


def _geometri(e):
    """Kant -> skissgeometri (linje, båge, cirkel eller B-spline) i skissens XY."""
    import Part
    c = e.Curve
    if c.TypeId == "Part::GeomLine":
        return Part.LineSegment(e.Vertexes[0].Point, e.Vertexes[-1].Point)
    if c.TypeId == "Part::GeomCircle":
        if e.isClosed():
            return Part.Circle(c.Center, c.Axis, c.Radius)
        return Part.ArcOfCircle(c, e.FirstParameter, e.LastParameter)
    return e.Curve.toBSpline(e.FirstParameter, e.LastParameter)


def kanter(sk, kantlista, las=True):
    """Lägger kanterna (Part.Edge i skissens XY, z = 0) i skissen och låser dem (Block). Returnerar index."""
    ut = []
    for e in kantlista:
        if e.Length < 1e-6:
            continue
        g = sk.geo(_geometri(e))
        if las:
            sk.begr("Block", g)
        ut.append(g)
    sk.d.doc.recompute()
    return ut


def _placera(former, bredd=None, hojd=None, mitt=(0, 0), vand_y=False):
    """Skala (bredd eller höjd), vänd y och centrera formerna (Part.Shape) kring mitt. Returnerar kanterna."""
    import Part
    from FreeCAD import Vector as V, Matrix
    c = Part.makeCompound(former)
    bb = c.BoundBox
    s = 1.0
    if bredd:
        s = float(bredd) / bb.XLength
    elif hojd:
        s = float(hojd) / bb.YLength
    m = Matrix()
    m.move(V(-(bb.XMin + bb.XMax) / 2, -(bb.YMin + bb.YMax) / 2, -bb.ZMin))
    sk = Matrix()
    sk.scale(s, -s if vand_y else s, 1)
    m = sk.multiply(m)
    fl = Matrix()
    fl.move(V(mitt[0], mitt[1], 0))
    m = fl.multiply(m)
    c = c.transformGeometry(m)
    return c.Edges


def svg(sk, fil, bredd=None, hojd=None, mitt=(0, 0)):
    """Konturerna i en SVG-fil (banor, rektanglar, cirklar) som låst geometri i skissen."""
    import FreeCAD as App
    import importSVG
    if not os.path.exists(fil):
        raise FileNotFoundError(fil)
    tmp = App.newDocument("SvgImport")
    try:
        importSVG.insert(fil, tmp.Name)
        tmp.recompute()
        former = [o.Shape for o in tmp.Objects if hasattr(o, "Shape") and not o.Shape.isNull() and o.Shape.Edges]
        if not former:
            raise RuntimeError("SVG-filen %s har inga konturer" % fil)
        kl = _placera(former, bredd, hojd, mitt)             # importSVG vänder redan y uppåt
    finally:
        App.closeDocument(tmp.Name)
        App.setActiveDocument(sk.d.doc.Name)
    return kanter(sk, kl)


def text(sk, s, hojd, font=None, mitt=(0, 0), sparning=0):
    """Texten som konturer (versalhöjd ca `hojd`) centrerad i mitt."""
    import Part
    tecken = Part.makeWireString(s, font or _font(), float(hojd), float(sparning))
    tradar = [w for t in tecken for w in t]
    if not tradar:
        raise RuntimeError("Texten '%s' gav inga konturer (saknas tecknen i typsnittet?)" % s)
    return kanter(sk, _placera(tradar, mitt=mitt))


def _polygon(punkter):
    import Part
    from FreeCAD import Vector as V
    p = [V(x, y, 0) for x, y in punkter]
    return Part.makePolygon(p + [p[0]])


def solfjader(sk, r_inre, r_yttre, antal, fran=0, till=180, andel=0.5, mitt=(0, 0)):
    """Solfjäder: `antal` strålar som ringsektorer mellan radierna, jämnt fördelade mellan vinklarna fran..till
    (grader, 0 = +x), varje stråle `andel` av sin delning bred."""
    import Part
    from FreeCAD import Vector as V
    kl = []
    delning = (till - fran) / float(antal)
    for i in range(antal):
        a0 = math.radians(fran + delning * (i + (1 - andel) / 2))
        a1 = math.radians(fran + delning * (i + (1 + andel) / 2))
        P = lambda r, a: V(mitt[0] + r * math.cos(a), mitt[1] + r * math.sin(a), 0)
        am = (a0 + a1) / 2
        yttre = Part.Arc(P(r_yttre, a0), P(r_yttre, am), P(r_yttre, a1)).toShape()
        inre = Part.Arc(P(r_inre, a1), P(r_inre, am), P(r_inre, a0)).toShape() if r_inre > 0 else None
        kl += [yttre, Part.LineSegment(P(r_yttre, a1), P(r_inre, a1)).toShape()]
        if inre is not None:
            kl += [inre, Part.LineSegment(P(r_inre, a0), P(r_yttre, a0)).toShape()]
        else:
            kl += [Part.LineSegment(P(0, a0), P(r_yttre, a0)).toShape()]
    return kanter(sk, kl)


def sicksack(sk, langd, hojd, antal, bredd, mitt=(0, 0)):
    """Sicksackband `langd` långt och `hojd` högt med `antal` toppar, banden `bredd` breda (lodrätt mätt)."""
    x0, y0 = mitt[0] - langd / 2.0, mitt[1] - hojd / 2.0
    n = 2 * antal
    upp = [(x0 + langd * i / n, y0 + (hojd if i % 2 else bredd)) for i in range(n + 1)]
    ned = [(x, y - bredd) for x, y in reversed(upp)]
    return kanter(sk, _polygon(upp + ned).Edges)


def trappsteg(sk, bredd, hojd, steg, mitt=(0, 0)):
    """Trappstegsmotiv (sluten kontur): `steg` lika avsatser från bredden nere till en topp i mitten."""
    x0, y0 = mitt[0], mitt[1] - hojd / 2.0
    dx, dy = bredd / (2.0 * steg + 1), hojd / float(steg)
    hoger = []
    for i in range(steg):
        x = x0 + bredd / 2.0 - i * dx
        hoger += [(x, y0 + i * dy), (x, y0 + (i + 1) * dy)]
    topp = [(x0 + dx / 2.0, y0 + hojd), (x0 - dx / 2.0, y0 + hojd)]
    vanster = [(2 * x0 - x, y) for x, y in reversed(hoger)]
    return kanter(sk, _polygon(hoger + topp + vanster).Edges)


def bagar(sk, r, bredd, antal, avstand, mitt=(0, 0)):
    """Rad av halvcirkelbågar (fjällmönster): `antal` bågar med yttre radien r och godsbredden `bredd`, delning
    `avstand`, centrerade kring mitt."""
    import Part
    from FreeCAD import Vector as V
    kl = []
    x0 = mitt[0] - avstand * (antal - 1) / 2.0
    for i in range(antal):
        c = V(x0 + i * avstand, mitt[1], 0)
        ri = r - bredd
        kl += [Part.Arc(c + V(r, 0, 0), c + V(0, r, 0), c + V(-r, 0, 0)).toShape(),
               Part.LineSegment(c + V(-r, 0, 0), c + V(-ri, 0, 0)).toShape(),
               Part.Arc(c + V(-ri, 0, 0), c + V(0, ri, 0), c + V(ri, 0, 0)).toShape(),
               Part.LineSegment(c + V(ri, 0, 0), c + V(r, 0, 0)).toShape()]
    return kanter(sk, kl)


def ring(sk, d_yttre, d_inre, mitt=(0, 0)):
    """Ring (två koncentriska cirklar) med namngivna diametrar, fullt bestämd utan Block."""
    sk.cirkel(d_yttre, mitt=mitt)
    sk.cirkel(d_inre, mitt=mitt)
