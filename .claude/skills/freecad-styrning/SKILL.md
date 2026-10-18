---
name: freecad-styrning
description: Tar fram tillverkningsritningar för smide och plåt i FreeCAD 1.x (licensfritt) från en textbeskrivning, kundens foton och mail, eller befintliga ritningar (även scannade PDF och DXF). Parametriska delar (Part Design, SheetMetal, variabelblad), stålkonstruktioner, räcken, grindar och dörrar med positionsbubblor, snitt, materiallista och detaljblad, bockad plåt och beklädnad, ornament och text, glas och beslag, DXF till laser och kantpress, STEP, glTF och IFC, 3D-bilder, plan- och översiktsritningar, ritningar på svenska, engelska eller kinesiska, mängdunderlag, regelkontroll, beställningspaket och leverans till en tillverkare, rörelsekontroll för grindar och dörrar och hållfasthetsöverslag (balk, FEM). Använd när användaren vill rita eller offerera ett smide eller en plåtdel, nämner FreeCAD eller en .FCStd-fil, skickar foton, mått eller en ritning att göra tillverkningsritning av, eller vill ha ritning eller DXF utan CAD-licens. Fungerar i alla kodagenter som kan köra Python och kommandon (Claude Code, Codex, Copilot, Cursor).
---

# FreeCAD-styrning

FreeCAD 1.x (testat 1.1.3 på Linux, 1.0.1 på Windows) styrs från vanlig Python. Skripten i `scripts/` är både
startare och jobb: körs de med `python3` startar `fcapi.kor()` FreeCAD med GUI (minimerat, i molnet i en virtuell
skärm), kör samma fil som jobb inne i FreeCAD, skriver ut jobbets logg löpande och avslutar FreeCAD. Ett jobb tar
5–10 s plus själva arbetet. Läs `references/fallor.md` innan något ändras i ritningsdelen. Verktygens API i detalj:
`references/verktyg.md`.

## Förutsättningar
- Skillen körs av en kodagent i en Linux-container i molnet: Claude Code (Claude-appen eller claude.ai/code),
  OpenAI Codex, GitHub Copilot coding agent eller Cursor cloud agents. Inget i skripten är bundet till en viss
  agent. `scripts/installera_linux.sh` installerar FreeCAD 1.1.3 med CalculiX, SheetMetal 0.7.24, Xvfb,
  ifcopenshell, ett typsnitt med kinesiska tecken och PyMuPDF/ezdxf/Pillow (10–15 min första gången, sedan
  sekunder). I Claude Code kör SessionStart-hooken det i bakgrunden; i Codex, Copilot och Cursor står det i
  miljöns installationssteg (se repots `AGENTS.md`). Utan root och sudo installeras det i `~/.local/opt`.
  Vänta på att FreeCAD finns (`/opt/freecad/bin/freecad` eller `~/.local/opt/freecad/bin/freecad`) innan första
  ritningen, eller kör skriptet själv. Starta skripten med system-`python3`, inte FreeCADs Python.
- Nätet: installationen hämtar från GitHub-releaser (micromamba, och SheetMetal från repots release
  "verktyg"), conda.anaconda.org, pypi.org, files.pythonhosted.org och Ubuntus paketarkiv – allt ingår i Claude
  Codes standardnät "Trusted". Reserver: micro.mamba.pm och cdn.jsdelivr.net/data.jsdelivr.com. Källorna
  (kallor.py) hämtas från raw.githubusercontent.com (Trusted) och eurocodeapplied.com (inte i Trusted: lägg till
  domänen för att materialkvaliteterna ska stå som verifierade). Komponenter söks på leverantörers webbplatser
  (webbsök).
- Frågor till användaren: använd agentens frågeformulär om det finns (i Claude Code AskUserQuestion), annars en
  kort fråga i chatten med numrerade alternativ.
- Lokalt fungerar skripten om FreeCAD 1.x finns (`FREECAD_BIN` = bin-mappen), men skillen underhålls för molnet.
- Ha inte samma .FCStd öppen i FreeCAD samtidigt som ett skript sparar den.

## Underlaget: text, foton, mail eller ritningar
Användaren kan börja hur som helst; fråga bara efter det som avgör utförandet och hitta aldrig på mått.
- **Bara text** ("en grind 1000 bred, 1100 hög, VKR40-ram, mässingsplåt med solfjäder"): rita med rimliga,
  vanliga mått för det som inte sägs, skriv antagandena i noterna (`ANTAGET`) och visa bilderna så att användaren
  kan rätta.
- **Foton och mail**: se "Från foton till offertunderlag" nedan.
- **Befintliga ritningar** (arkitektens eller konstruktörens PDF, en gammal ritning, en scannad eller fotad ritning,
  DXF): kör `python3 scripts/underlag.py las <filer> --ut ut/underlag`. Den gör översiktsbilder och rutor i hög
  upplösning per sida, plockar ut texten med läge och talen som ser ut som mått ur vektor-PDF:er, och lager,
  texter och måttvärden ur DXF. Läs översikten och sedan rutorna med Read, zooma med
  `underlag.py zoom <fil> --sida 2 --ruta 0.5,0.6,1,1` och skriv upp varje mått med var det står (sida, ruta).
  Sätt måtten i skriptets VARIABLER, gör tillverkningsritningen och notera underlaget: `UNDERLAG: ARK RITNING A-40-1-201
  REV C`. Mått som inte går att läsa säkert frågas efter. DWG läses inte: be om DXF eller PDF.

