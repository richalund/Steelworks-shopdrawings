"""Stålkonstruktioner (sammanställningar) i FreeCAD: profilbibliotek och byggare för balkar, plåtar och hål.

Används inne i FreeCAD av `sammanstallning.py bygg` via ett konstruktionsskript (se ../konstruktioner/):
  NAMN = "Balkongram"
  MARKE = "B/1"                                  # sammanställningsmärke = ritningsnummer
  VARIABLER = [("Langd", 2200, "mm, ramens längd (X)"), ...]       # blir kalkylbladet Variabler
  RITNING = dict(snitt=[...], noter=[...], ...)   # standardval för ritningen (kan ändras på kommandoraden)
  def bygg(k, v):                                # k = Konstruktion, v = variablerna (dict med tal)
      fram = k.balk("b/1", "UPE140", (0, 32.5, 70), ("Langd", 32.5, 70), oppning=(0, 1, 0), huvuddel=True)
      pl = k.plat("pl/3", "PL110*10", mitt=(550, 10, 70), langd=90, lriktning=(0, 0, 1), briktning=(1, 0, 0))
      k.hal([fram, pl], [(522.5, 10, 50), ...], riktning=(0, 1, 0), bult="M12x44")

Regeln i SKILL.md gäller: allt ritas med FreeCADs egna verktyg. Varje del blir en PartDesign::Body i gruppen
"Sammanstallning": skissen Tvarsnitt (fullt bestämd, namngivna mått b, h, tf, t ...), Pad "Langd", rotradierna
som Fillet "Rotradie" och hålen som Pocket från en skiss med cirklar (fickans egenskaper Bult och Halgrupp).
Kroppen har egenskaperna Pos (positionsnummer, t.ex. "b/1"), Profil (svensk profilbeteckning: "UPE140", "PL10*110",
"VKR100*6.3") och Material. Koordinater och längder får vara uttryck mot Variabler ("Langd", "Djup - 65"):
kroppens Placement och Pad-längden binds då till bladet och följer med när användaren ändrar en variabel.
Hålens lägen och antalet delar är tal - ändras de: bygg om (`sammanstallning.py bygg ... --var Bjalkar=4`).

Profilerna har verkliga radier (UPE/IPE/HEA/HEB roten, VKR inre och yttre radie enligt EN 10210,
KKR/RHS/SHS enligt EN 10219), så att vikt
och yta stämmer med tabellerna (UPE140 14,5 kg/m). L-profiler ritas utan radier.
"""
import re, json, math

# h, b, tw, tf, r  (mm)
UPE = {80: (80, 50, 4, 7, 10), 100: (100, 55, 4.5, 7.5, 10), 120: (120, 60, 5, 8, 12), 140: (140, 65, 5, 9, 12),
       160: (160, 70, 5.5, 9.5, 12), 180: (180, 75, 5.5, 10.5, 12), 200: (200, 80, 6, 11, 13), 220: (220, 85, 6.5, 12, 13),
       240: (240, 90, 7, 12.5, 15), 270: (270, 95, 7.5, 13.5, 15), 300: (300, 100, 9.5, 15, 15), 330: (330, 105, 11, 16, 18),
       360: (360, 110, 12, 17, 18), 400: (400, 115, 13.5, 18, 18)}
IPE = {80: (80, 46, 3.8, 5.2, 5), 100: (100, 55, 4.1, 5.7, 7), 120: (120, 64, 4.4, 6.3, 7), 140: (140, 73, 4.7, 6.9, 7),
       160: (160, 82, 5, 7.4, 9), 180: (180, 91, 5.3, 8, 9), 200: (200, 100, 5.6, 8.5, 12), 220: (220, 110, 5.9, 9.2, 12),
       240: (240, 120, 6.2, 9.8, 15), 270: (270, 135, 6.6, 10.2, 15), 300: (300, 150, 7.1, 10.7, 15), 330: (330, 160, 7.5, 11.5, 18),
       360: (360, 170, 8, 12.7, 18), 400: (400, 180, 8.6, 13.5, 21)}
HEA = {100: (96, 100, 5, 8, 12), 120: (114, 120, 5, 8, 12), 140: (133, 140, 5.5, 8.5, 12), 160: (152, 160, 6, 9, 15),
       180: (171, 180, 6, 9.5, 15), 200: (190, 200, 6.5, 10, 18), 220: (210, 220, 7, 11, 18), 240: (230, 240, 7.5, 12, 21),
       260: (250, 260, 7.5, 12.5, 24), 280: (270, 280, 8, 13, 24), 300: (290, 300, 8.5, 14, 27)}
HEB = {100: (100, 100, 6, 10, 12), 120: (120, 120, 6.5, 11, 12), 140: (140, 140, 7, 12, 12), 160: (160, 160, 8, 13, 15),
       180: (180, 180, 8.5, 14, 15), 200: (200, 200, 9, 15, 18), 220: (220, 220, 9.5, 16, 18), 240: (240, 240, 10, 17, 21),
       260: (260, 260, 10, 17.5, 24), 280: (280, 280, 10.5, 18, 24), 300: (300, 300, 11, 19, 27)}

# mässing: ca 8,4 g/cm3 för CuZn37 (CW508L) och CuZn39Pb3 (CW614N) enligt EN 12165/12167-tabellerna
# (color-metal.ro/en/extruded-copper-bars-and-profiles-subsequent-forging-or-stamping-en-12165, hämtad 2026-10-18)
DENSITET = {"stal": 7850.0, "rostfritt": 8000.0, "aluminium": 2700.0, "glas": 2500.0, "tra": 500.0, "massing": 8400.0}
NUM = r"(\d+(?:\.\d+)?)"


def densitet(material):
    m = (material or "").upper()
    if m.startswith("GLAS"):
        return DENSITET["glas"]
    if m.startswith(("TRÄ", "TRA", "EK", "FURU", "BJÖRK", "BJORK", "C24")):
        return DENSITET["tra"]
    if m.startswith(("6060", "6063", "6082", "AL", "EN AW")):
        return DENSITET["aluminium"]
    if m.startswith(("MÄSSING", "MASSING", "BRASS", "CUZN", "CW5", "CW6", "CW7")):
        return DENSITET["massing"]
    if m.startswith(("1.4", "EN 1.4", "ROSTFRITT", "SS", "A2", "A4")):
        return DENSITET["rostfritt"]
    return DENSITET["stal"]


def tolka(profil, kallor=True):
    """Profilnamn (svensk beteckning) -> dict med typ, mått och 'kalla' (var måtten kommer ifrån). Måtten hämtas i
    första hand ur källorna i kallor.py (standardtabeller på nätet med cache, FreeCAD:s profiltabell), annars ur
    de inbyggda tabellerna här. Plåt (PL), rundstång (D) och mått i namnet har ingen källa (kalla=None).
    Okänt namn ger ValueError med exempel."""
    p = profil.strip().upper().replace(",", ".").replace("X", "*").replace(" ", "")
    info = None
    if kallor:
        try:
            import kallor as K
            info = K.profil(p)
        except Exception as e:                       # nätfel m.m. får inte stoppa bygget
            info = None
            _kallor_fel.append("%s: %s" % (p, e))
    if info is not None:
        if info["typ"].endswith("_LUTANDE"):
            raise ValueError("%s har lutande flänsar (UPN/IPN) som tvärsnittsbyggaren inte stöder; använd UPE/IPE" % profil)
        if info["typ"] in ("U", "I") and info.get("r") is None:
            try:
                info["r"] = _inbyggd(p)["r"]
                info["kalla"]["standard"] += ", rotradie ur inbyggd tabell"
            except ValueError:
                info["r"] = info["tw"]
                info["kalla"]["standard"] += ", rotradie antagen = tw"
        if info["typ"] == "R" and info.get("ro") is None:
            t = info["t"]
            info["ro"] = 2.0 * t if t <= 6 else (2.5 * t if t <= 10 else 3.0 * t)
            info["ri"] = max(info["ro"] - t, 0.0)
            info["kalla"]["standard"] += ", radier enligt EN 10219-regel"
        info["profil"] = p
        return info
    info = _inbyggd(p)
    info["profil"] = p
    info["kalla"] = None if info["typ"] in ("PL", "D") else dict(INBYGGD_KALLA, profil=p)
    return info


