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

## Kom igång (ingen datavana behövs)

Du pratar med Claude på vanlig svenska; Claude sköter FreeCAD, filer och git.

1. **Konto:** logga in på https://claude.ai (ett abonnemang med Claude Code) och koppla ditt GitHub-konto på
   https://claude.ai/connect-github. Har du inget GitHub-konto: skapa ett gratis på https://github.com.
2. **Starta:** öppna https://claude.ai/code (eller Claude-appen på telefonen, fliken **Code**), välj repot
   `richalund/Steelworks-shopdrawings` och starta en ny session.
3. **Beskriv vad du vill ha** och bifoga gärna foton och mått, t.ex. *"Här är tre foton på ett trappräcke jag
   vill offerera. Trappan har 6 steg, ca 1,2 m bred. Rita räcket, gör en ritning och 3D-bilder."* Första gången
   frågar Claude efter företagsnamn, adress och signatur till titelblocket. FreeCAD installeras i bakgrunden
   första gången (10–15 minuter); Claude väntar in det.
4. **Titta på bilderna** Claude visar och be om ändringar som till en ritare: *"stolparna ska stå mitt på
   stegen"*, *"gör handledaren i rör 42"*. Filerna (PDF, DXF, STEP, FreeCAD) kan laddas ner från sessionen.
5. **Blev något bättre?** Skriv *"skicka in förbättringen"*. Claude gör det allmängiltigt, testar det och
   skickar ett förslag (en *pull request*) till repot, som granskas innan det blir en del av skillen för alla.
   För det behöver ditt GitHub-konto vara inbjudet till repot (be Richard), annars gör Claude en egen kopia
   (fork) åt dig.

Vill du köra på egen dator i stället: öppna en tom mapp i Claude Code och klistra in prompten i
`INSTALLATION.md`. Claude Code hämtar skillen, installerar FreeCAD och gör en testritning.

## Registrera skillen så den finns i alla dina repon

Vill du slippa ha skillen i varje repo finns två sätt att registrera den en gång:

- **Lokalt, som plugin (alla projekt på datorn).** I Claude Code:

  ```
  /plugin install freecad-styrning --marketplace richalund/Steelworks-shopdrawings
  ```

  Välj "Install for you" så gäller den i alla mappar du öppnar, och anropas som `/freecad-styrning:freecad-styrning`.
  Uppdatera med `/plugin update freecad-styrning@steelworks-shopdrawings`. FreeCAD, SheetMetal och
  Python-paketen installeras som i `INSTALLATION.md`. Plugins laddas inte i molnsessioner.
- **I ditt claude.ai-konto (molnet, telefonen och datorn).** Ladda ner `freecad-styrning.zip` från
  https://github.com/richalund/Steelworks-shopdrawings/releases/latest och ladda upp den på claude.ai under
  **Customize → Skills → + → Upload a skill**. Skillen följer då med i varje molnsession oavsett repo, och
  synkas till Claude Code på datorn när du är inloggad med samma konto. I molnet installerar Claude FreeCAD
  med `installera_linux.sh` på begäran (10–15 min), eftersom repots hook inte följer med.

Egna skript och `foretag.json` lägger du i det projekt du jobbar i, som beskrivs i `egna/README.md`.

## Använda i molnet (claude.ai/code, dator eller mobilapp)

Ingen FreeCAD-installation behövs på egen dator. Allt körs i Claude Codes molncontainer och resultatet
(PNG, PDF, DXF, STEP, FCStd) går att öppna och ladda ner från sessionen.