## Företagsuppgifter i titelblocket
Mallarna i `mallar/` är neutrala. Uppgifterna sparas en gång med `scripts/foretag.py` och används sedan av
`ritning.py`, `sammanstallning.py` och `oversikt.py` automatiskt:
```
python3 scripts/foretag.py visa
python3 scripts/foretag.py satt --foretag "Firma AB" --adress "Gatan 1" "123 45 Staden" "firma.se 08-123 45 67" \
        --ritad-av AB --handlaggare AB --ansvarig "A. Bson" [--logga logga.png]
```
**Första gången i en session:** kör `foretag.py visa`. Står det SAKNAS, fråga användaren innan första
ritningen, med frågeformuläret om det finns (annars i chatten): företagsnamn, adressrader, signatur (RITAD AV),
handläggare, ansvarig, landet där företaget finns (`--land SE`, för komponenter) och om en logga (PNG/JPEG) ska
användas i stället för namnet.
Spara svaren med `foretag.py satt` och fortsätt. Fråga inte igen i samma session. Enstaka fält kan alltid ges per
kommando (`--foretag`, `--adress`, `--ritad-av`, `--handlaggare`, `--ansvarig`, `--logga`); miljövariablerna
`FC_FORETAG`, `FC_ADRESS` (rader åtskilda med `|`), `FC_RITAD_AV`, `FC_HANDLAGGARE`, `FC_ANSVARIG`, `FC_LOGGA`, `FC_LAND` går
före filen. Filen `foretag.json` söks i `FC_FORETAG_FIL`, `egna/`, arbetsmappen och `~/.config/freecad-styrning/`.
I en molnsession försvinner den med containern; föreslå miljövariablerna i molnmiljöns inställningar (eller
filen i ett eget privat repo). Loggan läggs i en kopia av mallen i utmappen (`_A3_logga.svg`,
`_A2_logga.svg`).

## Källor för profilmått och materialkvaliteter
`scripts/kallor.py` hämtar profilmått och nominella hållfasthetsvärden från öppna databaser på nätet och sparar dem i
en cache (`~/.cache/freecad-styrning/kallor`, 30 dagar). Varje uppgift bär källa, standard och hämtdatum, och
ritningarna anger var måtten och materialet är verifierade (A2 i noterna, A3 efter "Material:").
- Profilmått: Steel_Section_Database (github.com/ulmewix, MIT): EN 10365 (IPE, HEA, HEB, HEM, UPE), EN 10219-2
  (VKR/RHS/SHS/rör), EN 10210-2 (KKR), EN 10056-1 (L). Reserv FreeCAD:s `profiles.csv`, sist de inbyggda tabellerna
  i `stal.py` ("ej verifierade" på ritningen).
- Materialkvaliteter: eurocodeapplied.com (EN 1993-1-1 tab. 3.1) per tjockleksområde; reserv FreeCAD:s materialkort.
- Motsvarande kvaliteter i andra standarder (t.ex. kinesisk GB): `kallor.py motsvarighet S355J2` ger bara rader
  som är verifierade mot en källa (tabellen MOTSVARIGHET). Saknas raden: sök upp standardens jämförelsetabell och
  lägg in den med källan, gissa inte.
- `python3 scripts/kallor.py profil UPE140 "VKR100*6.3"`, `... material S355J2 --t 12`, `... status`, `... uppdatera`;
  `FC_KALLOR=offline` använder bara cache och inbyggt; `--utan-kallor` tar bort noterna.
- Finns profilen, kvaliteten eller en densitet inte i någon källa: hitta inte på. Sök (WebSearch) efter tillverkarens
  eller standardens tabell, säg till användaren och lägg in värdet med källan i en kommentar.

## Eget material, och förbättringar av skillen
Skillen installeras från Steelworks-shopdrawings och ska gå att uppdatera därifrån. Det som görs för ett
uppdrag läggs därför utanför skillen:
- konstruktionsskript i `egna/konstruktioner/`, delskript i `egna/delar/`, ritskript för översikter i
  `egna/ritningar/`, egna ornament (SVG, typsnitt) i `egna/ornament/`, verkstadens gränser i `egna/verkstad.json`,
  komponenter (beslag, glas) i `egna/komponenter.json` och förifylld mottagare i `egna/leverans.json`. Priser
  ingår inte: prissättningen görs av tillverkaren utanför skillen. Skripten tar vilken sökväg som helst:
  `sammanstallning.py bygg egna/konstruktioner/x.py`.
- det som är unikt för uppdraget (kundens mått, förebildens stil, noter) skrivs i det egna skriptet. Delar som
  skillens byggare inte täcker byggs med `k.egen(pos, "TEXT", bygg, mitt=, rot=, material=)`, där `bygg(d)` ritar
  kroppen med Part Design-API:t i `scripts/pd.py`.
