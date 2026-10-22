# Räcken (scripts/racke.py, konstruktioner/racke.py)

Läs när ett räcke, trappräcke, balkongräcke eller en grind med räckesfyllnad ska ritas eller granskas.

## Arbetsgång
1. Kopiera `konstruktioner/racke.py` till `egna/konstruktioner/<projekt>.py`. Sätt Variabler (längd, höjd,
   lutning, stolpdelning, golvspalt) och profiler i `r.ram(...)`. Profiler för vanliga räcken: stolpe PL12*50
   eller VKR40*3–VKR60*4, handledare PL8*50 (plant), RÖR42.4*2.6 eller VKR40*3, liggare PL8*40, spjälor
   PL8*25, RHS20*20*2 eller D12–D16. `"PLt*b:plan"` ställer plattstålet med bredden i räckets plan.
2. Välj utfyllnad: `Spjalor(profil, max_oppning)`, `Ovaler(b, profil, delning, topp, botten, liggare)`,
   `Sprang(profil, delning, monster)`, `Skiva(t, material)`. Annat mönster (rutor, cirklar, kors, nät i ram,
   lameller): skriv en klass i det egna skriptet med `bygg(r, a, b, uk, ok, i)` och `snittlage(a, b)`, där
   `a`, `b` är fackets kanter i x och `uk`, `ok` fackets under- och överkant (Linje: `z(x)`, `punkt(x)`,
   `riktning`). Bygg stänger med `r.stang(prefix, profil, a, b, kap_a, kap_b)` och bockade ovaler med
   `r.oval(...)`: då följer öppningskontrollen och positionsnumren med.
3. `bygg` loggar räckeskontrollen. Avviker den: ändra mönster/delning, eller låt avvikelsen stå i noterna om
   räcket inte omfattas (t.ex. befintligt räcke som renoveras, eller där barn inte vistas) och säg det.
4. `ritning`: delningsmåtten sätts automatiskt, snitt A läggs genom första spjälan/ovalen. Kontrollera PNG:en.

## Krav som kontrolleras (KRAV i racke.py)
Allmänna råd i BBR 8:2321–8:2322 (BFS 2011:6 t.o.m. BFS 2020:4). Nya byggregler gäller från 2025-07-01
(de gamla fick väljas t.o.m. 2026-06-30) – stäm av mot gällande regler innan ritningen lämnas ut.
- Höjd: trapplopp 0,9 m; trapplan inom bostad 0,9 m (1,1 m om våningshöjden > 3,0 m); balkong, loftgång och
  trapplan utanför bostaden 1,1 m.
- Öppningar: högst 0,1 m där barn kan vistas (kontrolleras som största fria cirkel i räckets plan).
- Spalt mellan räckets underkant och stegnos högst 50 mm, mot golv/trapplan högst 100 mm.
- Inte klätterbart upp till 0,8 m (vågräta liggare som fotsteg) – kontrolleras inte automatiskt.
Källor: Boverkets PBL-kunskapsbank (Räcken och ledstänger, Trappor), BBR avsnitt 8.

## Vad som inte ritas
Svetsar (skriv a-mått i noterna), glasklämmor och lister, ändavslutningar på handledare (ändlock, böj ner),
ledstång på vägg, bultar och kemankare (hålangivelserna anger dimension), lastberäkning (räckets bärförmåga
mot horisontallast enligt EN 1991-1-1 tab. 6.12 kontrolleras separat när det behövs).

## Begränsningar
- Ovaler bara i plana räcken. Språngmönstret: grannstänger får inte springa mot varandra eller isär
  (ValueError). Lägena är tal: ändrad variabel kräver ny `bygg`.
- Golvlinjen är rak. Ett trappräcke som byter lutning (vilplan) görs som två räcken eller i ett eget skript.
