"""Tillverkningsgranskning (DFM) för bockad plåt och laserskurna plattor. Körs inne i FreeCAD på resultatet
av `plat.utbred()`. Varje anmärkning anger regeln, uppmätt värde och krav, så att den går att pröva.

Reglerna är tumregler för luftbockning i kantpress och laserskärning. De är satta efter vanlig praxis och
ska stämmas av mot verkstadens maskiner (V-öppningar, kantpressens längd, plåtformat) – ändra konstanterna
nedan eller skicka egna värden till `granska()`.
"""
import math
import Part
from FreeCAD import Vector as V

# V-öppningar (mm) som verktygen brukar finnas i. Standardvalet är minsta V >= 8 x tjockleken.
V_OPPNINGAR = [6, 8, 10, 12, 16, 20, 24, 32, 40, 50, 63, 80]
V_FAKTOR = 8.0
MIN_FLANS_FAKTOR = 0.7          # minsta yttre flänslängd = 0,7 x V (vanlig tabellregel för luftbockning)
NATURLIG_RADIE = (1 / 8.0, 1 / 6.0)   # luftbockning ger inre radie ca V/8 - V/6
HAL_BOCK_FAKTOR = 2.5           # hålkant till bockens mittlinje >= 2,5 t + R
KANTPRESS_LANGD = 3000.0        # mm, längsta bock
PLATFORMAT = [(2000, 1000), (2500, 1250), (3000, 1500), (4000, 2000)]
STANDARDTJOCKLEKAR = [0.5, 0.7, 0.8, 1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30]
# minsta inre bockradie som andel av tjockleken (kallbockning, vinkelrätt mot valsriktningen)
MIN_RADIE = [("6082", 3.0, "aluminium 6082-T6"), ("6061", 3.0, "aluminium 6061-T6"), ("6060", 2.0, "aluminium 6060-T6"),
             ("6063", 2.0, "aluminium 6063-T6"), ("5754", 1.0, "aluminium 5754"), ("aluminium", 2.0, "aluminium (okänd legering)"),
             ("1.4301", 1.0, "rostfritt 1.4301"), ("1.4404", 1.0, "rostfritt 1.4404"), ("rostfri", 1.0, "rostfritt"),
             ("s420", 2.0, "S420"), ("s355", 1.5, "S355"), ("dc01", 0.5, "DC01"), ("s275", 1.0, "S275"), ("s235", 1.0, "S235")]

FEL, VARNING, INFO, OK = "FEL", "VARNING", "INFO", "OK"


def fmt(x, dec=1):
    s = ("%." + str(dec) + "f") % x
    return (s.rstrip("0").rstrip(".") if "." in s else s).replace(".", ",")


def material_regel(material):
    m = (material or "").lower()
    for nyckel, faktor, namn in MIN_RADIE:
        if nyckel in m:
            return faktor, namn
    return 1.0, "stål (antaget S235)"


def valj_v(t):
    for v in V_OPPNINGAR:
        if v >= V_FAKTOR * t - 1e-9:
            return float(v)
    return V_OPPNINGAR[-1]


def _bockdata(b, t, k=0.5):
    """Yttre tillbakadragning (OSSB) och bockningstillägg (BA) för en bock."""
    th = math.radians(b["vinkel"])
    ossb = (b["radie"] + t) * math.tan(th / 2) if b["vinkel"] < 179 else b["radie"] + t
    ba = th * (b["radie"] + k * t)
    return ossb, ba


def _traffar(seg, kanter):
    """Avstånd från segmentets start till skärningspunkterna med kanterna."""
    ut = []
    p0 = seg.Vertexes[0].Point
    for e in kanter:
        try:
            d, par, _ = seg.distToShape(e)
        except Exception:
            continue
        if d < 1e-6:
            for a, _b in par:
                L = (a - p0).Length
                if L > 1e-4:
                    ut.append(L)
    return ut


