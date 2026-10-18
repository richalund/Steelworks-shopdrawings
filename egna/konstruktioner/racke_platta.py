"""Räcke R/2 på nedre plattans framkant hos P. Hellstone: plant smidesräcke i samma stil som R/1, se
egna/racke_bas.py. Plattan är ca 2,6 m bred enligt mailet; räcket står 60 mm in från kanten och börjar i hörnet
mot R/3 (handledaren gerad 45°) och slutar vid husfasaden: längd 2540 (antagen, kontrollmäts)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import racke_bas

NAMN = "Räcke platta framkant"
MARKE = "R/2"
VARIABLER = [
    ("Steg", 0, "0 = plant räcke"),
    ("Steghojd", 0, "mm, används ej för plant räcke"),
    ("Stegdjup", 1, "mm, används ej för plant räcke"),
    ("Langd", 2540, "mm, räckets längd från hörnet (handledarens ändar)"),
    ("Hojd", 1000, "mm, handledarens överkant över plattan"),
    ("Under", 80, "mm, underliggarens mitt över plattan"),
    ("Mellan", 70, "mm, fritt mellan handledare och överliggare"),
]


def bygg(k, v):
    racke_bas.bygg_racke(k, v, start="gering", slut="rak", hornmot="R/3")
