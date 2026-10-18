# Steelworks Shopdrawings – instruktioner till kodagenten

Gäller alla kodagenter (Claude Code, OpenAI Codex, GitHub Copilot coding agent, Cursor m.fl.). Claude Code läser
dessutom `CLAUDE.md`, som hänvisar hit.

Repot innehåller skillen `freecad-styrning`: tillverkningsritningar för smide och plåt i FreeCAD från Python – från
text, foton, mail eller befintliga (även scannade) ritningar – med klassiska sammanställningsritningar, DXF, STEP,
glTF/IFC, 3D-bilder, mängdunderlag, beställningspaket och leverans till en tillverkare.

**Läs `.claude/skills/freecad-styrning/SKILL.md` innan du gör något med en ritning, en modell eller skillen.** Den
beskriver flödet, reglerna och kommandona; verktygens API står i `references/verktyg.md` och kända fällor i
`references/fallor.md`. Samma mapp nås som `.agents/skills/freecad-styrning` och `.github/skills/freecad-styrning`.
Användarens guide: `ANVANDA.md`. Bidrag: `BIDRA.md`.

## Installation
- FreeCAD installeras med `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` (10–15 min första
  gången, sedan sekunder; kan köras igen). Den hamnar i `/opt/freecad`, eller i `~/.local/opt/freecad` utan root och
  sudo. Claude Code kör den från SessionStart-hooken, Copilot från `.github/workflows/copilot-setup-steps.yml`,
  Cursor från `.cursor/environment.json`, och i Codex anges den som miljöns installationsskript. Finns inte
  `freecad` i någon av mapparna när du ska rita: kör skriptet själv och vänta.
- Nätet: installationen behöver github.com med release-assets/objects.githubusercontent.com, conda.anaconda.org,
  pypi.org, files.pythonhosted.org och Ubuntus paketarkiv (allt ingår i Claude Codes standardnät "Trusted"; i andra
  agenter ska de vara tillåtna), med micro.mamba.pm och cdn.jsdelivr.net/data.jsdelivr.com som reserv. Källorna:
  raw.githubusercontent.com och eurocodeapplied.com. Komponenter söks upp med webbsök.
- Kör skripten med system-`python3`, inte FreeCADs Python i `/opt/freecad/bin`.

## Regler
- Lägg allt som genereras (FCStd, PDF, PNG, DXF, STEP) i `ut/` i repot, som är ignorerad av git. Visa PNG:erna för
  användaren efter varje ritning (bifoga eller öppna dem i chatten om agenten kan, annars beskriv dem och se nästa
  punkt). Vill användaren ha filerna någon annanstans, kopiera dit dem efteråt.
- Varje uppdrag sparas i sin projektmapp (t.ex. jobbets mapp i Google Drive, hittad på uppdragsnummer eller
  kundnamn), inte i git: ingen gren, ingen fork, aldrig i det här publika repot. PDF, 3D-bilder, modeller,
  egna skript och en `LASMIG.md` (SKILL.md, "Spara uppdraget i projektmappen"). Kunduppgifter committas aldrig.
- Kan användaren bara se det som committas (Codex, Copilot, Cursor) och repot är hens eget privata repo: kopiera
  det hen ska ha till `leverans/<uppdrag>/` (undantaget i `.gitignore`), committa på uppdragets gren och ge
  länken. Aldrig på `main`, aldrig i ett publikt repo.
- Frågor till användaren: använd agentens frågeformulär om det finns, annars en kort fråga i chatten med
  numrerade alternativ. Fråga bara om det som avgör utförandet.
- Företagsuppgifterna i titelblocket saknas som standard. Kör
  `python3 .claude/skills/freecad-styrning/scripts/foretag.py visa` före första ritningen; står det SAKNAS, fråga
  användaren om företagsnamn, adress, signatur, handläggare, ansvarig, land och eventuell logga, och spara med
  `foretag.py satt ...`. Fråga inte igen i samma session.
- Hitta aldrig på mått. Profilmått och materialkvaliteter hämtas från öppna källor via `scripts/kallor.py` och
  ritningen anger var de är verifierade; finns profilen eller kvaliteten inte i någon källa, sök efter tabellen,
  säg till användaren och lägg in måtten med källan i en kommentar.
- Beslag, lås, glas och andra inköpta komponenter finns inte i skillen: sök upp en produkt hos leverantörer i
  användarens land, lägg in databladets mått med källan (`scripts/komponenter.py`) och rita den med
  `k.inkop(komponent=...)` (SKILL.md, "Komponenter").
- Inga priser: skillen ger mängdunderlag, prissättningen görs av tillverkaren när underlaget kommit in. Ge inte
  användaren prisuppskattningar.
- När användaren är nöjd: fråga om underlaget ska skickas till en tillverkare (anbud@smide.com förifylld, valfri
  adress), gör paketet och mailet med `scripts/paket.py` och skicka aldrig något utan ett uttryckligt ja
  (SKILL.md, "Leverans till en tillverkare").
- Kunden kan ge bara text, foton, mail eller en ritning: läs ritningar (PDF, scannade, DXF) med
  `scripts/underlag.py` och hitta aldrig på mått som inte går att läsa.
- Uppdragets filer ändrar inte skillen: egna konstruktionsskript i `egna/konstruktioner/`, delskript i
  `egna/delar/`, ritskript för översikter i `egna/ritningar/`, motiv och typsnitt i `egna/ornament/`,
  företagsuppgifter i `egna/foretag.json`, verkstadens gränser i `egna/verkstad.json`, komponenter i
  `egna/komponenter.json` och mottagare i `egna/leverans.json`. Se `egna/README.md`. Kunduppgifter läggs aldrig i
  skillen.
- Skillen (`.claude/skills/freecad-styrning/`) förbättras bara genom en pull request mot `main`, enligt avsnittet
  "Eget material, och förbättringar av skillen" i SKILL.md: föreslå förbättringen för användaren, gör den generell
  (inga kunduppgifter, kundens särdrag som val), arbeta på en gren `forbattring/<namn>`, kör
  `python3 .claude/skills/freecad-styrning/scripts/testa.py` och öppna PR:en med `.github/pull_request_template.md`.
  Användaren behöver inte kunna git: "skicka in förbättringen" räcker. Slå på auto-merge på PR:en om agenten kan.
  Roller (bidragsgivare, granskare i `.github/CODEOWNERS`) och hur en PR granskas står i `BIDRA.md`.
