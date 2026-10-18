"""Trappräcke på en rak trappa med podest (exempel på scripts/racke.py): 6 steg 165/280, podest överst.
Stolpar VKR40*4 på fotplåtar, handledare rör 42,4x2,6, enkel liggande följare och underliggare FL30*8,
rundstångsspjälor D12 med fri öppning under 100. Handledaren knäcker mitt över en stolpe 60 mm in på podesten.
Trappstegen är referenskroppar (syns i modellen och 3D-bilderna, inte i materiallistan).

  python3 scripts/sammanstallning.py bygg konstruktioner/trappracke.py ut/TR1.FCStd --png
  python3 scripts/sammanstallning.py ritning ut/TR1.FCStd --uppdrag 2026-001 --objekt "TRAPPRÄCKE" "Kund AB" "Gatan 1"
  python3 scripts/rendera.py ut/TR1.FCStd --vyer iso,fram

Byt utförande med parametrarna till racke.bygg (se racke.py): t.ex. handledare=dict(profil="FL40*10",
rundad=True), start="snacka", foljare="dubbel", stolpe=dict(profil="FS20", fot="ingjutning", djup=100).
"""
import racke

NAMN = "Trappräcke"
MARKE = "TR/1"
VARIABLER = list(racke.VARIABLER)


def bygg(k, v):
    t = racke.rak_trappa(k, steg=6, steghojd=165, stegdjup=280, bredd=1200, podest=1000, knack_in=60, y0=-1240)
    x0, x1 = 0.5 * t["stegdjup"], t["knack"] + 860
    stolpar = racke.fordela([x0, t["knack"], x1], t["stegmitt"], max_cc=1300)
    info = racke.bygg(k, linje=t["linje"], yta=t["yta"], stolpar=stolpar, handledare_x=(x0 - 60, x1 + 60),
                      hojd=v["Hojd"], under=v["Under"], mellan=v["Mellan"],
                      handledare="RÖR42.4*2.6", foljare=dict(typ="enkel", profil="FL30*8"),
                      underliggare=dict(typ="enkel", profil="FL30*8"), spjalor=dict(profil="D12", fri=100),
                      stolpe=dict(profil="VKR40*4", fot="fotplat", plat="PL8*100", bult="M10", cc=60))
    racke.ritval(k, info, noter=["PRELIMINÄR RITNING – EJ FÖR TILLVERKNING",
                                 "TRAPPRÄCKE PÅ RAK TRAPPA 6 x 165/280 MED PODEST"] + racke.noter(info) +
                 ["HANDLEDARENS ÄNDAR 60 FÖRBI ÄNDSTOLPARNA, ÄNDARNA PROPPAS",
                  "YTBEHANDLING: VARMFÖRZINKAD (ENLIGT BESTÄLLNING)"])
