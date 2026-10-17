# Egna skript och uppgifter

Skillen i `.claude/skills/freecad-styrning/` ändras inte av användaren. Allt eget läggs här, så att skillen kan
uppdateras från Steelworks-shopdrawings utan att något går förlorat:

- `egna/konstruktioner/*.py` – egna konstruktionsskript (sammanställningar), samma form som
  `.claude/skills/freecad-styrning/konstruktioner/balkongram.py`
- `egna/delar/*.py` – egna delskript för Part Design, samma form som `.../delar/fotplatta.py`
- `egna/foretag.json` och loggan – företagsuppgifter till titelblocket (`scripts/foretag.py satt --fil egna/foretag.json`)
- `ut/` – allt som genereras (ignoreras av git)

Behöver ett skript en hjälpfunktion som skillen saknar: skriv den i skriptet (API:t i `scripts/pd.py` och
`scripts/stal.py` är tillgängligt), inte i skillens filer.

`foretag.json` är ignorerad av git. I en privat fork kan raden tas bort ur `.gitignore` så att uppgifterna följer med.
