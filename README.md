# Steelworks Shopdrawings (freecad-styrning)

En skill för kodagenter ([Claude Code](https://claude.ai/code), OpenAI Codex, GitHub Copilot, Cursor) som tar fram
färdiga tillverkningsunderlag för smide och plåt i **FreeCAD** (licensfritt). Du beskriver vad du vill ha, på vanlig
svenska, och får tillbaka klassiska tillverkningsritningar, DXF till laser och kantpress, 3D-bilder och ett
underlag som kan skickas till en tillverkare för offert.

**Infosida med installation från mobilen för fyra kodagenter och tips om abonnemanget:**
https://richalund.github.io/Steelworks-shopdrawings/

- **Underlag av alla slag:** bara en textbeskrivning, kundens foton och mail, eller befintliga ritningar –
  arkitektens PDF, en gammal ritning, en scannad eller fotad ritning eller en DXF – blir tillverkningsritningar.
- **Delar och konstruktioner:** plattor, konsoler, flänsar och hylsor, bockad plåt med utbredning, balkar,
  ramar, pelare, räcken och trappräcken, grindar och dörrar, beklädnad av plåt, glas, beslag och ornament
  (solfjäder, sicksack, egna SVG-motiv, text och monogram). Beslag, lås och glas söks upp hos leverantörer i ditt
  land och ritas med måtten ur deras datablad.
- **Ritningar:** sammanställningsritningar (A2) med positionsbubblor, snitt, måttkedjor, hålangivelser,
  materiallista, noteringar grupperade under rubriker (eget blad eller gemensam noteringsritning vid behov) och
  detaljblad, A3-ritningar för enstaka delar, plan- och översiktsritningar – på svenska,
  engelska eller kinesiska.
- **Till verkstaden:** DXF per plåtposition (kontur för laser, utbredning med bocklinjer för kantpressen), STEP,
  tillverkningsgranskning av plåt, regelkontroll mot verkstadens gränser.
- **Till kunden och arkitekten:** 3D-bilder med material (mässing, patinerat, svart, förzinkat, rostfritt, glas),
  glTF som öppnas i webbläsaren och IFC till arkitektens modell.
- **Till tillverkaren:** mängdunderlag (vikt, ytor, kap, hål, laser, bock, svets, inköpta komponenter) och ett
  beställningspaket som tillverkaren kan kontrollera och bygga om. När du är nöjd frågar agenten om underlaget ska
  mailas till en tillverkare (anbud@smide.com är förifylld, men du kan skicka det vart du vill). Priser sätts av
  tillverkaren, inte av skillen.
- **Kontroller:** krockar, rörelse för grindar och dörrar (slår bladet i något när det öppnas?), gångjärnslast och
  hållfasthetsöverslag (balk och FEM).

Allt byggs med FreeCADs egna objekt, så modellerna går att öppna och redigera vidare i FreeCAD.

## Kom igång i mobilen (ingen datavana behövs)

Du pratar med agenten på vanlig svenska; den sköter FreeCAD, filer och allt tekniskt. Allt körs i molnet,
så det fungerar likadant från datorn på https://claude.ai/code. Nedan Claude Code; för Codex, Copilot och
Cursor, se infosidan ovan eller [AGENTS.md](AGENTS.md).

1. **Konton:** ett abonnemang på Claude (Pro eller Max) och ett gratis GitHub-konto (https://github.com).
2. **Koppla GitHub:** logga in på https://claude.ai/connect-github med samma konton.
3. **Starta:** öppna Claude-appen på telefonen, gå till fliken **Code**, välj repot
   `richalund/Steelworks-shopdrawings` och starta en ny session.
   Repot är publikt: ingen inbjudan eller fork behövs för att rita. En färdig startprompt att kopiera finns på
   infosidan, liksom en prompt som installerar skillen i ett eget repo.
4. **Beskriv vad du vill ha** och bifoga gärna foton, mått eller en ritning, t.ex. *"Här är tre foton på ett
   trappräcke jag vill offerera. Trappan har 6 steg, ca 1,2 m bred. Rita räcket och gör ritning och 3D-bilder."*
   Första gången frågar Claude efter företagsnamn, adress och signatur till titelblocket, och FreeCAD installeras
   i bakgrunden (10–15 minuter).
5. **Titta på bilderna** Claude visar och be om ändringar som till en ritare: *"stolparna ska stå mitt på stegen"*,
   *"gör handledaren i rör 42"*. Filerna (PDF, DXF, STEP, FreeCAD) laddas ner från sessionen.

Mer om hur man använder skillen, med exempel på vad man kan be om: **[ANVANDA.md](ANVANDA.md)**.
Vill du förbättra skillen: **[BIDRA.md](BIDRA.md)** (skriv *"skicka in förbättringen"* i sessionen).

## Verkstadens egna uppgifter

Skillen är gemensam och generell. Det som hör till en verkstad eller ett uppdrag ligger i mappen `egna/`
(se `egna/README.md`):

- `egna/foretag.json` – företagsnamn, adress, signaturer och logga i titelblocket (Claude frågar första gången).
- `egna/verkstad.json` – verkstadens gränser för regelkontrollen: lagerlängd, plåtformat, lyft,
  förzinkningsbad, transport (mall: `.claude/skills/freecad-styrning/mallar/verkstad.json`).
- `egna/komponenter.json` – beslag, lås och glas som sökts upp hos leverantörer, med datablad och källa.
- `egna/leverans.json` – förifylld mottagare när underlaget skickas (mall: `.../mallar/leverans.json`).
- `egna/konstruktioner/`, `egna/delar/`, `egna/ritningar/`, `egna/ornament/` – uppdragets skript och motiv.

I en molnsession försvinner allt när sessionen stängs. Claude lägger därför upp ritningarna i chatten (en PDF och,
vid många filer, en zip) som du sparar eller delar där du vill. Uppdrag läggs aldrig på en gren: repot är publikt.
Företagsuppgifterna kan läggas som miljövariabler i molnmiljöns inställningar.

## Använda i ditt eget repo eller lokalt på datorn

Samma skill, två andra sätt att få in den. Det publika repot är huvudvägen; de här är för den som vill spara
uppdragen i ett eget privat repo eller slippa installationen i molnet.

- **Skill i claude.ai-kontot (molnet och telefonen, oavsett repo).** Hämta `freecad-styrning.zip` från
  https://github.com/richalund/Steelworks-shopdrawings/releases/latest (byggs automatiskt vid varje ändring av
  skillen) och ladda upp den på claude.ai under **Customize → Skills → + → Upload a skill**. Skillen laddas då i
  varje molnsession, även från ett eget repo, och synkas till Claude Code på datorn med samma konto. Repots hook
  följer inte med: be Claude köra `installera_linux.sh` före första ritningen, eller lägg skriptet som
  installationsskript i molnmiljöns inställningar. *Flödet är ännu inte provat från telefonen; säg till om något
  kärvar.*
- **Lokalt på datorn (Windows, macOS, Linux) med egen FreeCAD.** Ingen väntan på installation, filerna ligger
  kvar på disken och modellen kan öppnas direkt i FreeCAD. Installera skillen i alla projekt som plugin i
  Claude Code:

  ```
  /plugin install freecad-styrning --marketplace richalund/Steelworks-shopdrawings
  ```

  eller klona repot och öppna mappen. FreeCAD 1.x, SheetMetal 0.7.24 och `pip install pymupdf ezdxf` behövs;
  be Claude installera dem om du vill slippa göra det själv. Egna uppgifter och skript läggs i `egna/` i det
  projekt du jobbar i.

## Profilmått och materialkvaliteter verifieras mot öppna källor

Profilmått (IPE, HEA, HEB, HEM, UPE, VKR/RHS/SHS, KKR, rör, L) hämtas från
[Steel_Section_Database](https://github.com/ulmewix/Steel_Section_Database) (EN 10365, EN 10219-2, EN 10210-2)
och nominellt fy/fu för S-kvaliteter från [eurocodeapplied.com](https://eurocodeapplied.com/design/en1993/steel-design-properties)
(EN 1993-1-1 tab. 3.1). Ritningen anger var måtten och materialet är verifierade, med datum. Mått som inte finns i
någon källa hittas inte på: Claude säger till och söker upp tabellen.

## Innehåll

```
README.md, ANVANDA.md, BIDRA.md  – kom igång, användning, bidrag
AGENTS.md                        – instruktioner till alla kodagenter (Codex, Copilot, Cursor ...)
.claude-plugin/                  – plugin-manifest: installera skillen lokalt i alla projekt
.github/workflows/skill-zip.yml  – bygger freecad-styrning.zip till claude.ai vid varje ändring av skillen
CLAUDE.md                        – Claude Code: läser AGENTS.md och lägger till det som gäller Claude
docs/index.html                  – infosidan (GitHub Pages)
.agents/skills, .github/skills   – länkar till skillen för andra agenter
.cursor/environment.json, .github/workflows/copilot-setup-steps.yml – installation i Cursor och Copilot
egna/                            – verkstadens och uppdragens egna filer
.claude/settings.json, .claude/hooks/session-start.sh – installerar FreeCAD i molnsessionen
.claude/skills/freecad-styrning/
  SKILL.md                       – skillen: flöde, regler, kommandon
  VERSION                        – skillens version (datum)
  scripts/                       – kommandona (sammanstallning, ritning, oversikt, rendera, export, dxf, mangder,
                                   komponenter, regler, paket, rorelse, hallfasthet, underlag, testa ...) och modulerna
  delar/, konstruktioner/        – exempel: fotplatta, konsol, hylsa, H-profil; balkongram, pelare, soffbord,
                                   trappräcke, grind, handdukstork, skåp, solgaller, räcke med ovaler
  mallar/                        – titelblock A3.svg och A2.svg, verkstad.json, leverans.json
  references/                    – verktygen, ritningskonventioner, Part Design-API, fällor i FreeCAD
  tester/referens/               – referensbilder för testerna
.github/                         – PR-mall, granskare (CODEOWNERS), tester i GitHub Actions
ut/                              – genererade filer (ignoreras av git)
```

## Licens

MIT, se `LICENSE`. FreeCAD är LGPL och ingår inte i repot.
