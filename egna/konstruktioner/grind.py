"""Grind G/1 till Patrik Hellstone (mail "Offert räcke och grind", 2026-10-17): enkel smidesgrind mellan två
befintliga stolpar med 1400 mm fritt mått. Stil efter kundens förebilder (foton i mailet) och räckena R/1, R/2:
ram av plattstång 12*40 på högkant, stående spjälor av fyrkantstång FS12 som i räckena. Grinden hänger
mellan två granitstolpar (foto grind.jpg), 1400 mm fritt.

Grindbladet = Oppning - 2*Spalt brett (25 mm spalt mot stolpen på gångjärns- och låssidan). Stolparna st/1 går i
full höjd, liggarna l/1 sitter mellan stolparna, spjälorna sp/1 mellan liggarna, jämnt fördelade så att fri
öppning mellan spjälorna blir < 100 mm. Gångjärn och lås ritas inte (beslag enligt leverantör).

Koordinater: X = grindens bredd (gångjärnssidan x = 0), Y = djup (grindplanet y = 0), Z uppåt (mark z = 0).
Alla lägen och längder är uttryck mot Variabler; antalet spjälor (Spjalor) kräver ombyggnad.
"""
NAMN = "Grind"
MARKE = "G/1"
VARIABLER = [
    ("Oppning", 1400, "mm, fritt mått mellan stolparna"),
    ("Spalt", 25, "mm, spalt mellan grindblad och stolpe per sida (gångjärn/lås)"),
    ("Hojd", 1000, "mm, grindens överkant över mark"),
    ("Markfri", 100, "mm, fri höjd under grinden"),
    ("Ram", 40, "mm, ramens plattstång, höjd (på högkant)"),
    ("RamT", 12, "mm, ramens plattstång, tjocklek"),
    ("Spjala", 12, "mm, spjälans sida (fyrkantstång)"),
    ("Spjalor", 11, "antal spjälor, jämnt fördelade"),
]
RITNING = dict(
    vyer=["fram"],
    snitt=[dict(namn="A", axel="x", varde=675, mot="-")],        # genom den mittersta spjälan
    noter=["PRELIMINÄR RITNING – OFFERTUNDERLAG, EJ FÖR TILLVERKNING",
           "UNDERLAG: MAIL FRÅN P. HELLSTONE 2026-10-17, FRITT MÅTT MELLAN STOLPAR 1400 ENL. BESTÄLLARE",
           "ALLA MÅTT KONTROLLMÄTS PÅ PLATS FÖRE TILLVERKNING",
           "±0 = MARK VID GRIND, FRI HÖJD UNDER GRIND 100",
           "SPALT 25 MOT GRANITSTOLPE PÅ VARDERA SIDAN. GÅNGJÄRN OCH LÅS/HASPEL ENL. LEVERANTÖR, EJ RITADE",
           "INFÄSTNING I GRANITSTOLPARNA MED KEMANKARE M10 I KÄRNBORRADE HÅL",
           "SVETS: RAMHÖRN a4 GENOMSVETSADE OCH SLIPADE, SPJÄLOR MOT LIGGARE a3 RUNT OM",
           "YTBEHANDLING: VARMFÖRZINKAD OCH PULVERLACKAD SVART RAL 9005 (ANTAGET, ENLIGT BESTÄLLNING)"],
)

STAL = "S235JR"


def bygg(k, v):
    n = int(v["Spjalor"])
    B = "Oppning - 2 * Spalt"                                     # grindbladets bredd
    ram = "PL%g*%g" % (v["RamT"], v["Ram"])
    # Plattstången på högkant: 40 mm i grindplanet, tjockleken 12 längs Y (upp = plattstångens tjockleksriktning).
    # stolpar i full höjd (40 mm längs X)
    k.balk("st/1", ram, ("Ram / 2", 0, "Markfri"), ("Ram / 2", 0, "Hojd"), upp=(0, 1, 0), material=STAL, huvuddel=True)
    k.balk("st/1", ram, ("%s - Ram / 2" % B, 0, "Markfri"), ("%s - Ram / 2" % B, 0, "Hojd"), upp=(0, 1, 0), material=STAL)
    # liggare mellan stolparna (40 mm längs Z)
    for z in ("Hojd - Ram / 2", "Markfri + Ram / 2"):
        k.balk("l/1", ram, ("Ram", 0, z), ("%s - Ram" % B, 0, z), upp=(0, 1, 0), material=STAL)
    # spjälor av fyrkantstång mellan liggarna, jämnt fördelade: spalt = (fri bredd - n * Spjala) / (n + 1)
    spalt = "((%s - 2 * Ram) - Spjalor * Spjala) / (Spjalor + 1)" % B
    fri = ((v["Oppning"] - 2 * v["Spalt"] - 2 * v["Ram"]) - n * v["Spjala"]) / (n + 1)

    def fyrkantstang(d):                       # längd och sida bundna till Variabler
        sk = d.skiss("Tvarsnitt", "XY")
        sk.rektangel("Spjala", "Spjala", namn=("Sida", "Sida2"))
        d.kloss(sk, "Hojd - Markfri - 2 * Ram", "Langd")

    for i in range(n):
        x = "Ram + %s * %d + Spjala * %g" % (spalt, i + 1, i + 0.5)
        k.egen("sp/1", "FS%g" % v["Spjala"], fyrkantstang, mitt=(x, 0, "Markfri + Ram"), material=STAL)
    noter = list(RITNING["noter"])
    noter.insert(4, "SPJÄLOR sp/1: %d st FS%g JÄMNT FÖRDELADE, FRI ÖPPNING %.1f, c/c %.1f, FÖRSTA SPJÄLAN %.1f FRÅN RAMENS INSIDA"
                 % (n, v["Spjala"], fri, fri + v["Spjala"], fri))
    k.ritning(**dict(RITNING, noter=noter))
