# Steelworks Shopdrawings

Repot innehåller skillen `freecad-styrning` (`.claude/skills/freecad-styrning/SKILL.md`): parametriska
plåt- och stålkonstruktioner i FreeCAD från Python, med tillverkningsritningar (TechDraw, PDF),
DXF-utbredning, sammanställningsritningar i Tekla-stil och STEP.

- I en molnsession installerar SessionStart-hooken FreeCAD i bakgrunden (10–15 min första gången i en
  ny container). Vänta på att `/opt/freecad/bin/freecad` finns innan första ritningen, eller kör
  `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` själv.
- Kör skripten med system-`python3`, inte FreeCADs Python i `/opt/freecad/bin`.
- Lägg allt som genereras (FCStd, PDF, PNG, DXF, STEP) i mappen `ut/` i repot, som är ignorerad av git.
  Visa PNG:erna för användaren efter varje ritning. Vill användaren ha filerna i en Drive-mapp eller
  liknande, kopiera dit dem efteråt.
- Företagsuppgifterna i titelblocket saknas som standard: fråga användaren om företagsnamn, adress
  och signatur första gången och skicka dem med `--foretag`, `--adress`, `--ritad-av` (eller sätt
  `FC_FORETAG`, `FC_ADRESS`, `FC_RITAD_AV`).
- Profilmått och materialkvaliteter hämtas från öppna källor på nätet via `scripts/kallor.py` (cache i
  `~/.cache/freecad-styrning/kallor`) och ritningen anger var de är verifierade. Hitta aldrig på mått: finns
  profilen eller kvaliteten inte i någon källa, sök efter tabellen, säg till användaren och lägg in måtten
  med källan i en kommentar.
