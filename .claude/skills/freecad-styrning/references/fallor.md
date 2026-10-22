# Fällor i FreeCAD 1.0.1 via Python, uppmätt på Windows 11 2026-10-10

FreeCAD 1.0.1 (rev 39285, Python 3.11 i FreeCAD), SheetMetal-tillägget 0.7.24, system-Python 3.14 som startare.

## Start och körning
- Skripten körs som jobb i `freecad.exe` (GUI), inte `freecadcmd.exe`: TechDraw-PDF och mallen kräver
  TechDrawGui, och SheetMetal-objekt som skapas utan GUI får ingen ViewProvider (ingen ikon och ingen
  dialog när användaren dubbelklickar). Fönstret minimeras direkt.
- `freecad.exe <fil.py>` kör filen efter start. Jobbet läser sina argument från JSON-filen i miljövariabeln
  `FCJOBB`. Startfilen ligger i `%TEMP%` så att sökvägar med å/ä/ö (t.ex. `G:\...\Pågående projekt`) inte behöver
  gå via kommandoraden; skriptmappen läggs på `sys.path` i jobbet.
- FreeCAD avslutas med `os._exit()` efter att alla dokument stängts (`App.closeDocument`). Annars visas
  dialogen för dokumentåterställning vid nästa start. Inställningar som jobbet ändrar sparas därför inte.
- Loggen skrivs via `sys.stdout` i jobbet till en fil som startaren läser löpande.
- "SystemError: unknown opcode" skrivs ut många gånger under TechDraw-jobb (PySide2/shiboken + Python 3.11)
  utan att något går fel. Startaren filtrerar bort raden.
- Felsökning: `FC_FELSOK=25` skriver alla trådars Python-stack var 25:e sekund till loggen (faulthandler)
  och visar var en krasch sker. `FC_TIMEOUT=120` ändrar tidsgränsen (standard 600 s). `FC_INGEN_VAKT=1`
  stänger av dialogvakten. `FREECAD_BIN` pekar ut bin-mappen.

## SheetMetal
- Utan GUI saknas `SheetMetalTools.taskRestoreDefaults` (definieras bara med GUI). datastall.py lappar den
  om skriptet ändå körs i freecadcmd.
- `SMUnfold` med `GenerateSketch = True` kräver ViewObject (`bend_lines_doc_obj.ViewObject.DrawStyle`).
  Skillen använder inte skisserna – `plat.utbred()` tar fram kontur och bocklinjer själv och skriver DXF.
- `SMBaseBend` med en öppen profil: `BendSide = "Inside"` lägger materialet till vänster om profilens
  ritriktning. För dataställen (P0 → P1 → P2 → P3 → P4) ger det yttermåtten: undersida botten,
  baksida rygg, ovansida hylla, insida kant – samma som SolidWorks-versionen.
- Utbredningen läggs i den fasta ytans plan. Välj bottenplattans undersida (största plana yta med normal
  -Z, `plat.rotyta`), annars blir utbredningen lutad som i SolidWorks (hyllan som fast yta).
- K-faktor 0,5 (ansi) ger 730,5 × 350 mm för standarddataställen, exakt som SolidWorks.
- SheetMetals `BendDirection.from_face` gav UPP/NED omvänt för dataställen och radien R+T i stället för
  R. `plat.utbred` avgör riktningen på geometrin: rotsidans bockyta konvex = UPP (bocken går mot den som
  tittar från andra sidan), konkav = NED; inre radie = r - t respektive r.
- `Shape.BoundBox` är för stor runt fillets (BSplines): -0,2..350,2. Använd `optimalBoundingBox(False, False)`.
- Hörnradierna är en `Part::Fillet` med kantindex. Indexen letas om på geometrin vid varje `satt`
  (raka kanter med längd = tjockleken vid bottenplattans framhörn och kantens fria ände). Ändras Hornradie
  bara i kalkylbladet inne i FreeCAD uppdateras inte filletradien – kör `satt --hornradie`.
- Skissens vinkel: `Angle` mellan ryggens riktning (uppåt) och hyllans (framåt-nedåt) = 90° + lutningen.
  Uttrycket `(90 + Variabler.Lutning) * 1 deg` fungerar.

## TechDraw (ritningar)
- Mallen (SVG) ritas bara i PDF:en om bladet visas först: `page.ViewObject.show()` före
  `TechDrawGui.exportPageAsPdf`. Annars blir PDF:en utan ram och titelblock.
