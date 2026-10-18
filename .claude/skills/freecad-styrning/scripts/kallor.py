"""Källor för profilmått och materialkvaliteter: öppna databaser på nätet (med lokal cache), FreeCAD:s egna
data och som sista utväg de inbyggda tabellerna i stal.py. Varje svar bär med sig var uppgiften kommer
ifrån (källa, standard, hämtdatum), så att ritningen kan ange vad måtten och materialet är verifierade mot.

  python3 kallor.py profil UPE140 HEA160 "VKR100*6.3" "RÖR48.3*4" L50*5
  python3 kallor.py material S355J2 S235JR S355J2H [--t 12]
  python3 kallor.py uppdatera        # hämta om allt som ligger i cachen
  python3 kallor.py status           # källor, cache och eventuella fel vid senaste hämtning

Källor (alla läses med vanlig HTTPS, inga nycklar eller konton):
  profiler   Steel_Section_Database (github.com/ulmewix, MIT): EN 10365:2017 (IPE, HEA, HEB, HEM, UPE, UPN, IPN),
             EN 10219-2:2006 (kallformade VKR/RHS/SHS/CHS), EN 10210-2:2006 (varmformade KKR/CHS), EN 10056-1 (L).
             Reserv: FreeCAD:s BIM-profiltabell profiles.csv (lokalt i installationen eller från FreeCAD:s repo).
  material   eurocodeapplied.com, tabellen med nominellt fy/fu per EN 1993-1-1 tab. 3.1 (EN 10025-2..6,
             EN 10210-1, EN 10219-1), per tjockleksområde. Reserv: FreeCAD:s materialkort (Steel-S235JR.FCMat ...).
Cache: ~/.cache/freecad-styrning/kallor (FC_KALLOR_CACHE), förnyas efter 30 dagar (FC_KALLOR_DAGAR).
FC_KALLOR=offline använder bara cache och inbyggt; FC_KALLOR=uppdatera hämtar om. Nätet nås via https_proxy
och SSL_CERT_FILE om de är satta (som i Claude Codes molncontainer). Modulen använder bara standardbiblioteket
och kan importeras både i system-Python och i FreeCAD:s Python.
"""
import os, re, sys, json, ssl, time, glob, html, datetime, urllib.request, urllib.error

CACHE = os.environ.get("FC_KALLOR_CACHE") or os.path.join(os.path.expanduser("~"), ".cache", "freecad-styrning", "kallor")
LAGE = os.environ.get("FC_KALLOR", "auto").lower()          # auto | offline | uppdatera
MAXALDER = float(os.environ.get("FC_KALLOR_DAGAR", "30")) * 86400
TIMEOUT = float(os.environ.get("FC_KALLOR_TIMEOUT", "15"))
UA = "freecad-styrning (https://github.com/richalund/Steelworks-shopdrawings)"

SEKTIONSDB = dict(
    namn="Steel_Section_Database", kort="github.com/ulmewix/Steel_Section_Database", licens="MIT",
    url="https://raw.githubusercontent.com/ulmewix/Steel_Section_Database/main/generated/web/%s.json",
    spegel="https://cdn.jsdelivr.net/gh/ulmewix/Steel_Section_Database@main/generated/web/%s.json")
FREECAD_PROFILER = dict(
    namn="FreeCAD BIM profiles.csv", kort="github.com/FreeCAD/FreeCAD (profiles.csv)", licens="LGPL-2.0",
    url="https://raw.githubusercontent.com/FreeCAD/FreeCAD/main/src/Mod/BIM/Presets/profiles.csv",
    standard="EN-profiltabell utan rotradier")
EUROCODE = dict(
    namn="eurocodeapplied.com", kort="eurocodeapplied.com (EN 1993-1-1 tab. 3.1)",
    url="https://eurocodeapplied.com/design/en1993/steel-design-properties")