_kallor_fel = []
INBYGGD_KALLA = dict(namn="inbyggd tabell", kort="stal.py (inbyggd tabell)", standard="EN 10365 / EN 10219 (tabellvärden)",
                     lage="inbyggd", hamtad="")


def _inbyggd(p):
    """Inbyggda tabellerna och måtten i namnet (normaliserat namn p)."""
    for namn, tab in (("UPE", UPE), ("IPE", IPE), ("HEA", HEA), ("HEB", HEB)):
        m = re.fullmatch(namn + r"(\d+)", p)
        if m:
            if int(m.group(1)) not in tab:
                raise ValueError("%s finns inte i tabellen (%s)" % (p, ", ".join("%s%d" % (namn, k) for k in tab)))
            h, b, tw, tf, r = tab[int(m.group(1))]
            return dict(typ="U" if namn == "UPE" else "I", h=h, b=b, tw=tw, tf=tf, r=r)
    m = re.fullmatch(r"(VKR|KKR|RHS|SHS|KVR)" + NUM + r"\*" + NUM + r"(?:\*" + NUM + r")?", p)
    if m:
        a1, a2, a3 = float(m.group(2)), float(m.group(3)), m.group(4)
        h, b, t = (a1, a2, float(a3)) if a3 else (a1, a1, a2)
        if m.group(1) == "VKR":                                   # VKR = varmformad EN 10210: yttre radie 1,5 t
            ro = 1.5 * t
        else:                                                     # KKR, RHS, SHS = kallformad EN 10219
            ro = 2.0 * t if t <= 6 else (2.5 * t if t <= 10 else 3.0 * t)
        return dict(typ="R", h=h, b=b, t=t, ro=ro, ri=max(ro - t, 0.0))
    m = re.fullmatch(r"(PL|FL|FLA|PLT)" + NUM + r"\*" + NUM, p)
    if m:
        a1, a2 = float(m.group(2)), float(m.group(3))
        return dict(typ="PL", t=min(a1, a2), b=max(a1, a2))
    m = re.fullmatch(r"(FS|FKT)" + NUM, p)                          # fyrkantstång a x a (ritas som plåt a*a)
    if m:
        return dict(typ="PL", t=float(m.group(2)), b=float(m.group(2)))
    m = re.fullmatch(r"(D|RUND|RD)" + NUM, p)
    if m:
        return dict(typ="D", d=float(m.group(2)))
    m = re.fullmatch(r"(RÖR|ROR|CHS|VKCKR|KCKR)" + NUM + r"\*" + NUM, p)
    if m:
        return dict(typ="O", d=float(m.group(2)), t=float(m.group(3)))
    m = re.fullmatch(r"L" + NUM + r"\*" + NUM + r"(?:\*" + NUM + r")?", p)
    if m:
        a1, a2, a3 = float(m.group(1)), float(m.group(2)), m.group(3)
        h, b, t = (a1, a2, float(a3)) if a3 else (a1, a1, a2)
        return dict(typ="L", h=h, b=b, t=t)
    raise ValueError("Okänd profil '%s'. Exempel: UPE140, IPE100, HEA160, VKR100*6.3, VKR120*80*5, PL10*150, FS20, D20, RÖR48.3*4, L50*5" % p)


def bultdiameter(bult):
    """M12x44 -> håldiameter 14 (M+2 från M12, M+1 under), som på svenska tillverkningsritningar."""
    m = re.match(r"M(\d+)", (bult or "").upper())
    if not m:
        return None
    d = int(m.group(1))
    return d + 2 if d >= 12 else d + 1


def haltext(antal, d, bult=None):
    """4*Ø14 - M12x44 (som på ritningarna)."""
    s = "%s*Ø%s" % (antal, ("%.1f" % d).rstrip("0").rstrip("."))
    return s + (" - %s" % bult if bult else "")


# =====================================================================================================
# Inne i FreeCAD (Part Design via pd.py)
# =====================================================================================================
def _polygon(sk, pts, matt, utan):
    """Axelparallell sluten polygon i skissen: vågrät/lodrät, längdmått på alla sidor utom `utan` (en vågrät
    och en lodrät, som bestäms av de andra) och första hörnet låst i sitt läge -> fullt bestämd."""
    import pd
    g = sk.profil(pts, start=None)
    for i in range(len(pts)):
        if i not in utan:
            sk.matt("Distance", g[i], varde=round(math.dist(pts[i], pts[(i + 1) % len(pts)]), 4), namn=matt.get(i, ""))
    sk.placera(g[0], pd.START, round(pts[0][0], 4), round(pts[0][1], 4), namn="")
    return g


