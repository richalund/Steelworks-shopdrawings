# Använda skillen (utan att bidra)

För dig som vill rita och offerera smide med skillen och inte behöver ändra den. Du behöver inte kunna git,
programmering eller FreeCAD. Du skriver till Claude som till en ritare, och Claude gör resten.

## Det här behöver du
- Ett abonnemang på Claude, Pro eller Max (https://claude.ai). Claude Code ingår i båda.
- Ett gratis GitHub-konto (https://github.com), kopplat till Claude på https://claude.ai/connect-github.
- Claude-appen på telefonen (fliken **Code**), eller webbläsaren på datorn (https://claude.ai/code). Allt körs i
  molnet, så det fungerar likadant på båda.

Repot är publikt, så du behöver ingen inbjudan för att använda skillen. Inbjudan behövs bara för den som ska skicka
in förbättringar (se BIDRA.md).

## Starta ett jobb
1. Öppna **Code** i appen, välj repot `richalund/Steelworks-shopdrawings` och starta en ny session.
2. Skriv vad du vill ha och bifoga det du har. Första gången i en session installeras FreeCAD (10–15 minuter);
   du kan skriva direkt, Claude väntar in installationen.
3. Svara på frågorna om företagsnamn och signatur till titelblocket (en gång per session).
4. Titta på bilderna Claude visar och be om ändringar. Ladda ner filerna när du är nöjd.

Starta en ny session för varje nytt jobb. Då blir det snabbare och billigare än att fortsätta i en lång session.

## Vad du kan be om
Du kan börja med bara en mening, med foton, eller med en ritning.

- **Bara text:** *"Rita en grind 1000 bred och 1100 hög med ram i VKR40, nedre fyllning i plåt och en solfjäder i
  mässing upptill. Stolpar VKR80 som gjuts ner."* Claude väljer vanliga mått för det du inte sagt och skriver dem
  som antaganden på ritningen.
- **Foton och mått:** *"Här är fyra foton på trappan. Sex steg, ca 1,2 m bred. Rita räcket med plattstångshandledare
  och fyrkantsspjälor."* Måtten Claude antar ur fotona står i noterna och ska kontrollmätas på plats.
- **En befintlig ritning:** bifoga arkitektens PDF, en scannad eller fotad ritning eller en DXF: *"Gör
  tillverkningsritningar av räcket R3 på den här ritningen."* Claude läser ritningen, även små mått i en scannad
  PDF, och frågar om det som inte går att läsa säkert.
- **Ett mail från en kund:** *"Läs mailet från Patrik om grinden och gör en offertritning."* (kräver att Gmail är
  kopplat till Claude).
- **Ändringar:** *"Gör grinden 1200 bred"*, *"handledaren i rör 42,4"*, *"lägg till ett snitt genom stolpen"*,
  *"gör ritningen på engelska"*, *"visa grinden öppen 90 grader"*.
- **Kontroller:** *"Slår grinden i något när den öppnas?"*, *"Hur stor blir lasten på gångjärnen?"*,
  *"Klarar handledaren 0,5 kN/m?"* (överslag; bärande konstruktioner dimensioneras av en konstruktör).
- **Till verkstaden och kalkylen:** *"Gör DXF till lasern"*, *"Gör prisunderlag för 3 st"*, *"Gör ett
  beställningspaket"*, *"Exportera till IFC till arkitekten"*, *"Gör en 3D-fil kunden kan öppna i mobilen"* (glTF).

## Det här får du
| Fil | Till |
|---|---|
| PDF och PNG | ritningen (A2-sammanställning, A3-delritning, detaljblad, planritning) |
| `_materiallista.csv` | materiallistan (öppnas i Excel) |
| `_kontur.dxf`, `_utbredning.dxf` | laser och kantpress |
| `.step`, `.ifc`, `.glb` | CAD, arkitektens modell, 3D i webbläsaren |
| `_3d_iso.png` m.fl. | 3D-bilder till offerten |
| `_kalkyl.csv` | prisunderlag (och pris om verkstaden lagt in sina priser) |
| `_bestallning.zip` | allt ovan i ett paket, för beställning |
| `.FCStd` | modellen och ritningen, går att öppna och ändra i FreeCAD |

## Bra att veta
- **Mått hittas inte på.** Claude frågar, eller skriver tydligt vad som är antaget. Kontrollera alltid måtten på
  ritningen innan något tillverkas.
- **Företagsuppgifterna** följer inte med till nästa session. Be Claude spara dem, eller lägg dem som
  miljövariabler i molnmiljöns inställningar.
- **Användningsgränser:** abonnemanget har en gräns per fem timmar och per vecka, som delas med vanlig chatt. En
  ritning i en ny session tar en liten del; en lång session med många ändringar tar mer. Blir det stopp: vänta
  tills gränsen återställs, eller uppgradera.
- **Ansvar:** ritningarna är underlag. Den som tillverkar och säljer ansvarar för att produkten är rätt
  dimensionerad och uppfyller kraven (t.ex. räckeshöjd, spjälavstånd, CE-märkning).
- **Blir något fel eller saknas något?** Säg det till Claude. Har du blivit inbjuden kan du skriva *"skicka in
  förbättringen"* så blir det bättre för alla (BIDRA.md); annars räcker det att berätta för den som bjöd in dig.
