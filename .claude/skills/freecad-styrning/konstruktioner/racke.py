"""Räcke - plant eller i trappa - med valbar utfyllnad och infästning (scripts/racke.py).

Variablerna styr allt utan att skriptet ändras, t.ex. ett trappräcke 35° med språngmönster och sidomontage:
  python scripts/sammanstallning.py bygg konstruktioner/racke.py ut/R1.FCStd --var Lutning=35 --var Fyllnad=3 \
         --var Montage=2 --var Typ=2 --png
Fyllnad: 1 spjälor, 2 ovaler (bara plant), 3 språng, 4 glas. Montage: 1 fotplåt, 2 sidoplåt, 3 ingen.
Typ (för kontrollen av höjd och öppningar): 1 plan/trapplan, 2 trapplopp, 3 balkong/loftgång.
Profiler och mönsterparametrar ändras i en kopia i egna/konstruktioner/.
"""
import racke

NAMN = "Räcke"
MARKE = "R/1"
VARIABLER = [
    ("Langd", 2400, "mm, räckets längd (första till sista stolpens yttersida), mätt längs golvet/vågrätt"),
    ("Hojd", 1000, "mm, lodrätt från golvlinjen (stegnosarna i trappa) till handledarens ovansida"),
    ("Lutning", 0, "grader, 0 = plant räcke, trappans lutning för ett trappräcke"),
    ("Stolpdelning", 1200, "mm, största stolpavstånd c/c"),
    ("Golvspalt", 50, "mm, golvlinjen till underliggarens underkant"),
    ("Fyllnad", 1, "1 spjälor, 2 ovaler, 3 språng, 4 glas"),
    ("Montage", 1, "1 fotplåt, 2 sidoplåt, 3 ingen"),
    ("Typ", 1, "kontroll: 1 plan/trapplan, 2 trapplopp, 3 balkong/loftgång"),
]
RITNING = dict(
    vyer=["fram", "plan"],
    noter=["PRELIMINÄR RITNING – EJ FÖR TILLVERKNING FÖRRÄN MÅTT OCH UTFÖRANDE ÄR GODKÄNDA",
           "ALLA MÅTT FASTSTÄLLS VID INMÄTNING PÅ PLATS",
           "SVETS: ALLA ANSLUTNINGAR a3 RUNT OM, SLIPADE SYNLIGA SVETSAR",
           "YTBEHANDLING ENLIGT BESTÄLLNING"],
)

FYLLNAD = {1: lambda: racke.Spjalor("PL8*25"),
           2: lambda: racke.Ovaler(b=130, profil="PL10*20:plan", delning=187, topp=40, botten=40),
           3: lambda: racke.Sprang("PL12*12"),
           4: lambda: racke.Skiva(t=10, material="Glas 10 mm härdat laminerat")}
MONTAGE = {1: "golv", 2: "sida", 3: "ingen"}
TYP = {1: "plan", 2: "trappa", 3: "balkong"}


def bygg(k, v):
    r = racke.Racke(k, v["Langd"], v["Hojd"], lutning=v["Lutning"], stolpdelning=v["Stolpdelning"])
    r.ram(stolpe="PL12*50", handledare="PL8*50", underliggare="PL8*40", golvspalt=v["Golvspalt"],
          montage=MONTAGE[int(v["Montage"])])
    r.fyll(FYLLNAD[int(v["Fyllnad"])]())
    k.ritning(**r.ritning(RITNING, typ=TYP[int(v["Typ"])]))
