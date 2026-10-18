"""Räcke R/3 längs nedre trapploppets högra sida och vilplanets gavel (mot trädgården) hos P. Hellstone, se
egna/trappa_hellstone.py: nedre loppet och vilplanets gavel ligger i linje, så räcket går uppför de 5 stegen
och sedan plant över vilplanet fram till fasaden, med snäcka nedtill och knäck vid vilplanets kant."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))    # egna/ (skillens scripts/ finns redan)
import racke_bas, trappa_hellstone as T

NAMN = "Räcke nedre lopp höger och vilplan"
MARKE = "R/3"
VARIABLER = list(racke_bas.VARIABLER_RACKE)


def parametrar():
    nos, yta = T.linje_nedre(med_vilplan=True)
    g = T.G_NEDRE
    # stolpe mitt under handledarens knäck (60 in på vilplanet); sista sektionen 1300 c/c till stolpen vid fasaden
    x_kn = T.knack_nedre()
    x_sist = x_kn + 1300.0                             # 140 från fasaden
    stolpar = racke_bas.fordela([0.5 * g, x_kn, x_sist], lambda x: T.mitt_steg(x, g, T.N_NEDRE - 1))
    return dict(nos_pkt=nos, yta=yta, stolpar=stolpar, hl_x=(stolpar[0] - racke_bas.SNACKA_RAK, T.Y_FRAM - 20), start="snacka")


def bygg(k, v):
    info = racke_bas.bygg_racke(k, v, **parametrar())
    racke_bas.ritning(k, info, racke_bas.noter("RÄCKE R/3 LÄNGS NEDRE LOPPETS HÖGRA SIDA OCH VILPLANETS GAVEL MOT TRÄDGÅRDEN, GÅNG ±0 – VILPLAN +%g" % T.Z_VILPLAN,
                                    v, info, "snacka", "HANDLEDARENS ÖVRE ÄNDE 20 FRÅN FASADEN",
                                    ["HANDLEDARENS KNÄCK MITT ÖVER STOLPEN %g IN PÅ VILPLANET, DÄRIFRÅN PLANT %.0f ÖVER VILPLANET, UNDERLIGGAREN %g ÖVER STENEN"
                                     % (T.KANT, v["Hojd"] + T.KANT * T.R / T.G_NEDRE, v["Under"])]))