def _ui_skiss(sk, typ, h, b, tw, tf, r):
    """U- eller I-profil med rotradierna som tangerande bågar i skissen (som delar/hprofil.py), lådans mitt i
    origo, fullt bestämd med de namngivna måtten b, h, tw, tf och r. U: livet till vänster, flänsarna mot +x."""
    import Part
    import pd
    from FreeCAD import Vector as V
    S, E = pd.START, pd.SLUT
    H, B = h / 2, b / 2
    pi = math.pi

    def linje(a, c):
        return sk.geo(Part.LineSegment(V(a[0], a[1], 0), V(c[0], c[1], 0)))

    def bage(mx, my, v0, v1):
        return sk.geo(Part.ArcOfCircle(Part.Circle(V(mx, my, 0), V(0, 0, 1), r), v0, v1))

    if typ == "U":
        x1 = -B + tw                                   # livets insida
        x2 = x1 + r
        L0 = linje((-B, -H), (B, -H))
        L1 = linje((B, -H), (B, -H + tf))
        L2 = linje((B, -H + tf), (x2, -H + tf))
        A0 = bage(x2, -H + tf + r, pi, 1.5 * pi)       # start på livet, slut på flänsen
        L3 = linje((x1, -H + tf + r), (x1, H - tf - r))
        A1 = bage(x2, H - tf - r, 0.5 * pi, pi)        # start på flänsen, slut på livet
        L4 = linje((x2, H - tf), (B, H - tf))
        L5 = linje((B, H - tf), (B, H))
        L6 = linje((B, H), (-B, H))
        L7 = linje((-B, H), (-B, -H))
        for g1, g2 in ((L0, L1), (L1, L2), (L4, L5), (L5, L6), (L6, L7), (L7, L0)):
            sk.begr("Coincident", g1, E, g2, S)
        for g1, p1, g2, p2 in ((L2, E, A0, E), (A0, S, L3, S), (L3, E, A1, E), (A1, S, L4, S)):
            sk.begr("Tangent", g1, p1, g2, p2)
        for g in (L0, L2, L4, L6):
            sk.begr("Horizontal", g)
        for g in (L1, L3, L5, L7):
            sk.begr("Vertical", g)
        sk.begr("Equal", A0, A1)
        sk.begr("Equal", L1, L5)
        sk.begr("PointOnObject", L5, S, L1)
        sk.matt("DistanceX", L0, S, L0, E, varde=b, namn="b")
        sk.matt("DistanceY", L0, S, L7, S, varde=h, namn="h")
        sk.matt("DistanceY", L1, S, L1, E, varde=tf, namn="tf")
        sk.matt("DistanceX", L0, S, L3, S, varde=tw, namn="tw")
        sk.matt("Radius", A0, varde=r, namn="r")
        sk.placera(L0, S, -B, -H, namn="")
        return
    x1, x2 = tw / 2, tw / 2 + r                       # I: som delar/hprofil.py men med lådans mitt i origo
    y = lambda v: v - H
    L0 = linje((-B, y(0)), (B, y(0)))
    L1 = linje((B, y(0)), (B, y(tf)))
    L2 = linje((B, y(tf)), (x2, y(tf)))
    A0 = bage(x2, y(tf + r), pi, 1.5 * pi)
    L3 = linje((x1, y(tf + r)), (x1, y(h - tf - r)))
    A1 = bage(x2, y(h - tf - r), 0.5 * pi, pi)
    L4 = linje((x2, y(h - tf)), (B, y(h - tf)))
    L5 = linje((B, y(h - tf)), (B, y(h)))
    L6 = linje((B, y(h)), (-B, y(h)))
    L7 = linje((-B, y(h)), (-B, y(h - tf)))
    L8 = linje((-B, y(h - tf)), (-x2, y(h - tf)))
    A2 = bage(-x2, y(h - tf - r), 0, 0.5 * pi)
    L9 = linje((-x1, y(h - tf - r)), (-x1, y(tf + r)))
    A3 = bage(-x2, y(tf + r), 1.5 * pi, 2 * pi)
    L10 = linje((-x2, y(tf)), (-B, y(tf)))
    L11 = linje((-B, y(tf)), (-B, y(0)))
    for g1, g2 in ((L0, L1), (L1, L2), (L4, L5), (L5, L6), (L6, L7), (L7, L8), (L10, L11), (L11, L0)):
        sk.begr("Coincident", g1, E, g2, S)
    for g1, p1, g2, p2 in ((L2, E, A0, E), (A0, S, L3, S), (L3, E, A1, E), (A1, S, L4, S),
                           (L8, E, A2, E), (A2, S, L9, S), (L9, E, A3, E), (A3, S, L10, S)):
        sk.begr("Tangent", g1, p1, g2, p2)
    for g in (L0, L2, L4, L6, L8, L10):
        sk.begr("Horizontal", g)
    for g in (L1, L3, L5, L7, L9, L11):
        sk.begr("Vertical", g)
    for a in (A1, A2, A3):
        sk.begr("Equal", A0, a)
    for g in (L11, L5, L7):
        sk.begr("Equal", L1, g)
    sk.begr("Equal", L0, L6)
    sk.begr("PointOnObject", L5, S, L1)
    sk.begr("Equal", L2, L10)
    sk.matt("DistanceX", L0, S, L0, E, varde=b, namn="b")
    sk.matt("DistanceY", L0, S, L7, S, varde=h, namn="h")
    sk.matt("DistanceY", L1, S, L1, E, varde=tf, namn="tf")
    sk.matt("DistanceX", L9, E, L3, S, varde=tw, namn="tw")
    sk.matt("Radius", A0, varde=r, namn="r")
    sk.placera(L0, S, -B, -H, namn="")


def _tvarsnitt(d, info, langd, bredd=None):
    """Kroppens skiss Tvarsnitt på XY-planet (x = profilens bredd b, flänsarna mot +x för UPE; y = höjd h;
    lådans mitt i origo; rotradierna som bågar i skissen) och Pad "Langd" längs +Z. Returnerar Pad.
    `bredd` (uttryck) ersätter plåtens bredd, t.ex. "Djup" för en däckplåt."""
    t = info["typ"]
    sk = d.skiss("Tvarsnitt", "XY")
    if t in ("U", "I"):
        _ui_skiss(sk, t, info["h"], info["b"], info["tw"], info["tf"], info["r"])
    elif t == "R":
        b, h, tt = info["b"], info["h"], info["t"]
        if info["ro"] > 0:
            sk.rundad_rektangel(b, h, info["ro"], namn=("b", "h", "ro"))
        else:
            sk.rektangel(b, h, namn=("b", "h"))
        if info["ri"] > 0:
            sk.rundad_rektangel(b - 2 * tt, h - 2 * tt, info["ri"], namn=("bi", "hi", "ri"))
        else:
            sk.rektangel(b - 2 * tt, h - 2 * tt, namn=("bi", "hi"))
    elif t == "PL":
        sk.rektangel(bredd if bredd is not None else info["b"], info["t"], namn=("b", "t"))
    elif t == "D":
        sk.cirkel(info["d"], namn="d")
    elif t == "O":
        sk.cirkel(info["d"], namn="d")
        sk.cirkel(info["d"] - 2 * info["t"], namn="di")
    elif t == "L":
        h, b, tt = info["h"], info["b"], info["t"]
        pts = [(-b / 2, -h / 2), (b / 2, -h / 2), (b / 2, -h / 2 + tt), (-b / 2 + tt, -h / 2 + tt), (-b / 2 + tt, h / 2), (-b / 2, h / 2)]
        _polygon(sk, pts, {0: "b", 1: "t", 5: "h"}, (3, 4))
    return d.kloss(sk, langd, "Langd")


