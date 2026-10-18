"""Räcke R/3 på nedre plattans sida (mot gården) hos P. Hellstone: plant smidesräcke i samma stil som R/1 och
R/2, se egna/racke_bas.py. Från trappans nedre ände (rak ände vid plattans slut, där trappans räcke R/1 tar vid) till plattans hörn mot R/2
(handledaren gerad 45°): längd 1440 (antagen, 60 in från kanten, kontrollmäts)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import racke_bas

NAMN = "Räcke platta sida"
MARKE = "R/3"
VARIABLER = [
    ("Steg", 0, "0 = plant räcke"),
    ("Steghojd", 0, "mm, används ej för plant räcke"),
    ("Stegdjup", 1, "mm, används ej för plant räcke"),
    ("Langd", 1440, "mm, räckets längd till hörnet (handledarens ändar)"),
    ("Hojd", 1000, "mm, handledarens överkant över plattan"),
    ("Under", 80, "mm, underliggarens mitt över plattan"),
    ("Mellan", 70, "mm, fritt mellan handledare och överliggare"),
]


def bygg(k, v):
    racke_bas.bygg_racke(k, v, start="rak", slut="gering", hornmot="R/2")