def _flanser(utb, t, k):
    """Kortaste yttre flänslängd på varje sida av varje bocklinje (mätt i utbredningen, räknat om till
    yttermått mellan virtuella skärningar). Mäts vid 10, 50 och 90 % av bocklinjen."""
    face = utb["face2d"]
    kontur = list(face.OuterWire.Edges)
    bockar = utb["bockar2d"]
    bb = face.BoundBox
    L = math.hypot(bb.XLength, bb.YLength) * 2
    ut = []
    for i, b in enumerate(bockar):
        e = b["linje"]
        p1, p2 = e.Vertexes[0].Point, e.Vertexes[-1].Point
        r = (p2 - p1).normalize()
        n = V(-r.y, r.x, 0)
        ossb_i, ba_i = _bockdata(b, t, k)
        for tecken in (1, -1):
            minst = None
            for f in (0.1, 0.5, 0.9):
                p = p1 + (p2 - p1) * f
                seg = Part.makeLine(p, p + n * tecken * L)
                kant = _traffar(seg, kontur)
                andra = []
                for j, b2 in enumerate(bockar):
                    if j != i:
                        for d in _traffar(seg, [b2["linje"]]):
                            andra.append((d, j))
                kandidat = []
                if kant:
                    dk = min(kant)
                    kandidat.append((dk + ossb_i - ba_i / 2, "kant", dk, None))
                for d, j in andra:
                    ossb_j, ba_j = _bockdata(bockar[j], t, k)
                    kandidat.append((d + ossb_i - ba_i / 2 + ossb_j - ba_j / 2, "bock", d, j))
                if not kandidat:
                    continue
                narmast = min(kandidat, key=lambda c: c[2])
                if minst is None or narmast[0] < minst[0]:
                    minst = narmast
            if minst is not None:
                ut.append(dict(bock=i, sida=tecken, yttre=minst[0], mot=minst[1], till=minst[3], flat=minst[2]))
    return ut


def _ordnade_hornen(wire):
    """Konturens hörnpunkter med inre vinkel (grader) – > 180 = inåtgående hörn."""
    kanter = Part.__sortEdges__(wire.Edges)
    pts = [e.Vertexes[0].Point for e in kanter]
    # orientering (positiv yta = moturs)
    yta = 0.0
    for e in kanter:
        for a, b in zip(e.discretize(8), e.discretize(8)[1:]):
            yta += a.x * b.y - b.x * a.y
    if yta < 0:
        kanter = [e.reversed() if hasattr(e, "reversed") else e for e in reversed(kanter)]
    ut = []
    n = len(kanter)
    for i in range(n):
        e_in, e_ut = kanter[i - 1], kanter[i]
        p = e_ut.Vertexes[0].Point
        try:
            t_in = e_in.tangentAt(e_in.LastParameter).normalize()
            t_ut = e_ut.tangentAt(e_ut.FirstParameter).normalize()
        except Exception:
            continue
        if (e_in.Vertexes[-1].Point - p).Length > 1e-3:      # tangenterna gäller kantens riktning – kontrollera
            continue
        sv = t_in.x * t_ut.y - t_in.y * t_ut.x
        vinkel = math.degrees(math.atan2(sv, t_in.dot(t_ut)))
        ut.append((p, 180.0 - vinkel))
    return ut


