"""Räcke R/3 längs nedre trapploppets högra sida och vilplanets gavel (mot trädgården) hos P. Hellstone, se
egna/trappa_hellstone.py: nedre loppet och vilplanets gavel ligger i linje, så räcket går uppför de 5 stegen
och sedan plant över vilplanet fram till fasaden, med snäcka nedtill och knäck vid vilplanets kant."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import racke_bas, trappa_hellstone as T

NAMN = "Räcke nedre lopp höger och vilplan"
MARKE = "R/3"
VARIABLER = list(racke_bas.VARIABLER_RACKE)


def parametrar():
    nos, yta = T.linje_nedre(med_vilplan=True)
    g = T.G_NEDRE
    x_kn = T.L_NEDRE + 30                              # på vilplanet, vid knäcken
    x_sist = T.Y_FRAM - 120                            # 120 från fasaden
    stolpar = [0.5 * g, 2.5 * g, x_kn, (x_kn + x_sist) / 2, x_sist]
    return dict(nos_pkt=nos, yta=yta, stolpar=stolpar, hl_x=(stolpar[0] - racke_bas.SNACKA_RAK, T.Y_FRAM - 20), start="snacka")


def bygg(k, v):
    info = racke_bas.bygg_racke(k, v, **parametrar())
    racke_bas.ritning(k, info, racke_bas.noter("RÄCKE R/3 LÄNGS NEDRE LOPPETS HÖGRA SIDA OCH VILPLANETS GAVEL MOT TRÄDGÅRDEN, GÅNG ±0 – VILPLAN +%g" % T.Z_VILPLAN,
                                    v, info, "snacka", "HANDLEDARENS ÖVRE ÄNDE 20 FRÅN FASADEN"))