FREECAD_MATERIAL = dict(
    namn="FreeCAD materialkort", kort="github.com/FreeCAD/FreeCAD (Steel-*.FCMat)", licens="LGPL-2.0-or-later",
    url="https://raw.githubusercontent.com/FreeCAD/FreeCAD/main/src/Mod/Material/Resources/Materials/Standard/Metal/Steel/Steel-%s.FCMat")
INBYGGD = dict(namn="inbyggd tabell", kort="stal.py (inbyggd tabell)", standard="EN 10365 / EN 10219 (tabellvärden)",
               lage="inbyggd", hamtad="")

# FreeCAD:s kortnamn för vanliga beteckningar (korten använder äldre beteckningar, t.ex. S355J2G3 = S355J2)
FCMAT_NAMN = {"S235JR": "S235JR", "S235J0": "S235JO", "S235JRG1": "S235JRG1", "S275JR": "S275JR", "S275J0": "S275JO",
              "S275N": "S275N", "S355J2": "S355J2G3", "S355J2+N": "S355J2G3", "S355J2G3": "S355J2G3",
              "S420N": "S420N", "S460N": "S460N", "S420MC": "S420MC", "S460MC": "S460MC", "S355MC": "S355MC",
              "S185": "S185", "S500MC": "S500MC", "S550MC": "S550MC", "S690MC": "S690MC"}

NUM = r"(\d+(?:\.\d+)?)"
_fel = []            # fel vid senaste hämtningarna (för status och loggning)
_notiser = []        # förklaringar när något inte kunde verifieras


def _num(x):
    return ("%g" % float(x))


def fel():
    return list(_fel)


def notiser():
    return list(_notiser)


# ----------------------------------------------------------------------------------------------- hämtning
def _ladda(urls):
    ctx = ssl.create_default_context()
    sista = None
    for u in urls:
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=TIMEOUT, context=ctx)
            return r.read().decode("utf-8", "replace"), u
        except Exception as e:                    # nästa spegel
            sista = "%s: %s" % (u, e)
    raise RuntimeError(sista or "ingen adress")


