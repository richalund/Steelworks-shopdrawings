# Installera på egen dator med en prompt

Du behöver bara Claude Code på datorn (appen för Windows/Mac eller terminalversionen, se
https://claude.ai/code). Ingen kunskap om git, Python eller FreeCAD behövs: Claude Code gör installationen
åt dig och frågar innan den installerar program.

1. Skapa en tom mapp där du vill ha dina ritningar, t.ex. `Dokument\Ritningar`, och öppna den i Claude Code.
2. Klistra in den här prompten:

```
Installera skillen freecad-styrning från https://github.com/richalund/Steelworks-shopdrawings på den här
datorn. Hämta https://raw.githubusercontent.com/richalund/Steelworks-shopdrawings/main/INSTALLATION.md och
följ avsnittet "Instruktion till Claude Code" steg för steg. Fråga mig innan du installerar program.
```

3. Svara på frågorna (om FreeCAD får installeras, företagsnamn, adress och signatur till titelblocket).
4. Prova: *"Rita en fotplatta 300×300×15 med fyra hål Ø22 c/c 240 och gör ritning"*.

Nästa gång öppnar du samma mapp i Claude Code, så finns skillen där. Dina egna ritningar och skript ligger i
mappen `egna/` och `ut/`, skillen ligger i `.claude/skills/freecad-styrning/` och rörs inte.

Vill du i stället köra i molnet (ingen installation, fungerar även från telefonen): se README.md, avsnittet
"Använda i molnet".

---

## Instruktion till Claude Code

Du installerar skillen `freecad-styrning` åt en användare som inte är tekniskt lagd. Arbeta i den mapp
användaren öppnat. Förklara kort vad du gör, fråga innan du installerar program (FreeCAD, Python), och avsluta
med en testritning. Stöter du på fel: försök lösa dem, och förklara annars vad som saknas i vanliga ord.

### 1. Hämta repot
Hämta https://github.com/richalund/Steelworks-shopdrawings till den aktuella mappen så att `.claude/skills/freecad-styrning/`,
`egna/`, `CLAUDE.md` och `README.md` hamnar direkt i mappen (inte i en undermapp).
- Finns `git`: `git clone https://github.com/richalund/Steelworks-shopdrawings .` i en tom mapp (eller klona till en
  tillfällig mapp och flytta innehållet). Behåll `.git` så att skillen kan uppdateras med `git pull`.
- Saknas `git`: ladda ner https://github.com/richalund/Steelworks-shopdrawings/archive/refs/heads/main.zip, packa
  upp och flytta innehållet i `Steelworks-shopdrawings-main/` till mappen.
Mappen blir användarens projektmapp: Claude Code laddar skillen från `.claude/skills/` när mappen är öppen.
Egna konstruktioner och delar läggs i `egna/`, genererade filer i `ut/`. Skillens filer ändras bara genom en
pull request (se SKILL.md, "Eget material, och förbättringar av skillen").

### 2. FreeCAD 1.x
Kontrollera om FreeCAD 1.0 eller senare finns:
- Windows: `C:\Program Files\FreeCAD*\bin\freecad.exe` eller `%LOCALAPPDATA%\Programs\FreeCAD*\bin\freecad.exe`
- macOS: `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD`
- Linux: `freecad` i PATH eller `/opt/freecad/bin/freecad`

Saknas det, fråga användaren och installera:
- Windows: `winget install --id FreeCAD.FreeCAD -e` (annars installationsprogrammet från https://www.freecad.org/downloads.php)
- macOS: `brew install --cask freecad` (annars dmg från freecad.org). Sätt sedan `FREECAD_BIN` till
  `/Applications/FreeCAD.app/Contents/MacOS` i användarens miljö (t.ex. i `~/.zshrc`), eftersom skripten letar
  efter `freecad` i PATH.
- Linux: `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` (FreeCAD 1.1.3 i `/opt/freecad`,
  SheetMetal, Xvfb och Python-paketen i ett svep, 5–15 minuter). Hoppa då över steg 3 och 4.

Starta FreeCAD en gång efter installationen (eller kör `freecadcmd -c "print(1)"`) så att konfigmappen skapas.

### 3. SheetMetal-tillägget (version 0.7.24)
Ta reda på FreeCADs Mod-mapp: kör FreeCADs egen Python,
`freecadcmd -c "import FreeCAD; print(FreeCAD.getUserAppDataDir())"` (Windows: `"C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe"`,
macOS: `/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd`), och lägg tillägget i `<den mappen>/Mod/SheetMetal`:
- med git: `git clone --depth 1 --branch V0.7.24-beta https://github.com/shaise/FreeCAD_SheetMetal "<Mod>/SheetMetal"`
- utan git: ladda ner https://github.com/shaise/FreeCAD_SheetMetal/archive/refs/tags/V0.7.24-beta.zip, packa upp och
  döp mappen till `SheetMetal`.
Går github.com inte att nå: hämta filerna från jsDelivr-spegeln `https://cdn.jsdelivr.net/gh/shaise/FreeCAD_SheetMetal@V0.7.24-beta/<fil>`
(fillista: `https://data.jsdelivr.com/v1/package/gh/shaise/FreeCAD_SheetMetal@V0.7.24-beta/flat`), som `installera_linux.sh` gör.
Kontroll: `<Mod>/SheetMetal/package.xml` innehåller `<version>0.7.24<`. Alternativ för användaren: FreeCAD →
Verktyg → Tilläggshanterare → SheetMetal (senaste versionen fungerar oftast också).

### 4. Python-paket
Skripten körs med datorns vanliga Python 3.10 eller senare (inte FreeCADs). Saknas Python: Windows
`winget install --id Python.Python.3.12 -e`, macOS `brew install python`. Installera sedan:
`python -m pip install pymupdf ezdxf` (Windows: `py -m pip install pymupdf ezdxf`).

### 5. Testritning
Kör från projektmappen (Windows: `python` i stället för `python3`):
```
python3 .claude/skills/freecad-styrning/scripts/partdesign.py bygg .claude/skills/freecad-styrning/delar/fotplatta.py ut/Fotplatta.FCStd --png
python3 .claude/skills/freecad-styrning/scripts/ritning.py ut/Fotplatta.FCStd --namn "Fotplatta" --nummer "FP-01"
```
FreeCAD startar minimerat i ca 10 sekunder per kommando. Visa `ut/Fotplatta_blad1.png` för användaren.
Blir det fel: läs felmeddelandet, kontrollera FreeCAD-sökvägen (`FREECAD_BIN`), SheetMetal-mappen och
Python-paketen, och läs `.claude/skills/freecad-styrning/references/fallor.md`.

### 6. Företagsuppgifter till titelblocket
Kör `python3 .claude/skills/freecad-styrning/scripts/foretag.py visa`. Fråga användaren om företagsnamn,
adress (upp till tre rader), signatur (initialer), handläggare, ansvarig och om en logga (PNG/JPEG) ska
användas. Spara med
`python3 .claude/skills/freecad-styrning/scripts/foretag.py satt --fil egna/foretag.json --foretag "..." --adress "..." "..." --ritad-av XX ...`
och gör om testritningen så att användaren ser sitt titelblock.

### 7. Avsluta
Berätta att allt är klart, att användaren öppnar samma mapp i Claude Code nästa gång, och att man beskriver
vad som ska ritas i vanliga ord, t.ex. *"Rita en konsol 200x150 av 10 mm plåt med två hål Ø14 och gör
ritning med DXF"*. Uppdatering av skillen senare: `git pull` i mappen (eller ny zip), `egna/` och `ut/` påverkas inte.
