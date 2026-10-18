# Steelworks Shopdrawings

Repot innehåller skillen `freecad-styrning` (`.claude/skills/freecad-styrning/SKILL.md`): tillverkningsritningar
för smide och plåt i FreeCAD från Python – från text, foton, mail eller befintliga (även scannade) ritningar –
med klassiska sammanställningsritningar, DXF, STEP, glTF/IFC, 3D-bilder, prisunderlag och beställningspaket.
Användning utan att bidra: `ANVANDA.md`. Bidrag: `BIDRA.md`.

- I en molnsession installerar SessionStart-hooken FreeCAD i bakgrunden (10–15 min första gången i en
  ny container). Vänta på att `/opt/freecad/bin/freecad` finns innan första ritningen, eller kör
  `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` själv.
- Kör skripten med system-`python3`, inte FreeCADs Python i `/opt/freecad/bin`.
- Lägg allt som genereras (FCStd, PDF, PNG, DXF, STEP) i mappen `ut/` i repot, som är ignorerad av git.
  Visa PNG:erna för användaren efter varje ritning. Vill användaren ha filerna någon annanstans, kopiera
  dit dem efteråt.
- Företagsuppgifterna i titelblocket saknas som standard. Kör
  `python3 .claude/skills/freecad-styrning/scripts/foretag.py visa` före första ritningen; står det SAKNAS,
  fråga användaren (AskUserQuestion-formuläret) om företagsnamn, adress, signatur, handläggare, ansvarig och
  eventuell logga, och spara med `foretag.py satt ...`. Fråga inte igen i samma session.
- Profilmått och materialkvaliteter hämtas från öppna källor på nätet via `scripts/kallor.py` (cache i
  `~/.cache/freecad-styrning/kallor`) och ritningen anger var de är verifierade. Hitta aldrig på mått: finns
  profilen eller kvaliteten inte i någon källa, sök efter tabellen, säg till användaren och lägg in måtten
  med källan i en kommentar.
- Uppdragets filer ändrar inte skillen: egna konstruktionsskript läggs i `egna/konstruktioner/`, delskript i
  `egna/delar/`, ritskript för översikter i `egna/ritningar/`, motiv och typsnitt i `egna/ornament/`,
  företagsuppgifter i `egna/foretag.json`, verkstadens gränser i `egna/verkstad.json` och priser i
  `egna/priser.json`. Se `egna/README.md`. Priser och kunduppgifter läggs aldrig i skillen.
- Kunden kan ge bara text, foton, mail eller en ritning: läs ritningar (PDF, scannade, DXF) med
  `scripts/underlag.py` och hitta aldrig på mått som inte går att läsa.
- Skillen (`.claude/skills/freecad-styrning/`) förbättras bara genom en pull request mot `main`, enligt avsnittet
  "Eget material, och förbättringar av skillen" i SKILL.md: föreslå förbättringen för användaren, gör den
  generell (inga kunduppgifter, kundens särdrag som val), arbeta på en gren `forbattring/<namn>`, kör
  `python3 .claude/skills/freecad-styrning/scripts/testa.py` och öppna PR:en med `.github/pull_request_template.md`.
  Användaren behöver inte kunna git: "skicka in förbättringen" räcker. Slå på auto-merge på PR:en. Roller
  (bidragsgivare, granskare i `.github/CODEOWNERS`) och hur en PR granskas står i `BIDRA.md`.