def _hamta(urls, nyckel):
    """Text från cache eller nätet. Returnerar (text, meta) där meta har url, hamtad (datum) och lage
    (online / cache / cache, nätet nåddes inte), eller (None, None) om inget finns."""
    if isinstance(urls, str):
        urls = [urls]
    fil = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9._-]", "_", nyckel))
    mfil = fil + ".meta.json"
    meta = None
    if os.path.exists(fil) and os.path.exists(mfil):
        try:
            with open(mfil, encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = None
    farsk = meta is not None and time.time() - meta.get("tid", 0) < MAXALDER
    if meta is not None and LAGE != "uppdatera" and (LAGE == "offline" or farsk):
        with open(fil, encoding="utf-8") as f:
            return f.read(), dict(meta, lage="cache")
    if LAGE == "offline":
        return None, None
    try:
        text, u = _ladda(urls)
    except Exception as e:
        _fel.append(str(e))
        if meta is not None:
            with open(fil, encoding="utf-8") as f:
                return f.read(), dict(meta, lage="cache, nätet nåddes inte")
        return None, None
    os.makedirs(CACHE, exist_ok=True)
    meta = dict(url=u, hamtad=datetime.date.today().isoformat(), tid=time.time())
    with open(fil, "w", encoding="utf-8") as f:
        f.write(text)
    with open(mfil, "w", encoding="utf-8") as f:
        json.dump(meta, f)
    return text, dict(meta, lage="online")


def _kalla(src, meta, **extra):
    k = dict(namn=src["namn"], kort=src["kort"], licens=src.get("licens", ""), url=meta.get("url", src.get("url", "")),
             hamtad=meta.get("hamtad", ""), lage=meta.get("lage", ""))
    k.update(extra)
    return k


# ----------------------------------------------------------------------------------------------- profiler
def normalisera(profil):
    """Tekla-namn -> versaler, '*' mellan måtten, punkt som decimaltecken, inga mellanslag."""
    return profil.strip().upper().replace(",", ".").replace("X", "*").replace(" ", "")


def _serie(p):
    """(serie-id i Steel_Section_Database, beteckning där, typ, alternativ serie) för ett normaliserat namn."""
    m = re.fullmatch(r"(UPE|IPE|HEA|HEB|HEM|UPN|UNP|INP|IPN)(\d+)", p)
    if m:
        s = {"UNP": "UPN", "INP": "IPN"}.get(m.group(1), m.group(1))
        typ = "U" if s in ("UPE", "UPN") else "I"
        return s, "%s %s" % (s, m.group(2)), typ, None
    m = re.fullmatch(r"(VKR|KKR|RHS|SHS|KVR)" + NUM + r"\*" + NUM + r"(?:\*" + NUM + r")?", p)
    if m:
        a1, a2, a3 = float(m.group(2)), float(m.group(3)), m.group(4)
        h, b, t = (a1, a2, float(a3)) if a3 else (a1, a1, a2)
        h, b = max(h, b), min(h, b)
        varm = m.group(1) == "KKR"
        if h == b:
            s, alt = ("SHS-HF", "SHS-CF") if varm else ("SHS-CF", "SHS-HF")
            return s, "SHS %sx%sx%s" % (_num(b), _num(b), _num(t)), "R", alt
        s, alt = ("RHS-HF", "RHS-CF") if varm else ("RHS-CF", "RHS-HF")
        return s, "RHS %sx%sx%s" % (_num(h), _num(b), _num(t)), "R", alt
    m = re.fullmatch(r"(RÖR|ROR|CHS|VKCKR|KCKR)" + NUM + r"\*" + NUM, p)
    if m:
        varm = m.group(1) == "KCKR"
        s, alt = ("CHS-HF", "CHS-CF") if varm else ("CHS-CF", "CHS-HF")
        return s, "CHS %sx%s" % (_num(m.group(2)), _num(m.group(3))), "O", alt
    m = re.fullmatch(r"L" + NUM + r"\*" + NUM + r"(?:\*" + NUM + r")?", p)
    if m:
        a1, a2, a3 = float(m.group(1)), float(m.group(2)), m.group(3)
        h, b, t = (a1, a2, float(a3)) if a3 else (a1, a1, a2)
        if h == b:
            return "L-EQ", "L %sx%sx%s" % (_num(h), _num(h), _num(t)), "L", None
        return "L", "L %sx%sx%s" % (_num(max(h, b)), _num(min(h, b)), _num(t)), "L", None
    return None


def _sektionsdb(serie):
    text, meta = _hamta([SEKTIONSDB["url"] % serie, SEKTIONSDB["spegel"] % serie], "ssdb_%s.json" % serie)
    if text is None:
        return None, None
    try:
        return json.loads(text), meta
    except ValueError as e:
        _fel.append("%s: ogiltig JSON (%s)" % (serie, e))
        return None, None


def _ur_sektionsdb(serie, bet, typ):
    d, meta = _sektionsdb(serie)
    if d is None:
        return None
    for prof in d.get("profiles", []):
        if prof.get("designation", "").replace(" ", "").upper() == bet.replace(" ", "").upper():
            g = prof["geometry"]
            k = _kalla(SEKTIONSDB, meta, standard=d.get("standard", ""), serie=serie, beteckning=prof["designation"])
            massa = (prof.get("properties") or {}).get("mass_per_length")
            if typ in ("U", "I"):
                if "slope_pct" in g:        # UPN/IPN med lutande flänsar
                    info = dict(typ=typ + "_LUTANDE", h=g["h"], b=g["b"], tw=g["tw"], tf=g["tf"], r=g["r1"], r2=g.get("r2"))
                else:
                    info = dict(typ=typ, h=g["h"], b=g["b"], tw=g["tw"], tf=g["tf"], r=g["r"])
            elif typ == "R":
                b = g["b"]
                info = dict(typ="R", h=g.get("h", b), b=b, t=g["t"], ro=g["ro"], ri=g["ri"])
            elif typ == "O":
                info = dict(typ="O", d=g["D"], t=g["t"])
            else:
                info = dict(typ="L", h=g.get("h", g["b"]), b=g["b"], t=g["t"], r1=g.get("r1"), r2=g.get("r2"))
            info["massa_m"] = massa
            info["kalla"] = k
            return info
    _notiser.append("%s finns inte i serien %s hos %s (%s)" % (bet, serie, SEKTIONSDB["namn"], d.get("standard", "")))
    return None


def _freecad_profiler_text():
    """profiles.csv: lokalt i FreeCAD-installationen, annars från FreeCAD:s repo."""
    kandidater = []
    fb = os.environ.get("FREECAD_BIN", "")
    if fb:
        kandidater.append(os.path.join(os.path.dirname(os.path.dirname(fb)), "share", "Mod", "BIM", "Presets", "profiles.csv"))
        kandidater.append(os.path.join(os.path.dirname(os.path.dirname(fb)), "Mod", "BIM", "Presets", "profiles.csv"))
    kandidater += ["/opt/freecad/share/Mod/BIM/Presets/profiles.csv", "/usr/share/freecad/Mod/BIM/Presets/profiles.csv"]
    for rot in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.path.expandvars(r"%LOCALAPPDATA%\Programs")):
        kandidater += glob.glob(os.path.join(rot, "FreeCAD*", "Mod", "BIM", "Presets", "profiles.csv"))
    for f in kandidater:
        if os.path.exists(f):
            with open(f, encoding="utf-8", errors="replace") as fh:
                return fh.read(), dict(url=f, hamtad="", lage="lokal FreeCAD-installation")
    return _hamta(FREECAD_PROFILER["url"], "freecad_profiles.csv")