1. Koppla ditt GitHub-konto till Claude (https://claude.ai/connect-github). Ett publikt repo som det här
   går att köra direkt utan att forka. Vill du spara egna delskript eller resultat i git, forka repot
   först och använd din fork.
2. Starta en ny session på https://claude.ai/code, eller i Claude-appen på telefonen under **Code**, med
   `richalund/Steelworks-shopdrawings` (eller din fork) som repo.
3. Sessionen installerar FreeCAD i bakgrunden när den startar (10–15 minuter, ca 4 GB). Du kan börja
   beskriva vad som ska ritas direkt; Claude väntar in installationen innan första ritningen. Vill du
   slippa väntan varje gång: lägg `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` som
   setup-skript i molnmiljön (Settings → Environments), så sparas installationen i miljöns cache.
4. Skriv t.ex. *"Rita en fotplatta 300×300×15 med fyra hål Ø22 c/c 240 och gör ritning"*. Claude bygger
   modellen, gör ritningen, visar PNG:en och lägger filerna i `ut/`.
5. Första gången frågar Claude efter företagsnamn, adress, signatur och logga till titelblocket och sparar
   dem för resten av sessionen (`scripts/foretag.py`).

## Egna skript och förbättringar av skillen

Skillen är generisk och ska kunna uppdateras från det här repot. Det som görs för ett uppdrag ligger därför
utanför den, i `egna/`: konstruktionsskript i `egna/konstruktioner/`, delskript i `egna/delar/`, ritskript för
översikter i `egna/ritningar/`, företagsuppgifter och logga i `egna/foretag.json`. Se `egna/README.md`.

Det som fler har nytta av (en buggfix, ett nytt verktyg, en ny fälla, en ritningskonvention) skickas in till
skillen som en pull request: Claude gör det allmängiltigt på en egen gren, kör `scripts/testa.py` (bygger och
ritar alla exempel) och öppnar PR:en med mallen i `.github/pull_request_template.md`. Det bästa sättet att
utveckla skillen är att använda den på riktiga jobb – rita något du har fotat – och skicka in det som saknades.
I en fork följer `egna/` med mellan sessionerna, och skillen uppdateras genom att hämta in `main` från det här
repot utan konflikter.

## Använda lokalt (Windows, macOS, Linux)

Enklast: öppna en tom mapp i Claude Code och klistra in prompten i `INSTALLATION.md`. Den innehåller också
en steg-för-steg-instruktion som Claude Code följer: hämta repot, installera FreeCAD 1.x, SheetMetal och
Python-paketen, göra en testritning och fråga efter företagsuppgifterna.

För hand:

```bash
git clone https://github.com/richalund/Steelworks-shopdrawings
```

Öppna sedan mappen i Claude Code, så används skillen som projektskill. Vill du ha den i alla projekt:
kopiera `.claude/skills/freecad-styrning` till `~/.claude/skills/freecad-styrning`.

Förutsättningar (se `SKILL.md` och `INSTALLATION.md`):

- FreeCAD 1.0.x eller senare (Windows: letas i `C:\Program Files\FreeCAD*`; macOS/Linux: `freecad` i PATH;
  annars miljövariabeln `FREECAD_BIN`)
- SheetMetal-tillägget 0.7.24 (tilläggshanteraren eller `Mod/SheetMetal`)
- Python 3.10+ med `pip install pymupdf ezdxf`
- Linux: `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` installerar allt (FreeCAD 1.1.3,
  SheetMetal, Xvfb och Python-paketen)

## Företagsuppgifter i titelblocket

Mallarna i `mallar/` är neutrala. Första gången frågar Claude efter företagsnamn, adress, signatur och
eventuell logga och sparar svaren med `scripts/foretag.py`; sedan används de automatiskt:

```bash
python3 $S/scripts/foretag.py visa
python3 $S/scripts/foretag.py satt --foretag "Firma AB" --adress "Gatan 1" "123 45 Staden" "firma.se 08-123 45 67" \
        --ritad-av AB --handlaggare AB --ansvarig "A. Bson" --logga logga.png
```

Uppgifterna hamnar i `foretag.json` (arbetsmappen eller `~/.config/freecad-styrning/`, på Windows
`%APPDATA%\freecad-styrning\`). Loggan (PNG/JPEG) bäddas in i titelblocket i stället för namnet. Allt går
också att ge per kommando (`--foretag`, `--adress`, `--ritad-av`, `--handlaggare`, `--ansvarig`, `--logga`)
eller med miljövariablerna `FC_FORETAG`, `FC_ADRESS` (rader åtskilda med `|`), `FC_RITAD_AV`,
`FC_HANDLAGGARE`, `FC_ANSVARIG`, `FC_LOGGA`.

I en molnsession försvinner `foretag.json` med containern. Vill du slippa frågan varje gång: lägg
miljövariablerna i molnmiljöns inställningar (Settings → Environments), eller forka repot privat och lägg
`foretag.json` och loggan i forken (filen är gitignorerad, ta bort raden i `.gitignore` i så fall).

## Profilmått och materialkvaliteter verifieras mot öppna källor

`scripts/kallor.py` hämtar profilmått (IPE, HEA, HEB, HEM, UPE, VKR/RHS/SHS, KKR, rör, L) från
[Steel_Section_Database](https://github.com/ulmewix/Steel_Section_Database) (EN 10365, EN 10219-2,
EN 10210-2, MIT) och nominellt fy/fu för S-kvaliteter från
[eurocodeapplied.com](https://eurocodeapplied.com/design/en1993/steel-design-properties) (EN 1993-1-1
tab. 3.1: EN 10025-2…6, EN 10210-1, EN 10219-1). FreeCAD:s egen profiltabell och materialkort är reserv, och
sist de inbyggda tabellerna. Svaren cachas i `~/.cache/freecad-styrning/kallor` i 30 dagar. Ritningen anger
var måtten och materialet är verifierade, med datum, i noterna:

```
PROFILMÅTT ENL. EN 10365:2017 VERIFIERADE MOT GITHUB.COM/ULMEWIX/STEEL_SECTION_DATABASE 2026-10-17.
S355J2 ENL. EN 10025-2: fy 355 MPa, fu 490 MPa (t ≤ 40 mm). VERIFIERAT MOT EUROCODEAPPLIED.COM (EN 1993-1-1 TAB. 3.1) 2026-10-17.
```

```bash
python3 $S/scripts/kallor.py profil UPE140 "VKR100*6.3"     # mått, kg/m och källa
python3 $S/scripts/kallor.py material S355J2 --t 12         # fy, fu, standard och källa
python3 $S/scripts/kallor.py status                         # cache och källor
```

`FC_KALLOR=offline` stänger av nätet (cache och inbyggda tabeller), `--utan-kallor` tar bort noterna.

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
INSTALLATION.md                  – installera på egen dator med en prompt (instruktion som Claude Code följer)
CLAUDE.md                        – instruktioner till Claude Code för repot
.claude-plugin/                  – plugin- och marketplace-manifest (installera som plugin lokalt)
.github/workflows/skill-zip.yml  – bygger freecad-styrning.zip till claude.ai vid push
.github/pull_request_template.md – mall för bidrag till skillen
egna/                            – användarens egna konstruktioner, delar och företagsuppgifter
.claude/settings.json            – SessionStart-hook som installerar FreeCAD i molnsessioner
.claude/hooks/session-start.sh
.claude/skills/freecad-styrning/
  SKILL.md                       – skillen: flöde, regler, kommandon
  scripts/fcapi.py               – startar FreeCAD och kör ett skript som jobb (Windows och Linux/Xvfb)
  scripts/pd.py                  – Part Design-hjälpare (skisser, Pad, Pocket, Hole, Fillet, mönster)
  scripts/partdesign.py          – bygg / satt / las för Part Design-delar
  scripts/stal.py                – profiltabeller, Konstruktion, hålgrupper, gering, materiallista
  scripts/kallor.py              – profilmått och materialkvaliteter ur öppna källor, cache, källangivelse
  scripts/foretag.py             – företagsuppgifter och logga till titelblocket (foretag.json)
  scripts/sammanstallning.py     – bygg konstruktion + A2-sammanställningsritning med detaljblad
  scripts/racke.py               – räcken och trappräcken (stolpar, handledare, följare, spjälor, snäcka)
  scripts/rendera.py             – 3D-bilder från flera håll
  scripts/oversikt.py            – översikts- och planritning (GA) med ritskript
  scripts/testa.py               – bygger och ritar alla exempel (kör före en pull request)
  scripts/plat.py, datastall.py  – SheetMetal, utbredning, DXF, exempeldel
  scripts/ritning.py             – A3-ritning för plåt och Part Design, DXF-utbredning
  scripts/dfm.py, granska.py     – tillverkningsgranskning för kantpress och laser
  scripts/rendera_pdf.py         – PDF till PNG för granskning
  scripts/installera_linux.sh    – installation på Linux / molnsession
  delar/                         – delskript: fotplatta, konsol, hylsa, H-profil
  konstruktioner/                – konstruktionsskript: balkongram, pelare, soffbord, trappräcke
  mallar/                        – A3.svg och A2_tekla.svg (TechDraw-mallar, redigerbara fält)
  references/                    – ritningskonventioner (även räcken), Part Design-API, fällor i FreeCAD
ut/                              – genererade filer (ignoreras av git)
```

## Licens

MIT, se `LICENSE`. FreeCAD är LGPL och ingår inte i repot.
