"""Räcke R/2 längs nedre trapploppets vänstra sida (mot innergården) hos P. Hellstone, se
egna/trappa_hellstone.py: rakt nedför de 5 stegen från R/1:s hörnstolpe på vilplanet (gemensam stolpe i innerhörnet), med snäcka
nedtill. De
nedre stegen breddas förbi räcket ut mot innergården; räcket står på stegen i linje med vilplanets kant."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))    # egna/ (skillens scripts/ finns redan)
import racke_bas, trappa_hellstone as T

NAMN = "Räcke nedre lopp vänster"
MARKE = "R/2"
VARIABLER = list(racke_bas.VARIABLER_RACKE)


def parametrar():
    nos, yta = T.linje_nedre(med_vilplan=False)
    g = T.G_NEDRE
    y_horn = T.BREDD - T.KANT                          # R/1:s hörnstolpe (global y)
    x_topp = T.Y_FRAM - (y_horn + racke_bas.ST_A / 2 + 2)       # handledaren mot hörnstolpens sida
    x_horn = T.Y_FRAM - y_horn                         # R/1:s hörnstolpe: gemensam, byggs inte här
    stolpar = racke_bas.fordela([0.5 * g, x_horn], lambda x: T.mitt_steg(x, g, T.N_NEDRE - 1))
    return dict(nos_pkt=nos, yta=yta, stolpar=stolpar, hl_x=(stolpar[0] - racke_bas.SNACKA_RAK, x_topp), start="snacka",
                extern=(2,))


def bygg(k, v):
    info = racke_bas.bygg_racke(k, v, **parametrar())
    racke_bas.ritning(k, info, racke_bas.noter("RÄCKE R/2 LÄNGS NEDRE LOPPETS VÄNSTRA SIDA MOT INNERGÅRDEN, GÅNG ±0 – VILPLAN +%g" % T.Z_VILPLAN,
                                    v, info, "snacka", "ÖVRE ÄNDEN: HANDLEDARE OCH FÖLJARE SVETSAS MOT R/1:S HÖRNSTOLPE PÅ VILPLANET (INGEN EGEN STOLPE I HÖRNET)"))