def _ur_freecad_profiler(p, typ):
    text, meta = _freecad_profiler_text()
    if text is None:
        return None
    namn = p.replace("*", "x")
    for rad in text.splitlines():
        if rad.startswith("#") or not rad.strip():
            continue
        c = [x.strip() for x in rad.split(",")]
        if len(c) < 4 or c[1].replace(" ", "").upper() != namn:
            continue
        k = _kalla(FREECAD_PROFILER, meta, standard=FREECAD_PROFILER["standard"], serie=c[0], beteckning=c[1])
        if c[2] == "H" and typ == "I":
            return dict(typ="I", b=float(c[3]), h=float(c[4]), tw=float(c[5]), tf=float(c[6]), r=None, kalla=k)
        if c[2] == "U" and typ == "U":
            a1, a2 = float(c[3]), float(c[4])
            return dict(typ="U", h=max(a1, a2), b=min(a1, a2), tw=float(c[5]), tf=float(c[6]), r=None, kalla=k)
        if c[2] == "RH" and typ == "R":
            h, b, t = float(c[3]), float(c[4]), float(c[5])
            return dict(typ="R", h=max(h, b), b=min(h, b), t=t, ro=None, ri=None, kalla=k)
        if c[2] == "C" and typ == "O":
            return dict(typ="O", d=float(c[3]), t=float(c[4]), kalla=k)
    return None


def profil(namn):
    """Mått för ett Tekla-profilnamn ur källorna, med 'kalla'. None om ingen källa känner profilen (plattor,
    rundstång och okända namn), så att anroparen kan använda inbyggda tabeller eller måtten i namnet."""
    p = normalisera(namn)
    s = _serie(p)
    if s is None:
        return None
    serie, bet, typ, alt = s
    info = _ur_sektionsdb(serie, bet, typ)
    if info is None and alt:
        info = _ur_sektionsdb(alt, bet, typ)
    if info is None:
        info = _ur_freecad_profiler(p, typ)
    return info


