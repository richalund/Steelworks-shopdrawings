r"""Distanshylsa: rotationskropp med fas på ytterkanterna (Part Design, Revolution + Chamfer).
  python scripts/partdesign.py bygg delar/hylsa.py "<mapp>\Hylsa.FCStd" --png --step
Hylsans axel är Z.
"""
NAMN = "Hylsa"
VARIABLER = [
    ("Ytterdiameter", 40, "mm"),
    ("Innerdiameter", 21, "mm"),
    ("Langd", 50, "mm, längd (Z)"),
    ("Fas", 1, "mm, fas på ytterkanterna"),
]


def bygg(d):
    sk = d.skiss("Halvsnitt", "XZ")                     # skissens x = radie (X), y = Z
    sk.rektangel("(Ytterdiameter - Innerdiameter)/2", "Langd", horn=("Innerdiameter/2", 0), namn=("Godstjocklek", None))
    d.varv(sk, 360, "V", "Hylsa")
    d.fas("Fas", {"cirkel": True, "radie": "Ytterdiameter/2"}, "Fas")
