#!/bin/bash
# Bygger P. Hellstones räcken, grind och översikt med skillens verktyg: sammanställningsritningar med detaljblad
# (sammanstallning.py), 3D-bilder (rendera.py) och planritningen R-101 (oversikt.py). Kör från repots rot:
#   bash egna/bygg_hellstone.sh
set -e
S=.claude/skills/freecad-styrning/scripts
OBJ=("Patrik Hellstone, 0733 41 42 21" "Adress enligt beställare")
kor() {   # skript, utfil, objektrad 1
  echo "== $2"
  python3 $S/sammanstallning.py bygg egna/konstruktioner/$1.py ut/$2.FCStd --png --step | grep -E "^Delar|Krock|Skisser|OBS|rror" || true
  python3 $S/sammanstallning.py ritning ut/$2.FCStd --uppdrag OFFERT --objekt "$3" "${OBJ[@]}" --antal 1 --hal 14 --svets 3.0 \
    | grep -E "OBS|rror|Blad 2|bubblor|PDF" || true
}
kor racke_r1_ovre R1_Racke_ovre_lopp "RÄCKE ÖVRE LOPP, VILLA"
kor racke_r2_nedre_vanster R2_Racke_nedre_vanster "RÄCKE NEDRE LOPP VÄNSTER, VILLA"
kor racke_r3_nedre_hoger R3_Racke_nedre_hoger "RÄCKE NEDRE LOPP HÖGER + VILPLAN, VILLA"
kor grind G1_Grind "GRIND VID ENTRÉTRAPPA, VILLA"
echo "== T1"
python3 $S/sammanstallning.py bygg egna/konstruktioner/trappa_oversikt.py ut/T1_Trappa_oversikt.FCStd | grep -E "^Delar|Krock|Skisser|OBS|rror" || true
python3 $S/rendera.py ut/T1_Trappa_oversikt.FCStd --vyer plan --vy innergard:-0.40,-0.82,-0.42 --vy tradgard:0.65,-0.65,-0.38 \
  --vy fram:0,-1,-0.12 | grep -E "PNG|rror" || true
python3 $S/oversikt.py ut/T1_Trappa_oversikt.FCStd egna/ritningar/R-101_Planritning.py --uppdrag OFFERT | grep -E "Översikt|PDF|OBS|rror" || true
