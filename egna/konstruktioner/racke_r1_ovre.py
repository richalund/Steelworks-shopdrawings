"""Räcke R/1 längs övre trapploppets utsida (mot innergården) hos P. Hellstone, se egna/trappa_hellstone.py:
från vilplanets hörn vid nedre loppet, uppför de 4 stegen och längs dörrpodesten fram till husets utbyggnad.
Hörnstolpen på vilplanet delas med R/2, vars handledare svetsas mot den."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import racke_bas, trappa_hellstone as T

NAMN = "Räcke övre lopp"
MARKE = "R/1"
VARIABLER = list(racke_bas.VARIABLER_RACKE)


def parametrar():
    nos, yta = T.linje_ovre()
    x_horn = -T.KANT                                   # hörnstolpen, i linje med R/2
    x_sist = T.X_VAGG - 120                            # 120 från husets utbyggnad
    x_mitt = (T.N_OVRE - 2 + 0.625) * T.G_OVRE          # på fjärde steget: fack 1220 + 1100 (max c/c 1300)
    stolpar = [x_horn, x_mitt, x_sist]
    return dict(nos_pkt=nos, yta=yta, stolpar=stolpar, hl_x=(x_horn - racke_bas.ST_A / 2, T.X_VAGG - 20), start="rak")


def bygg(k, v):
    info = racke_bas.bygg_racke(k, v, **parametrar())
    racke_bas.ritning(k, info, racke_bas.noter("RÄCKE R/1 LÄNGS ÖVRE LOPPETS UTSIDA MOT INNERGÅRDEN, VILPLAN +%g – DÖRRPODEST +%g" % (T.Z_VILPLAN, T.Z_PODEST),
                                    v, info, "rak", "HANDLEDARENS NEDRE ÄNDE KANT I KANT MED HÖRNSTOLPEN, ÖVRE ÄNDE 20 FRÅN HUSETS UTBYGGNAD",
                                    ["HÖRNSTOLPEN st/1 PÅ VILPLANET ÄR GEMENSAM MED R/2 (R/2:S HANDLEDARE OCH FÖLJARE SVETSAS MOT DEN)"]))