- företagsuppgifter i `egna/foretag.json` (eller konfigmappen), genererade filer i `ut/`.
- själva uppdraget (ritningar, modeller, egna skript) lämnas till användaren i chatten (se "Filerna till
  användaren"); det committas aldrig i ett publikt repo.

**Skillen förbättras genom bidrag (pull request), aldrig genom att ändra den i smyg.** När ett uppdrag har
löst något som fler har nytta av (en buggfix, ett nytt verktyg, en ny fälla, en ritningskonvention) gör du så här:
1. Säg till användaren i en mening vad som borde in i skillen och varför, och fråga om du ska skicka in det.
   Användare utan datavana säger bara "ja" eller "skicka in förbättringen"; de ska inte behöva kunna git.
2. Gör förbättringen **generell**: inget kundnamn, inga projektmått, och kundens särdrag (t.ex. en snäcka) blir
   ett val med ett neutralt standardvärde, inte standard. Flytta in hjälpfunktioner från det egna skriptet
   och låt det egna skriptet använda skillens version.
3. Arbeta på en egen gren från `main` (`git checkout -b forbattring/<kort-namn> origin/main`). Uppdatera
   SKILL.md, `references/` (verktyg i `verktyg.md`, fällor i `fallor.md`, konventioner i `smidesritningar.md`) och
   lägg gärna till ett exempel i `delar/` eller `konstruktioner/`. Höj datumet i `VERSION`.
4. Kör `python3 scripts/testa.py` (alla exempel byggs, ritas och körs genom verktygen, ritningarna jämförs med
   referensbilderna) och granska PNG:erna och eventuella `_diff.png` i `ut/test/`. Allt ska vara OK; en avsedd
   ändring av en ritning: `testa.py --uppdatera-referens --bara <exempel>` och de nya referensbilderna med i PR:en.
5. Pusha grenen och öppna en pull request mot `main` i richalund/Steelworks-shopdrawings med mallen i
   `.github/pull_request_template.md` (vad, varför, hur det testats, bilder), och slå på auto-merge så att den
   går in när en granskare godkänt och testerna ("Testa skillen" i GitHub Actions) är gröna. Har användaren
   inte skrivrätt: säg att ägaren behöver bjuda in hen (BIDRA.md), eller forka repot och öppna PR:en från
   forken. Ge användaren länken.
Ändra inte skillen på `main` direkt och blanda inte in uppdragets filer (`egna/`, `ut/`) i PR:en.

**Granska en pull request** (när användaren skriver t.ex. "granska PR 12"): läs beskrivningen och hela diffen,
kontrollera att testerna i GitHub Actions är gröna (annars kör `scripts/testa.py` på PR:ens gren), titta på
bilderna och diffbilderna, och bedöm mot reglerna ovan: allmängiltigt, inga kunduppgifter, testat, dokumenterat,
inga oavsiktliga ändringar i befintliga exempel. Skriv en kort granskning på svenska. Godkänn bara när användaren
ber om det, när hen står i `.github/CODEOWNERS` och inte själv skickat in PR:en; annars "begär ändringar" eller
kommentera. Roller och ägarens inställningar står i BIDRA.md i repots rot.

## Arbetssätt
**Regel: rita alltid med FreeCADs egna verktyg så att användaren kan redigera vidare.**
Modellen ska bestå av kalkylbladet `Variabler`, fullt bestämda skisser med namngivna mått som uttryck mot
bladet och features (Pad, Pocket, Hole, Revolution, Fillet, SheetMetal-features …) – samma objekt som om
detaljen ritats för hand i GUI:t. Aldrig döda former (`Part::Feature` med en Shape från `Part.makeBox`,
booleska operationer i skriptet, importerad STEP) och aldrig egna skriptade objekt eller makron i filen
(SheetMetal-tilläggets objekt är undantaget). Varje stång är en egen Body via `stal.Konstruktion` – aldrig en compound
"för att det går fortare" (204 kroppar byggs på under en minut). Ornament ur SVG och text läggs som låst
geometri (Block-villkor) i en skiss.

1. **Befintlig fil:** läs av (`las`): variabler, skissens status, låda, massa och utbredning med bocknoter.
   Ändra med `satt --<variabel> <värde>` (plåt) eller `partdesign.py satt --var Namn=värde` (Part Design).
2. **Ny del eller konstruktion:** bockad plåt med utbredning: SheetMetal (exempel `scripts/datastall.py`, i en
   sammanställning `k.bockad`/`k.trag`); solid del (platta, konsol, fläns, hylsa): Part Design med ett delskript; flera
   delar (ram, pelare, räcke, grind, dörr, trappa): ett konstruktionsskript med `stal.Konstruktion`.
3. **Ritning:** flera delar: `scripts/sammanstallning.py` (A2, klassisk tillverkningsritning). En del:
   `scripts/ritning.py` (A3; plåt får blad 2 med utbredning och DXF). Översikt/plan: `scripts/oversikt.py`.
4. **Kontrollera alltid** innan leverans: skisserna fullt bestämda, inga krockar, regelkontrollen utan FEL, lådan och
   vikten rimliga, tillverkningsgranskningen utan FEL (plåt), PNG:erna granskade med Read. Jämför med
   `references/smidesritningar.md`.
5. **Leverera** FCStd, PDF, DXF och STEP i `ut/` bredvid varandra, och vid offert mängdunderlaget och
   beställningspaketet. Skriv aldrig över kundens eller användarens originalfil. När användaren är nöjd: fråga om
   underlaget ska skickas till en tillverkare (se "Leverans till en tillverkare"), och lägg upp filerna i
   chatten (se "Filerna till användaren").

## Part Design (solida delar: plattor, konsoler, flänsar, hylsor)
Läs `references/partdesign.md` (API:t i `scripts/pd.py`) innan ett nytt delskript skrivs. Ett delskript i `delar/`
har `NAMN`, `VARIABLER` (blir kalkylbladet `Variabler`) och `bygg(d)`, där skisser ligger på kroppens origoplan och
alla mått är uttryck mot variablerna, t.ex. `sk.rundad_rektangel("Bredd", "Langd", "Hornradie")`,
`d.kloss(sk, "Tjocklek")`, `hal.halbild("HalD", "CCx", "CCy")`, `d.hal(hal, "HalD")`. Mönster: `delar/fotplatta.py`,
`delar/konsol.py`, `delar/hylsa.py`.
```
python3 scripts/partdesign.py bygg delar/fotplatta.py ut/Fotplatta.FCStd --var Bredd=300 --png --step
python3 scripts/partdesign.py satt ut/Fotplatta.FCStd --var HalD=22 --var CCx=240 --png
python3 scripts/ritning.py ut/Fotplatta.FCStd --namn "Fotplatta" --nummer "FP-01" [--sprak en]
```
- Ritningen blir ett blad enligt E-metoden: framvy, ovanvy, sidovy och isometri, totalmåtten plus skissernas
  namngivna mått (namn som börjar på `_` sätts inte ut), hål som `4×⌀18` / `6×M10`, radier som `4×R20`. En platta
  får `_kontur.dxf` för laser.
- Saknas ett mått på ritningen – säg det, eller lägg ett namngivet mått i skissen.

## Sammanställningsritning (A2, klassisk tillverkningsritning)
För balkar, ramar, pelare, konsoler, räcken, grindar och dörrar med flera delar: samma blad som en svensk
sammanställningsritning från ett smidesföretag. Läs `references/smidesritningar.md` först.
Modellen byggs med ett konstruktionsskript (API i `scripts/stal.py`, se `references/verktyg.md`): `NAMN`, `MARKE`
(sammanställningsmärke, t.ex. `B/1`), `VARIABLER`, `RITNING` (vyer, snitt, noter, detaljer, språk), valfritt
`REGLER`, och `bygg(k, v)` med bl.a. `k.balk`, `k.plat`, `k.hal`, `k.gera`, `k.skiva`, `k.egen`, `k.referens`,
`k.bockad`, `k.trag`, `k.glas`, `k.inkop`, `k.rorelse` och `k.utseende`. Varje del blir en Part Design-kropp (eller
SheetMetal-del) med egenskaperna Pos/Profil/Material. Koordinater och längder får vara uttryck mot Variabler.
Mönster: `konstruktioner/balkongram.py`, `pelare.py`, `soffbord.py`, `trappracke.py`, `grind.py`, `handdukstork.py`
(rör med gerade knän, fiskmunskapade pinnar, väggfästen i snitt).
```
python3 scripts/sammanstallning.py bygg konstruktioner/balkongram.py ut/B1.FCStd [--var Langd=2400] --png --step
python3 scripts/sammanstallning.py ritning ut/B1.FCStd --uppdrag 2026-001 --objekt "KV EXEMPEL 1" "Byggbolaget AB" "Exempelgatan 1"
       [--bet A --rev "A|Bultad anslutning|2026-10-07|AB"] [--stomnat A-B/2] [--antal 1] [--not "PRELIMINÄR ..." ...]
       [--snitt A:x=300:-] [--vyer fram,plan] [--skala 10] [--hal 22] [--svets 3.0] [--sprak sv|en|zh] [--bubblor nara|rad]
```
- `bygg` skriver materiallistan, vikt, låda, "Skisser N, fullt bestämda: alla", krockar och regelkontrollen.
  Krockar ska vara "inga" och regelkontrollen utan FEL.
- `ritning` lägger bladet i modellens FCStd: framvy och planvy (E-metoden), snitten med egen skala, isometri,
  måttkedjor, positionsbubblor intill delen, hålangivelser `4*Ø14 - M12x44`, materiallista med ALLMÄNNA
  NOTERINGAR, noterna och titelblocket. `RITNING["detaljer"]`/`["delvyer"]` ger detaljblad (blad 2). Ger
  `<modell>.pdf`, `<modell>.png` (och `_detaljer.png`) och `_materiallista.csv`.
- Snitt `A:x=300:-` = planet x = 300, blicken mot -x. Lägg snittet genom en hålrad för att få hålens lägen.
- Måttkedjorna går till hål av sig själva. Upprepade delar utan hål (pinnar, spjälor, regler, steg) får en kedja
  till delarnas mitt med `RITNING["kedjor"] = [dict(pos="pi/1", vy="fram")]` (`vy` och `axel="x"|"y"` valfria):
  t.ex. 177.5-138-138-...-101.5 i framvyn.
- Utskriften säger vilka positioner som inte syns (ingen bubbla) och hålgrupper som inte syns som cirklar: lägg till
  ett snitt eller en vy (`--vyer fram,plan,vanster`).
- Noterna skrivs som de står (versaler, men `pl/3` och `a4` med gemener). Bultar, svetssymboler och mer än en
  revisionsrad ritas inte – skriv dem i noterna.
- **Noteringarna grupperas** under rubriker i två spalter (`scripts/noter.py`): STATUS (överst, utan rubrik),
  UNDERLAG OCH ANTAGANDEN, UTFÖRANDE, MONTAGE OCH INFÄSTNING, SVETS, YTBEHANDLING, MATERIAL OCH KÄLLOR, INKÖPTA
  KOMPONENTER, KONTROLL. Rubriken väljs ur notens början (`"SVETS: ..."`, `"YTBEHANDLING: ..."`, `"UNDERLAG: ..."`)
  eller nyckelord (ANTAGNA, NEDGJUTNA, FÖRZINKAD ...); allt annat blir UTFÖRANDE. Ange rubriken själv med prefixet
  eller med `RITNING["noter"] = {"SVETS": [...], "MONTAGE": [...]}`. Ryms noterna inte på blad 1 (eller med
  `--noter-blad`/`RITNING["noter_blad"] = True`) får de ett eget blad NOTERINGAR.
- **Projekt med många ritningar:** lägg de gemensamma noterna på en noteringsritning,
  `python3 scripts/sammanstallning.py noteringar egna/<uppdrag>_noter.py ut/N-01.FCStd --nummer N-01 --uppdrag ...`
  (filen har `NOTER = {...}` eller är en .json), och rita varje sammanställning med `--noter-ref N-01`
  (statusraden GEMENSAMMA NOTERINGAR SE RITNING N-01) och bara sina egna noter.
- **Språk**: `--sprak en|zh` (eller `RITNING["sprak"]`) ger materiallistans, titelblockets och detaljbladets fasta
  texter på engelska eller kinesiska (`scripts/sprak.py`). Noterna skrivs på ritningens språk av den som skriver
  skriptet; källnoterna och racke.noter är svenska (använd `--utan-kallor` och egna noter vid behov).

## Plåt, beklädnad, glas och beslag i en sammanställning
- `k.bockad(pos, t, punkter, langd, mitt=, rot=, radie=)`: kantvikt plåt ur en profil (L, U, Z, hatt, kantkappa).
- `k.trag(pos, t, langd, bredd, kant, mitt=, rot=, sidor=)`: plåttråg med uppbockade kanter och hörnurtag –
  beklädnad av blad, luckor och pelare, fyllningar, täckplåtar.
- `k.glas(pos, horn1, horn2, normal=, t=, glipa=, list_profil=)`: glasruta i en öppning, med glaslister.
- `k.inkop(pos, komponent="id", mitt=, rot=)`: inköpt detalj (gångjärn, lås, handtag, stängare, motor) som
  utrymmesmodell med databladets mått och vikt ur komponentregistret (se "Komponenter" nedan). Utan register:
  `k.inkop(pos, text, lada= | cylinder=, mitt=, vikt=)` med mått ur ett datablad. Hitta aldrig på mått.
- `python3 scripts/dxf.py <modell.FCStd>`: en DXF per plåtposition (`_kontur.dxf` för laser med märkning,
  `_utbredning.dxf` med bocklinjer och bocknoter för bockade delar).

## Ornament
`scripts/ornament.py` i ett delskript eller i `bygg(d)` till `k.egen`: `ornament.svg(sk, fil, bredd=)` (motiv ur
en SVG, t.ex. ritat i Inkscape eller vektoriserat ur ett foto), `ornament.text(sk, "NO 12", hojd=, font=)` (text,
monogram; egna typsnitt i `egna/ornament/`), och genererade motiv `solfjader`, `sicksack`, `trappsteg`, `bagar`,
`ring`. Skissen används till `d.kloss` (relief), `d.ficka(sk, djup)` (gravyr) eller `d.ficka(sk, "genom")`
(laserskuren genombrytning). Upprepa med `d.monster`/`d.polart`.

## Räcken och trappräcken (scripts/racke.py)
Ett räcke byggs med `racke.bygg(k, linje=, stolpar=, handledare_x=, ...)` och ritas med `sammanstallning.py`
(framvy, snitt genom en spjäla, delvy längs handledaren och detaljer på blad 2 via `racke.ritval`). Exempel:
`konstruktioner/trappracke.py`. Läs räckesavsnittet i `references/smidesritningar.md`.
- `racke.rak_trappa(k, steg, steghojd, stegdjup, bredd, podest, knack_in)` ger framkantslinjen och ritar stegen som
  referenskroppar; `racke.fordela([...], lage=stegmitt, max_cc=1300)` ger stolplägen.
- Utförandet är val, inget är kundspecifikt: `handledare` (`"FL40*10"`, `dict(profil="FL40*10", rundad=True)`,
  `"RÖR42.4*2.6"`), `start="rak"|"snacka"` (smidd snäcka bara när kunden vill ha det), `foljare`/`underliggare`,
  `spjalor=dict(profil="FS12"|"D12", fri=100)`, `stolpe=dict(profil=..., fot="ingjutning"|"fotplat", ...)`.
- `racke.noter(info)` ger utförandenoterna; lägg till uppdragets egna rader (underlag, antaganden, ytbehandling).

## Grindar, dörrar och luckor
- `k.rorelse(namn, delar, axel=((x, y, z), (0, 0, 1)), fran=0, till=-100, gangjarn=[...])` i skriptet, sedan
  `python3 scripts/rorelse.py <modell.FCStd>`: krockkontroll mot stolpar, vägg och mark genom hela öppningen,
  tyngdpunkt och gångjärnslast. `--oppen 80 --ut <fil>_oppen.FCStd` sparar en öppen kopia för 3D-bilder. Exempel:
  `konstruktioner/grind.py` (axeln framför stolpen, annars slår bladet i stolpen före 90°).
- **Produktregler** (`REGLER` i skriptet, `scripts/regler.py`): vad en kund eller återförsäljare får ändra, t.ex.
  `dict(villkor="600 <= Bredd <= 1500", text="...")`, kontrolleras vid varje bygge tillsammans med verkstadens
  gränser (`egna/verkstad.json`, mall `mallar/verkstad.json`) och står som not på ritningen.

## Från foton till offertunderlag
När en kund skickar foton och några mått (mail, chatt) på ett räcke, en grind, en dörr eller en trappa:
1. Läs underlaget och bilagorna (fallor.md: Gmail-bilagor; ritningar med underlag.py). Beskriv kort hur du tolkar
   fotona (lopp, vilplan, antal steg, förebildens profiler) innan du modellerar, och fråga bara om det som avgör
   utförandet.
2. Rita omgivningen som referenskroppar (`k.referens`, `racke.rak_trappa`) med antagna mått, och skriv i noterna
   att måtten är antagna ur foton och kontrollmäts på plats.
3. Bygg varje räcke/grind som en egen sammanställning (R/1, R/2, G/1) i `egna/konstruktioner/`, gemensamma mått
   i en egen modul (`egna/<uppdrag>.py`) som alla skript och översikten importerar.
4. Gör en översikt (alla delar på plats + omgivningen) för 3D-bilderna (`rendera.py`) och planritningen
   (`oversikt.py`), och visa PNG:erna för användaren efter varje steg.
5. Offert: mängdunderlaget (`mangder.py`), beställningspaketet (`paket.py skapa`) och, när användaren vill,
   leveransen till en tillverkare (`paket.py skicka`).

## Komponenter: beslag, lås, glas och motorer
Skillen innehåller inga komponentdata. Inköpta komponenter (gångjärn, lås, handtag, dörrstängare, grindmotorer,
glas, bultar) ritas med mått ur en leverantörs datablad, som söks upp på nätet i landet där skillen används:
1. **Land:** `python3 scripts/komponenter.py visa` visar registret och landet (`land` i foretag.json, `FC_LAND`).
   Okänt: fråga användaren och spara med `foretag.py satt --land SE`.
2. **Sök** (webbsök) efter komponenten hos leverantörer och grossister i det landet, på landets språk, för
   uppgiften: t.ex. "gångjärn grind kullager 120 kg" eller "门铰链 不锈钢 承重" i Kina. Välj en vanlig produkt som
   finns i lager, eller den användaren anger. Läs produktsidan eller databladet: ytterkontur och montagemått,
   vikt och tillåten last. Säg till användaren vilken produkt som valts och varför; de kan byta.
3. **Lägg in** den med källan: `python3 scripts/komponenter.py lagg-till --id gj-grind-120 --typ gångjärn
   --benamning "GÅNGJÄRN KULLAGRAT" --tillverkare "..." --artikel "..." --cylinder 22x120 --vikt 0.4
   --last "120 kg/par" --kalla <URL>`. Registret ligger i `egna/komponenter.json` och följer med uppdraget.
4. **Rita:** `k.inkop("gj/1", komponent="gj-grind-120", mitt=(...), rot=(...))`. Benämning, tillverkare och
   artikelnummer hamnar i materiallistan, källan i noterna (`INKÖP gj/1: ... MÅTT ENL. DATABLAD <domän> <datum>`),
   vikten i rörelsekontrollens gångjärnslast. Jämför lasten från `rorelse.py` med databladets.
- **Glas:** glastyp och tjocklek väljs efter landets regler för glas i byggnader (i Sverige t.ex. Svensk Planglas
  glasguide och BBR, för räcken och dörrar ofta laminerat säkerhetsglas) eller leverantörens dimensioneringsguide,
  med källan i noterna. `k.glas(..., t=)` ritar rutan; glipa och lister efter leverantörens anvisning.
- Hittas inget datablad med mått: fråga användaren efter produkten eller måtten. Gissa aldrig, och skriv aldrig
  `ANTAGET` på en komponents mått utan att säga det till användaren.

## Mängdunderlag och beställningspaket
- `python3 scripts/mangder.py <modell.FCStd> [--antal 2]`: vikt per material, yta för ytbehandling, kap och
  geringar, hål, laserlängd och håltagningar, bockningar, uppskattad svetslängd och inköpta komponenter
  (`_mangder.csv`, `_mangder.json`). Det är underlag för tillverkarens kalkyl. Skillen sätter inga priser och
  användaren ska inte få några prisuppgifter ur den: prissättningen görs av tillverkaren när underlaget kommit in
  och konstruktionen verifierats.
- `python3 scripts/paket.py skapa <modell.FCStd>` samlar ritningar, modell, DXF, STEP, mängdunderlag, skriptet och
  dess egna moduler med skillens version, variablerna, regelkontrollen och kontrollsummor i
  `<modell>_bestallning.zip`. Tillverkaren kör `paket.py kontrollera <zip>`: kontrollsummorna jämförs och modellen
  byggs om med den egna versionen av skillen; vikt, antal delar och regelkontroll ska stämma.

## Leverans till en tillverkare
När användaren säger sig vara nöjd med ritningarna (eller ber om offert):
1. Fråga, med frågeformuläret om det finns: **"Vill du skicka underlaget till en tillverkare för offert?"** med
   alternativen *Ja, till <mottagare> (förifylld)*, *Ja, till en annan adress* och *Nej, inte nu*. Den förifyllda
   mottagaren står i `egna/leverans.json` eller `mallar/leverans.json` (anbud@smide.com). Användaren kan skicka
   vart hen vill; fråga efter adressen vid "annan adress", och efter namn och telefon till mailets avslutning.
2. `python3 scripts/paket.py skapa <modell.FCStd> --skript <konstruktionsskript>` och
   `python3 scripts/paket.py skicka ut/<modell>_bestallning.zip --till <adress> --avsandare "Namn, telefon"
   [--meddelande "..."]`. Det ger `<modell>_mail.eml` (osänt mail med paketet som bilaga) och en mailto-länk.
3. Har agenten ett mailverktyg (t.ex. Gmail): lägg ett **utkast** till mottagaren med ämne, text och paketet
   som bilaga, visa det och skicka bara när användaren uttryckligen säger "skicka". Annars: ge användaren
   .eml-filen och zip:en att skicka själv (se "Filerna till användaren"). Skicka aldrig något utan ett tydligt ja.
4. Paket över 20 MB går inte med vanlig mail: föreslå en delningslänk (Drive, Dropbox) i mailet i stället.

## Filerna till användaren
Lägg upp filerna i chatten när en ritning är klar, så att användaren kan spara dem i telefonen, dela dem som mail
eller lägga dem i valfri molntjänst. Skillen förutsätter ingen viss lagring.
1. **Få filer** (en ritning): lägg upp PDF:en och PNG:erna direkt (agentens verktyg för att skicka eller bifoga
   filer).
2. **Många filer** (flera ritningar, 3D, modeller, DXF, STEP, materiallistor):
   `python3 scripts/paket.py samla <pdf:er i bladordning> <övriga filer eller ut-mappen> --namn "<uppdrag>"
   --skript egna/konstruktioner/<x>.py ...` ger `<uppdrag> ritningar.pdf` (alla blad i en fil) och
   `<uppdrag> underlag.zip` (ritningar/, 3d/, modeller/, dxf/, materiallistor/, skript/, LASMIG.md). Lägg upp
   båda.
3. **För stora för chatten:** lägg upp dem som nedladdningsbara filer (eller en länk till filen) och säg vad som
   finns i dem. Har användaren sagt var jobbets filer ska ligga, skriv det med i meddelandet.
4. Har användaren bett om det och har agenten en koppling till hens lagring (en molntjänst, ett eget privat
   repo): lägg filerna där också och säg var. Annars bara chatten.

Uppdrag committas aldrig i ett publikt repo: inte i Steelworks-shopdrawings, inte på en gren och inte i en fork
(en fork av ett publikt repo är också publik). Kunduppgifter (namn, adress, telefon) committas aldrig. I agenter
där bara det som committas syns (Codex, Copilot, Cursor) och repot är användarens eget **privata** repo: kopiera
PDF:en och zip-filen till `leverans/<uppdrag>/`, committa på uppdragets gren och ge länken. Är repot publikt:
committa inga leveranser och säg att agenten behöver ett privat repo (en importerad kopia, se infosidan
`docs/index.html`, "Andra kodagenter"). Lägg aldrig leveranser på `main` och aldrig i en förbättrings-PR för
skillen.

## 3D-bilder, export och översiktsritning
- `python3 scripts/rendera.py <modell.FCStd> [--vyer iso,iso2,bak,fram,sida,plan] [--vy namn:dx,dy,dz]
  [--utseende "g/=patinerad,st/=svart"] [--utan-omgivning]`: `<modell>_3d_<vy>.png` med material och ytor (mässing,
  patinerad, verdigris, svart, förzinkad, rostfritt, corten, glas …; `k.utseende({...})` i skriptet).
- `python3 scripts/export.py <modell.FCStd> --format glb,ifc,step,stl`: glTF för webbläsare och mobil, IFC4 för
  arkitekter (positionsnummer, profil och material som egenskaper), STEP, STL.
- `python3 scripts/oversikt.py <modell.FCStd> <ritskript.py> [--uppdrag ...] [--sprak en]`: A2-översikt (plan,
  fasad, montage) med ritskript (`NUMMER`, `SKALA`, `OBJEKT`, `SPRAK`, `rita(r)`), se docstringen.

## Hållfasthet (överslag)
`python3 scripts/hallfasthet.py balk <modell> --pos hl/1 --fall fritt|konsol|fast --q 0.5|--p 1.0 [--riktning sida]`
räknar tvärsnittet ur modellen och ger spänning (med lastfaktor 1,5) mot fy och nedböjning mot L/200;
`hallfasthet.py fem <del.FCStd> --fast=-y --last "+z:8=2000"` räknar en enskild del med Gmsh och CalculiX.
Lasterna ges av användaren eller konstruktören (skriv aldrig in en last som krav utan källa). Resultaten är
kontroller, inte dimensionering: säg det, och att räcken, bärande delar och infästningar ska dimensioneras av en
konstruktör.

## Testa skillen
`python3 scripts/testa.py` bygger och ritar alla exempel, kör verktygen på dem (mängder, dxf, rörelse, export, paket,
hållfasthet, underlag) och jämför ritningarna med referensbilderna i `tester/referens/`. OK/ÄNDRAD/FEL per exempel;
`--snabb` bara bygger, `--bara namn,namn` väljer exempel, `--uppdatera-referens` sparar nya referensbilder.
Kör det efter varje ändring i skillen och innan en pull request.

## Tillverkningsgranskning (plåt)
`scripts/dfm.py` granskar utbredningen mot tumregler för kantpress och laser: flänslängd mot V-öppningen, inre
bockradie mot material, hål till bock, håldiameter och liv, bockavlastning, bocklängd mot kantpressen, plåtformat.
```
python3 scripts/granska.py <del.FCStd> --material S355J2 [--v-oppning 24] [--kantpress 3000] [--fil]
```
`ritning.py` kör granskningen automatiskt och skriver sammanfattningen på blad 2. FEL ska åtgärdas eller motiveras
innan DXF:en går till lasern. Gränsvärdena står överst i `dfm.py` – stäm av mot verkstaden.

## Bockad plåtdel som enstaka del (exempel)
`scripts/datastall.py` är ett exempel på en bockad plåtdel med profilskiss, SheetMetal-bas, hörnradier och
utbredning: `bygg`, `satt --bredd 400 ...`, `las`, och sedan `ritning.py`. Skriv nya plåtdelar efter samma mönster
(kalkylbladet `Variabler`, profilskissen `Profil` med namngivna mått, `SMBaseBend` med BendSide "Inside" =
yttermått, utbredningen `Utbredning` med K-faktor 0,5) eller som `k.bockad`/`k.trag` i en sammanställning.

## Rapportera
Säg vilken fil som ändrades, vilka mått som sattes och vad kontrollen visade (låda, vikt, krockar, regelkontroll,
utbredning, bocknoter, DXF-raden). Lyft det som inte gjordes eller som behöver användarens beslut, t.ex.
ritningsnummer, material, ytbehandling, beslag och antagna mått.

## Filer i skillen
- `scripts/fcapi.py` startar FreeCAD och kör jobb; `scripts/pd.py` Part Design-hjälpare; `scripts/stal.py`
  Konstruktion (balk, plåt, hål, gering, bockad plåt, tråg, glas, inköp, rörelse, utseende) och materiallista.
- Kommandon: `partdesign.py`, `datastall.py`, `ritning.py` (A3), `sammanstallning.py` (A2), `oversikt.py`,
  `rendera.py`, `export.py`, `dxf.py`, `mangder.py`, `regler.py`, `paket.py`, `rorelse.py`, `hallfasthet.py`,
  `underlag.py`, `granska.py`, `foretag.py`, `komponenter.py`, `kallor.py`, `testa.py`.
- Moduler: `racke.py` (räcken), `ornament.py`, `sprak.py`, `noter.py` (noteringarnas rubriker och spalter),
  `plat.py` (utbredning, DXF), `dfm.py`.
- `delar/`, `konstruktioner/` exempel; `mallar/A3.svg`, `mallar/A2.svg` (titelblock med stomnät, etapp och
  revisionsrad), `mallar/verkstad.json`, `mallar/leverans.json`, `mallar/noter_projekt.py`; `tester/referens/` referensbilder; `VERSION`.
- `references/verktyg.md` verktygens API, `references/smidesritningar.md` ritningskonventionerna,
  `references/partdesign.md` Part Design-API:t, `references/fallor.md` kända fällor i FreeCAD 1.0.1 och 1.1.3.

## Begränsningar
- Modell och ritning ligger i samma .FCStd. Variablerna i kalkylbladet `Variabler`.
- TechDraw kräver GUI, så FreeCAD öppnas minimerat under jobbet (i molnet i Xvfb).
- Svetssymboler, bultar och fler än en revisionsrad ritas inte (skrivs i noterna).
- Hållfasthet och svetslängd är överslag. Inga priser: mängdunderlaget prissätts av tillverkaren.
