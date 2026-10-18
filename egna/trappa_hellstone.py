"""Mått för P. Hellstones entrétrappa, tolkade ur fotona trapp1.jpg och trapp2.jpg och mailet 2026-10-17
("150 cm bred, lite under 4 meter lång och ca 2,6 meter bred på den främre delen"). Alla mått är antagna och
kontrollmäts på plats; de används av räckena R/1–R/3 och översikten T/1 så att allt hänger ihop.

Trappan:
- Övre lopp längs fasaden: dörrpodest framför dörren, 4 granitsteg ner till vilplanet. Bredd 1500 ut från
  fasaden, utsidan är en murad blockvägg mot en stenlagd innergård.
- Vilplan (granitram med mittfält) i övre loppets nedre ände, lika djupt som loppet.
- Nedre lopp vinkelrätt ut från fasaden: 5 granitsteg från vilplanets framkant ner till gången, jämnbrett i
  hela loppet (lika brett som vilplanet, 1600), sidorna i linje med vilplanets gavel och övre loppets början.
- 11 lika stigningar à 130 från gården till dörren: vilplanet +780, dörrpodesten +1430.

Koordinater: X längs fasaden (x = 0 där övre loppet börjar vid vilplanet, dörren åt +x), Y ut från fasaden
(fasaden y = 0), Z uppåt (innergården/gången ±0). Räckena står KANT in från stenkanterna.
"""
import math

R = 130.0                      # steghöjd
G_OVRE = 320.0                 # stegdjup övre lopp
G_NEDRE = 350.0                # stegdjup nedre lopp
N_OVRE = 5                     # stigningar vilplan -> dörrpodest (4 steg)
N_NEDRE = 6                    # stigningar gång -> vilplan (5 steg)
BREDD = 1500.0                 # övre loppets bredd = vilplanets djup från fasaden
VILPLAN = 1600.0               # vilplanets längd längs fasaden = nedre loppets översta bredd
PODEST = 1100.0                # dörrpodestens längd längs fasaden
NEDRE_UTBREDNING = 0.0         # nedre loppet jämnbrett (fotot antydde breddning mot innergården)
KANT = 60.0                    # räckets avstånd in från stenkanten

Z_VILPLAN = N_NEDRE * R                                    # 780
Z_PODEST = Z_VILPLAN + N_OVRE * R                          # 1430
X_PODEST = (N_OVRE - 1) * G_OVRE                           # 1280, dörrpodestens framkant
X_VAGG = X_PODEST + PODEST                                 # 2380, husets utbyggnad vid podestens ände
X_VILPLAN = -VILPLAN                                       # -1600, vilplanets gavel (rak sida nedre lopp)
L_NEDRE = (N_NEDRE - 1) * G_NEDRE                          # 1750
Y_FRAM = BREDD + L_NEDRE                                   # 3250, nedersta stegets framkant


def nedre_steg():
    """Nedre loppets steg nerifrån: (k, y0, y1, x0, x1, z_ovansida) med k = 1 nederst."""
    ut = []
    for k in range(1, N_NEDRE):
        y1 = Y_FRAM - (k - 1) * G_NEDRE
        bredd = VILPLAN + (N_NEDRE - k) * NEDRE_UTBREDNING
        ut.append((k, y1 - G_NEDRE, y1, X_VILPLAN, X_VILPLAN + bredd, k * R))
    return ut


# ---- räckeslinjer i räckenas lokala x (uppför): framkantslinjens knäckpunkter och ytan under en stolpe
def linje_ovre():
    """R/1 längs övre loppets utsida, lokal x = global x."""
    nos = [(-G_OVRE, Z_VILPLAN), (X_PODEST, Z_PODEST), (X_VAGG + 1000, Z_PODEST)]

    def yta(x):
        if x < 0:
            return Z_VILPLAN
        if x >= X_PODEST:
            return Z_PODEST
        return Z_VILPLAN + (math.floor(x / G_OVRE) + 1) * R
    return nos, yta


def linje_nedre(med_vilplan):
    """R/2 och R/3 längs nedre loppet, lokal x = Y_FRAM - global y (x = 0 vid nedersta stegets framkant)."""
    nos = [(-G_NEDRE, 0.0), (L_NEDRE, Z_VILPLAN)]
    if med_vilplan:
        nos.append((L_NEDRE + BREDD + 1000, Z_VILPLAN))

    def yta(x):
        if x < 0:
            return 0.0
        if x >= L_NEDRE:
            return Z_VILPLAN
        return (math.floor(x / G_NEDRE) + 1) * R
    return nos, yta
