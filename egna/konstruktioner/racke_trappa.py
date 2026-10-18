"""Räcke R/1 längs trappans öppna sida (mot gården) hos P. Hellstone: snett smidesräcke i stilen från kundens
förebilder, se egna/racke_bas.py. Trappan enligt foton: granitsteg längs husväggen, 4 steghöjder från nedre
plattan upp till entréplanet (antaget steghöjd 150, stegdjup 350 – kontrollmäts). Stolpar på steg 1 och 3 och
på entréplanet, handledaren rak i trappans lutning med snäcka nedtill."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import racke_bas

NAMN = "Räcke trappa"
MARKE = "R/1"
VARIABLER = [
    ("Steg", 4, "antal steghöjder från nedre plattan till entréplanet"),
    ("Steghojd", 150, "mm, steghöjd (antagen)"),
    ("Stegdjup", 350, "mm, stegdjup (antaget)"),
] + racke_bas.VARIABLER_BAS


def bygg(k, v):
    racke_bas.bygg_racke(k, v)
