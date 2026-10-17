---
name: freecad-styrning
description: Styr FreeCAD 1.x (licensfritt, LGPL) från Python för att bygga och ändra parametriska plåt- och smidesdelar med SheetMetal-tillägget eller Part Design (kropp, skisser, Pad/Pocket/Hole/Revolution/Fillet/mönster) och ett variabelblad, läsa av mått, massa och utbredning, exportera STEP och bild, och ta fram tillverkningsritningar med titelblock (TechDraw, PDF) samt DXF-utbredning till laser och bockning, och sammanställningsritningar för stålkonstruktioner i Tekla-stil (A2, positionsbubblor, snitt, materiallista). Använd när användaren nämner FreeCAD, en .FCStd-fil, vill rita en del i Part Design (fotplatta, konsol, fläns, hylsa, bearbetad detalj), vill ta fram varianter av en plåtprodukt (dataställ, fotplåtar, stativ) med ritning och DXF på en dator utan SolidWorks-licens, eller vill rita en stålkonstruktion som i Tekla (balkongram, pelare med fotplåt).
---

# FreeCAD-styrning

FreeCAD 1.0 (testat 1.0.1 på Windows, 1.1.3 på Linux) styrs från vanlig Python. Skripten i `scripts/` är både
startare och jobb: körs de med `python` startar `fcapi.kor()` FreeCAD med GUI (minimerat), kör samma fil som
jobb inne i FreeCAD, skriver ut jobbets logg löpande och avslutar FreeCAD. Ett jobb tar 5–10 s inklusive start.
Läs `references/fallor.md` innan något ändras i ritningsdelen – TechDraw i 1.0.1 har flera buggar som
skripten går runt.

## Förutsättningar
- **FreeCAD 1.0.x** installerat (letas i `C:\Program Files\FreeCAD*\bin`, annars miljövariabeln `FREECAD_BIN`).
- **SheetMetal-tillägget** (FreeCAD: Verktyg → Tilläggshanterare → SheetMetal, testat 0.7.24). Det tar med networkx.
- **Python 3** på PATH med `pip install pymupdf` (slår ihop PDF-bladen och gör PNG). `ezdxf` är frivilligt
  och används för att kontrollera DXF:erna automatiskt.
- **Linux / Claude Code-molnsession:** kör först `bash scripts/installera_linux.sh` (FreeCAD 1.1.3 från
  conda-forge i `/opt/freecad`, SheetMetal 0.7.24, Xvfb, PyMuPDF och ezdxf; 5–10 min första gången).
  `fcapi.py` hittar FreeCAD där och kör det i en virtuell skärm. Starta skripten med system-Python
  (`python3`), inte FreeCADs Python i `/opt/freecad/bin`.
- Stäng inte FreeCAD-fönstret som dyker upp minimerat under ett jobb. Ha inte samma .FCStd öppen i FreeCAD
  samtidigt som ett skript sparar den.

## Företagsuppgifter i titelblocket
Mallarna i `mallar/` är neutrala. Uppgifterna sparas en gång med `scripts/foretag.py` och används sedan av
`ritning.py` och `sammanstallning.py` automatiskt:

```
python3 scripts/foretag.py visa
python3 scripts/foretag.py satt --foretag "Firma AB" --adress "Gatan 1" "123 45 Staden" "firma.se 08-123 45 67" \
        --ritad-av AB --handlaggare AB --ansvarig "A. Bson" [--logga logga.png]
```

**Första gången i en session:** kör `foretag.py visa`. Står det SAKNAS, fråga användaren innan första
ritningen, med AskUserQuestion-formuläret om det finns (annars i chatten): företagsnamn, adressrader,
signatur (RITAD AV), handläggare, ansvarig och om en logga (PNG/JPEG) ska användas i stället för namnet.
Spara svaren med `foretag.py satt` och fortsätt. Fråga inte igen i samma session. Enstaka fält kan alltid
ges per kommando (`--foretag`, `--adress`, `--ritad-av`, `--handlaggare`, `--ansvarig`, `--logga`) och
miljövariablerna `FC_FORETAG`, `FC_ADRESS` (rader åtskilda med `|`), `FC_RITAD_AV`, `FC_HANDLAGGARE`,
`FC_ANSVARIG`, `FC_LOGGA` går före filen.

