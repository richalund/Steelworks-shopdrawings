"""Gemensam byggare för smidesräcken i stilen från P. Hellstones förebilder (mail 2026-10-17): fyrkantiga
stolpar FS20 nedgjutna i granitstegen, plan handledare PL40*8 med smidd snäcka i nedre änden, överliggare
PL30*8 på högkant under handledaren, underliggare PL40*8 plant, stående spjälor D12 mellan liggarna med fri
öppning < 100 mm. Används av egna/konstruktioner/racke_trappa.py (R/1, snett räcke längs trappan) och
racke_platta.py (R/2, plant räcke på nedre plattan): Steg = 0 ger ett plant räcke.

Koordinater: X längs räcket (uppför trappan), Y = tvärs (räckesplanet y = 0), Z uppåt. ±0 = nedre plattans
översida (Steg > 0) resp. plattans översida (Steg = 0). Framkantslinjen (noslinjen) går genom stegens
framkanter: z = Steghojd + x * Steghojd/Stegdjup, första steget vid x = 0.
Måtten räknas ut i Python (sned geometri): ändrade variabler kräver ombyggnad (sammanstallning.py bygg --var).
"""
import math

STAL = "S235JR"
HL_B, HL_T = 40.0, 8.0          # handledare PL40*8, plant
OL_H, OL_T = 30.0, 8.0          # överliggare PL30*8 på högkant
UL_B, UL_T = 40.0, 8.0          # underliggare PL40*8, plant
SPJ_D = 12.0                    # spjäla D12
ST_A = 20.0                     # stolpe FS20
INGJUT = 100.0                  # stolparnas ingjutning i stenen
SNACKA = 250.0                  # handledarens utstick förbi nedersta stolpen (snäckan)
UTSTICK = 150.0                 # handledarens utstick förbi översta stolpen
SPALT = 2.0                     # svetsspalt vid liggarnas ändar

VARIABLER_BAS = [
    ("Hojd", 900, "mm, handledarens överkant lodrätt över stegframkant (plant räcke: över plattan)"),
    ("Under", 80, "mm, underliggarens mitt lodrätt över framkantslinjen"),
    ("Mellan", 70, "mm, fritt mellan handledare och överliggare"),
]


def noter_bas(v, n, a_deg, cc, fri, stolp_cc):
    return ["PRELIMINÄR RITNING – OFFERTUNDERLAG, EJ FÖR TILLVERKNING",
            "UNDERLAG: FOTON OCH MÅTT I MAIL FRÅN P. HELLSTONE 2026-10-17, UTFÖRANDE EFTER KUNDENS FÖREBILDER",
            "STEGHÖJD %g OCH STEGDJUP %g ÄR ANTAGNA – ALLA MÅTT KONTROLLMÄTS PÅ PLATS FÖRE TILLVERKNING" % (v["Steghojd"], v["Stegdjup"])
            if n else "LÄNGDEN %g ÄR ANTAGEN – ALLA MÅTT KONTROLLMÄTS PÅ PLATS FÖRE TILLVERKNING" % v["Langd"],
            "±0 = NEDRE PLATTANS ÖVERSIDA, RÄCKESHÖJD %g LODRÄTT ÖVER STEGFRAMKANT, LUTNING %.1f°" % (v["Hojd"], a_deg)
            if n else "±0 = PLATTANS ÖVERSIDA, RÄCKESHÖJD %g" % v["Hojd"],
            "STOLPAR st: FS20, %g mm NEDGJUTNA I KÄRNBORRADE HÅL Ø40 I GRANITEN (INGÅR I LÄNGDEN), c/c MAX %.0f" % (INGJUT, stolp_cc),
            "HANDLEDARE hl/1 PL40*8 PLANT, NEDRE ÄNDEN AVSLUTAS MED SMIDD SNÄCKA (UTSTICK %g, EJ RITAD)" % SNACKA,
            "SPJÄLOR sp D12 MELLAN LIGGARNA, c/c %.0f, FRI ÖPPNING %.0f (< 100)" % (cc, fri),
            "SVETS: STOLPAR MOT HANDLEDARE a4, LIGGARE MOT STOLPAR a3 RUNT OM, SPJÄLOR MOT LIGGARE a3 RUNT OM",
            "YTBEHANDLING: VARMFÖRZINKAD OCH PULVERLACKAD SVART RAL 9005 (ANTAGET, ENLIGT BESTÄLLNING)"]