def granska(utb, material="S235", v_oppning=None, kantpress=KANTPRESS_LANGD, platformat=PLATFORMAT, kfaktor=0.5):
    """Returnerar (anmärkningar, sammanfattning). Anmärkning = dict(niva, regel, varde, krav, plats)."""
    t = utb["tjocklek"]
    face = utb["face2d"]
    bockar = utb["bockar2d"]
    am = []

    def lagg(niva, regel, varde, krav, plats=""):
        am.append(dict(niva=niva, regel=regel, varde=varde, krav=krav, plats=plats))

    # tjocklek
    if not any(abs(t - s) < 0.02 for s in STANDARDTJOCKLEKAR):
        lagg(VARNING, "Plåttjocklek finns i standardsortiment", "%s mm" % fmt(t, 2), ", ".join(fmt(s, 2) for s in STANDARDTJOCKLEKAR if 1 <= s <= 12) + " mm")
    else:
        lagg(OK, "Plåttjocklek finns i standardsortiment", "%s mm" % fmt(t, 2), "standard")
    # plåtformat
    fb = face.BoundBox
    Lf, Wf = max(fb.XLength, fb.YLength), min(fb.XLength, fb.YLength)
    passar = [f for f in platformat if Lf <= f[0] - 10 and Wf <= f[1] - 10]
    if passar:
        lagg(OK, "Utbredningen ryms på plåtformat (10 mm kant)", "%s x %s mm" % (fmt(Lf), fmt(Wf)), "%d x %d" % passar[0])
    else:
        lagg(FEL, "Utbredningen ryms på plåtformat (10 mm kant)", "%s x %s mm" % (fmt(Lf), fmt(Wf)),
             "största " + " / ".join("%d x %d" % f for f in platformat[-1:]) + " – dela detaljen eller skarva")
    # laser: hål och liv
    inre = [w for w in face.Wires if not w.isSame(face.OuterWire)]
    for i, w in enumerate(inre, start=1):
        cirkel = len(w.Edges) == 1 and w.Edges[0].Curve.TypeId == "Part::GeomCircle"
        storlek = 2 * w.Edges[0].Curve.Radius if cirkel else min(w.BoundBox.XLength, w.BoundBox.YLength)
        namn = ("hål ⌀%s" % fmt(storlek)) if cirkel else ("urtag %s x %s" % (fmt(w.BoundBox.XLength), fmt(w.BoundBox.YLength)))
        if storlek < t - 1e-6:
            lagg(FEL, "Håldiameter/urtagsbredd >= plåttjockleken (laser)", namn, ">= %s mm" % fmt(t), "hål %d" % i)
        liv = w.distToShape(face.OuterWire)[0]
        if liv < t - 1e-6:
            lagg(VARNING, "Liv mellan hål och ytterkant >= t (gärna 2 t)", "%s mm" % fmt(liv), ">= %s mm" % fmt(t), namn)
        for j, w2 in enumerate(inre[i:], start=i + 1):
            d = w.distToShape(w2)[0]
            if d < t - 1e-6:
                lagg(VARNING, "Liv mellan hål >= t", "%s mm" % fmt(d), ">= %s mm" % fmt(t), "hål %d och %d" % (i, j))
        for k, b in enumerate(bockar, start=1):
            d = w.distToShape(b["linje"])[0]
            krav = HAL_BOCK_FAKTOR * t + b["radie"]
            if d < krav - 1e-6:
                lagg(FEL, "Hål/urtag till bockens mittlinje >= 2,5 t + R (annars deformeras hålet)", "%s mm" % fmt(d), ">= %s mm" % fmt(krav),
                     "%s vid bock %d (%s)" % (namn, k, bockar[k - 1]["riktning"]))
    if inre:
        lagg(INFO, "Hål och urtag kontrollerade", "%d st" % len(inre), "")
    if not bockar:
        sam = "%d fel, %d varningar" % (sum(a["niva"] == FEL for a in am), sum(a["niva"] == VARNING for a in am))
        return am, sam

    # bockning
    rf, mnamn = material_regel(material)
    V_ = float(v_oppning) if v_oppning else valj_v(t)
    bmin = MIN_FLANS_FAKTOR * V_
    lagg(INFO, "Antagen V-öppning (V >= %g t, ändra med --v-oppning)" % V_FAKTOR, "V%s" % fmt(V_), "minsta yttre fläns %s mm" % fmt(bmin))
    radier = sorted({round(b["radie"], 2) for b in bockar})
    for r in radier:
        krav = rf * t
        if r < krav - 1e-6:
            lagg(VARNING, "Inre bockradie >= %s t för %s (risk för sprickor)" % (fmt(rf), mnamn), "R%s" % fmt(r), ">= R%s" % fmt(krav))
        else:
            lagg(OK, "Inre bockradie >= %s t för %s" % (fmt(rf), mnamn), "R%s" % fmt(r), ">= R%s" % fmt(krav))
        lo, hi = V_ * NATURLIG_RADIE[0], V_ * NATURLIG_RADIE[1]
        if not (lo - 0.5 <= r <= hi + 0.5):
            lagg(INFO, "Luftbockning i V%s ger inre radie ca %s–%s mm" % (fmt(V_), fmt(lo), fmt(hi)), "R%s i modellen" % fmt(r),
                 "stäm av radie och K-faktor med verkstaden – utbredningen kan avvika")
    for k, b in enumerate(bockar, start=1):
        if b["linje"].Length > kantpress + 1e-6:
            lagg(FEL, "Bocklängd <= kantpressens längd", "%s mm" % fmt(b["linje"].Length), "<= %s mm" % fmt(kantpress), "bock %d" % k)
    lagg(OK if all(b["linje"].Length <= kantpress for b in bockar) else FEL, "Bocklängd <= kantpressens längd",
         "längsta %s mm" % fmt(max(b["linje"].Length for b in bockar)), "<= %s mm" % fmt(kantpress))
    korta = 0
    for f in _flanser(utb, t, kfaktor):
        b = bockar[f["bock"]]
        plats = "bock %d (%s %s°), %s" % (f["bock"] + 1, b["riktning"], fmt(b["vinkel"]),
                                          "mot fri kant" if f["mot"] == "kant" else "mot bock %d" % (f["till"] + 1))
        if f["yttre"] < bmin - 1e-6:
            korta += 1
            lagg(FEL, "Yttre flänslängd >= 0,7 x V (flänsen måste ligga an över V-öppningen)", "%s mm" % fmt(f["yttre"]),
                 ">= %s mm i V%s" % (fmt(bmin), fmt(V_)), plats)
    if not korta:
        alla = _flanser(utb, t, kfaktor)
        kortast = min(alla, key=lambda f: f["yttre"]) if alla else None
        if kortast:
            lagg(OK, "Yttre flänslängd >= 0,7 x V", "kortast %s mm" % fmt(kortast["yttre"]), ">= %s mm i V%s" % (fmt(bmin), fmt(V_)))
    # bockavlastning: inåtgående hörn i konturen nära en bocklinjes ände
    hörn = [(p, v) for p, v in _ordnade_hornen(face.OuterWire) if v > 181.0]
    saknas = 0
    for k, b in enumerate(bockar, start=1):
        for ande in (b["linje"].Vertexes[0].Point, b["linje"].Vertexes[-1].Point):
            for p, v in hörn:
                if (p - ande).Length < b["radie"] + t + 1e-6:
                    saknas += 1
                    lagg(VARNING, "Bockavlastning där bocken slutar i ett inåtgående hörn (annars rivs plåten)", "hörn %s° vid bockände" % fmt(v),
                         "avlastning ca %s x %s mm (bredd >= t, djup >= R + t)" % (fmt(t), fmt(b["radie"] + t + 1)), "bock %d" % k)
    if not saknas:
        lagg(OK, "Bockavlastning", "inga bockar slutar i inåtgående hörn", "")
    lagg(INFO, "Bockföljd och verktygskollision kontrolleras inte automatiskt", "%d bockar" % len(bockar),
         "gå igenom bockföljden med verkstaden för U- och Z-former")
    sam = "%d fel, %d varningar" % (sum(a["niva"] == FEL for a in am), sum(a["niva"] == VARNING for a in am))
    return am, sam


def rapport(am, sam, rubrik="Tillverkningsgranskning"):
    rad = ["%s: %s" % (rubrik, sam)]
    ordning = {FEL: 0, VARNING: 1, INFO: 2, OK: 3}
    for a in sorted(am, key=lambda a: ordning[a["niva"]]):
        rad.append("  %-7s %s: %s (krav %s)%s" % (a["niva"], a["regel"], a["varde"], a["krav"] or "-", ("  [%s]" % a["plats"]) if a["plats"] else ""))
    return "\n".join(rad)