def tjocklek(namn):
    """Godstjocklek att välja fy/fu-område efter: tf för I/U, t för rör och L, plåttjocklek för PL."""
    p = normalisera(namn)
    i = profil(p) if _serie(p) else None
    if i:
        return i.get("tf") or i.get("t")
    m = re.fullmatch(r"(PL|FL|FLA|PLT)" + NUM + r"\*" + NUM, p)
    if m:
        return min(float(m.group(2)), float(m.group(3)))
    m = re.fullmatch(r"(VKR|KKR|RHS|SHS|KVR|RÖR|ROR|CHS|VKCKR|KCKR|L)" + NUM + r"\*" + NUM + r"(?:\*" + NUM + r")?", p)
    if m:
        return float(m.group(4) or m.group(3))
    m = re.fullmatch(r"(FS|FKT|D|RUND|RD)" + NUM, p)              # massiv fyrkant- och rundstång
    if m:
        return float(m.group(2))
    return None


# ----------------------------------------------------------------------------------------------- material
def beteckning(material):
    """'Stål S355J2, varmförzinkad' -> ('S355J2', 'S355', 'J2'). None om ingen S-kvalitet hittas."""
    m = re.search(r"\bS\s*(\d{3})\s*([A-Z0-9+/]*)", (material or "").upper())
    if not m:
        return None
    return "S%s%s" % (m.group(1), m.group(2)), "S" + m.group(1), m.group(2)


def _kolumn(grupp, kval, varmformad=False):
    """Kolumnrubriken hos eurocodeapplied för kvaliteten: 'S355', 'S355 N/NL', 'S355 H' ..."""
    k = kval.replace("+", "")
    if k.endswith("H") or "H" in k:
        if k.startswith("N"):
            return grupp + " NH/NLH", ("EN 10210-1" if varmformad else "EN 10219-1")
        if k.startswith("M"):
            return grupp + " MH/MLH", "EN 10219-1"
        return grupp + " H", ("EN 10210-1" if varmformad else "EN 10219-1")
    if k.startswith("N"):
        return grupp + " N/NL", "EN 10025-3"
    if k.startswith("M"):
        return grupp + " M/ML", "EN 10025-4"
    if k.startswith("W"):
        return grupp + " W", "EN 10025-5"
    if k.startswith("Q"):
        return grupp + " Q/QL/QL1", "EN 10025-6"
    return grupp, "EN 10025-2"


def _celler(rad):
    ut = []
    for m in re.finditer(r"<t([dh])([^>]*)>(.*?)</t\1>", rad, re.S):
        cs = re.search(r'colspan="?(\d+)', m.group(2))
        txt = html.unescape(re.sub(r"<[^>]+>", " ", m.group(3)))
        ut.append((re.sub(r"\s+", " ", txt).strip(), int(cs.group(1)) if cs else 1))
    return ut


