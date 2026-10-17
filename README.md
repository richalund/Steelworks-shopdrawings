# Steelworks Shopdrawings (freecad-styrning)

En skill för [Claude Code](https://claude.ai/code) (och andra agenter som läser `SKILL.md`) som styr
**FreeCAD 1.x** från Python och tar fram färdiga tillverkningsunderlag för smide och plåt:

- **Parametriska delar** i Part Design (plattor, konsoler, flänsar, hylsor, profiler) och bockad plåt med
  SheetMetal-tillägget. Alla mått ligger i kalkylbladet `Variabler` och kan ändras i FreeCAD efteråt.
- **Stålkonstruktioner** i Tekla-stil: balkar, ramar, pelare, räcken med positionsnummer, hålgrupper,
  geringar och materiallista (`scripts/stal.py`, `konstruktioner/*.py`).
- **Tillverkningsritningar** med TechDraw: A3-blad för enstaka delar, A2-sammanställningar med
  positionsbubblor, snitt, måttkedjor, hålangivelser, materiallista och noter. Export till PDF och PNG.
- **DXF-utbredning** till laser och kantpress, med bocklinjer och bocknoter på egna lager, samt en
  tillverkningsgranskning (flänslängd, bockradie, hål mot bock, avlastning, plåtformat).
- **STEP**-export och kontrollutskrift (låda, massa, utbredning, fullt bestämda skisser).

Allt byggs med FreeCADs egna objekt (Body, Sketch, Pad, Pocket, SheetMetal-features), så modellerna går
att redigera vidare för hand. Språket i skill, skript och ritningar är svenska.

## Installation

**Claude Code, lokalt:** kopiera repot till din skillmapp.

```bash
git clone https://github.com/richalund/steelworks-shopdrawings ~/.claude/skills/freecad-styrning
```

eller med skills-CLI:t: `npx skills add richalund/steelworks-shopdrawings`.

**Claude Code, i ett projekt:** lägg mappen under `.claude/skills/freecad-styrning` i repot, så laddas
skillen för alla som öppnar projektet, även i molnsessioner.

**Förutsättningar** (se `SKILL.md`):

- FreeCAD 1.0.x (Windows: `C:\Program Files\FreeCAD*`, annars miljövariabeln `FREECAD_BIN`)
- SheetMetal-tillägget via FreeCADs tilläggshanterare
- Python 3 med `pip install pymupdf` (`ezdxf` frivilligt)
- Linux: `bash scripts/installera_linux.sh` installerar FreeCAD 1.1.3, SheetMetal, Xvfb och Python-paketen

## Företagsuppgifter i titelblocket

Mallarna i `mallar/` är neutrala. Sätt företagsnamn, adress och signaturer en gång med miljövariabler:

```
FC_FORETAG="Firma AB"
FC_ADRESS="Gatan 1|123 45 Staden|firma.se 08-123 45 67"
FC_RITAD_AV=AB
FC_HANDLAGGARE=AB
FC_ANSVARIG="A. Bson"
```

eller per kommando med `--foretag`, `--adress`, `--ritad-av`, `--handlaggare`, `--ansvarig`. Vill du ha en
logga byter du `Foretag`-texten i `mallar/A3.svg` och `mallar/A2_tekla.svg` mot en `<image>`; rutan anges i
mallens kommentar.

## Snabbstart

```bash
# Part Design-del med ritning
python scripts/partdesign.py bygg delar/fotplatta.py ut/Fotplatta.FCStd --var Bredd=300 --png --step
python scripts/ritning.py ut/Fotplatta.FCStd --namn "Fotplatta" --nummer "FP-01"

# Bockad plåt: bygg, ändra, ritning med DXF-utbredning
python scripts/datastall.py bygg ut/Datastall.FCStd --png
python scripts/datastall.py satt ut/Datastall.FCStd --bredd 400 --png
python scripts/ritning.py ut/Datastall.FCStd --namn "Dataställ" --nummer "DS-01" --material S235JR

# Stålkonstruktion med sammanställningsritning (A2, Tekla-stil)
python scripts/sammanstallning.py bygg konstruktioner/balkongram.py ut/B1.FCStd --var Langd=2400 --png --step
python scripts/sammanstallning.py ritning ut/B1.FCStd --uppdrag 2026-001 --objekt "KV EXEMPEL 1" "Byggbolaget AB" "Exempelgatan 1"
```

Skripten startar FreeCAD minimerat, kör jobbet inne i FreeCAD och skriver loggen löpande. Ett jobb tar
5–10 sekunder plus själva bygget.

## Innehåll

```
SKILL.md                     – skillen: flöde, regler, kommandon
scripts/fcapi.py             – startar FreeCAD och kör ett skript som jobb (Windows och Linux/Xvfb)
scripts/pd.py                – Part Design-hjälpare (skisser, Pad, Pocket, Hole, Fillet, mönster)
scripts/partdesign.py        – bygg / satt / las för Part Design-delar
scripts/stal.py              – profiltabeller, Konstruktion, hålgrupper, gering, materiallista
scripts/sammanstallning.py   – bygg konstruktion + A2-sammanställningsritning
scripts/plat.py, datastall.py – SheetMetal, utbredning, DXF, exempeldel
scripts/ritning.py           – A3-ritning för plåt och Part Design, DXF-utbredning
scripts/dfm.py, granska.py   – tillverkningsgranskning för kantpress och laser
scripts/rendera_pdf.py       – PDF till PNG för granskning
scripts/installera_linux.sh  – installation på Linux / molnsession
delar/                       – delskript: fotplatta, konsol, hylsa, H-profil
konstruktioner/              – konstruktionsskript: balkongram, pelare
mallar/                      – A3.svg och A2_tekla.svg (TechDraw-mallar, redigerbara fält)
references/                  – ritningskonventioner, Part Design-API, fällor i FreeCAD 1.0.1
agents/openai.yaml           – gränssnittsmetadata
```

## Licens

MIT, se `LICENSE`. FreeCAD är LGPL och ingår inte i repot.
