r"""Konsol: L-vinkel med stag, två hål i väggbenet och två i hyllbenet, rundade fria hörn (Part Design).
  python scripts/partdesign.py bygg delar/konsol.py "<mapp>\Konsol.FCStd" --png --step
Koordinater: X = bredd (centrerad), Y = djup ut från väggen, Z = höjd. Väggbenet ligger mot väggen i Y = 0.
"""
NAMN = "Konsol"
VARIABLER = [
    ("Bredd", 100, "mm, konsolens bredd (X)"),
    ("Hojd", 150, "mm, väggbenets höjd (Z)"),
    ("Djup", 200, "mm, hyllbenets djup (Y)"),
    ("Tjocklek", 8, "mm, plåt/plattstång"),
    ("Stag", 90, "mm, stagets ben längs vägg och hylla"),
    ("StagT", 8, "mm, stagets tjocklek"),
    ("HalD", 13, "mm, håldiameter"),
    ("CCVagg", 60, "mm, hålavstånd i väggbenet"),
    ("HalHojd", 115, "mm, väggbenets hål över underkant"),
    ("CCHylla", 60, "mm, hålavstånd i hyllbenet"),
    ("HalDjup", 160, "mm, hyllbenets hål från väggen"),
    ("Hornradie", 10, "mm, fria hörn"),
]


def bygg(d):
    # profilen i YZ-planet: skissens x = Y (djup), y = Z (höjd)
    pr = d.skiss("Profil", "YZ")
    pr.profil([(0, 0), (200, 0), (200, 8), (8, 8), (8, 150), (0, 150)],
              matt={0: "Djup", 1: "Tjocklek", 4: "Tjocklek", 5: "Hojd"})
    d.kloss(pr, "Bredd", "Vinkel", symmetrisk=True)
    st = d.skiss("Stagprofil", "YZ")
    st.profil([(8, 8), (98, 8), (8, 98)], matt={0: "Stag", 2: "Stag"}, start=("Tjocklek", "Tjocklek"))
    d.kloss(st, "StagT", "Stag", symmetrisk=True)
    hv = d.skiss("HalVagg", "XZ")                       # skissens x = X, y = Z
    hv.halbild("HalD", "CCVagg", 0, mitt=(0, "HalHojd"))
    d.ficka(hv, "genom", "VaggHal")
    hh = d.skiss("HalHylla", "XY")
    hh.halbild("HalD", "CCHylla", 0, mitt=(0, "HalDjup"))
    d.ficka(hh, "genom", "HyllHal")
    d.avrunda("Hornradie", [{"parallell": "Y", "lada": ["x", "zmax"]},      # väggbenets övre hörn
                            {"parallell": "Z", "lada": ["x", "ymax"]}],     # hyllbenets främre hörn
              "Hornradier")
