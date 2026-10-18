# Egna skript och uppgifter

Skillen i `.claude/skills/freecad-styrning/` ändras inte för ett enskilt uppdrag. Allt eget läggs här, så att
skillen kan uppdateras från Steelworks-shopdrawings utan att något går förlorat (förbättringar som fler har nytta
av skickas in till skillen som en pull request, se SKILL.md):

- `egna/konstruktioner/*.py` – egna konstruktionsskript (sammanställningar), samma form som
  `.claude/skills/freecad-styrning/konstruktioner/balkongram.py`
- `egna/delar/*.py` – egna delskript för Part Design, samma form som `.../delar/fotplatta.py`
- `egna/ritningar/*.py` – ritskript för översikts- och planritningar (`scripts/oversikt.py`)
- `egna/foretag.json` och loggan – företagsuppgifter till titelblocket (`scripts/foretag.py satt --fil egna/foretag.json`)
- `egna/verkstad.json` – verkstadens gränser för regelkontrollen (kopia av `.claude/skills/freecad-styrning/mallar/verkstad.json`)
- `egna/komponenter.json` – inköpta komponenter (beslag, lås, glas) med databladets mått och källa (`scripts/komponenter.py`)
- `egna/leverans.json` – förifylld mottagare när underlaget skickas (kopia av `.../mallar/leverans.json`)
- `egna/ornament/` – egna SVG-motiv och typsnitt till ornament (`scripts/ornament.py`)
- `ut/` – allt som genereras (ignoreras av git)

Behöver ett skript något som skillen saknar: skriv det först i skriptet. Visar det sig vara allmängiltigt,
föreslå att det skickas in till skillen. Delar som `k.balk`, `k.plat` och `k.skiva` inte täcker byggs med `k.egen`
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

`foretag.json` och uppdragens skript (`konstruktioner/`, `delar/`, `ritningar/`) är ignorerade av git. Ett
uppdrag lämnas i chatten som en PDF och en zip (SKILL.md, "Filerna till användaren"), inte i repot. Verkstadens egna
filer (`foretag.json`, `verkstad.json`, `komponenter.json`) kan committas i ett eget privat repo (en importerad
kopia, inte en fork: en fork av ett publikt repo är publik).