- Vyernas HLR räknas i en tråd: vänta med `pump()` tills `getVisibleEdges()` returnerar något.
- Ytor fylls ljusgrå; inställningen ClearFace hjälpte inte. Sätt `view.ViewObject.FaceColor = (1, 1, 1)`.
- `TechDraw.makeDistanceDim3d` ger dubbla värden (560 i stället för 280 vid skala 1:2) och returnerar None.
  Använd inte.
- Kosmetiska PUNKTER (`makeCosmeticVertex3d`) lagras med Y nedåt och visas Y-speglade i vyer med negativ
  X-riktning (utbredningsvyn). Mått mellan dem fick förlängningslinjer över hela plåten, och sneda
  mått (Distance) och Angle3Pt ritades fel. `removeCosmeticVertex` när bladet visas kraschade FreeCAD
  (access violation). Skillen använder därför bara kosmetiska LINJER: varje mått mäts på en osynlig
  kosmetisk linje mellan de två modellpunkterna (`Vy.matt`), vinklar mellan två tunna kosmetiska linjer
  från spetsen (`Vy.vinkel`, typ Angle). Ingen kosmetik tas bort.
- Pappersläge för en modellpunkt: `projectPoint(p)` ger oskalad projektion utan centrering. Vyns mitt
  kalibreras med en kosmetisk linje (dess `Start` är oskalad, relativt vyns mitt, Y uppåt):
  papper = vy.X + skala·(projectPoint - mitt). Måttens `X`/`Y` är etikettens läge i bladmillimeter
  relativt vyns mitt.
- `getEdgeByIndex` ger kanter oskalade, relativt vyns mitt, Y uppåt (cirklar med radien i modellmått).
- Linjestil går inte att styra: kosmetiska linjer ritas alltid streckade oavsett `Format["style"]`, och
  `formatGeometricEdge(i, stil, bredd, färg, synlig)` tar bredd och färg men inte stil. Bocklinjerna är
  därför riktig geometri (objektet `Bocklinjer` i utbredningsvyns Source), UPP som en linje och NED som
  egna streck (5 mm/2,5 mm på papperet), formaterade tunna och grå. De måste ligga strax OVANFÖR plåtens
  ovansida, annars döljs de i HLR.
- Radiemått med egen `FormatSpec` tappar R-prefixet: använd `"R%.1w"`. `%.1w` tar bort onödiga nollor.
- `%w` följer enhetsschemat. Med standardschemat ("Standard (mm, kg, s, °)") skrivs längder från 10 m i
  meter utan enhet: totalmåttet 10530 blev "10.5" (uppmätt 1.1.3, 2026-10-19). Dokumentets egenskap `UnitSystem`
  går före användarinställningen och sparas med filen, så en modell byggd med standardschemat fick fel mått även
  när inställningen ändrats. `fcapi.mm_enheter(doc)` sätter "MmMin" (mm även över 10 m) för sessionen och
  dokumentet; jobben anropar den när ett dokument skapas eller öppnas för ritning.
- `DrawViewAnnotation`: `X`/`Y` är textblockets MITT. TextSize 3,5 ritas med 4,8 mm teckenhöjd (×1,371);
  `LineSpace` 100 ger radavstånd 1,69 × TextSize. Noter läggs som ett flerradigt block (raderna
  vänsterjusteras mot varandra) och blockets vänsterkant räknas med Qt-fontmått × 1,371 (±1–2 mm).
- Att ta bort ett blad tar med dess vyer och mått: samla namnen först och kontrollera `getObject` innan
  `removeObject` (annars ReferenceError på borttagna objekt).
- Objektnamn med å/ä/ö blir `__` (Bockläge → Bockl__ge). Använd ASCII i objektnamn.

## Ritningslayout (ritning.py)
- Blad 1: planvy uppe till vänster, profil uppe till höger, isometri i ytan till höger om planvyn under
  profilens mått (skala ≥ blad 1, oftast 2×), noter nere till vänster från y = 46. Blad 2: utbredningen
  överst, totalmått ovan och till höger, kedjemått under, noter under kedjan.
- Automatisk skala: blad 1 minsta av 1, 1,5, 2, 2,5, 3, 4, 5 ... där planvy + profil ≤ 330 mm bredd,
  planvy ≤ 150 och profil ≤ 120 mm höjd. Blad 2: utbredning ≤ 375 × 180 mm. Dataställ 14 tum → 1:2/1:2;
  450 × 340 → 1:2,5/1:3.
- Profilvyn tittar längs skissen Profils normal med skissens x-axel åt höger, så profilen ritas som skissen.

## Part Design (pd.py, partdesign.py)
- Origoplanens riktningar: XY normal +Z; XZ skissens x = X, y = Z, normal -Y; YZ skissens x = Y, y = Z,
  normal +X. Origoobjekten hittas på `Role` (`XY_Plane`, `Z_Axis`), inte på namn.
