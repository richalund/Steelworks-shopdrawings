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
- Företagsuppgifterna i titelblocket saknas som standard. Kör
  `python3 .claude/skills/freecad-styrning/scripts/foretag.py visa` före första ritningen; står det SAKNAS,
  fråga användaren (AskUserQuestion-formuläret) om företagsnamn, adress, signatur, handläggare, ansvarig och
  eventuell logga, och spara med `foretag.py satt ...`. Fråga inte igen i samma session.
- Profilmått och materialkvaliteter hämtas från öppna källor på nätet via `scripts/kallor.py` (cache i
  `~/.cache/freecad-styrning/kallor`) och ritningen anger var de är verifierade. Hitta aldrig på mått: finns
  profilen eller kvaliteten inte i någon källa, sök efter tabellen, säg till användaren och lägg in måtten
  med källan i en kommentar.
- Ändra inte skillens filer i `.claude/skills/freecad-styrning/`. Egna konstruktionsskript läggs i
  `egna/konstruktioner/`, delskript i `egna/delar/`, företagsuppgifter i `egna/foretag.json`, hjälpfunktioner
  som saknas i det egna skriptet. Se `egna/README.md`.
