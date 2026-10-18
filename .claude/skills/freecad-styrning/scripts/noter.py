"""Noteringar på ritningarna: grupperade under rubriker, i spalter, och vid behov på ett eget blad.

Noterna kommer från konstruktionsskriptets RITNING["noter"] (eller --not), racke.noter, källnoterna (kallor.py),
inköpta komponenter och regelkontrollen. De sorteras under fasta rubriker i den här ordningen:

  STATUS                     (utan rubrik, överst: PRELIMINÄR, EJ FÖR TILLVERKNING, GEMENSAMMA NOTERINGAR SE ...)
  UNDERLAG OCH ANTAGANDEN    UNDERLAG:, ANTAGNA, KONTROLLMÄTS ...
  UTFÖRANDE                  allt som inte passar någon annanstans
  MONTAGE OCH INFÄSTNING     MONTAGE:, NEDGJUTNA, KEMANKARE, INFÄSTNING ...
  SVETS                      SVETS: ...
  YTBEHANDLING               YTBEHANDLING:, FÖRZINKAD, PULVERLACK, RAL, PATINERAD ...
  MATERIAL OCH KÄLLOR        MATERIAL: och källnoterna (var profiler och kvaliteter är verifierade)
  INKÖPTA KOMPONENTER        k.inkop med register (leverantör, artikel, datablad)
  KONTROLL                   regelkontrollen

Skriptet kan också ange rubriken själv, med en sträng "RUBRIK: text" där RUBRIK är en av rubrikerna ovan eller
deras korta form (STATUS, UNDERLAG, UTFÖRANDE, MONTAGE, SVETS, YTBEHANDLING, MATERIAL, INKÖP, KONTROLL), eller med
en dict {"SVETS": ["...", "..."], ...} i stället för en lista. Egna rubriker i en dict läggs efter UTFÖRANDE.
Prefixet tas bort när det är samma som rubriken ("SVETS: STOLPAR a4" -> "STOLPAR a4" under SVETS).

  import noter
  grupper = noter.gruppera(RITNING["noter"], kallor=kallrader, inkop=inkoprader, kontroll=regelrader)
  spalter = noter.spalter(grupper, antal=2, tecken=80)       # [[(typ, text), ...], ...]

Ett eget blad (NOTERINGAR) används när noterna inte ryms på blad 1 (sammanstallning.py avgör) eller när
skriptet sätter RITNING["noter_blad"] = True eller `--noter-blad` ges. För ett projekt med många ritningar kan
de gemensamma noterna läggas på en egen noteringsritning (`sammanstallning.py noteringar <noter.py|json>`), och
varje ritning får en statusrad "GEMENSAMMA NOTERINGAR SE RITNING N-01".
"""
import re

ORDNING = ["STATUS", "UNDERLAG OCH ANTAGANDEN", "UTFÖRANDE", "MONTAGE OCH INFÄSTNING", "SVETS", "YTBEHANDLING",
           "MATERIAL OCH KÄLLOR", "INKÖPTA KOMPONENTER", "KONTROLL"]
KORT = {"STATUS": "STATUS", "UNDERLAG": "UNDERLAG OCH ANTAGANDEN", "ANTAGANDEN": "UNDERLAG OCH ANTAGANDEN",
        "UTFÖRANDE": "UTFÖRANDE", "MONTAGE": "MONTAGE OCH INFÄSTNING", "INFÄSTNING": "MONTAGE OCH INFÄSTNING",
        "SVETS": "SVETS", "YTBEHANDLING": "YTBEHANDLING", "MATERIAL": "MATERIAL OCH KÄLLOR",
        "KÄLLOR": "MATERIAL OCH KÄLLOR", "INKÖP": "INKÖPTA KOMPONENTER", "KONTROLL": "KONTROLL"}
KORT.update({k: k for k in ORDNING})
# nyckelord (versaler) när skriptet inte angett rubriken; första träffen i listans ordning gäller
REGLER = [
    ("STATUS", r"PRELIMINÄR|EJ FÖR TILLVERKNING|FÖR GRANSKNING|BYGGHANDLING|GEMENSAMMA NOTERINGAR"),
    ("UNDERLAG OCH ANTAGANDEN", r"^UNDERLAG\b|ANTAG|KONTROLLMÄT|MÄTS PÅ PLATS|UR FOTO"),
    ("SVETS", r"^SVETS"),
    ("YTBEHANDLING", r"^YTBEHANDLING|FÖRZINK|PULVERLACK|\bLACKAD|\bRAL ?\d|PATINER|BLÄSTR|GRUNDMÅL|BETS"),
    ("MONTAGE OCH INFÄSTNING", r"^MONTAGE|NEDGJUTN|INGJUT|KEMANKAR|EXPANDER|INFÄST|KÄRNBORR"),
    ("MATERIAL OCH KÄLLOR", r"^MATERIAL\b|ENL\. EN 10|VERIFIERA"),
    ("INKÖPTA KOMPONENTER", r"^INKÖP\b"),
    ("KONTROLL", r"^REGELKONTROLL"),
]