class Konstruktion:
    """Bygger en sammanställning av Part Design-kroppar med positionsnummer i gruppen Sammanstallning."""

    def __init__(self, doc, marke, namn="", material="S355J2", logg=print, variabler=()):
        self.doc, self.marke, self.material, self.logg = doc, marke, material, logg
        sh = doc.addObject("Spreadsheet::Sheet", "Variabler")
        sh.set("A1", "Variabel"); sh.set("B1", "Värde"); sh.set("C1", "Beskrivning")
        for i, (v, varde, beskr) in enumerate(variabler, start=2):
            sh.set("A%d" % i, v)
            sh.set("B%d" % i, str(varde))
            sh.setAlias("B%d" % i, v)
            sh.set("C%d" % i, beskr)
        sh.setStyle("A1:C1", "bold")
        doc.recompute()
        g = doc.addObject("App::DocumentObjectGroup", "Sammanstallning")
        g.Label = "Sammanställning %s" % marke
        for p, beskr in (("Marke", "sammanställningsmärke"), ("Namn", "benämning"), ("Huvuddel", "objektnamn för huvuddelen"),
                         ("Ritning", "ritningens standardval (JSON)"), ("Kallor", "källor för profilmåtten (JSON-lista)")):
            g.addProperty("App::PropertyString", p, "Stal", beskr)
        g.Marke, g.Namn, g.Ritning, g.Kallor = marke, namn, "{}", "[]"
        self.grupp, self.antal_halgrupper, self.baser, self.kallor = g, 0, {}, []

    def _notera_kalla(self, info):
        """Sparar var profilens mått kommer ifrån i gruppens Kallor (för ritningens noter) och loggar en gång per profil."""
        k = info.get("kalla")
        if not k:
            return
        post = dict(profil=info.get("profil", ""), namn=k.get("namn", ""), kort=k.get("kort", ""), standard=k.get("standard", ""),
                    hamtad=k.get("hamtad", ""), lage=k.get("lage", ""), url=k.get("url", ""))
        if post in self.kallor:
            return
        self.kallor.append(post)
        self.grupp.Kallor = json.dumps(self.kallor, ensure_ascii=False)
        matt = ", ".join("%s=%g" % (x, info[x]) for x in ("h", "b", "tw", "tf", "r", "t", "ro", "ri", "d") if info.get(x) is not None)
        self.logg("Profil %s: %s; %s [%s] %s%s" % (post["profil"], matt, post["kort"], post["standard"], post["lage"],
                                                   " " + post["hamtad"] if post["hamtad"] else ""))

    def _del(self, pos):
        import pd
        namn = re.sub(r"[^A-Za-z0-9]", "", pos) or "Del"
        body = self.doc.addObject("PartDesign::Body", namn)
        return pd.Del(self.doc, body.Name)

    def _placera(self, d, rot, bas):
        """Kroppens Placement: rotation (u, v, w) och bas; baskomponenter som är uttryck binds till Variabler."""
        import FreeCAD as App
        from FreeCAD import Vector as V
        u, v, w = rot
        m = App.Matrix(u.x, v.x, w.x, 0, u.y, v.y, w.y, 0, u.z, v.z, w.z, 0, 0, 0, 0, 1)
        vals = [d.uttryck(x) for x in bas]
        self.baser[d.body.Name] = tuple(bas)
        d.body.Placement = App.Placement(V(*[val for _, val in vals]), App.Rotation(m))
        for k, (ex, _) in zip("xyz", vals):
            if ex:
                d.body.setExpression(".Placement.Base." + k, ex)

    def _ny(self, d, pos, profil, material, huvuddel):
        o = d.body
        o.Label = "%s %s" % (pos, profil)
        for p, beskr in (("Pos", "positionsnummer (stycklitterering)"), ("Profil", "profil (svensk beteckning)"), ("Material", "material")):
            o.addProperty("App::PropertyString", p, "Stal", beskr)
        o.Pos, o.Profil, o.Material = pos, profil, material or self.material
        self.grupp.addObject(o)
        if huvuddel:
            self.grupp.Huvuddel = o.Name
        d.stada()
        try:
            o.ViewObject.ShapeColor = (0.62, 0.64, 0.67)
        except Exception:
            pass
        return o

    def balk(self, pos, profil, start, slut, upp=(0, 0, 1), oppning=None, material=None, huvuddel=False):
        """Balk/profil längs linjen start->slut genom tvärsnittets mitt (koordinater: tal eller uttryck mot
        Variabler). `upp` = tvärsnittets höjdriktning (livet för I/U), `oppning` = riktningen som U-profilens
        flänsar (L-profilens ena ben) pekar åt."""
        from FreeCAD import Vector as V
        info = tolka(profil)
        self._notera_kalla(info)
        d = self._del(pos)
        a = V(*[d.uttryck(x)[1] for x in start])
        b = V(*[d.uttryck(x)[1] for x in slut])
        w = b - a
        L = w.Length
        w.normalize()
        if oppning is not None:
            u = V(*oppning)
            u = (u - w * u.dot(w)).normalize()
            v = w.cross(u)
        else:
            v = V(*upp)
            v = v - w * v.dot(w)
            if v.Length < 1e-9:                 # upp parallell med balken (stående pelare): välj Y
                v = V(0, 1, 0) - w * w.y
            v.normalize()
            u = v.cross(w)
        langd = round(L, 4)
        axel = [k for k in range(3) if abs(abs(w[k]) - 1) < 1e-9]
        if axel and (isinstance(start[axel[0]], str) or isinstance(slut[axel[0]], str)):
            k = axel[0]
            langd = "(%s) - (%s)" % ((slut[k], start[k]) if w[k] > 0 else (start[k], slut[k]))
        _tvarsnitt(d, info, langd)
        self._placera(d, (u, v, w), start)
        return self._ny(d, pos, profil, material, huvuddel)

    def plat(self, pos, profil, mitt, langd, lriktning=(1, 0, 0), briktning=(0, 1, 0), material=None, huvuddel=False, bredd=None):
        """Rektangulär plåt PLt*b (tjockleken = det minsta talet) med längden `langd` längs `lriktning` och bredden
        längs `briktning`, centrerad i `mitt` (tal eller uttryck). Tjockleken ligger längs lriktning x briktning.
        `bredd` = uttryck för bredden (t.ex. "Djup"); profilnamnet i materiallistan räknas då om från skissen."""
        from FreeCAD import Vector as V
        info = tolka(profil)
        if info["typ"] != "PL":
            raise ValueError("plat() vill ha en plåt (PLt*b), fick %s" % profil)
        d = self._del(pos)
        lr, br = V(*lriktning).normalize(), V(*briktning).normalize()
        tr = lr.cross(br).normalize()
        br = tr.cross(lr)
        bas = []
        for k in range(3):
            if abs(lr[k]) < 1e-9:
                bas.append(mitt[k])
            elif abs(abs(lr[k]) - 1) < 1e-9 and (isinstance(mitt[k], str) or isinstance(langd, str)):
                bas.append("(%s) %s (%s) / 2" % (mitt[k], "-" if lr[k] > 0 else "+", langd))
            else:
                bas.append(round(d.uttryck(mitt[k])[1] - lr[k] * d.uttryck(langd)[1] / 2, 4))
        _tvarsnitt(d, info, langd, bredd)
        self._placera(d, (br, tr, lr), bas)
        return self._ny(d, pos, profil, material, huvuddel)

    # -------------------------------------------------------------- hål
    def skiva(self, pos, profil, langd, bredd, t, mitt=(0, 0, 0), material=None, form="ellips", huvuddel=False):
        """Plan skiva (bordsskiva, lock, glas): ellips eller rektangel langd x bredd (tal eller uttryck mot
        Variabler, x- resp. y-riktning) med tjockleken t uppåt från `mitt` (skivans undersida). `profil` är
        texten i materiallistan (t.ex. "GLAS 8"), `material` t.ex. "Glas 8 mm härdat" (vikt med 2500 kg/m3)."""
        d = self._del(pos)
        sk = d.skiss("Tvarsnitt", "XY")
        if form == "ellips":
            sk.ellips(langd, bredd, namn=("Langd", "Bredd"))
        else:
            sk.rektangel(langd, bredd, namn=("Langd", "Bredd"))
        d.kloss(sk, t, "Tjocklek")
        from FreeCAD import Vector as V
        self._placera(d, (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), tuple(mitt))
        return self._ny(d, pos, profil, material, huvuddel)

    def glas(self, pos, horn1, horn2, normal=(0, 1, 0), t=8, glipa=5, djup=0, material="Glas härdat", profil=None,
             list_profil=None, list_pos=("li/1", "li/2"), list_material=None):
        """Glas i en öppning: hörnen `horn1`, `horn2` (globala, diagonalt motsatta) i öppningens plan med normalen
        `normal`; rutan blir öppningen minus `glipa` runt om, `t` tjock, centrerad i planet förskjutet `djup` längs
        normalen. Profiltext "GLAS t", vikt med 2500 kg/m3. `list_profil` (t.ex. "FL15*8") ger fyra glaslister på
        rutans +normal-sida mot öppningens kant: de längs x hela bredden (pos list_pos[0]), de andra emellan
        (list_pos[1]).
        Returnerar rutan (och listerna som rutan.Lister)."""
        from FreeCAD import Vector as V
        n = V(*normal).normalize()
        a_, b_ = V(*horn1), V(*horn2)
        d = b_ - a_
        axlar = [V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)]
        u = next(x for x in axlar if abs(x.dot(n)) < 1e-6 and abs(d.dot(x)) > 1e-6)
        w_ = n.cross(u)
        L, B = abs(d.dot(u)), abs(d.dot(w_))
        mitt = (a_ + b_) * 0.5 + n * float(djup)

        def ruta(dd):
            sk = dd.skiss("Glas", "XY")
            sk.rektangel(round(L - 2 * glipa, 3), round(B - 2 * glipa, 3), namn=("Langd", "Bredd"))
            dd.kloss(sk, t, "Tjocklek", symmetrisk=True)
        o = self.egen(pos, profil or "GLAS %s" % _txt(t), ruta, mitt=tuple(mitt), rot=(tuple(u), tuple(w_), tuple(n)), material=material)
        try:
            o.ViewObject.ShapeColor, o.ViewObject.Transparency = (0.70, 0.85, 0.90), 60
        except Exception:
            pass
        lister = []
        if list_profil:
            info = tolka(list_profil)
            lb, lt = info["b"], info["t"]
            z = n * (float(djup) + t / 2.0 + lt / 2.0)
            c = (a_ + b_) * 0.5
            for s_, langd_, riktn in ((1, L, u), (-1, L, u), (1, B - 2 * lb, w_), (-1, B - 2 * lb, w_)):
                tvar = w_ if riktn is u else u
                halv = (B if riktn is u else L) / 2.0 - lb / 2.0
                m_ = c + z + tvar * (s_ * halv)
                lister.append(self.plat(list_pos[0 if riktn is u else 1], list_profil, mitt=tuple(m_), langd=round(langd_, 3), lriktning=tuple(riktn),
                                        briktning=tuple(tvar), material=list_material))
        o.addProperty("App::PropertyLinkList", "Lister", "Stal", "glaslister")
        o.Lister = lister
        return o

    def inkop(self, pos, text=None, lada=None, cylinder=None, komponent=None, mitt=(0, 0, 0),
              rot=((1, 0, 0), (0, 1, 0), (0, 0, 1)), vikt=None, material="INKÖP", farg=(0.25, 0.25, 0.28)):
        """Inköpt detalj (gångjärn, lås, handtag, dörrstängare, motor, bult) som utrymmesmodell: en låda
        `lada=(x, y, z)` centrerad i `mitt` eller en cylinder `cylinder=(d, l)` längs delens z från `mitt`.
        `komponent="id"` hämtar benämning, tillverkare, artikelnummer, mått, vikt och källa ur komponentregistret
        (komponenter.py, egna/komponenter.json) – vägen för riktiga uppdrag: komponenten söks upp hos en leverantör
        i landet där skillen används och läggs in med databladets mått. Utan register anges `text`, mått och `vikt`
        direkt (t.ex. i ett exempel). Syns i ritningen och 3D-bilderna, ingår i krock- och rörelsekontrollen;
        källan skrivs i ritningens noter."""
        info = {}
        if komponent:
            import komponenter
            info = komponenter.hamta(komponent)
            m = info.get("matt", {})
            lada, cylinder = m.get("lada"), m.get("cylinder")
            text = text or info.get("benamning") or komponent
            vikt = vikt if vikt is not None else info.get("vikt_kg")

        def form(dd):
            sk = dd.skiss("Kontur", "XY")
            if lada is not None:
                sk.rektangel(lada[0], lada[1], namn=("Langd", "Bredd"))
                dd.kloss(sk, lada[2], "Hojd", symmetrisk=True)
            else:
                sk.cirkel(cylinder[0], namn="d")
                dd.kloss(sk, cylinder[1], "Langd")
        if (lada is None) == (cylinder is None):
            raise ValueError("inkop(): ange komponent=, eller lada=(x, y, z) eller cylinder=(d, l)")
        o = self.egen(pos, text or "INKÖP", form, mitt=mitt, rot=rot, material=material)
        for p_, typ, beskr in (("Vikt", "App::PropertyFloat", "vikt per styck (kg) ur datablad; 0 = räknas på materialet"),
                               ("Kalla", "App::PropertyString", "datablad eller produktsida (URL) och hämtdatum"),
                               ("Inkopstext", "App::PropertyString", "benämning, tillverkare och artikelnummer")):
            o.addProperty(typ, p_, "Stal", beskr)
        o.Vikt = float(vikt or 0)
        if info:
            o.Kalla = "%s %s" % (info.get("kalla", ""), info.get("hamtad", ""))
            o.Inkopstext = ", ".join(x for x in (info.get("benamning", ""), info.get("tillverkare", ""),
                                                  ("ART.NR " + info["artikel"]) if info.get("artikel") else "") if x)
        try:
            o.ViewObject.ShapeColor = tuple(farg)
        except Exception:
            pass
        return o

    def egen(self, pos, profil, bygg, mitt=(0, 0, 0), rot=((1, 0, 0), (0, 1, 0), (0, 0, 1)), material=None, huvuddel=False):
        """Egen kropp som konstruktionsskriptet bygger självt: `bygg(d)` får en pd.Del (skisser, Pad, Pocket, Hole,
        Fillet, mönster ... enligt references/partdesign.md) och ritar delen kring kroppens origo; kroppen placeras
        sedan med `mitt` (tal eller uttryck) och `rot` = (x-, y-, z-riktning) och får positionsnummer, profiltext
        i materiallistan och material som de andra delarna. Det är vägen för allt som balk/plat/skiva inte täcker,
        utan att ändra skillen: hjälpfunktionerna ligger i det egna skriptet."""
        from FreeCAD import Vector as V
        d = self._del(pos)
        bygg(d)
        self._placera(d, tuple(V(*r) for r in rot), tuple(mitt))
        return self._ny(d, pos, profil, material, huvuddel)

    def referens(self, namn, lada=None, bygg=None, mitt=(0, 0, 0), rot=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                 farg=(0.8, 0.8, 0.78), transparens=0):
        """Referenskropp för omgivningen (trappsteg, vägg, bjälklag, mark, befintlig stomme): syns i modellen, i
        3D-bilderna (rendera.py) och på översiktsritningen (oversikt.py), men saknar positionsnummer och kommer
        därför inte med i materiallistan, bubblorna eller sammanställningsritningens vyer. `lada` = (x0, x1, y0,
        y1, z0, z1) ger en låda; annars ritar `bygg(d)` kroppen med pd-API:t som i egen(), placerad med mitt/rot.
        Kropparna samlas i gruppen Omgivning."""
        import pd
        import FreeCAD as App
        from FreeCAD import Vector as V
        body = self.doc.addObject("PartDesign::Body", re.sub(r"[^A-Za-z0-9_]", "", namn) or "Referens")
        body.Label = namn
        d = pd.Del(self.doc, body.Name)
        if lada is not None:
            x0, x1, y0, y1, z0, z1 = [float(q) for q in lada]
            sk = d.skiss("Kontur", "XY")
            sk.rektangel(round(x1 - x0, 3), round(y1 - y0, 3), namn=("Langd", "Bredd"))
            d.kloss(sk, round(z1 - z0, 3), "Hojd")
            body.Placement = App.Placement(V((x0 + x1) / 2, (y0 + y1) / 2, z0), App.Rotation())
        else:
            bygg(d)
            u, v, w = (V(*r) for r in rot)
            m = App.Matrix(u.x, v.x, w.x, 0, u.y, v.y, w.y, 0, u.z, v.z, w.z, 0, 0, 0, 0, 1)
            body.Placement = App.Placement(V(*[d.uttryck(c)[1] for c in mitt]), App.Rotation(m))
        d.stada()
        g = self.doc.getObject("Omgivning")
        if g is None:
            g = self.doc.addObject("App::DocumentObjectGroup", "Omgivning")
        g.addObject(body)
        try:
            body.ViewObject.ShapeColor = tuple(farg)
            body.ViewObject.Transparency = int(transparens)
        except Exception:
            pass
        return body

    # -------------------------------------------------------------- bockad plåt (SheetMetal)
    SIDA = {"vanster": "Inside", "hoger": "Outside", "mitt": "Middle"}

    def _plat_del(self, obj, pos, profil, material, huvuddel, skiss):
        """Gemensamt för SheetMetal-delar: egenskaperna Pos/Profil/Material, gruppen, färg."""
        obj.Label = "%s %s" % (pos, profil)
        for p_, beskr in (("Pos", "positionsnummer (stycklitterering)"), ("Profil", "profil / benämning i materiallistan"),
                          ("Material", "material"), ("Skiss", "profilskissen")):
            obj.addProperty("App::PropertyLink" if p_ == "Skiss" else "App::PropertyString", p_, "Stal", beskr)
        obj.Pos, obj.Profil, obj.Material, obj.Skiss = pos, profil, material or self.material, skiss
        self.grupp.addObject(obj)
        if huvuddel:
            self.grupp.Huvuddel = obj.Name
        try:
            obj.ViewObject.ShapeColor = (0.62, 0.64, 0.67)
            skiss.ViewObject.Visibility = False
        except Exception:
            pass
        return obj

    def _fri_profil(self, namn, mitt, rot):
        """Fristående skiss (pd.fri_skiss) placerad i `mitt` (tal eller uttryck, binds till Variabler) med delens
        x-, y- och z-riktning `rot`."""
        import pd
        import FreeCAD as App
        from FreeCAD import Vector as V
        u, v, w = (V(*r) for r in rot)
        m = App.Matrix(u.x, v.x, w.x, 0, u.y, v.y, w.y, 0, u.z, v.z, w.z, 0, 0, 0, 0, 1)
        sk = pd.fri_skiss(self.doc, namn, App.Placement())
        vals = [sk.d.uttryck(c) for c in mitt]
        sk.obj.Placement = App.Placement(V(*[val for _, val in vals]), App.Rotation(m))
        for k, (ex, _) in zip("xyz", vals):
            if ex:
                sk.obj.setExpression(".Placement.Base." + k, ex)
        return sk

    def bockad(self, pos, t, punkter, langd, mitt=(0, 0, 0), rot=((1, 0, 0), (0, 1, 0), (0, 0, 1)), radie=None,
               sida="vanster", material=None, huvuddel=False, profil=None, matt=None):
        """Kantvikt plåt (SheetMetal): profilen `punkter` [(x, y), ...] i delens XY-plan (öppen polylinje, t.ex.
        L, U, Z, hatt eller en kantkappa över en dörrkant), bockad med inre radien `radie` (standard = t) och
        utdragen `langd` (tal eller uttryck) längs delens z. Materialet ligger till vänster om profilens riktning
        (`sida="vanster"`, då är punkterna yttermått om profilen går moturs), "hoger" eller "mitt". `mitt` = delens
        origo (profilens nollpunkt), `rot` = delens x-, y- och z-riktning. `matt` = {sträcka: uttryck} binder
        sträckornas längder till Variabler. Blir en SheetMetal-bas (redigerbar i FreeCAD) med Pos/Profil/Material
        i materiallistan som "PL<t> BOCKAD"; utbredning och DXF med dxf.py."""
        import SheetMetalBaseCmd
        namn = re.sub(r"[^A-Za-z0-9]", "", pos) or "Plat"
        sk = self._fri_profil(namn + "_Profil", mitt, rot)
        sk.linjetag(punkter, matt=matt)
        self.doc.recompute()
        if not sk.obj.FullyConstrained:
            raise RuntimeError("bockad %s: profilskissen blev inte fullt bestämd" % pos)
        bf = self.doc.addObject("Part::FeaturePython", namn)
        SheetMetalBaseCmd.SMBaseBend(bf, sk.obj)
        try:
            SheetMetalBaseCmd.SMBaseViewProvider(bf.ViewObject)
        except Exception:
            pass
        bf.BendSide = self.SIDA[sida]
        for prop, x in (("Thickness", t), ("Radius", radie if radie is not None else t), ("Length", langd)):
            ex, val = sk.d.uttryck(x)
            setattr(bf, prop, val)
            if ex:
                bf.setExpression(prop, ex)
        self.doc.recompute()
        if not bf.Shape.Solids:
            raise RuntimeError("bockad %s: SheetMetal gav ingen solid (kontrollera profilen och radien)" % pos)
        return self._plat_del(bf, pos, profil or "PL%s BOCKAD" % _txt(sk.d.uttryck(t)[1]), material, huvuddel, sk.obj)

    def trag(self, pos, t, langd, bredd, kant, mitt=(0, 0, 0), rot=((1, 0, 0), (0, 1, 0), (0, 0, 1)), radie=None,
             sidor=("-x", "+x", "-y", "+y"), material=None, huvuddel=False, profil=None):
        """Plåttråg (SheetMetal): botten langd x bredd (yttermått, x resp. y) med uppbockade kanter `kant` högt
        (yttermått, längs delens +z) på `sidor` ("-x", "+x", "-y", "+y"; standard alla fyra, med hörnurtag).
        Beklädnad av ett dörrblad, en lucka eller en pelare, täckplåt, låda. `mitt` = bottens mitt (undersida),
        `rot` = delens riktningar. Utbredning och DXF med dxf.py."""
        import SheetMetalBaseCmd, SheetMetalCmd
        import pd
        import FreeCAD as App
        from FreeCAD import Vector as V
        namn = re.sub(r"[^A-Za-z0-9]", "", pos) or "Trag"
        sk = self._fri_profil(namn + "_Botten", mitt, rot)
        L, B, T, K = (float(sk.d.uttryck(x)[1]) for x in (langd, bredd, t, kant))
        R = float(sk.d.uttryck(radie)[1]) if radie is not None else T
        g = sk.rektangel(L, B, mitt=(0, 0), namn=("Langd", "Bredd"))
        self.doc.recompute()
        bas = self.doc.addObject("Part::FeaturePython", namn + "_Bas")
        SheetMetalBaseCmd.SMBaseBend(bas, sk.obj)
        bas.Thickness, bas.Radius = T, R
        self.doc.recompute()
        inv = sk.obj.Placement.inverse()

        def lokal(p):
            return inv.multVec(p)
        topp = max((f for f in bas.Shape.Faces if f.Surface.TypeId == "Part::GeomPlane"),
                   key=lambda f: lokal(f.CenterOfMass).z)
        kanter = []
        for i, e in enumerate(bas.Shape.Edges):
            if not any(e.isSame(te) for te in topp.Edges):
                continue
            c = lokal(e.CenterOfMass)
            sidan = ("+x" if c.x > 0 else "-x") if abs(abs(c.x) - L / 2) < abs(abs(c.y) - B / 2) else ("+y" if c.y > 0 else "-y")
            if sidan in sidor:
                kanter.append("Edge%d" % (i + 1))
        if not kanter:
            raise RuntimeError("trag %s: hittade inga kanter för sidorna %s" % (pos, sidor))
        w = self.doc.addObject("Part::FeaturePython", namn)
        SheetMetalCmd.SMBendWall(w, bas, kanter)
        try:
            SheetMetalCmd.SMViewProviderTree(w.ViewObject)
            SheetMetalBaseCmd.SMBaseViewProvider(bas.ViewObject)
        except Exception:
            pass
        w.length, w.radius = K, R
        self.doc.recompute()
        # bocken lägger kanten utanför botten och flänsen blir något högre: mät och justera till yttermåtten
        p0 = sk.obj.Placement                        # skissens läge i mitt
        for _ in range(3):
            bb = w.Shape.transformed(inv.toMatrix()).BoundBox
            q = lambda x: App.Units.Quantity(x, App.Units.Length)
            sk.obj.setDatum("Langd", q(sk.obj.getDatum("Langd").Value - (bb.XLength - L)))
            sk.obj.setDatum("Bredd", q(sk.obj.getDatum("Bredd").Value - (bb.YLength - B)))
            w.length = getattr(w.length, "Value", w.length) - (bb.ZLength - K)
            self.doc.recompute()
            # centrerat kring mitt (även när bara några sidor bockas), undersidan i mitt. Formen följer skissen, så
            # lådan mäts i skissens system och flyttningen räknas från ursprungsläget p0 (inte från förra varvets
            # läge: då dubblerades flyttningen och tråget hamnade en plåttjocklek fel när bara en sida bockades
            # eller delens z pekade i negativ riktning).
            bb = w.Shape.transformed(inv.toMatrix()).BoundBox
            sk.obj.Placement = App.Placement(p0.Base - p0.Rotation.multVec(V((bb.XMin + bb.XMax) / 2, (bb.YMin + bb.YMax) / 2, bb.ZMin)), p0.Rotation)
            inv = sk.obj.Placement.inverse()
            self.doc.recompute()
        bb = w.Shape.transformed(inv.toMatrix()).BoundBox
        if abs(bb.XLength - L) > 0.2 or abs(bb.YLength - B) > 0.2 or abs(bb.ZLength - K) > 0.2:
            self.logg("OBS: tråget %s blev %.1f x %.1f x %.1f (önskat %g x %g x %g)" % (pos, bb.XLength, bb.YLength, bb.ZLength, L, B, K))
        try:
            bas.ViewObject.Visibility = False
        except Exception:
            pass
        return self._plat_del(w, pos, profil or "PL%s BOCKAD" % _txt(T), material, huvuddel, sk.obj)

    def hal(self, delar, punkter, riktning, d=None, bult=None, langd=None):
        """Hål med diametern d (eller bultens: M12 -> Ø14) genom `delar` i punkterna (globala tal), längs
        riktningen: en skiss med cirklarna och en Pocket (genom allt, åt båda hållen) i varje kropp. Med `langd`
        går fickan bara +-langd/2 kring punkterna (t.ex. genom en fläns men inte den andra). Hålgruppen blir en
        hålangivelse 4*Ø14 - M12x44 på ritningen (fickans egenskaper Bult och Halgrupp).
        Punkternas koordinater får vara uttryck ("Langd / 4 - 27.5"): ligger kroppen axelparallellt binds
        cirklarnas lägen i skissen till Variabler, så att hålen följer med delen när en variabel ändras."""
        import pd
        import FreeCAD as App
        from FreeCAD import Vector as V
        dia = d or bultdiameter(bult)
        if not dia:
            raise ValueError("hal() behöver d eller bult (t.ex. 'M12x44')")
        self.antal_halgrupper += 1
        nr = self.antal_halgrupper
        for o in delar:
            dd = pd.Del(self.doc, o.Name)
            inv = o.Placement.inverse()
            rl = inv.Rotation.multVec(V(*riktning)).normalize()
            pv = [V(*[dd.uttryck(c)[1] for c in p]) for p in punkter]
            pl_ = [inv.multVec(p) for p in pv]
            rot = App.Rotation(V(0, 0, 1), rl)
            origo = rl * pl_[0].dot(rl)
            sk = dd.skiss("Hal%d" % nr, "XY")
            sk.obj.AttachmentOffset = App.Placement(origo, rot)
            self.doc.recompute()
            ri = rot.inverted()
            T = ri.multiply(o.Placement.Rotation.inverted())       # global riktning -> skissens x/y
            bas = self.baser.get(o.Name, (o.Placement.Base.x, o.Placement.Base.y, o.Placement.Base.z))
            for p, pg, praw in zip(pl_, pv, punkter):
                q = ri.multVec(p - origo)
                mitt = []
                for j, qj in ((0, q.x), (1, q.y)):
                    koef = [T.multVec(V(*[1.0 if i == k else 0.0 for i in range(3)]))[j] for k in range(3)]
                    k = max(range(3), key=lambda i: abs(koef[i]))
                    perm = abs(abs(koef[k]) - 1) < 1e-9 and all(abs(koef[i]) < 1e-9 for i in range(3) if i != k)
                    if perm and (isinstance(praw[k], str) or isinstance(bas[k], str)):
                        a_, b_ = (_txt(praw[k]), _txt(bas[k])) if koef[k] > 0 else (_txt(bas[k]), _txt(praw[k]))
                        mitt.append("(%s) - (%s)" % (a_, b_))
                    else:
                        mitt.append(round(qj, 4))
                sk.cirkel(round(dia, 4), mitt=tuple(mitt))
            f = dd.ficka(sk, "genom" if langd is None else langd, "Hal%d" % nr, symmetrisk=True)
            f.addProperty("App::PropertyString", "Bult", "Stal", "bult, t.ex. M12x44 (hålangivelsen på ritningen)")
            f.addProperty("App::PropertyInteger", "Halgrupp", "Stal", "hålgrupp: samma nummer i alla delar som hålen går genom")
            f.Bult, f.Halgrupp = bult or "", nr
            dd.stada()

    # -------------------------------------------------------------- gering
    def gera(self, o, yttre, inre, riktning=None):
        """Geringskapa änden av profilen `o` (hörn i en ram, 45° när två lika profiler möts): snittplanet går
        genom hörnets yttre och inre punkt (globala koordinater, tal eller uttryck) och profilens höjdriktning.
        Pocket "Gering" genom allt från en sluten skiss i kroppens XZ-plan (fullt bestämd). I slutänden följer
        skissen Pad-längden (uttryck på AttachmentOffset), så geringen följer med när längden ändras.
        Kapet tar bara bort det som ligger utanför planet: en profil som slutar innan planet når hela tvärsnittet
        (t.ex. ett snett plattstål kapat lodrätt i sin ände) blir bara kapad på halva höjden. Bygg den förlängd
        med (h/2)·|tan v| + några mm och kapa sedan. Skär kapet ingenting blir det fel (RuntimeError).
        `riktning` (global vektor) = en riktning som ska ligga i kapplanet; den måste vara tvärsnittets bredd- eller
        höjdriktning. Standard är höjdriktningen (`upp` i balk()); bredden används t.ex. för ett liggande plattstål
        som kapas lodrätt mot en stolpe."""
        import pd
        import FreeCAD as App
        from FreeCAD import Vector as V
        dd = pd.Del(self.doc, o.Name)
        pad = next(f for f in o.Group if f.TypeId == "PartDesign::Pad")
        self.doc.recompute()
        L = pad.Length.Value
        inv = o.Placement.inverse()
        c = 0                                                        # kroppens x i skissen (plan genom kroppens y)
        if riktning is not None:
            rl = inv.Rotation.multVec(V(*riktning)).normalize()
            if abs(abs(rl.x) - 1) < 1e-6:
                c = 1                                                # planet genom kroppens x: skiss i YZ
            elif abs(abs(rl.y) - 1) > 1e-6:
                raise ValueError("gera: riktningen %s är varken tvärsnittets bredd eller höjd i %s" % (tuple(riktning), o.Label))
        p1, p2 = (inv.multVec(V(*[dd.uttryck(c_)[1] for c_ in q])) for q in (yttre, inre))
        slut = (p1.z + p2.z) / 2 > L / 2
        ze = L if slut else 0.0
        a, b = (p1[c], p1.z - ze), (p2[c], p2.z - ze)
        lb = o.Shape.transformed(inv.toMatrix()).BoundBox            # tvärsnittets utsträckning i kroppen
        W = max(lb.XLength, lb.YLength) + 20
        span = max(abs(a[1]), abs(b[1]))
        z0, z1 = (-W, span + W) if not slut else (-(span + W), W)
        cmin, cmax = (lb.XMin, lb.XMax) if c == 0 else (lb.YMin, lb.YMax)
        ruta = [(cmin - 20, z0), (cmax + 20, z0), (cmax + 20, z1), (cmin - 20, z1)]
        kors = lambda q: (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
        sida = -1 if kors((0.0, L / 2 - ze)) > 0 else 1              # bort: sidan utan balkens mitt
        ut = []
        for i in range(len(ruta)):                                   # klipp rutan mot halvplanet (Sutherland-Hodgman)
            P, Q = ruta[i], ruta[(i + 1) % len(ruta)]
            fp, fq = sida * kors(P), sida * kors(Q)
            if fp >= 0:
                ut.append(P)
            if fp * fq < 0:
                t = fp / (fp - fq)
                ut.append((P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])))
        ut = [q for i, q in enumerate(ut) if math.dist(q, ut[i - 1]) > 1e-6]
        nr = sum(1 for f in o.Group if f.Name.startswith("Gering")) // 2 + 1
        sk = dd.skiss("Gering%d" % nr, "XZ" if c == 0 else "YZ")
        sk.obj.AttachmentOffset = App.Placement(V(0, ze, 0), App.Rotation())
        if slut:
            sk.obj.setExpression(".AttachmentOffset.Base.y", "%s.Length" % pad.Name)
        import Part
        g = [sk.geo(Part.LineSegment(V(*ut[i], 0), V(*ut[(i + 1) % len(ut)], 0))) for i in range(len(ut))]
        for i in range(len(g)):
            sk.begr("Coincident", g[i], pd.SLUT, g[(i + 1) % len(g)], pd.START)
            sk.placera(g[i], pd.START, round(ut[i][0], 4), round(ut[i][1], 4), namn="")
        dd.ficka(sk, "genom", "Gering%d" % nr, symmetrisk=True)
        dd.stada()

    def ritning(self, **val):
        self.grupp.Ritning = json.dumps(val, ensure_ascii=False)

    def utseende(self, val):
        """Utseende i 3D-bilderna per positionsprefix, t.ex. {"g/": "patinerad", "st/": "svart"} (rendera.py UTSEENDE)."""
        if not hasattr(self.grupp, "Utseende"):
            self.grupp.addProperty("App::PropertyString", "Utseende", "Stal", "utseende i 3D-bilderna (JSON, rendera.py)")
        d = json.loads(self.grupp.Utseende or "{}")
        d.update(val)
        self.grupp.Utseende = json.dumps(d, ensure_ascii=False)

    def rorelse(self, namn, delar, axel, fran=0, till=90, gangjarn=None):
        """Rörlig del (dörrblad, grind, lucka) för rorelse.py: `delar` = positionsnummer (lista, eller ett prefix
        som "g/" för alla som börjar så), `axel` = (punkt, riktning) för gångjärnsaxeln (globalt), vridning fran..till
        grader (positivt moturs kring riktningen), `gangjarn` = gångjärnens lägen längs axeln (globala punkter) för
        lasten. Sparas i gruppen (egenskapen Rorelser)."""
        if not hasattr(self.grupp, "Rorelser"):
            self.grupp.addProperty("App::PropertyString", "Rorelser", "Stal", "rörliga delar för rorelse.py (JSON)")
        lst = json.loads(self.grupp.Rorelser or "[]")
        lst.append(dict(namn=namn, delar=delar, axel=[list(axel[0]), list(axel[1])], fran=fran, till=till,
                        gangjarn=[list(p) for p in gangjarn or []]))
        self.grupp.Rorelser = json.dumps(lst, ensure_ascii=False)