def bygg_racke(k, v, max_stolp_cc=1200.0):
    n = int(v.get("Steg", 0))
    Sh, Sd = (v["Steghojd"], v["Stegdjup"]) if n else (0.0, 1.0)
    H, under, mellan = v["Hojd"], v["Under"], v["Mellan"]
    t = Sh / Sd if n else 0.0                         # lutning
    a = math.atan(t)
    c = math.cos(a)
    nos = lambda x: (Sh if n else 0.0) + x * t        # framkantslinjen
    hl_ok = lambda x: nos(x) + H                      # handledarens överkant
    hl_uk = lambda x: hl_ok(x) - HL_T / c             # handledarens underkant (lodrätt)
    hl_mitt = lambda x: hl_ok(x) - HL_T / 2 / c
    ol_mitt = lambda x: hl_uk(x) - mellan - OL_H / 2 / c
    ol_uk = lambda x: ol_mitt(x) - OL_H / 2 / c
    ul_mitt = lambda x: nos(x) + under
    ul_ok = lambda x: ul_mitt(x) + UL_T / 2 / c

    # ---- stolpar: (x, z vid stenens översida)
    if n:
        stolpar = [((kk - 1) * Sd + Sd / 2, kk * Sh) for kk in range(1, n + 1, 2)]
        stolpar.append(((n - 1) * Sd + 250.0, n * Sh))
    else:
        L = v["Langd"]
        m = max(2, int(math.ceil((L - 200.0) / max_stolp_cc)) + 1)
        stolpar = [(100.0 + (L - 200.0) * i / (m - 1), 0.0) for i in range(m)]
    stolp_cc = max(b[0] - a_[0] for a_, b in zip(stolpar, stolpar[1:]))

    def fs20(L):
        def bygg(d):
            sk = d.skiss("Tvarsnitt", "XY")
            sk.rektangel(ST_A, ST_A, namn=("Sida", "Sida2"))
            d.kloss(sk, round(L, 2), "Langd")
        return bygg

    langder = {}
    for i, (x, z) in enumerate(stolpar):
        z0 = z - INGJUT
        z1 = hl_uk(x) + ST_A / 2 * t                  # räcker upp till handledarens underkant på uppsidan
        Lp = round(z1 - z0, 1)
        pos = langder.setdefault(Lp, "st/%d" % (len(langder) + 1))
        st = k.egen(pos, "FS%g" % ST_A, fs20(Lp), mitt=(x, 0, z0), material=STAL, huvuddel=(i == 0))
        if t:
            k.gera(st, (x - ST_A / 2, 0, hl_uk(x - ST_A / 2)), (x + ST_A / 2, 0, hl_uk(x + ST_A / 2)))

    # ---- handledare, plant PL40*8 längs lutningen, snäcka förbi nedersta stolpen
    x0, x1 = stolpar[0][0] - SNACKA, stolpar[-1][0] + UTSTICK
    k.balk("hl/1", "PL%g*%g" % (HL_T, HL_B), (x0, 0, hl_mitt(x0)), (x1, 0, hl_mitt(x1)), upp=(0, 0, 1), material=STAL)

    # ---- liggare och spjälor per fack
    cc_max, fri_min = 0.0, 1e9
    snitt_x = None
    lpos = {}                                          # (profil, längd) -> positionsnummer: lika liggare får samma

    def lnr(profil, L):
        return lpos.setdefault((profil, round(L, 1)), "l/%d" % (len(lpos) + 1))
    for (xa, _), (xb, _) in zip(stolpar, stolpar[1:]):
        fa, fb = xa + ST_A / 2, xb - ST_A / 2         # stolparnas sidor
        # överliggare på högkant: lodräta ändar mot stolparna (gering), byggs med spalt och kapas
        prof = "PL%g*%g" % (OL_T, OL_H)
        ol = k.balk(lnr(prof, (fb - fa - 2 * SPALT) / c), prof, (fa + SPALT, 0, ol_mitt(fa + SPALT)), (fb - SPALT, 0, ol_mitt(fb - SPALT)),
                    upp=(0, 1, 0), material=STAL)
        if t:
            for xf in (fa + SPALT, fb - SPALT):
                k.gera(ol, (xf, 0, ol_mitt(xf) - 40), (xf, 0, ol_mitt(xf) + 40))
        # underliggare plant: ändarna vinkelrätt mot lutningen, spalt så hörnen inte går in i stolpen
        g = SPALT + UL_T / 2 * t
        prof = "PL%g*%g" % (UL_T, UL_B)
        k.balk(lnr(prof, (fb - fa - 2 * g) / c), prof, (fa + g, 0, ul_mitt(fa + g)), (fb - g, 0, ul_mitt(fb - g)), upp=(0, 0, 1), material=STAL)
        # spjälor: fri öppning < 100 vågrätt
        w = fb - fa
        m = int(math.ceil((w - 100.0) / (100.0 + SPJ_D)))
        fri = (w - m * SPJ_D) / (m + 1)
        cc_max, fri_min = max(cc_max, fri + SPJ_D), min(fri_min, fri)
        for j in range(m):
            x = fa + fri * (j + 1) + SPJ_D * (j + 0.5)
            if snitt_x is None and j == 1:
                snitt_x = x
            zb, zt = ul_ok(x), ol_uk(x)
            r = SPJ_D / 2
            sp = k.balk("sp/1", "D%g" % SPJ_D, (x, 0, zb - r * t), (x, 0, zt + r * t), material=STAL)
            if t:
                k.gera(sp, (x - r, 0, ul_ok(x - r)), (x + r, 0, ul_ok(x + r)))
                k.gera(sp, (x - r, 0, ol_uk(x - r)), (x + r, 0, ol_uk(x + r)))
    noter = noter_bas(v, n, math.degrees(a), cc_max, fri_min, stolp_cc)
    k.ritning(vyer=["fram"], snitt=[dict(namn="A", axel="x", varde=round(snitt_x or stolpar[0][0] + 100, 1), mot="-")], noter=noter)
    return dict(stolpar=stolpar, lutning=math.degrees(a), cc=cc_max, fri=fri_min)