def _eurocode_tabell():
    """{(kolumn, standard): dict(fy40, fu40, fy80, fu80)} ur eurocodeapplied, plus meta."""
    text, meta = _hamta(EUROCODE["url"], "eurocodeapplied_steel.html")
    if text is None:
        return None, None
    tabeller = re.findall(r"<table.*?</table>", text, re.S)
    ut = {}
    for tb in tabeller:
        rader = [_celler(r) for r in re.findall(r"<tr.*?</tr>", tb, re.S)]
        ify = next((i for i, r in enumerate(rader) if r and re.match(r"f\s*y\b", r[0][0], re.I)), None)
        ifu = next((i for i, r in enumerate(rader) if r and re.match(r"f\s*u\b", r[0][0], re.I)), None)
        if ify is None or ifu is None or ify < 1:
            continue
        # raden före fy: Symbol | Description | kvaliteter; raden före den: produktstandarder med colspan
        kval = [c[0] for c in rader[ify - 1]]
        std = []
        if ify >= 2:
            for txt, cs in rader[ify - 2]:
                m = re.search(r"EN\s*(\d{5}(?:-\d)?)", txt)
                std += [("EN " + m.group(1)) if m else ""] * cs
        fy = [c[0] for c in rader[ify]]
        fu = [c[0] for c in rader[ifu]]
        for i in range(len(kval)):
            if i >= len(fy) or i >= len(fu) or not re.match(r"S\d{3}", kval[i]):
                continue
            s_ = std[i] if i < len(std) else ""
            try:
                vy, vu = float(fy[i]), float(fu[i])
            except ValueError:
                continue
            post = ut.setdefault((kval[i], s_), {})
            if "fy40" not in post:
                post.update(fy40=vy, fu40=vu)
            else:
                post.update(fy80=vy, fu80=vu)
    if not ut:
        _fel.append("eurocodeapplied: hittade ingen fy/fu-tabell i sidan (layouten kan ha ändrats)")
        return None, None
    return ut, meta


def _fcmat(bet):
    """fy, fu, densitet ur FreeCAD:s materialkort, lokalt eller från FreeCAD:s repo."""
    kort = FCMAT_NAMN.get(bet)
    if not kort and re.fullmatch(r"S\d{3}", bet):
        kort = FCMAT_NAMN.get({"S235": "S235JR", "S275": "S275JR", "S355": "S355J2"}.get(bet, ""))
        if kort:
            _notiser.append("%s utan kvalitetsbokstäver: FreeCAD-kortet %s används" % (bet, kort))
    if not kort:
        return None
    text = meta = None
    for mapp in (["/opt/freecad/share/Mod/Material/Resources/Materials/Standard/Metal/Steel"]
                 + glob.glob(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "FreeCAD*", "Mod", "Material",
                                          "Resources", "Materials", "Standard", "Metal", "Steel"))):
        f = os.path.join(mapp, "Steel-%s.FCMat" % kort)
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                text, meta = fh.read(), dict(url=f, hamtad="", lage="lokal FreeCAD-installation")
            break
    if text is None:
        text, meta = _hamta(FREECAD_MATERIAL["url"] % kort, "fcmat_%s.FCMat" % kort)
    if text is None:
        return None
    def v(nyckel):
        m = re.search(nyckel + r':\s*"?([\d.]+)', text)
        return float(m.group(1)) if m else None
    std = re.search(r'StandardCode:\s*"([^"]+)"', text)
    nr = re.search(r'MaterialNumber:\s*"([^"]+)"', text)
    return dict(fy=v("YieldStrength"), fu=v("UltimateTensileStrength"), densitet=v("Density"), t_omrade="",
                standard=(std.group(1) if std else "EN 10025"), materialnummer=(nr.group(1) if nr else ""),
                kalla=_kalla(FREECAD_MATERIAL, meta, standard=(std.group(1) if std else "EN 10025"), beteckning=kort))