def _txt(x):
    return x if isinstance(x, str) else ("%.4f" % x).rstrip("0").rstrip(".")


def profilnamn(o):
    """Profilnamnet; för en plåt räknat ur skissen Tvarsnitt (b och t), så att det följer en ändrad bredd."""
    p = o.Profil
    m = re.fullmatch(r"(PL|FL|FLA|PLT)" + NUM + r"\*" + NUM, p.upper().replace(",", "."))
    sk = next((f for f in getattr(o, "Group", []) if f.TypeId == "Sketcher::SketchObject" and f.Name.startswith("Tvarsnitt")), None)
    if not m or sk is None:
        return p
    try:
        b, t = sk.getDatum("b").Value, sk.getDatum("t").Value
    except Exception:
        return p
    g = lambda x: ("%.1f" % x).rstrip("0").rstrip(".")
    return "%s%s*%s" % (m.group(1), g(t), g(b)) if float(m.group(2)) <= float(m.group(3)) else "%s%s*%s" % (m.group(1), g(b), g(t))


def langd(o):
    """Delens längd i materiallistan: Pad-längden (följer variablerna); för en bockad plåt utdragslängden,
    för ett tråg den längsta sidan."""
    if not hasattr(o, "Group"):
        if hasattr(o, "Length") and hasattr(o, "BendSide"):
            return float(getattr(o.Length, "Value", o.Length))
        return round(max(o.Shape.BoundBox.XLength, o.Shape.BoundBox.YLength, o.Shape.BoundBox.ZLength), 1)
    pad = next((f for f in o.Group if f.TypeId == "PartDesign::Pad"), None)
    L = float(pad.Length.Value) if pad is not None else 0.0
    if (getattr(o, "Profil", "") or "").upper().startswith("GLAS"):                   # glasruta: längsta sidan
        bb = o.Shape.BoundBox
        return round(max(bb.XLength, bb.YLength, bb.ZLength), 1)
    m = re.fullmatch(r"(PL|FL|FLA|PLT)" + NUM + r"\*" + NUM, (getattr(o, "Profil", "") or "").upper().replace(",", "."))
    if m and L and abs(L - min(float(m.group(2)), float(m.group(3)))) < 0.01:     # egen platta utdragen i tjockleken
        b = max(float(m.group(2)), float(m.group(3)))
        bb = o.Shape.BoundBox
        rest = sorted((bb.XLength, bb.YLength, bb.ZLength))
        rest.remove(min(rest, key=lambda x: abs(x - L)))
        rest.remove(min(rest, key=lambda x: abs(x - b)))
        return round(rest[0], 1)
    return L


