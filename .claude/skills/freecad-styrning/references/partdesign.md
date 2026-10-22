# Part Design-API (scripts/pd.py), testat i FreeCAD 1.0.1 2026-10-10

Ett delskript körs inne i FreeCAD av `partdesign.py bygg`:
```python
NAMN = "Fotplatta"                                   # kroppens etikett
VARIABLER = [("Bredd", 250, "mm, plattans bredd (X)"), ...]   # (alias, standardvärde, beskrivning)

def bygg(d):                                         # d = pd.Del
    sk = d.skiss("Kontur", "XY")
    sk.rundad_rektangel("Bredd", "Langd", "Hornradie")
    d.kloss(sk, "Tjocklek", "Platta")
```
Använd ASCII i variabel- och objektnamn (Hojd, HalD, CCx): å/ä/ö blir `__` i objektnamn och fungerar inte
som alias. Ge features och skisser olika namn (annars blir det `Platta001`).

## Mått och uttryck
Alla mått tar tal (fast mått) eller text (uttryck): `"Bredd"`, `"Bredd/2 - Kantavstand"`,
`"(Ytterdiameter - Innerdiameter)/2"`. Variabelnamn får prefixet `Variabler.` automatiskt. Vinklar i grader.
- Ett mått som är exakt en variabel får variabelns namn (`Bredd`, dubblett blir `Bredd_2`) och sätts ut på
  ritningen. Andra uttryck får namnet `_m<n>` och sätts inte ut. `namn="Godstjocklek"` ger eget namn,
  `namn=""` tvingar bort det från ritningen.
- `d.uttryck(v)` ger (uttryck, värde), `d.satt(obj, "Egenskap", v)` sätter en egenskap med uttryck,
  `d.kombi("{0} - {1}/2", "Mitt", "Bredd")` bygger ett uttryck av flera mått.

## Skisser (`d.skiss(namn, plan, forskjutning=0, vand=False)`)
Skisser ligger alltid på kroppens origoplan, förskjutna längs normalen (uttryck tillåtet), aldrig på ytor:
då följer de med när måtten ändras.

| plan | skissens x | skissens y | normal |
|------|-----------|-----------|--------|
| XY   | X         | Y         | +Z     |
| XZ   | X         | Z         | -Y     |
| YZ   | Y         | Z         | +X     |

Hjälpare (returnerar geometriindex; alla låser geometrin fullt):
- `rektangel(b, h, mitt=(0, 0) | horn=(x, y), namn=(nb, nh))`
- `rundad_rektangel(b, h, r, mitt=(0, 0) | horn=(x, y), namn=(nb, nh, nr))` – tangerande bågar i skissen
  (bättre än Fillet: inga kanter att leta).
- `stadion(b, h, mitt=(0, 0), namn=(nb, nraka))` – stående oval med raka sidor (halvcirklar i ändarna, radie b/2);
  två i samma skiss (yttre och inre) ger en ring, t.ex. en oval av bockat plattstål.
- `cirkel(d, mitt=(x, y), namn=None)`
- `halbild(d, ccx, ccy=0, mitt=(0, 0))` – 4 hål i rektangel, eller 2 på rad om ccx eller ccy är 0.
  Mittens läge blir namngivet mått om det är en variabel (t.ex. `mitt=(0, "HalHojd")`).
- `profil(punkter, matt={sida: mått}, start=(0, 0))` – sluten polygon, axelparallella sidor låses, sida i
  går från punkt i till i+1. Punkterna är ungefärliga startvärden; måtten bestämmer.
- Lågnivå: `geo(Part.LineSegment(...))`, `begr("Horizontal", g)`, `begr("Coincident", g1, 2, g2, 1)`,
  `matt("DistanceX", g1, 1, g2, 1, varde="CC")`, `placera(g, pos, x, y)`. Punkt: 1 start, 2 slut, 3 mitt.
  Origo = (-1, 1), H-axel = -1, V-axel = -2.
Kontrollera att `fullt bestämd=True` i utskriften för varje skiss.

## Features (på `d`)
- `kloss(sk, langd, namn, symmetrisk=False, omvand=False)` – Pad.
- `ficka(sk, djup="genom" | mått, namn, symmetrisk=None, omvand=False)` – Pocket; "genom" skär åt båda håll.
- `hal(sk, diameter, djup="genom", ganga="M12", namn)` – Hole på skissens cirklar (gänga ej modellerad,
  hålet får borrdiametern, ritningen skriver `n×M12`).
- `varv(sk, vinkel=360, axel="V" | "H" | "X"/"Y"/"Z", namn, spar=False)` – Revolution (Groove med spar=True).
- `avrunda(radie, kantval, namn)` / `fas(storlek, kantval, namn)` – Fillet/Chamfer.
- `spegla([features], plan="YZ")`, `monster([features], "X", langd, antal)`, `polart([features], "Z", 360, antal)`.
Fickor och hål som inte skär något vänds automatiskt; en feature som inte går att räkna ger fel direkt.

## Kantval (Fillet/Chamfer)
Dict (alla villkor ska gälla) eller lista av dict (union). Sparas i featurens egenskap `Kantval` och letas
om av `pd.uppdatera` efter varje `satt`.
- `{"parallell": "Z", "lada": ["x", "y"]}` – lodräta ytterhörn (på xmin/xmax och ymin/ymax).
- `{"parallell": "Y", "lada": ["x", "zmax"]}` – övre hörn i ett lodrätt ben.
- `{"cirkel": True, "radie": "Diameter/2", "lada": ["zmax"]}` – ytterkanten upptill.
- `{"parallell": "X", "vid": {"y": "Tjocklek", "z": "Tjocklek"}}` – innerhörnet i en L-profil.
- `"langd": mått` – kantens längd.

## Kontroll (`pd.kontroll`) och ritning
Utskriften: variabler, skisser, features (ok/fel, spets), låda, volym, massa (7850 kg/m3 eller `--densitet`).
`ritning.py` känner igen en Part Design-del på att filen saknar `Utbredning` och har en `PartDesign::Body`.