def material(namn, t=None, varmformad=False):
    """Nominellt fy/fu för en S-kvalitet: dict(beteckning, grupp, kolumn, standard, fy, fu, t_omrade, kalla)
    eller None om kvaliteten inte känns igen eller inte finns i någon källa."""
    b = beteckning(namn)
    if not b:
        return None
    bet, grupp, kval = b
    kol, std = _kolumn(grupp, kval, varmformad)
    tab, meta = _eurocode_tabell()
    if tab:
        post = tab.get((kol, std)) or next((p for (k, s), p in tab.items() if k == kol), None)
        if post is None and kol != grupp:                       # t.ex. S355 J2H utan egen kolumn: EN 10025-2-värdet
            post, kol, std = tab.get((grupp, "EN 10025-2")), grupp, "EN 10025-2"
            if post:
                _notiser.append("%s: ingen egen kolumn hos %s, fy/fu enligt %s" % (bet, EUROCODE["namn"], grupp))
        if post:
            if t is not None and t > 40 and "fy80" in post:
                fy, fu, omr = post["fy80"], post["fu80"], "40 < t ≤ 80 mm"
            else:
                fy, fu, omr = post["fy40"], post["fu40"], "t ≤ 40 mm"
            if t is not None and t > 80:
                _notiser.append("%s: t = %s mm över tabellens 80 mm, värdena för 40–80 mm anges" % (bet, _num(t)))
            return dict(beteckning=bet, grupp=grupp, kolumn=kol, standard=std, fy=fy, fu=fu, t_omrade=omr,
                        kalla=_kalla(EUROCODE, meta, standard="EN 1993-1-1 tab. 3.1 / " + std))
        _notiser.append("%s finns inte i tabellen hos %s" % (bet, EUROCODE["namn"]))
    fc = _fcmat(bet)
    if fc:
        fc.update(beteckning=bet, grupp=grupp, kolumn=bet)
        return fc
    return None


# ----------------------------------------------------------------------------------------------- text till ritning
def bryt(s, n=72):
    """Radbrytning vid mellanslag så att ingen rad blir längre än n tecken."""
    ut, rad = [], ""
    for ord_ in s.split():
        if rad and len(rad) + 1 + len(ord_) > n:
            ut.append(rad)
            rad = ord_
        else:
            rad = (rad + " " + ord_).strip()
    if rad:
        ut.append(rad)
    return ut


def _versaler(s):
    """Versaler som i Tekla-noterna, men enheter och storheter behåller sin skrivning."""
    u = s.upper()
    for a, b in (("MPA", "MPa"), ("FY ", "fy "), ("FU ", "fu "), ("(T ≤", "(t ≤"), ("< T ≤", "< t ≤"), (" MM)", " mm)"),
                 (" MM,", " mm,"), (" MM.", " mm."), ("KG/M³", "kg/m³")):
        u = u.replace(a, b)
    return u


def _datum(k):
    return (" " + k["hamtad"]) if k.get("hamtad") else (" (%s)" % k["lage"] if k.get("lage") else "")


def text_profiler(kallor):
    """En mening om var profilmåtten är verifierade, ur listan av källposter (dict) från bygget."""
    if not kallor:
        return ""
    verif = [k for k in kallor if k.get("lage") != "inbyggd"]
    inb = [k for k in kallor if k.get("lage") == "inbyggd"]
    delar = []
    if verif:
        per = {}
        for k in verif:
            per.setdefault((k["kort"], k.get("hamtad", "")), set()).add(k.get("standard", ""))
        for (kort, datum), stds in per.items():
            delar.append("profilmått enl. %s verifierade mot %s%s" % (", ".join(sorted(s for s in stds if s)), kort, " " + datum if datum else ""))
    if inb:
        delar.append("profilmått för %s enl. inbyggd tabell (%s), ej verifierade mot extern källa"
                     % (", ".join(sorted({k.get("profil", "?") for k in inb})), INBYGGD["standard"]))
    return "; ".join(delar) + "."


def text_material(info, namn=None, kort=False):
    """En mening om materialkvaliteten och var den är verifierad; info från material(). namn = texten på
    ritningen. kort=True ger en kortare form för A3-bladens noter."""
    if not info:
        return "Material %s: ej verifierat mot någon källa." % (namn or "")
    k = info["kalla"]
    s = "%s enl. %s: fy %s MPa, fu %s MPa" % (info["beteckning"], info["standard"], _num(info["fy"]), _num(info["fu"]))
    if info.get("t_omrade"):
        s += " (%s)" % info["t_omrade"]
    if info.get("densitet") and not kort:
        s += ", %s kg/m³" % _num(info["densitet"])
    var = k["kort"].split(" (")[0] if kort else k["kort"]
    return s + ". Verifierat mot %s%s." % (var, _datum(k))