def halgrupper(ds):
    """Hålgrupperna ur fickorna (Pocket med egenskapen Halgrupp): punkter (globala hålmitter), riktning,
    diameter och bult. Samma grupp i flera delar slås ihop (hålmitterna projiceras på första skissens plan)."""
    import Part
    from FreeCAD import Vector as V
    grp = {}
    for o in ds:
        for f in getattr(o, "Group", []):
            if f.TypeId != "PartDesign::Pocket" or not hasattr(f, "Halgrupp"):
                continue
            sk = f.Profile[0] if isinstance(f.Profile, (list, tuple)) else f.Profile
            pl = sk.getGlobalPlacement()
            r = pl.Rotation.multVec(V(0, 0, 1))
            g = grp.setdefault(f.Halgrupp, dict(punkter=[], riktning=[r.x, r.y, r.z], d=None, bult=f.Bult, delar=[], p0=None))
            g["delar"].append(o.Name)
            rg = V(*g["riktning"])
            for geo in sk.Geometry:
                if isinstance(geo, Part.Circle):
                    c = pl.multVec(geo.Center)
                    if g["p0"] is None:
                        g["p0"] = c
                    c = c - rg * (c - g["p0"]).dot(rg)
                    g["d"] = round(geo.Radius * 2, 3)
                    if all((c - V(*p)).Length > 0.01 for p in g["punkter"]):
                        g["punkter"].append([c.x, c.y, c.z])
    ut = []
    for k in sorted(grp):
        g = grp[k]
        g.pop("p0")
        ut.append(g)
    return ut


