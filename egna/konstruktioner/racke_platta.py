"""Räcke R/2 på nedre plattans fria kant hos P. Hellstone: plant smidesräcke i samma stil som R/1, se
egna/racke_bas.py. Längd 2600 enligt mailet ("ca 2,6 meter bred på den främre delen") – kontrollmäts; vilka
kanter som ska ha räcke bestäms med kunden."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import racke_bas

NAMN = "Räcke platta"
MARKE = "R/2"
VARIABLER = [
    ("Steg", 0, "0 = plant räcke"),
    ("Steghojd", 0, "mm, används ej för plant räcke"),
    ("Stegdjup", 1, "mm, används ej för plant räcke"),
    ("Langd", 2600, "mm, räckets längd (handledarens ändar)"),
] + [("Hojd", 1000, "mm, handledarens överkant över plattan"), ("Under", 80, "mm, underliggarens mitt över plattan"),
     ("Mellan", 70, "mm, fritt mellan handledare och överliggare")]


def bygg(k, v):
    racke_bas.bygg_racke(k, v)
