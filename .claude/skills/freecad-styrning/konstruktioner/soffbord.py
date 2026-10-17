"""Soffbord i stål med oval glasskiva - efter ett trebent ekbord med oval skiva och Y-formade stag (foto).

Tre utåtlutade ben av rör 26,9x2 (EN 10219) bär en nav-och-ekrar-ram under glaset: ett runt nav Ø100x8 i
mitten och tre stående plattstål PL8*40 ut till benens toppar. På 150 mm höjd ett Y-stag av rör 21,3x2 mot
ett nav Ø80x8. Glasskivan 1000 x 700 x 8 mm (härdat glas) limmas mot nav och ekrar med silikon. Antagna
mått: skivan 1000 x 700, höjd 450, benens toppar på en cirkel R300 (lika ben, ekrar och stag), fotpunkter
12 % längre ut (utåtlutning ca 5°). Rörändarna slutar 2 mm från ekra och ben (svetsspalt) så att inga
delar överlappar.

Koordinater: X = skivans längdriktning, Y = bredd, Z uppåt (golv z = 0). Ramens mått är fasta tal; Langd,
Bredd och Glas i Variabler styr glasskivan.
"""
import math

NAMN = "Soffbord"
MARKE = "SB/1"
VARIABLER = [
    ("Langd", 1000, "mm, glasskivans längd (X)"),
    ("Bredd", 700, "mm, glasskivans bredd (Y)"),
    ("Hojd", 450, "mm, bordets höjd till glasets ovansida"),
    ("Glas", 8, "mm, glasets tjocklek"),
]
RITNING = dict(
    vyer=["plan"],                                            # planvy 1:5; uppställningarna som snitt A och B
    dolda=["plan"],
    snitt=[dict(namn="A", axel="x", varde=0, mot="-"),        # genom nav, ekra och ben vid 90° (bredden 700)
           dict(namn="B", axel="y", varde=0, mot="-")],       # genom navet längs bordet (längden 1000)
    noter=["PRELIMINÄR TESTRITNING UR FREECAD EFTER FOTO AV EKBORD – EJ FÖR TILLVERKNING",
           "GLASSKIVA gl/1 1000x700x8 HÄRDAT, OVAL, POLERAD, SILIKONLIMMAD MOT pl/1, pl/2",
           "SVETS: EKRAR MOT NAV OCH BEN a3 RUNT OM, STAG b/2 MOT NAV OCH BEN a3",
           "BEN UTÅTLUTADE CA 5°, KAPADE PLANT MOT GOLV OCH EKRA, PLASTPLUGG I RÖRÄNDARNA",
           "YTBEHANDLING: PULVERLACK SVART RAL 9005"],
)

R_TOP = 300.0                        # radie till benens toppar (cirkel: lika ben)
SPLAY = 1.12                         # fotpunkter = toppunkter * SPLAY (utåtlutning)
VINKLAR = (90, 210, 330)             # benens lägen (grader från +X)
ROR_BEN, ROR_STAG = 26.9, 21.3         # CHS enligt EN 10219-2
SPALT = 2.0                          # svetsspalt vid rörändarna
EKRA_H = 40.0                        # ekrornas höjd (stående plattstål)
NAV_T = 8.0
Z_STAG = 150.0
STAL = "S235JR"


def bygg(k, v):
    H, g = v["Hojd"], v["Glas"]
    z_glas = H - g                    # glasets undersida
    z_nav = z_glas - NAV_T            # navets undersida
    z_ekra = z_glas - EKRA_H          # ekrornas underkant = benens topp
    # glasskivan (ellips, mått ur Variabler)
    k.skiva("gl/1", "GLAS %g" % g, "Langd", "Bredd", "Glas", mitt=(0, 0, z_glas), material="Glas", huvuddel=True)
    # nav
    k.balk("pl/2", "D100", (0, 0, z_nav), (0, 0, z_glas), material=STAL)
    k.balk("pl/3", "D80", (0, 0, Z_STAG - NAV_T / 2), (0, 0, Z_STAG + NAV_T / 2), material=STAL)
    for vink in VINKLAR:
        a = math.radians(vink)
        px, py = R_TOP * math.cos(a), R_TOP * math.sin(a)          # benets topp (ekrans ände)
        r = math.hypot(px, py)
        ux, uy = px / r, py / r
        # ekra: stående PL8*40 från navets kant (r = 50) till benets topp
        k.plat("pl/1", "PL8*40", mitt=(ux * (50 + r) / 2, uy * (50 + r) / 2, z_glas - EKRA_H / 2), langd=r - 50,
               lriktning=(ux, uy, 0), briktning=(0, 0, 1), material=STAL)
        # ben: rör från golvet (utåt) till ekrans ände, rörets topp centrerat under ekrans ände. Byggs 3 mm
        # längre i båda ändar och kapas plant (k.gera) mot golvet och mot ekran; v = tangentiell riktning så
        # att kapplanen blir vågräta.
        tx, ty = px - ux * ROR_BEN / 2, py - uy * ROR_BEN / 2
        fx, fy = tx * SPLAY, ty * SPLAY
        zt = z_ekra - SPALT
        dx, dy = (fx - tx) / zt * 3, (fy - ty) / zt * 3
        ben = k.balk("b/1", "RÖR%g*2" % ROR_BEN, (fx + dx, fy + dy, -3), (tx - dx, ty - dy, zt + 3), upp=(-uy, ux, 0), material=STAL)
        k.gera(ben, (fx + ux * 30, fy + uy * 30, 0), (fx - ux * 30, fy - uy * 30, 0))
        k.gera(ben, (tx + ux * 30, ty + uy * 30, zt), (tx - ux * 30, ty - uy * 30, zt))
        # stag: rör från navets kant (r = 40) till benets mantelyta på Z_STAG
        s = Z_STAG / z_ekra
        lx, ly = fx + (tx - fx) * s, fy + (ty - fy) * s              # benets axel på staghöjden
        k.balk("b/2", "RÖR%g*2" % ROR_STAG, (ux * 40, uy * 40, Z_STAG), (lx - ux * (ROR_BEN / 2 + SPALT), ly - uy * (ROR_BEN / 2 + SPALT), Z_STAG), material=STAL)
    k.ritning(**RITNING)