Filen heter `foretag.json` och söks i `FC_FORETAG_FIL`, i `egna/`, i arbetsmappen och i `~/.config/freecad-styrning/`
(Windows `%APPDATA%\freecad-styrning\`). I en molnsession försvinner den med containern; vill användaren
slippa frågan varje gång, föreslå miljövariablerna i molnmiljöns inställningar eller en `foretag.json` i
en egen (privat) fork. `foretag.json` är gitignorerad i repot. Loggan läggs in som inbäddad bild i en kopia
av mallen i utmappen (`_A3_logga.svg`, `_A2_tekla_logga.svg`), i rutan som mallens kommentar anger.

## Källor för profilmått och materialkvaliteter
`scripts/kallor.py` hämtar profilmått och nominella hållfasthetsvärden från öppna databaser på nätet och
sparar dem i en lokal cache (`~/.cache/freecad-styrning/kallor`, förnyas efter 30 dagar). Varje uppgift bär
med sig källa, standard och hämtdatum, och ritningarna anger var måtten och materialet är verifierade:
A2-sammanställningen i noterna nere till vänster (och sist i `_materiallista.csv`), A3-bladet i raderna
efter "Material:". Inga nycklar eller konton behövs.
- Profilmått: Steel_Section_Database (github.com/ulmewix, MIT): EN 10365:2017 (IPE, HEA, HEB, HEM, UPE),
  EN 10219-2 (kallformade VKR/RHS/SHS/rör), EN 10210-2 (varmformade KKR), EN 10056-1 (L). Reserv:
  FreeCAD:s egen profiltabell `profiles.csv` (utan rotradier), sist de inbyggda tabellerna i `stal.py`,
  som då märks "ej verifierade" på ritningen. `stal.tolka()` använder källorna automatiskt vid `bygg`, och
  loggen visar en rad per profil med mått och källa.
- Materialkvaliteter: eurocodeapplied.com, tabellen med nominellt fy/fu enligt EN 1993-1-1 tab. 3.1
  (EN 10025-2…6, EN 10210-1, EN 10219-1) per tjockleksområde; reserv FreeCAD:s materialkort (`Steel-*.FCMat`).
  Kvaliteten tolkas ur materialtexten (`S355J2`, `S355J2H`, `Stål S235, obehandlad`); H-kvaliteter räknas
  som EN 10219-1 (kallformat) om inte profilen är KKR. Verifieringen görs när ritningen tas fram.
- Kontrollera själv: `python3 scripts/kallor.py profil UPE140 "VKR100*6.3"`, `python3 scripts/kallor.py material
  S355J2 --t 12`, `... status` (cache och källor), `... uppdatera` (hämta om). `FC_KALLOR=offline` använder bara
  cache och inbyggt; `--utan-kallor` på `ritning.py` och `sammanstallning.py ritning` tar bort noterna.
- Finns profilen eller kvaliteten inte i någon källa: hitta inte på mått. Sök (WebSearch) efter tillverkarens
  eller standardens tabell, säg till användaren vad som inte kunde verifieras och lägg in måtten i
  konstruktionsskriptet eller tabellen i `stal.py` med källan i en kommentar.

## Skillen ändras inte – eget material ligger utanför
Skillen installeras från Steelworks-shopdrawings och ska gå att uppdatera därifrån. Ändra därför inte filerna i
`.claude/skills/freecad-styrning/`. Allt som görs för användaren läggs utanför skillen:
- nya konstruktionsskript i `egna/konstruktioner/`, nya delskript i `egna/delar/` (i repots rot; lokalt i
  användarens projektmapp). Skripten tar vilken sökväg som helst: `sammanstallning.py bygg egna/konstruktioner/x.py`.
- hjälpfunktioner som skillen saknar skrivs i det egna skriptet, inte i skillens filer. Delar som `k.balk`,
  `k.plat` och `k.skiva` inte täcker byggs med `k.egen(pos, "TEXT", bygg, mitt=, rot=, material=)`, där
  `bygg(d)` ritar kroppen med Part Design-API:t i `scripts/pd.py` (skisser, Pad, Pocket, Hole, Fillet, mönster).
  Det är regel, inte undantag: varje ritning har sina egna utmaningar, och de löses i det skriptet.
- företagsuppgifter i `egna/foretag.json` (eller konfigmappen), genererade filer i `ut/`.
Saknas något i skillen som inte går att lösa i det egna skriptet: säg det till användaren och föreslå att det
rapporteras som ett ärende på github.com/richalund/Steelworks-shopdrawings, i stället för att ändra skillen lokalt.
I en molnsession utan fork försvinner allt eget när containern stängs; föreslå en egen fork om användaren vill
behålla sina skript.

## Arbetssätt
**Regel: rita alltid med FreeCADs egna verktyg så att användaren kan redigera vidare.**
Modellen ska bestå av kalkylbladet `Variabler`, fullt bestämda skisser med namngivna mått som uttryck mot
bladet och features (Pad, Pocket, Hole, Revolution, Fillet, SheetMetal-features …) – samma objekt som om
detaljen ritats för hand i GUI:t. Aldrig döda former (`Part::Feature` med en Shape från `Part.makeBox`,
booleska operationer i skriptet, importerad STEP) och aldrig skriptade objekt (`App::FeaturePython`) eller
makron i filen. Profiler (HEA/HEB/IPE) byggs med `delar/hprofil.py`. Det gäller även stora stång- och
gallerkonstruktioner (vinställ, galler, räcken med hundratals stänger): varje stång är en egen Body via
`stal.Konstruktion` – aldrig en compound av `Part.makeCylinder` "för att det går fortare" (204 kroppar
byggs på under en minut). Kontrollera efter bygget att filen bara har Body/Sketch/Pad/Pocket/…-objekt.

1. **Befintlig fil:** läs av (`las`): variabler, skissens status, låda, massa och utbredning med bocknoter.
   Ändra med `satt --<variabel> <värde>`. Kontrollera lådan, massan och utbredningen i utskriften.
   Part Design-filer (en `PartDesign::Body`) läses och ändras med `partdesign.py las/satt --var Namn=värde`.
2. **Ny del:** välj arbetsbänk efter delen. Bockad plåt med utbredning: SheetMetal enligt nedan. Solid del
   (platta med hål, konsol av plattstång, fläns, hylsa, svarvad eller fräst detalj): Part Design med ett
   delskript, se avsnittet Part Design. För plåt: skriv ett byggskript efter mönstret i `scripts/datastall.py`: kalkylbladet `Variabler`
   (alias = variabelnamn), skissen `Profil` med namngivna mått som uttryck mot bladet
   (`sk.setExpression("Constraints.Djup", "Variabler.Djup")`), SheetMetal-basen (`SMBaseBend`, BendSide
   "Inside" = yttermått), eventuella hörnradier (`Part::Fillet`, kanter letas på geometrin) och
   utbredningen `Utbredning` (`SMUnfold`, K-faktor 0,5, fast yta = bottenplattans undersida). Användaren
   kan sedan ändra variablerna direkt i FreeCAD (dubbelklicka på Variabler) och `satt` ändrar samma celler.
3. **Ritning:** för stålkonstruktioner med flera delar (Tekla-stil, A2): `scripts/sammanstallning.py`, se
   avsnittet Sammanställningsritning. För Part Design-delar se avsnittet nedan. För plåt lägger `scripts/ritning.py` blad 1
   (planvy, profil, isometri, mått, noter) och blad 2
   (utbredning med bocklinjer, bocknoter, totalmått, kedjemått till bocklinjerna och hörnradie) i
   delens .FCStd, fyller titelblocket (Företag, Namn, Ritningsnummer, Datum, Ritad av, Filnamn) och exporterar PDF,
   PNG per blad och två DXF: `_kontur.dxf` (laser, lager KONTUR) och `_utbredning.dxf` (KONTUR +
   BOCKLINJER + BOCKNOTER). De namngivna måtten i skissen `Profil` blir mått i profilvyn. Skalan väljs
   automatiskt (eller `--skala` / `--skala-utbredning`). Granska PNG:erna innan leverans: inga
   överlappande mått, inget utanför ramen, rätt text i titelblocket. Kontrollera DXF-raden i utskriften
   (låda, lager, "sneda linjer: 0").
4. **Kontrollera alltid** innan leverans: skisserna fullt bestämda, lådan stämmer med måtten, utbredning och
   bockar rimliga (plåt), volymen rimlig (Part Design), tillverkningsgranskningen utan FEL (plåt), PNG:erna
   granskade med Read. Jämför med konventionerna i `references/smidesritningar.md` när ritningen gäller en
   stålkonstruktion.
5. **Leverera** FCStd, PDF, DXF och STEP i projektmappen bredvid varandra. Ritningen ligger i samma
   FCStd som modellen. Skriv aldrig över kundens eller användarens originalfil; lägg nya filer bredvid
   (`--ut <mapp>` för ritningen).

## Part Design (solida delar: plattor, konsoler, flänsar, hylsor)
Används när delen inte är bockad plåt. Läs `references/partdesign.md` (API:t i `scripts/pd.py`) innan ett
nytt delskript skrivs. Ett delskript i `delar/` har `NAMN`, `VARIABLER` (blir kalkylbladet `Variabler`) och
`bygg(d)`, där skisser ligger på kroppens origoplan (XY, XZ, YZ med förskjutning) och alla mått är uttryck
mot variablerna, t.ex. `sk.rundad_rektangel("Bredd", "Langd", "Hornradie")`, `d.kloss(sk, "Tjocklek")`,
`hal.halbild("HalD", "CCx", "CCy")`, `d.hal(hal, "HalD")`. Mönster: `delar/fotplatta.py` (rundad platta
med hålbild), `delar/konsol.py` (L-vinkel med stag, hål och avrundade hörn), `delar/hylsa.py` (Revolution
och fas).
```
python scripts/partdesign.py bygg delar/fotplatta.py "<mapp>\Fotplatta.FCStd" --var Bredd=300 --png --step
python scripts/partdesign.py satt "<mapp>\Fotplatta.FCStd" --var HalD=22 --var CCx=240 --png
python scripts/partdesign.py las  "<mapp>\Fotplatta.FCStd"
python scripts/ritning.py "<mapp>\Fotplatta.FCStd" --namn "Fotplatta" --nummer "FP-01"
```
- Utskriften visar variablerna, varje skiss (fullt bestämd + namngivna mått), features med status, låda,
  volym och massa. Räkna gärna volymen för hand som kontroll.
- `satt` ändrar celler i `Variabler`, räknar om och letar om kanterna för Fillet/Chamfer (kantvalet sparas
  i featuren). Okända variabler ger fel med listan över de som finns.
- Ritningen (`ritning.py`, samma kommando som för plåt) blir ett blad enligt E-metoden: framvy, ovanvy under,
  sidovy (sedd från vänster) till höger och isometri. Måtten är totalmåtten plus skissernas namngivna mått
  i den vy som tittar längs skissens normal (mått med namn som börjar på `_` sätts inte ut), hål som
  `4×⌀18` / `6×M10`, radier som `4×R20` och rotationsdelars diametrar. Skalan väljs från 5:1 till 1:50.
  En platta (två lika ändytor, tjocklek < halva minsta sidan) får `_kontur.dxf` för laser.
- Mått bundna till en enda variabel får variabelns namn och hamnar på ritningen. Vill man ha ett mått
  på ritningen som är ett uttryck: ge det `namn=` i skisshjälparen.
- Saknas något mått på ritningen (t.ex. bultcirkelns diameter) – säg det, eller lägg ett namngivet mått i skissen.

## Sammanställningsritning för stålkonstruktioner (Tekla-stil, A2)
För balkar, ramar, pelare och konsoler med flera delar: samma blad som en Tekla-sammanställning från ett
svenskt smidesföretag. Läs `references/smidesritningar.md` först.
Modellen byggs med ett konstruktionsskript i `konstruktioner/` (API i `scripts/stal.py`): `NAMN`, `MARKE`
(sammanställningsmärke, t.ex. `B/1`), `VARIABLER` (kalkylbladet `Variabler`), `RITNING` (vyer, snitt, noter,
stomnät) och `bygg(k, v)` med `k.balk(pos, profil, start, slut, upp=, oppning=)`, `k.plat(pos, "PL10*110",
mitt=, langd=, lriktning=, briktning=)` och `k.hal(delar, punkter, riktning, bult="M12x44")` och `k.gera(del, yttre_hörn, inre_hörn)` (geringskapning, t.ex.
UPE-ram med 45°-hörn). `k.egen(pos, "TEXT", bygg)` för kroppar som skriptet bygger självt med pd-API:t. `k.skiva(pos, "GLAS 8", langd, bredd, t, mitt=, material="Glas", form="ellips"|"rektangel")`
ger en plan skiva (bordsskiva, glas, lock; vikt med 2500 kg/m3 för glas). `k.gera` kapar också plant: två
punkter i kapplanet och `upp=` vald så att profilens y-riktning ligger i planet (se `konstruktioner/soffbord.py`,
ett trebent bord med utåtlutade rör, nav-och-ekrar-ram och oval glasskiva). Varje del blir en
Part Design-kropp (skissen Tvarsnitt fullt bestämd med rotradier som bågar, Pad `Langd`, hål som Pocket) med
egenskaperna Pos/Profil/Material. Koordinater och längder får vara uttryck mot Variabler (`"Langd"`,
`"Djup - 32.5"`, även hålens lägen): då följer delar och hål med när användaren ändrar en variabel i FreeCAD.
Antal delar (t.ex. `Bjalkar`) kräver ombyggnad. Profiler: UPE, IPE, HEA, HEB (tabell), VKR/KKR/RHS a*t eller
h*b*t, PL t*b, D, RÖR d*t, L (utan radier). Mönster: `konstruktioner/balkongram.py` (gerad UPE-ram, IPE100 med
ändplåtar bultade mot påsvetsade plåtar, däckplåt), `konstruktioner/pelare.py` (VKR med fot- och toppplåt).
```
python scripts/sammanstallning.py bygg konstruktioner/balkongram.py "<mapp>\B1.FCStd" [--var Langd=2400] --png --step
python scripts/sammanstallning.py ritning "<mapp>\B1.FCStd" --uppdrag 2026-001 --objekt "KV EXEMPEL 1" "Byggbolaget AB" "Exempelgatan 1, Stockholm"
       [--foretag "Firma AB" --adress "Gatan 1" "123 45 Staden" "firma.se 08-123 45 67"] [--ritad-av AB --handlaggare AB --ansvarig "A. Bson"]
       [--bet A --rev "A|Bultad anslutning|2026-10-07|AB"] [--stomnat A-B/2] [--antal 1] [--not "PRELIMINÄR ..." ...]
       [--snitt A:x=300:- --snitt B:x=575:-] [--vyer fram,plan] [--skala 10] [--skala-snitt 5] [--hal 22] [--svets 3.0]
```
- `bygg` skriver materiallistan, antal hålgrupper, vikt, låda, "Skisser N, fullt bestämda: alla" och
  krockar mellan delar (överlappande volym). Krockar och ej bestämda skisser ska vara "inga"/"alla".
- `ritning` lägger bladet `Sammanstallningsritning` (mall `mallar/A2_tekla.svg`) i modellens FCStd:
  framvy och planvy (E-metoden, planvyn med dolda linjer om `RITNING["dolda"]`), snitten med egen skala och
  rubrik `A - A`, isometri, måttkedjor (hål, hålgruppernas mitt, totalmått), positionsbubblor (varje
  positionsnummer en gång där delen syns störst; huvuddelen som `B/1 b/1 UPE140`), hålangivelser
  `4*Ø14 - M12x44` där hålen syns som cirklar, materiallista med ALLMÄNNA NOTERINGAR och noterna. Ger
  `<modell>.pdf`, `<modell>.png` och `<modell>_materiallista.csv`.
- Snitt `A:x=300:-` = planet x = 300, blicken mot -x (det som ligger på x < 300 visas). Lägg snittet genom en
  hålrad för att få hålens lägen måttsatta i snittet. Snittens lägen är tal: flytta dem om måtten ändras.
- Hålgrupper som skyms i alla vyer (t.ex. bultförbandet bakom UPE-livet) får hålangivelse och måttkedjor i
  första vyn där hålen ligger längs blickriktningen, som Teklas ledare till dolda hål.
- Utskriften säger vilka positioner som inte syns i någon vy (ingen bubbla) och hålgrupper som inte syns
  som cirklar: lägg till ett snitt eller en vy (`--vyer fram,plan,vanster`).
- Noterna skrivs som de står (versaler som i Tekla, men `pl/3` och `a4` med gemener). Bultar, svetssymboler
  och mer än en revisionsrad ritas inte – skriv dem i noterna.

**Stångkonstruktioner (exempel: vinställ, galler, räcken).** Rundjärn som `k.balk(pos, "D10", start, slut)`,
vinkeljärn som `"L30*30*3"`/`"L30*20*3"` (h = benet längs `w x oppning`, b = benet längs `oppning`; vänd
start/slut om benen hamnar fel), inköps- och beslagsdetaljer som `k.plat`, geringade ramar med `k.gera`.
Höjder som är summor av fack skrivs som uttryck i kedja (`"FotNiva + Fack1 + Fack2 - 15"`), så att en ändrad
fackhöjd i Variabler flyttar alla hyllplan, hyllor och dörrar utan ombyggnad. Ett konstruktionsskript kan
hämta geometrin ur en egen regelmotor eller en orderfil och köra bygg + ritning i ett svep. Riktvärde från ett
vinställ 6 x 360, djup 520: 204 kroppar, 258 skisser, 98,9 kg, bygg 45 s, ritning ca 70 s. Höga objekt:
`--vyer fram,hoger --skala 20` (vyerna staplas på höjden; med planvyn krävs 1:25 på A2).

## Tillverkningsgranskning (plåt)
`scripts/dfm.py` granskar utbredningen mot tumregler för kantpress och laser och anger regel, uppmätt värde
och krav för varje anmärkning: yttre flänslängd >= 0,7 x V-öppningen (V = minsta standard-V >= 8 t),
inre bockradie mot material (S235 1 t, S355 1,5 t, rostfritt 1 t, Al 6082-T6 3 t …), luftbockningens naturliga
radie (V/8–V/6), hål/urtag till bockens mittlinje >= 2,5 t + R, håldiameter och liv >= t, bockavlastning där en
bock slutar i ett inåtgående hörn, bocklängd <= kantpressen (3000 mm), plåtformat och standardtjocklek.
```
python scripts/granska.py "<del.FCStd>" --material S355J2 [--v-oppning 24] [--kantpress 3000] [--fil]
```
`ritning.py` kör granskningen automatiskt (`--material` och `--v-oppning`), sparar `<del>_granskning.txt` och
skriver sammanfattningen i noterna på blad 2; `datastall.py` visar FEL/VARNING i kontrollen. FEL ska åtgärdas
eller motiveras innan DXF:en går till lasern. Gränsvärdena står överst i `dfm.py` – stäm av V-öppningar,
kantpressens längd och plåtformat mot verkstaden. Bockföljd och verktygskollision granskas inte.

## Dataställ (exempel på bockad plåtdel)
```
python scripts/datastall.py bygg "<mapp>\Dataställ param.FCStd" --png --step
python scripts/datastall.py satt "<mapp>\Dataställ param.FCStd" --bredd 400 --hylla 320 --lutning 8 --png
python scripts/datastall.py las  "<mapp>\Dataställ param.FCStd"
python scripts/ritning.py "<mapp>\Dataställ param.FCStd" --namn "Dataställ" --nummer "DS-01"
```
Variabler: Bredd, Djup (bottenplatta), Rygg (höjd), Hylla (djup), Kant
(uppvikt framkant som stopp för datorn), Lutning (hyllans lutning nedåt framåt, grader), Tjocklek,
Bockradie, Hornradie (0 = inga). Yttermått: undersida botten, baksida rygg, ovansida hylla och kantens
insida. Hyllan lutar nedåt mot användaren och kanten viks uppåt. Koordinater: X = bredd, Y = djup bakåt,
Z = höjd. Standardmåtten ger utbredning 730,5 × 350 mm och bockarna UPP 90° R3, UPP 95° R3, NED 90° R3
(K = 0,5). Massan räknas med 7850 kg/m³.
Efter en måttändring: kör `ritning.py` igen så görs bladen om från grunden.

## Rapportera
Säg vilken fil som ändrades, vilka mått som sattes och vad kontrollen visade (låda, massa, utbredning,
bocknoter, antal mått per blad, DXF-raden). Lyft det som inte gjordes eller som behöver användarens beslut,
t.ex. ritningsnummer, material och ytbehandling i noterna.

## Filer i skillen
- `scripts/dfm.py` + `scripts/granska.py` tillverkningsgranskning.
- `scripts/fcapi.py` startar FreeCAD och kör jobb; `scripts/plat.py` utbredning och DXF; `scripts/pd.py`
  Part Design-hjälpare; `scripts/datastall.py`, `scripts/partdesign.py` och `scripts/ritning.py` är kommandona.
- `scripts/kallor.py` profilmått och materialkvaliteter ur öppna källor på nätet, med cache och källangivelse.
- `scripts/foretag.py` företagsuppgifter och logga till titelblocket (foretag.json).
- `scripts/sammanstallning.py` (bygg + sammanställningsritning) och `scripts/stal.py` (profiltabeller,
  Konstruktion, hålgrupper, materiallista); `konstruktioner/*.py` konstruktionsskript.
- `scripts/rendera_pdf.py` PDF till PNG för granskning; `scripts/installera_linux.sh` installation på Linux.
- `delar/*.py` delskript för Part Design; `mallar/A3.svg` (enkelt titelblock) och `mallar/A2_tekla.svg`
  (Tekla-titelblock med stomnät, etapp och revisionsrad).
- `references/smidesritningar.md` ritningskonventionerna; `references/partdesign.md` API:t;
  `references/fallor.md` kända fällor i FreeCAD 1.0.1.

## Begränsningar
- Modell och ritning ligger i samma .FCStd (ingen separat ritningsfil). Variablerna i kalkylbladet `Variabler`.
- DXF:erna har egna lager (KONTUR, BOCKLINJER, BOCKNOTER) och bocknoter som text.
- Skalan väljs automatiskt så att vyerna får plats på A3; blad 2 får kedjemått till bocklinjerna.
- TechDraw kräver GUI, så FreeCAD öppnas minimerat under jobbet (på Linux i Xvfb).
