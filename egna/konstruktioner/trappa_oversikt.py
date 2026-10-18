"""Översikt T/1: P. Hellstones entrétrappa med räckena R/1, R/2 och R/3 på plats, för 3D-visualisering.
Trappan ritas som på fotona (se egna/trappa_hellstone.py): granitsteg på murade blockväggar, övre lopp längs
fasaden med dörrpodest, vilplan med granitram, jämnbrett nedre lopp vinkelrätt ut från fasaden. Bara trappan
och räckena är med (inget hus eller mark). Stenen är referenskroppar utan positionsnummer (syns i 3D men ingår
inte i materiallistan); bara räckena får positionsnummer.

Bygg: sammanstallning.py bygg egna/konstruktioner/trappa_oversikt.py ut/T1_Trappa_oversikt.FCStd --png
Bilder från fler håll: python3 .claude/skills/freecad-styrning/scripts/rendera.py ut/T1_Trappa_oversikt.FCStd --vy ...
"""
import os, sys, importlib.util
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import racke_bas, trappa_hellstone as T

NAMN = "Trappa med räcken"
MARKE = "T/1"
VARIABLER = list(racke_bas.VARIABLER_RACKE)

GRANIT = (0.82, 0.82, 0.80)
BLOCK = (0.43, 0.35, 0.29)
SLAB = 130.0                    # granitstegens tjocklek (= steghöjden)


def referens(k, namn, x0, x1, y0, y1, z0, z1, farg, transparens=0):
    """Referenskropp (låda) i omgivningen: syns i 3D och på planen men saknar positionsnummer."""
    return k.referens(namn, lada=(x0, x1, y0, y1, z0, z1), farg=farg, transparens=transparens)


def racke(modul):
    spec = importlib.util.spec_from_file_location(modul, os.path.join(os.path.dirname(os.path.abspath(__file__)), modul + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.parametrar()


def bygg(k, v):
    B, Zv, Zp = T.BREDD, T.Z_VILPLAN, T.Z_PODEST
    # ---- vilplan: murad kärna och granitram med mittfält
    referens(k, "Ref_Vilplan_mur", T.X_VILPLAN, 0, 0, B, 0, Zv - SLAB, BLOCK)
    ram = 250.0
    referens(k, "Ref_Vilplan_fram", T.X_VILPLAN, 0, B - ram, B, Zv - SLAB, Zv, GRANIT)
    referens(k, "Ref_Vilplan_bak", T.X_VILPLAN, 0, 0, ram, Zv - SLAB, Zv, GRANIT)
    referens(k, "Ref_Vilplan_gavel", T.X_VILPLAN, T.X_VILPLAN + ram, ram, B - ram, Zv - SLAB, Zv, GRANIT)
    referens(k, "Ref_Vilplan_sida", -ram, 0, ram, B - ram, Zv - SLAB, Zv, GRANIT)
    for i in range(3):
        a = T.X_VILPLAN + ram + i * (T.VILPLAN - 2 * ram) / 3
        referens(k, "Ref_Vilplan_mitt%d" % (i + 1), a + 2, a + (T.VILPLAN - 2 * ram) / 3 - 2, ram + 2, B - ram - 2, Zv - SLAB, Zv - 2, GRANIT)
    # ---- övre lopp: murad trappstegsformad blockvägg och granitsteg, dörrpodest
    for kk in range(1, T.N_OVRE):
        x0, x1 = (kk - 1) * T.G_OVRE, kk * T.G_OVRE
        z = Zv + kk * T.R
        referens(k, "Ref_Ovre_mur%d" % kk, x0, x1, 0, B, 0, z - SLAB, BLOCK)
        referens(k, "Ref_Ovre_steg%d" % kk, x0, x1, 0, B, z - SLAB, z, GRANIT)
    referens(k, "Ref_Podest_mur", T.X_PODEST, T.X_VAGG, 0, B, 0, Zp - SLAB, BLOCK)
    referens(k, "Ref_Podest", T.X_PODEST, T.X_VAGG, 0, B, Zp - SLAB, Zp, GRANIT)
    # ---- nedre lopp: granitsteg som breddas mot innergården
    for (kk, y0, y1, x0, x1, z) in T.nedre_steg():
        referens(k, "Ref_Nedre_mur%d" % kk, x0, x1, y0, y1, 0, z - SLAB, BLOCK) if z > SLAB else None
        referens(k, "Ref_Nedre_steg%d" % kk, x0, x1, y0, y1, max(z - SLAB, 0), z, GRANIT)
    # ---- räckena
    y_r1 = B - T.KANT
    x_r2, x_r3 = -T.KANT, T.X_VILPLAN + T.KANT
    racke_bas.bygg_racke(k, v, ursprung=(0, y_r1, 0), prefix="R1 ", **racke("racke_r1_ovre"))
    racke_bas.bygg_racke(k, v, ursprung=(x_r2, T.Y_FRAM, 0), ex=(0, -1, 0), ey=(1, 0, 0), prefix="R2 ", huvuddel=False,
                         **racke("racke_r2_nedre_vanster"))
    racke_bas.bygg_racke(k, v, ursprung=(x_r3, T.Y_FRAM, 0), ex=(0, -1, 0), ey=(1, 0, 0), prefix="R3 ", huvuddel=False,
                         **racke("racke_r3_nedre_hoger"))
    k.ritning(vyer=["fram", "plan"], noter=["ÖVERSIKT – RÄCKEN R/1, R/2, R/3 PÅ ENTRÉTRAPPAN, TRAPPMÅTT ANTAGNA UR FOTON",
                                             "TILLVERKNINGSRITNINGAR: R/1, R/2, R/3, GRIND G/1"])