def noter(kallor_profiler, material_info, bredd=72, versaler=True):
    """Rader till ritningens noter: en (bruten) mening om profilmåtten och en per material.
    material_info = {materialtext: material()-resultat eller None}."""
    rader = []
    tp = text_profiler(kallor_profiler)
    if tp:
        rader += bryt(tp, bredd)
    for namn, info in material_info.items():
        rader += bryt(text_material(info, namn), bredd)
    return [_versaler(r) for r in rader] if versaler else rader


# ----------------------------------------------------------------------------------------------- CLI
def _skriv_kalla(k):
    return "%s%s, %s%s" % (k.get("kort", k.get("namn", "")), " [%s]" % k["standard"] if k.get("standard") else "",
                           k.get("lage", ""), " " + k["hamtad"] if k.get("hamtad") else "")


def uppdatera():
    global LAGE
    LAGE = "uppdatera"
    n = 0
    for f in glob.glob(os.path.join(CACHE, "*.meta.json")):
        with open(f, encoding="utf-8") as fh:
            m = json.load(fh)
        nyckel = os.path.basename(f)[:-len(".meta.json")]
        text, meta = _hamta(m["url"], nyckel)
        print("%-40s %s" % (nyckel, meta["lage"] if meta else "MISSLYCKADES"))
        n += 1
    if n == 0:
        print("Cachen är tom (%s). Kör 'profil' eller 'material' så fylls den." % CACHE)
    for e in _fel:
        print("FEL:", e)


def status():
    print("Cache:", CACHE, "(läge %s, förnyas efter %g dagar)" % (LAGE, MAXALDER / 86400))
    for f in sorted(glob.glob(os.path.join(CACHE, "*.meta.json"))):
        with open(f, encoding="utf-8") as fh:
            m = json.load(fh)
        print("  %-40s hämtad %s  %s" % (os.path.basename(f)[:-len(".meta.json")], m.get("hamtad"), m.get("url")))
    print("Källor:")
    for s in (SEKTIONSDB, FREECAD_PROFILER, EUROCODE, FREECAD_MATERIAL):
        print("  %-28s %s  (%s)" % (s["namn"], s["url"].replace("%s", "<namn>"), s.get("licens", "webbsida")))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("lage", choices=["profil", "material", "uppdatera", "status"])
    ap.add_argument("namn", nargs="*")
    ap.add_argument("--t", type=float, default=None, help="godstjocklek (mm) för fy/fu-området")
    ap.add_argument("--varmformad", action="store_true", help="hålprofil enligt EN 10210 (KKR) i stället för EN 10219")
    a = ap.parse_args(argv)
    if a.lage == "uppdatera":
        return uppdatera()
    if a.lage == "status":
        return status()
    if not a.namn:
        ap.error("ange minst ett namn")
    for n in a.namn:
        if a.lage == "profil":
            i = profil(n)
            if i is None:
                print("%-14s ingen källa (plåt, rundstång eller okänt namn: måtten tas ur namnet eller inbyggd tabell)" % n)
                continue
            k = i.pop("kalla")
            massa = i.pop("massa_m", None)
            matt = ", ".join("%s=%s" % (x, _num(v)) for x, v in i.items() if x != "typ" and v is not None)
            print("%-14s %s%s" % (n, matt, "  %.2f kg/m" % massa if massa else ""))
            print("%-14s källa: %s  (%s)" % ("", _skriv_kalla(k), k.get("url", "")))
        else:
            i = material(n, a.t, a.varmformad)
            if i is None:
                print("%-14s ingen källa känner kvaliteten" % n)
                continue
            print("%-14s %s" % (n, text_material(i)))
            print("%-14s källa: %s  (%s)" % ("", _skriv_kalla(i["kalla"]), i["kalla"].get("url", "")))
    for s in _notiser:
        print("OBS:", s)
    for e in _fel:
        print("FEL:", e)


if __name__ == "__main__":
    main()