- `PartDesign::Hole` kräver att profilskissen är omräknad innan `DepthType` m.m. sätts ("Linked shape object
  is empty"). `pd.Del._ny` kör `doc.recompute()` före varje ny feature.
- `PolarPattern`/`LinearPattern`/`Mirrored` som skapas med `body.newObject` blir INTE kroppens spets; nästa
  feature hamnar då före mönstret och mönstret faller ur kedjan (syntes bara på volymen). `_ny` sätter
  `body.Tip` till varje ny feature.
- `Occurrences` måste vara int (float ger TypeError).
- Sketcher-uttryck kräver namngivet villkor (`Constraints.<namn>`); pd.py ger uttrycksbundna villkor utan
  eget namn namnet `_m<index>`. Uttryck på skissens läge: `.AttachmentOffset.Base.z`.
- `sh.evalExpression("Variabler.Bredd / 2")` räknar ett uttryck (används för startvärden till geometrin).
- Fillet/Chamfer: kanterna letas med kantval på geometrin vid bygget och efter varje `satt`
  (`pd.uppdatera`), eftersom kantnummer ändras när måtten ändras.

## Ritning av Part Design-del (ritning.py, del_ritning)
- Vyer: framvy Direction (0,-1,0) X (1,0,0); ovanvy (0,0,1)/(1,0,0) under framvyn; sidovy (-1,0,0)/(0,-1,0)
  till höger (E-metoden). Vyns mitt = projektionen av kroppens lådmitt, så måttens lägen kan räknas innan
  vyerna finns (används för skalvalet och måttnivåerna).
- Diameter-/radiemått med FormatSpec utan `%` (t.ex. "6×M10") ritas utan text. Sätt `Arbitrary = True`.
- `ViewObject.RenderingExtent = "Reduced"` på diametermått: en pil mot cirkeln i stället för en linje genom
  mitten (som annars korsar centrumhål och andra cirklar).
- Cirkelkanter i vyn: `getEdgeByIndex` ger fulla cirklar med `isClosed()` True, bågar False; radien är oskalad.
- Skissmått med namn som börjar på `_` hoppas över; totalmått tas bort när ett skissmått eller en diameter
  redan ger samma utsträckning.

## Titelblocket (2026-10-11)
- Fältet Filnamn har 3,5 mm text (SolidWorks-mallen 4,67 mm), annars gick "Dataställ param FreeCAD" utanför
  rutan och ramen. Rutan är 53 mm bred: ca 28 tecken får plats. Längre filnamn – korta filnamnet.

## Sammanställningsritning (sammanstallning.py, stal.py), uppmätt 2026-10-11
- **Symbol (DrawViewSymbol) med SVG i mm** ritas med faktorn 90/96 (100 mm blev 93,6 mm). `Scale = 96/90` ger
  rätt storlek. `X`/`Y` = symbolens MITT, Y uppåt. Sätt X/Y EFTER `page.addView`, annars hamnar symbolen mitt
  på bladet. Materiallistan, noterna och snittrubrikerna (`A - A` med skalan) är symboler: exakt geometri,
  ingen gissning av textbredder som med DrawViewAnnotation.
- **Ballong (DrawViewBalloon):** `X`, `Y`, `OriginX`, `OriginY` är OSKALADE modellmått relativt vyns mitt,
  Y uppåt (på papperet = vyns X/Y + Scale × värdet). `BubbleShape` "Inspection" = den avlånga bubblan på svenska tillverkningsritningar, bubbla,
  "Line" = understruken text med ledare (hålangivelsen `4*Ø14 - M12x44`). `EndType` "None", `KinkLength` 0.
  Utan `ViewObject.Font/Fontsize` blir texten 13,7 mm Tahoma.
- Ballongerna fylls med inställningen `Mod/TechDraw/Colors/PageColor` (ljusgrå F1F3F5 på testdatorn) och
  linjerna ritas i `NormalColor` (mörkgrå 212529). Jobbet sätter PageColor/FaceColor vita och Normal-,
  Hidden-, Section-, Center- och VertexColor svarta (sparas inte: FreeCAD avslutas med os._exit).
- **Måttpilar:** `ArrowStyle` finns inte på måttets ViewObject i 1.0.1. Inställningen
  `Mod/TechDraw/Dimensions/ArrowStyle` = 2 ger snedstreck (tick) som på svenska tillverkningsritningar.
- **Snittbokstäverna** (A, B i basvyn) får teckenhöjden 1,39 × `Mod/TechDraw/Dimensions/FontSize` (em) och
  typsnittet `Mod/TechDraw/Labels/LabelFont`. FontSize 3,4 ger 4,7 mm som på förlagorna. Bokstäverna hamnar strax
  utanför vyn: måtten och bubblorna i en vy med snittlinjer läggs 6 mm längre ut.
- **DrawViewSection:** `SectionNormal` n behåller materialet på -n-sidan; `Direction` = n (betraktaren på
  +n-sidan), `XDirection` = Z × n (Z uppåt i snittet), `SectionDirection` "Right"/"Left"/"Up"/"Down" = n
  projicerad i basvyn. Snittvyns egen etikett syns inte i PDF:en - rubriken är en symbol. Kosmetiska linjer
  och `projectPoint` fungerar i snittvyer som i vanliga vyer (samma kalibrering, `Vy.papper`).
- Text i TechDraw: Fontsize 3,0 i Arial Narrow blir 4,1 mm em (samma faktor 1,371 som Century Gothic).
- **Hål sett längs axeln:** en stråle längs hålets axel går genom tomrummet i alla hål i linje (bakre ramens hål
  "syns" genom främre). Hålgrupper med samma projicerade hålbild räknas en gång (den närmaste). Hål som skyms
  av en annan del (fotplåtens hål under toppplåten) testas med en stråle från hålmitten mot betraktaren.
- **Part Design-kroppar som delar:** `PartDesign::Fillet` på Pad-kanterna (rotradier) gick sönder ("Invalid")
  när Pad-längden ändrades via ett uttryck mot Variabler. Rotradierna ritas därför som tangerande bågar i
  skissen (som `delar/hprofil.py`). U-profilen: 8 linjer + 2 bågar, 42 frihetsgrader; utan
  `PointOnObject(L5 start, L1)` blir den högra flänsspetsen obestämd.
- Kroppens läge binds med `body.setExpression(".Placement.Base.x", "Variabler.Langd - 32.5")`. Hålskissen
  fästs på kroppens XY-plan med `AttachmentOffset = Placement(origo, Rotation(Z, hålriktning i kroppen))`;
  Pocket "ThroughAll" + `Midplane` skär åt båda hållen. För en axelparallell kropp är skissens x/y en
  teckenbytt koordinat minus kroppens bas, så cirklarnas lägen kan bindas till Variabler som uttryck.
- Gering (`k.gera`): Pocket genom allt från en sluten skiss i kroppens XZ-plan (skissens y = profilens längd).
  I slutänden binds skissens läge med `setExpression(".AttachmentOffset.Base.y", "<Pad>.Length")` och
  hörnen ritas relativt änden - geringen följer med när Langd ändras (testat 2200 -> 2400 utan fel).
- Ritningens hålgrupper läses ur fickorna (egenskaperna `Halgrupp`, `Bult`); samma grupp i två delar ligger i
  olika skissplan och projiceras på första skissens plan innan dubbletter tas bort.

## Partier med många kroppar och variabelstyrd topologi (mässingsparti, 2026-10-11)
Förebild: ett mässingsparti till en hisshall byggt som konstruktionsskript (118 kroppar,
allt i globala koordinater: kroppens placering är noll, skissernas lägen och Pad-längder är uttryck).
- **Alias som liknar en celladress** (`KX1`, `DX0`, `LY0`) ger `ValueError: Invalid alias`. Använd t.ex. `KxH`, `DxV`.
- **Måttnamn som är enheter** (`h` = timme, `s`, `m`, `g`, `A` ...) går inte att binda med uttryck:
  `setExpression("Constraints.h", ...)` ger ParserError. Ge skissmåtten längre namn (`RorDjup`).
- **`Distance` (oriktat) i en polygonprofil kan vika profilen** när ett läge ändras mycket (U-kanalens fläns
  vek sig tillbaka; Pad-volymen sjönk utan fel). Använd riktade `DistanceX`/`DistanceY` från lägre till
  högre koordinat för varje sida (pd:s `rektangel`/`rundad_rektangel` gör redan så, `profil(matt=...)` inte).
- **Slå av delar med en variabel:** featurens `Suppressed` kan bindas, men bara med villkorsuttryck:
  `"Variabler.Overljus > 0 ? 0 : 1"` (ett rent jämförelseuttryck ger ParserError). `Visibility` går inte att
  binda. En kropp där **alla** features är avstängda blir "Invalid" och **behåller sin gamla form** (syns, följer
  med i STEP och krockkontroller). Lösning: första featuren en `PartDesign::AdditiveBox` "Vilande" 0,1 mm (inne i
  ett rör) med omvänt villkor - aktiv bara när delen är avstängd. Pads på en avstängd bas fungerar.
- Kalkylbladet tar villkorsformler: `=Karmhojd + Env + (Overljus > 0 ? Overljus + Env : 0)`.
- **En Pocket som skär av en list helt** delar kroppen; Part Design behåller då en av bitarna utan felmeddelande
  (listen "försvann", vikten 0,02 kg). Dela sådana delar i flera kroppar mellan urtagen i stället.
- **Färgen** på kroppen sätts sist: en ny spets (t.ex. en Pocket efter `ShapeColor`) visas med standardfärgen.
- Urtag för beslag: bygg beslaget som egen kropp (förenklade block), testa skärning mot varje kropp numeriskt
  (`Shape.common(...)`) och lägg en Pocket med beslagets mått (uttryck + spel) bara i de kroppar som skärs.
  Urtagen följer med när beslagets lägesvariabel ändras.
- **Gering som Pocket** (XZ-skiss, triangel genom kuvertens ytter- och innerhörn, genom allt): vilken triangel som
  tas bort ska avgöras av en punkt **inne i hörnkvadraten** nära delens egen ytterkant (stående rör: 1/4 in i X,
  3/4 upp i Z från ytterhörnet; liggande tvärtom). En punkt långt ut längs delen ligger utanför båda trianglarna och
  gav fel triangel - de liggande rören tappade nästan hela hörnet (vikten 0,06 kg i materiallistan avslöjade det).
- Ritning med full kontroll över mått: `TechDraw.projectEx(form, riktning)` ger synliga kanter (index 0 skarpa,
  3 kontur); planets koordinater kalibreras med två provklossar. Snitt: `form.common(låda).slice(normal, d)` och
  `Wire.discretize()` (kanterna en och en i `OrderedEdges` gav korsande linjer). Allt läggs som en SVG-symbol över
  hela A2-bladet (`DrawViewSymbol`, Scale 96/90, X/Y = bladets mitt)..

## Stångkonstruktion med många kroppar (vinställ, 2026-10-11)
- Första versionen byggdes som döda `Part::Feature`-compounds (en `Part.makeCylinder` per stång) – fel enligt
  regeln i SKILL.md och gick inte att redigera. Ombyggd med `stal.Konstruktion`: 204 Body, 258 skisser
  (alla fullt bestämda), 204 Pad, 54 Pocket (geringar + hål). Bygget tar 45 s inkl. krockkontroll, ritningen ca 70 s.
- Kedjade höjduttryck (`FotNiva + Fack1 + Fack2 + 5`) i Placement och Pad-längd fungerar: Fack1 360 -> 540 i
  Variabler och recompute flyttade alla hyllplan, hyllor och dörrar, förlängde stående stänger och dörrarnas L-järn
  (710 -> 890), utan fel och utan krockar.
- L-profil i `k.balk`: tvärsnittets b-ben går längs `oppning` (u), h-benet längs `w x u`. Hamnar h-benet åt fel
  håll: byt start och slut (w byter tecken). `k.gera` skär genom kroppens v-riktning, så v ska vara det ben som
  ska geras med (dörramens djupben).
- Sammanställningsritningen staplar vyerna på höjden: för ett 2,2 m högt objekt ryms fram + höger i 1:20 på A2;
  med planvyn krävs 1:25 (i 1:15 hamnar planvyn utanför bladet och över noterna).


## Linux / molnsession (FreeCAD från conda-forge, 2026-10-11)
- Ubuntu 24.04 har inget FreeCAD-paket och github.com nås inte från molnsessionen. `scripts/installera_linux.sh`
  tar FreeCAD från conda-forge (micromamba) och SheetMetal från jsDelivr-spegeln av GitHub.
- SheetMetal **0.8.x** (master) har ändrat `SheetMetalNewUnfolder`: `plat.utbred` ger
  `'BendInfo' object has no attribute 'transformed'`. Håll 0.7.24 tills plat.py anpassats.
- TechDraw kräver GUI: `freecad` med `QT_QPA_PLATFORM=offscreen` hänger, men `xvfb-run -a freecad` fungerar
  (fcapi.py gör det när DISPLAY saknas). FreeCAD kan segfaulta när det stängs – resultatet är redan skrivet.
- `ritning.py` igen på en fil som redan har blad segfaultade i `rensa()` när bladen togs bort medan TechDraw
  fortfarande räknade vyerna. Rättat: `pump(1.0)` först och vyerna tas bort före blad och mallar.
- Lägg inte `/opt/freecad/bin` först i PATH: då blir `python3` FreeCADs Python utan PyMuPDF och
  efterbehandlingen (PDF/PNG) faller. Använd system-Python; fcapi hittar FreeCAD ändå.
- FreeCAD 1.1 visar en modal dialog ("Migrate the configuration…") vid start om en annan versions
  konfiguration finns men inte den egna. Under xvfb blockerar den jobbet tills timeout utan logg.
  installera_linux.sh skapar därför `~/.config/FreeCAD/v1-1`. Samma dialog kan dyka upp på Windows efter
  en uppgradering – starta FreeCAD en gång för hand och svara på den.

## FreeCAD 1.1.3 på Linux: räcken, detaljblad och översikter (2026-10-18)
- **Symmetrisk Pocket "genom allt" skär ibland ingenting.** En FS20-stolpe med en geringsskiss i änden gav
  volymen oförändrad med `Type = ThroughAll`, `SideType = Symmetric`; "One side" skar halva, `Length` symmetrisk
  skar allt. Andra kroppar med samma uppställning skar rätt, så felet är inte förutsägbart. `pd.ficka` (och
  därmed `k.hal` och `k.gera`) kontrollerar nu volymen och gör om en sådan ficka till symmetrisk längd
  2 × kroppens diagonal + 10. En ficka som ändå inte skär något ger RuntimeError i stället för att tyst bli fel.
- **Ett kap tar bara bort det som ligger utanför planet.** Ett snett plattstål på högkant som kapas lodrätt
  precis i sin ände blir bara kapat på övre halvan (nedre halvan når aldrig planet). Bygg delen förlängd med
  (h/2)·|tan v| + några mm och kapa sedan (racke.py gör så för följare och handledare).
- `k.gera` skär i ett plan som innehåller tvärsnittets höjdriktning (`upp`). För ett liggande plattstål som ska
  kapas lodrätt behövs bredden i planet: `k.gera(o, a, b, riktning=tvärs)` (skissen läggs då i YZ).
- **TechDraws snitt med fri normal** (`DrawViewSection` med en sned `SectionNormal`, t.ex. vinkelrätt mot en
  sned handledare) gav fel geometri. Använd en vanlig `DrawViewPart` som tittar längs delen med bara de delar
  som ska synas som Source (delvyer på blad 2, `RITNING["delvyer"]`). En Pad-feature kan vara Source för att
  slippa en snäcka i änden; featurens Shape ska då mätas med kroppen (`getParentGeoFeatureGroup()`).
- Vyns storlek för en delvy ska räknas på hörnen (`Shape.Vertexes`), inte på lådan: sneda delar ger en
  axelparallell låda som är mycket större än det som syns, och skalan blev 1:10 i stället för 1:5.
- **`DrawViewDetail`**: `AnchorPoint` är i basvyns centrerade, oskalade koordinater (samma som `Start` på en
  kosmetisk linje genom punkten). Detaljvyerna räknas i bakgrunden: skapa alla, `recompute`, och vänta in
  `getVisibleEdges()` för var och en (upp till 30 s) innan måtten sätts och bladet exporteras; annars blir en
  detalj tom i PDF:en. Kanterna (`getEdgeByIndex`) är oskalade relativt detaljens mitt. En cirkel som ses
  nästan rakt framifrån kan komma som `Ellipse` med lika halvaxlar.
- `DrawViewAnnotation` har typsnittet som egenskap på objektet (`t.Font`), inte i ViewObject.
- `DrawViewBalloon`: `OriginX/Y` och `X/Y` är oskalade modellmått relativt vyns mitt. `EndType` väljs ur
  `getEnumerationsOfProperty("EndType")` ("Filled arrow" i 1.1), `EndTypeScale` 0,6 ger en kort pil.
- TechDraw-inställningar (färger, typsnitt, pilar) gäller bara jobbet de sätts i: sätt dem i varje jobb som
  ritar (`stall_in()`), annars blir ytor svarta och texter i standardtypsnittet.
- **Ytdetekteringen** (`TechDraw/General/HandleFaces`) hittade falska ytor i en framvy med rör och VKR (stora
  vita fält mellan handledaren och vyns kant). `sammanstallning.py` stänger av den; bladet blir enhetligt.
- **Att ta bort ritningsobjekt kraschar ibland FreeCAD** (segfault utan logg) när en fil med detaljblad ritas om.
  Ta bort i ordningen mått/bubblor/texter, detaljvyer, snitt, vyer, blad, mallar, med `KeepUpdated = False` på
  bladen och en kort `pump()` mellan grupperna (`rensa()`); tre omritningar i rad gick sedan utan krasch.
- **3D-bilder**: `ActiveView.setViewDirection` gav samma bild från alla håll. Sätt kamerans rotation med
  `setCameraOrientation(Rotation(matris))` och stäng av animeringen (`setAnimationEnabled(False)`), annars
  sparas bilden mitt i övergången. Är ett ritningsblad aktivt saknar ActiveView metoden: hämta 3D-vyn med
  `gd.mdiViewsOfType("Gui::View3DInventor")` (rendera.py).
- Synlighet för positionsbubblor: en rundstång eller ett rör har en enda cylinderyta, och ytans tyngdpunkt
  ligger på axeln (utanför ytan). Välj bland punkter spridda över ytan den vars normal pekar mot betraktaren,
  annars får runda delar ingen bubbla.
- Skissmått som heter `h` eller `t` fungerar, men går inte att använda i uttryck (`Constraints.t` tolkas som
  enheten ton). Döp mått som ska användas i uttryck till något längre (`Sida`, `Tjocklek`).
- `Quantity` från FreeCAD (t.ex. `ballong.OriginX`) går inte att räkna med tal direkt: använd `.Value`.
- Lambdas i en loop binder variabeln sent: spara talen i en dict eller som standardargument
  (`lambda x, z0=z0: ...`), annars får alla detaljer sista värdet.

## Stålstomme med svetsade balkar och många sammanställningar (takbjälklag, 2026-10-19)
- **Dubbla etiketter räknas upp.** FreeCAD tillåter som standard inte samma `Label` på två objekt: den andra
  delen "pl/1 PL10*255" blev "pl/1 PL10*256" och stubbarna "st/1 KCKR273*12.001", "*12.002". Det syntes som
  påhittade profiler i regelkontrollen, i mängdunderlagets namn och i glTF-exportens nodnamn. Jobben slår på
  `DuplicateLabels` (`fcapi.dubbla_etiketter()` i `kor_jobb`), och loggar och listor tar namnet ur egenskaperna
  Pos och Profil (`fcapi.etikett(o)`), så även äldre filer med uppräknade etiketter blir rätt.
- **L-profil som kantvinkel** (liggande ben under bjälklaget, stående ben mot väggen): med `upp=(0, 0, 1)` pekar
  det liggande benet åt `upp x w`, där w är riktningen start -> slut. Ska benet peka åt andra hållet: byt start och
  slut. Tvärsnittets låda ligger centrerad på linjen, så hälen hamnar b/2 från linjen.
- **Hål i ett stående ben** (ankare genom en vinkel mot väggen, riktning vinkelrätt mot balken) syns inte som
  cirklar i fram- eller planvyn och får ingen hålangivelse: lägg till en sidovy, `vyer=["fram", "plan", "vanster"]`.
- **Långa remsor i svetsade balkar** (flänsar och liv på 10–17 m) gav FEL mot plåtformatet 1500 x 3000.
  `remsa_langd_mm` i verkstad.json prövar remsor (bredd inom plåtformatets kortsida) mot remslängden i stället,
  och längre remsor ger VARNING om stumsvetsad skarv.
- **Uppdragets gemensamma modul** (`egna/<uppdrag>.py` med stomnät, nivåer och kunduppgifter, som både
  sammanställningarna och översikten importerar) var inte ignorerad av git och syntes som en ny fil att committa.
  `.gitignore` ignorerar nu `egna/*.py`; kontrollera ändå `git status` innan något committas.
- Sammanställningar som delar geometri med en översikt: lägg byggfunktionerna (balk, pelare) i uppdragsmodulen
  med en avbildning lokal -> global (`axel="x"|"-x"|"y"|"-y"`, origo) och låt både sammanställningsskriptet
  (lokalt) och översikten (globalt) anropa dem. Ge delarna ett prefix per märke i översikten (`pfx="sb11"`), så
  att samma positionsnummer i olika märken inte krockar.

## Underlag från kunden
- Bilagor i Gmail-trådar går inte alltid att hämta som bilaga via connectorn: hämta meddelandet i RAW-format,
  spara JSON:en och packa upp den med Pythons `email`-modul till egna filer.
- Scannade PDF:er har ingen text: läs bilderna (underlag.py ger rutor i 300 dpi med höjd kontrast). En sida i
  hög upplösning som en enda bild skalas ner av bildvisningen och små mått blir oläsliga – läs rutorna eller zooma.
- **Fotade ritningar ligger på tvären** (ett liggande A1-blad fotat i porträtt): texten läses nedifrån och upp.
  `underlag.py zoom ... --rotera 90` vänder utsnittet; rutan anges i originalets läge. Kontrollera vridningen på
  stomlinjernas siffror och bokstäver innan läget tolkas: fel håll speglar planen.
- **Mått som bara står "ENL. PLAN"** finns på ett annat blad: be om det bladet (t.ex. stomplanen) innan något
  skalas. Förklaringsrutan på stomplanen ger ofta profilerna (SP01 = VKR 200x200x8, SB01 = HSQ H270:B200x450).
- **Skalade mått ur foton** blir ungefärliga (perspektiv, veck, ±2–5 %): mät mot två stomlinjer nära punkten
  (`underlag.py skala`) och avrunda till rimliga värden; skriv SKALAT/ANTAGET.

## Installation (conda-forge, micromamba)
- `micromamba install` av ett extra paket (calculix, ifcopenshell) utan att låsa FreeCAD kan byta FreeCAD 1.1.3 mot
  en utvecklingsversion (freecad-2026.x med OCCT 8) som inte startar: jobben hänger utan logg. Lås alltid
  `freecad=1.1.3` i samma kommando. Återställ med `micromamba install -p /opt/freecad freecad=1.1.3 occt=7.9.3`.
- conda-paketet ifcopenshell kräver OCCT 8 och går inte ihop med FreeCAD 1.1.3. Pip-hjulet har eget OCCT: lägg
  det i en egen mapp (`pip install --no-deps --target /opt/freecad-extra ifcopenshell`) och lägg mappen i sys.path
  i jobbet (export.py).

## TechDraw, SheetMetal, FEM och jobben (1.1.3)
- `DrawViewSymbol` ritar SVG-symbolens mm rätt i 1.1 men med faktorn 90/96 i 1.0: skala 96/90 bara i 1.0
  (sammanstallning.py `symbol`), annars blir materiallistan 6 % för stor och hamnar utanför ramen.
- `SMBendWall` lägger kanten utanför basplåten och flänsens höjd räknas inte från undersidan: mät lådan och justera
  basens mått, `length` och placeringen (stal.trag). Utan `SMViewProviderTree` på objektet syns det inte i GUI:t
  och inte i 3D-bilderna; dölj basen.
- SheetMetal-delar är compounds: `Shape.CenterOfMass` finns inte, räkna tyngdpunkten per solid.
- **Tråg som flyttas efter bygget** (stal.trag): formen följer skissen, så lådan mätt i skissens system ändras inte
  när skissen flyttas. Flyttningen ska räknas från ursprungsläget (`mitt`), inte från förra varvets läge: annars
  dubblerades den och tråget hamnade en plåttjocklek fel när bara en eller två sidor bockades eller delens z pekade
  i negativ riktning (lock och hyllor med kanterna nedåt). Måtten var rätt, bara läget fel – syns som krockar.
- Ett lock med bockade kanter mot en stomme av VKR: bockens inre radie ligger mot rörets kant. Mot en rörände som
  kapats rakt blir det en krock på några mm3; låt locket ligga mot rörens rundade längskanter (hörnstolparna slutar
  under ett övre rör som går hela djupet, konstruktioner/skap.py) eller låt ryggen täcka lockets bakkant.
- **Snitten på sammanställningsritningen** staplades i en kolumn som bara slutade ovanför materiallistan och kunde
  hamna över noterna nere till vänster. Snitten läggs nu i kolumner (sammanstallning.py `packa`): en ny kolumn till
  höger när nästa snitt inte ryms ovanför noterna eller materiallistan där kolumnen står.
- **Materiallistan på A2** hade alltid 5 mm rader och gick vid fler än ca 59 positioner upp genom ETAPP-rutan och
  ramen. Raderna blir nu tätare när listan annars inte ryms (sammanstallning.py `ml_radhojd`, minst `RAD_MIN` = 3
  mm). Hålangivelserna och bubblorna i raden under en vy spreds över hela bladets bredd (x 44–570) och kunde hamna
  ovanpå materiallistan, titelrutan eller noterna; raden kortas nu förbi dem (`radgrans`).
- `importSVG` vänder redan SVG:ns y-axel uppåt: vänd den inte en gång till.
- `Part.makeWireString(text, typsnitt, storlek, spärrning)` ger textens konturer utan Draft-objekt; osifont följer med
  FreeCAD (`Mod/TechDraw/Resources/fonts`).
- FEM: `makeConstraintForce.Direction` är en referens (yta eller kant), inte en vektor; `Reversed` vänder den.
  `FemToolsCcx`: `update_objects`, `setup_working_dir`, `setup_ccx`, `check_prerequisites`, `write_inp_file`,
  `ccx_run`, `load_results`; resultatet har `vonMises` och `DisplacementLengths`.
- Jobbets resultat-dict får inte ha nyckeln `ok` (krockar med `fcapi.avsluta(ok, ...)`): använd t.ex. `godkand`.
- argparse tolkar ett värde som börjar med `-` som en flagga: skriv `--fast=-z`, inte `--fast -z`.
