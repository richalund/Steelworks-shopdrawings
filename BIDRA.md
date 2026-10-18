# Bidra till skillen

Skillen blir bättre av att användas på riktiga jobb. Den som ritar något och märker att något saknas eller blir
fel ber Claude rätta det och skriver **"skicka in förbättringen"**. Ingen kunskap om git eller programmering
behövs; Claude gör ändringen allmängiltig, testar den och skickar ett förslag (en *pull request*, PR) som
granskas innan det blir en del av skillen för alla.

## Roller

| Roll | Kan | Hur man blir det |
|---|---|---|
| **Användare** | rita med skillen i en egen session (se ANVANDA.md) | GitHub-konto + claude.ai, inget mer (repot är publikt) |
| **Bidragsgivare** | skicka in förbättringar (PR) direkt från sin session | inbjuden som *collaborator* till repot |
| **Granskare** | godkänna andras PR:er; ett godkännande räcker för att de går in | inbjuden *och* uppskriven i `.github/CODEOWNERS` |
| **Ägare** | allt ovan, ändra inställningar och granskarlistan | richalund |

Ingen kan godkänna sin egen PR. När en granskare godkänt och testerna är gröna går PR:en in automatiskt
(auto-merge), utan att ägaren behöver bekräfta.

## Så skickar en bidragsgivare in en förbättring
1. Starta en session på https://claude.ai/code med repot `richalund/Steelworks-shopdrawings` och rita som vanligt.
2. Skriv "skicka in förbättringen" (eller "det här borde finnas i skillen"). Claude
   - flyttar det allmängiltiga från uppdragets skript in i skillen, utan kunduppgifter och med kundens
     särdrag som val i stället för standard,
   - arbetar på en egen gren `forbattring/<namn>`, uppdaterar dokumentationen och kör `scripts/testa.py`,
   - öppnar PR:en med mallen `.github/pull_request_template.md`, slår på auto-merge och ger dig länken.
3. GitHub kör testerna igen (Actions: "Testa skillen") och lägger bilderna som nedladdning på PR:en. Testerna
   jämför ritningarna med referensbilderna i `tester/referens/`; en ändrad ritning ger en diffbild (ändringarna i
   rött) att titta på. Är ändringen avsedd följer nya referensbilder med i PR:en.

## Så granskar en granskare
Öppna PR-länken (GitHub-appen eller webben) och titta på beskrivningen, bilderna och testresultatet. Eller
starta en session och skriv **"granska PR 12"**: Claude läser ändringarna, kontrollerar testerna och bilderna
och skriver vad som är bra och vad som behöver rättas. Skriv sedan "godkänn" (Claude godkänner i ditt namn) eller
"be om ändringar". Godkänn bara det som är allmängiltigt, testat och dokumenterat; tveka hellre och fråga.

## Ägarens inställningar (en gång)
Det här görs på GitHub av ägaren, det kan inte Claude göra:
1. **Bjud in** bidragsgivare och granskare: repot → Settings → Collaborators → Add people (GitHub-användarnamn).
2. **Skydda main:** Settings → Rules → Rulesets → New branch ruleset (eller Settings → Branches → Add rule) för
   `main`: *Require a pull request before merging* med *Required approvals: 1* och *Require review from Code
   Owners*, *Require status checks to pass* med checken **testa** (jobbet i "Testa skillen"), och *Block force
   pushes*. Lägg dig själv i bypass-listan om du vill kunna gå förbi i nödfall.
3. **Auto-merge:** Settings → General → Pull Requests → *Allow auto-merge*.
4. **Granskare:** lägg till deras användarnamn i `.github/CODEOWNERS` (eller be Claude göra det i en PR).

## Regler för innehållet
- Inga kunduppgifter, adresser, priser eller foton från kunder i skillen; uppdragets filer ligger i `egna/`.
- Allmängiltigt: det som bara gäller ett uppdrag blir ett val med neutralt standardvärde.
- Testat: `python3 .claude/skills/freecad-styrning/scripts/testa.py` utan FEL, bilderna och diffbilderna granskade
  med ögonen.
- Dokumenterat: SKILL.md, verktyg i `references/verktyg.md`, nya fällor i `references/fallor.md`, konventioner i
  `references/smidesritningar.md`. Datumet i `VERSION` höjt.