def delar(doc):
    """Sammanställningens delar (kroppar med egenskapen Pos), gruppen och hålgrupperna."""
    g = doc.getObject("Sammanstallning")
    if g is None:
        raise RuntimeError("Filen saknar gruppen Sammanstallning (bygg med sammanstallning.py bygg)")
    ds = [o for o in g.Group if hasattr(o, "Pos")]
    return g, ds, halgrupper(ds)


def materiallista(ds):
    """Rader per positionsnummer: pos, profil, material, antal, längd, area/st (m2), vikt/st (kg), sorterade efter
    vikt (tyngst först). Varnar (fel=...) om delar med samma nummer skiljer sig."""
    grp = {}
    for o in ds:
        grp.setdefault(o.Pos, []).append(o)
    rader = []
    for pos, lst in grp.items():
        o = lst[0]
        vol = o.Shape.Volume
        L = langd(o)
        fel = [x.Label for x in lst[1:] if abs(x.Shape.Volume - vol) > 1e-3 * max(vol, 1) or x.Profil != o.Profil or abs(langd(x) - L) > 0.5]
        vikt = float(getattr(o, "Vikt", 0) or 0) or vol * 1e-9 * densitet(o.Material)      # inköpt: databladets vikt
        rader.append(dict(pos=pos, profil=profilnamn(o), material=o.Material, antal=len(lst), langd=L,
                          area=o.Shape.Area / 1e6, vikt=vikt, fel=fel))
    rader.sort(key=lambda r: (-round(r["vikt"], 1), r["pos"]))
    return rader