def rubrik_for(text):
    """(rubrik, text utan prefix) för en not."""
    m = re.match(r"^\s*([A-ZÅÄÖ][A-ZÅÄÖ ]*?)\s*:\s*(.*)$", text)
    if m and m.group(1).strip().upper() in KORT:
        r = KORT[m.group(1).strip().upper()]
        rest = m.group(2).strip()
        # prefix som är rubrikens första ord tas bort ("SVETS: ..."), annars står det kvar ("UNDERLAG: ..." blir kvar
        # om rubriken är längre, så att raden går att läsa ensam)
        return r, (rest if r.split()[0] == m.group(1).strip().upper() and r not in ("UNDERLAG OCH ANTAGANDEN",
                                                                                    "MATERIAL OCH KÄLLOR") else text.strip())
    u = text.upper()
    for r, mon in REGLER:
        if re.search(mon, u):
            return r, text.strip()
    return "UTFÖRANDE", text.strip()


def gruppera(noter, kallor=(), inkop=(), kontroll=()):
    """[(rubrik, [noter])] i ORDNING. noter: lista av strängar eller dict {rubrik: [rader]}. kallor, inkop och
    kontroll är färdiga noter (en not per element, kan vara radbrutna i förväg: element som börjar med två
    mellanslag räknas som fortsättning på föregående)."""
    grupper = {}
    egna = []
    if isinstance(noter, dict):
        for r, rader in noter.items():
            r_ = KORT.get(str(r).strip().upper().rstrip(":"), str(r).strip().upper().rstrip(":"))
            if r_ not in ORDNING and r_ not in egna:
                egna.append(r_)
            grupper.setdefault(r_, []).extend([rader] if isinstance(rader, str) else list(rader))
    else:
        for n in noter or []:
            r, t = rubrik_for(str(n))
            if t:
                grupper.setdefault(r, []).append(t)
    for r, lst in (("MATERIAL OCH KÄLLOR", kallor), ("INKÖPTA KOMPONENTER", inkop), ("KONTROLL", kontroll)):
        for t in lst or []:
            grupper.setdefault(r, []).append(t)
    ordning = ORDNING[:3] + egna + ORDNING[3:]
    return [(r, grupper[r]) for r in ordning if grupper.get(r)]


def lagg_till_status(grupper, text, sist=False):
    """Grupperna med en statusrad till (först eller sist bland statusraderna)."""
    ut = [(r, list(l)) for r, l in grupper]
    if ut and ut[0][0] == "STATUS":
        ut[0][1].insert(len(ut[0][1]) if sist else 0, text)
    else:
        ut.insert(0, ("STATUS", [text]))
    return ut


def bryt(s, n):
    """Radbrytning vid mellanslag (n tecken)."""
    ut, rad = [], ""
    for o in s.split():
        if rad and len(rad) + 1 + len(o) > n:
            ut.append(rad)
            rad = o
        else:
            rad = (rad + " " + o).strip()
    if rad:
        ut.append(rad)
    return ut or [""]


def rader(grupper, tecken=80, T=None):
    """Grupperna som rader att rita: ("rubrik", text), ("not", text) för första raden i en not och ("forts",
    text) för fortsättningen. STATUS får ingen rubrik."""
    T = T or (lambda s, *a: s % a if a else s)
    ut = []
    for r, noter_ in grupper:
        if r != "STATUS":
            ut.append(("rubrik", T(r)))
        for n in noter_:
            if n.startswith("  ") and ut and ut[-1][0] in ("not", "forts"):
                ut.append(("forts", n.strip()))
                continue
            for i, t in enumerate(bryt(n, tecken - 2)):
                ut.append(("status" if r == "STATUS" else "not" if i == 0 else "forts", t))
        ut.append(("luft", ""))
    while ut and ut[-1][0] == "luft":
        ut.pop()
    return ut


def spalter(grupper, antal=2, tecken=80, T=None):
    """Raderna fördelade på `antal` spalter, hela rubriker per spalt så långt det går (en lång grupp får delas),
    så att spalterna blir ungefär lika höga. STATUS-raderna står först i första spalten."""
    T = T or (lambda s, *a: s % a if a else s)
    alla = rader(grupper, tecken, T)
    if antal <= 1 or not alla:
        return [alla]
    mal = len(alla) / float(antal)
    spalt, ut, senaste = [], [], None
    for r in alla:
        # byt spalt vid en rubrik när spalten nått målet, eller mitt i en grupp när den blivit för lång
        if spalt and len(ut) < antal - 1 and ((r[0] == "rubrik" and len(spalt) >= mal * 0.85)
                                             or (r[0] == "not" and len(spalt) >= mal * 1.25)):
            ut.append(spalt)
            spalt = [("rubrik", T("%s (FORTS.)", senaste))] if r[0] == "not" and senaste else []
        if r[0] == "rubrik":
            senaste = r[1]
        if not spalt and r[0] == "luft":
            continue
        spalt.append(r)
    ut.append(spalt)
    while len(ut) < antal:
        ut.append([])
    return ut
