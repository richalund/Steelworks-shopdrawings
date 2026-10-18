"""Räcke R/1 längs övre trapploppets utsida (mot innergården) hos P. Hellstone, se egna/trappa_hellstone.py:
från vilplanets hörn vid nedre loppet, uppför de 4 stegen och längs dörrpodesten fram till husets utbyggnad.
Hörnstolpen på vilplanet delas med R/2, vars handledare svetsas mot den."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))    # egna/ (skillens scripts/ finns redan)
import racke_bas, trappa_hellstone as T

NAMN = "Räcke övre lopp"
MARKE = "R/1"
VARIABLER = list(racke_bas.VARIABLER_RACKE)


def parametrar():
    nos, yta = T.linje_ovre()
    x_horn = -T.KANT                                   # hörnstolpen, i linje med R/2
    x_sist = T.X_VAGG - 120                            # 120 från husets utbyggnad
    # stolpe mitt under handledarens knäck (60 in på podesten); mellanstolpar på stegmitt, c/c max 1300
    stolpar = racke_bas.fordela([x_horn, T.knack_ovre(), x_sist], lambda x: T.mitt_steg(x, T.G_OVRE, T.N_OVRE - 1))
    return dict(nos_pkt=nos, yta=yta, stolpar=stolpar, hl_x=(x_horn - racke_bas.ST_A / 2, T.X_VAGG - 20), start="rak")


def bygg(k, v):
    info = racke_bas.bygg_racke(k, v, **parametrar())
    racke_bas.ritning(k, info, racke_bas.noter("RÄCKE R/1 LÄNGS ÖVRE LOPPETS UTSIDA MOT INNERGÅRDEN, VILPLAN +%g – DÖRRPODEST +%g" % (T.Z_VILPLAN, T.Z_PODEST),
                                    v, info, "rak", "HANDLEDARENS NEDRE ÄNDE KANT I KANT MED HÖRNSTOLPEN, ÖVRE ÄNDE 20 FRÅN HUSETS UTBYGGNAD",
                                    ["HANDLEDARENS KNÄCK MITT ÖVER STOLPEN %g IN PÅ PODESTEN, DÄRIFRÅN PLANT %.0f ÖVER PODESTEN, UNDERLIGGAREN %g ÖVER STENEN"
                                     % (T.KANT, v["Hojd"] + T.KANT * T.R / T.G_OVRE, v["Under"]),
                                     "HÖRNSTOLPEN st/1 PÅ VILPLANET ÄR GEMENSAM MED R/2 (R/2:S HANDLEDARE OCH FÖLJARE SVETSAS MOT DEN)"]))
