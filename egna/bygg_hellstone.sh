#!/bin/bash
# Bygger P. Hellstones räcken, grind och översikt, ritar sammanställningarna, efterbehandlar (korta
# hänvisningar, detaljblad 1:2) och renderar 3D-bilder. Kör från repots rot: bash egna/bygg_hellstone.sh
set -e
S=.claude/skills/freecad-styrning/scripts/sammanstallning.py
OBJ=("Patrik Hellstone, 0733 41 42 21" "Adress enligt beställare")
kor() {   # skript, utfil, objektrad 1
  echo "== $2"
  python3 $S bygg egna/konstruktioner/$1.py ut/$2.FCStd --png --step | grep -E "^Delar|Krock|Skisser|OBS|rror" || true
  python3 $S ritning ut/$2.FCStd --uppdrag OFFERT --objekt "$3" "${OBJ[@]}" --antal 1 --hal 14 --svets 3.0 | grep -E "OBS|rror" || true
  python3 egna/ritning_detaljer.py ut/$2.FCStd | grep -E "Positionsbubblor|Blad 2|Snitt|OBS|rror|PDF" || true
}
kor racke_r1_ovre R1_Racke_ovre_lopp "RÄCKE ÖVRE LOPP, VILLA"
kor racke_r2_nedre_vanster R2_Racke_nedre_vanster "RÄCKE NEDRE LOPP VÄNSTER, VILLA"
kor racke_r3_nedre_hoger R3_Racke_nedre_hoger "RÄCKE NEDRE LOPP HÖGER + VILPLAN, VILLA"
kor grind G1_Grind "GRIND VID ENTRÉTRAPPA, VILLA"
echo "== T1"
python3 $S bygg egna/konstruktioner/trappa_oversikt.py ut/T1_Trappa_oversikt.FCStd | grep -E "^Delar|Krock|Skisser|OBS|rror" || true
python3 egna/rendera.py ut/T1_Trappa_oversikt.FCStd | grep -E "PNG|rror" || true
