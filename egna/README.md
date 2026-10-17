# Egna skript och uppgifter

Skillen i `.claude/skills/freecad-styrning/` ändras inte av användaren. Allt eget läggs här, så att skillen kan
uppdateras från Steelworks-shopdrawings utan att något går förlorat:

- `egna/konstruktioner/*.py` – egna konstruktionsskript (sammanställningar), samma form som
  `.claude/skills/freecad-styrning/konstruktioner/balkongram.py`
- `egna/delar/*.py` – egna delskript för Part Design, samma form som `.../delar/fotplatta.py`
- `egna/foretag.json` och loggan – företagsuppgifter till titelblocket (`scripts/foretag.py satt --fil egna/foretag.json`)
- `ut/` – allt som genereras (ignoreras av git)

Behöver ett skript något som skillen saknar: skriv det i skriptet, inte i skillens filer. Det är regeln, för
varje ritning har sina egna utmaningar. Delar som `k.balk`, `k.plat` och `k.skiva` inte täcker byggs med `k.egen`
och Part Design-API:t (`.claude/skills/freecad-styrning/references/partdesign.md`):

```python
def bygg(k, v):
    def fastplatta(d):                                   # d = pd.Del: skisser och features kring kroppens origo
        sk = d.skiss("Kontur", "XY")
        sk.rundad_rektangel(120, 80, 10, namn=("b", "h", "r"))
        d.kloss(sk, 6, "Tjocklek")
        hal = d.skiss("Hal", "XY")
        hal.halbild(9, 90, 50)                           # 4 hål Ø9, c/c 90 x 50
        d.ficka(hal)
    k.egen("pl/5", "PL6*80", fastplatta, mitt=(300, 0, 150), rot=((0, 0, 1), (0, 1, 0), (-1, 0, 0)), material="S235JR")
```

`rot` är kroppens x-, y- och z-riktning i konstruktionen (här står plattan på högkant). Hjälpfunktioner som
används i flera egna skript läggs i en egen modul i `egna/`, t.ex. `egna/hjalp.py`, och importeras därifrån.

`foretag.json` är ignorerad av git. I en privat fork kan raden tas bort ur `.gitignore` så att uppgifterna följer med.
