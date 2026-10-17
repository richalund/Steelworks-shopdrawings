# Steelworks Shopdrawings (freecad-styrning)

En skill för [Claude Code](https://claude.ai/code) som styr **FreeCAD 1.x** från Python och tar fram
färdiga tillverkningsunderlag för smide och plåt:

- **Parametriska delar** i Part Design (plattor, konsoler, flänsar, hylsor, profiler) och bockad plåt med
  SheetMetal-tillägget. Alla mått ligger i kalkylbladet `Variabler` och kan ändras i FreeCAD efteråt.
- **Stålkonstruktioner** i Tekla-stil: balkar, ramar, pelare, räcken med positionsnummer, hålgrupper,
  geringar och materiallista.
- **Tillverkningsritningar** med TechDraw: A3-blad för enstaka delar, A2-sammanställningar med
  positionsbubblor, snitt, måttkedjor, hålangivelser, materiallista och noter. Export till PDF och PNG.
- **DXF-utbredning** till laser och kantpress, med bocklinjer och bocknoter på egna lager, samt en
  tillverkningsgranskning (flänslängd, bockradie, hål mot bock, avlastning, plåtformat).
- **STEP**-export och kontrollutskrift (låda, massa, utbredning, fullt bestämda skisser).

Allt byggs med FreeCADs egna objekt (Body, Sketch, Pad, Pocket, SheetMetal-features), så modellerna går
att redigera vidare för hand. Språket i skill, skript och ritningar är svenska.

Skillen ligger i `.claude/skills/freecad-styrning/` så att den laddas automatiskt när repot öppnas i
Claude Code, lokalt eller i molnet.

## Använda i molnet (claude.ai/code, dator eller mobilapp)

Ingen FreeCAD-installation behövs på egen dator. Allt körs i Claude Codes molncontainer och resultatet
(PNG, PDF, DXF, STEP, FCStd) går att öppna och ladda ner från sessionen.

1. Koppla ditt GitHub-konto till Claude (https://claude.ai/connect-github). Ett publikt repo som det här
   går att köra direkt utan att forka. Vill du spara egna delskript eller resultat i git, forka repot
   först och använd din fork.
2. Starta en ny session på https://claude.ai/code, eller i Claude-appen på telefonen under **Code**, med
   `richalund/Steelworks-shopdrawings` (eller din fork) som repo.
3. Sessionen installerar FreeCAD i bakgrunden när den startar (5–10 minuter, ca 4 GB). Du kan börja
   beskriva vad som ska ritas direkt; Claude väntar in installationen innan första ritningen. Vill du
   slippa väntan varje gång: lägg `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` som
   setup-skript i molnmiljön (Settings → Environments), så sparas installationen i miljöns cache.
4. Skriv t.ex. *"Rita en fotplatta 300×300×15 med fyra hål Ø22 c/c 240 och gör ritning"*. Claude bygger
   modellen, gör ritningen, visar PNG:en och lägger filerna i `ut/`.
5. Första gången frågar Claude efter företagsnamn, adress och signatur till titelblocket.

## Använda lokalt (Windows, egen FreeCAD)

```bash
git clone https://github.com/richalund/Steelworks-shopdrawings
```

Öppna sedan mappen i Claude Code, så används skillen som projektskill. Vill du ha den i alla projekt:
kopiera `.claude/skills/freecad-styrning` till `~/.claude/skills/freecad-styrning`.

Förutsättningar (se `SKILL.md`):

- FreeCAD 1.0.x (letas i `C:\Program Files\FreeCAD*`, annars miljövariabeln `FREECAD_BIN`)
- SheetMetal-tillägget via FreeCADs tilläggshanterare
- Python 3 med `pip install pymupdf` (`ezdxf` frivilligt)
- Linux: `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` installerar FreeCAD 1.1.3,
  SheetMetal, Xvfb och Python-paketen

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
mallens kommentar. I en molnsession kan variablerna läggas i miljöns inställningar så att de följer med
varje session.

## Snabbstart från kommandoraden

```bash
S=.claude/skills/freecad-styrning

# Part Design-del med ritning
python3 $S/scripts/partdesign.py bygg $S/delar/fotplatta.py ut/Fotplatta.FCStd --var Bredd=300 --png --step
python3 $S/scripts/ritning.py ut/Fotplatta.FCStd --namn "Fotplatta" --nummer "FP-01" --foretag "Firma AB"

# Bockad plåt: bygg, ändra, ritning med DXF-utbredning
python3 $S/scripts/datastall.py bygg ut/Datastall.FCStd --png
python3 $S/scripts/datastall.py satt ut/Datastall.FCStd --bredd 400 --png
python3 $S/scripts/ritning.py ut/Datastall.FCStd --namn "Dataställ" --nummer "DS-01" --material S235JR

# Stålkonstruktion med sammanställningsritning (A2, Tekla-stil)
python3 $S/scripts/sammanstallning.py bygg $S/konstruktioner/balkongram.py ut/B1.FCStd --var Langd=2400 --png --step
python3 $S/scripts/sammanstallning.py ritning ut/B1.FCStd --uppdrag 2026-001 --objekt "KV EXEMPEL 1" "Byggbolaget AB" "Exempelgatan 1"
```

Skripten startar FreeCAD minimerat (i molnet i en virtuell skärm), kör jobbet inne i FreeCAD och skriver
loggen löpande. Ett jobb tar 5–10 sekunder plus själva bygget.

## Innehåll

```
CLAUDE.md                        – instruktioner till Claude Code för repot
.claude/settings.json            – SessionStart-hook som installerar FreeCAD i molnsessioner
.claude/hooks/session-start.sh
.claude/skills/freecad-styrning/
  SKILL.md                       – skillen: flöde, regler, kommandon
  scripts/fcapi.py               – startar FreeCAD och kör ett skript som jobb (Windows och Linux/Xvfb)
  scripts/pd.py                  – Part Design-hjälpare (skisser, Pad, Pocket, Hole, Fillet, mönster)
  scripts/partdesign.py          – bygg / satt / las för Part Design-delar
  scripts/stal.py                – profiltabeller, Konstruktion, hålgrupper, gering, materiallista
  scripts/sammanstallning.py     – bygg konstruktion + A2-sammanställningsritning
  scripts/plat.py, datastall.py  – SheetMetal, utbredning, DXF, exempeldel
  scripts/ritning.py             – A3-ritning för plåt och Part Design, DXF-utbredning
  scripts/dfm.py, granska.py     – tillverkningsgranskning för kantpress och laser
  scripts/rendera_pdf.py         – PDF till PNG för granskning
  scripts/installera_linux.sh    – installation på Linux / molnsession
  delar/                         – delskript: fotplatta, konsol, hylsa, H-profil
  konstruktioner/                – konstruktionsskript: balkongram, pelare
  mallar/                        – A3.svg och A2_tekla.svg (TechDraw-mallar, redigerbara fält)
  references/                    – ritningskonventioner, Part Design-API, fällor i FreeCAD 1.0.1
ut/                              – genererade filer (ignoreras av git)
```

## Licens

MIT, se `LICENSE`. FreeCAD är LGPL och ingår inte i repot.
