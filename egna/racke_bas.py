"""P. Hellstones räckesutförande (förebilderna i mailet 2026-10-17), byggt med skillens scripts/racke.py:
- stolpar FS20, 100 mm nedgjutna i kärnborrade hål Ø40 i granitstegen
- handledare FL40*10: plattstål 40x10 med rundad översida (sidorna 6 höga, R52), smidd snäcka i nedre änden
  på räckena längs nedre loppet
- följare under handledaren och underliggare nedtill: 2 st PL5*20 på högkant, ett på var sida om spjälorna
- spjälor FS12 med fri öppning < 100
Här ligger bara projektets val och noter; geometrin (knäckar, geringar, kap, detaljer) gör skillen.
"""
import racke
import trappa_hellstone as T

VARIABLER_RACKE = list(racke.VARIABLER)
ST_A = 20.0                     # stolpe FS20 (för handledarens ände kant i kant med hörnstolpen)
SNACKA_RAK = racke.SNACKA_RAK
fordela = racke.fordela
UTFORANDE = dict(handledare=dict(profil="FL40*10", rundad=True, sida=6),
                 foljare=dict(typ="dubbel", profil="PL5*20"), underliggare=dict(typ="dubbel", profil="PL5*20"),
                 spjalor=dict(profil="FS12", fri=100), stolpe=dict(profil="FS20", fot="ingjutning", djup=100, hal="Ø40"),
                 material="S235JR")


def bygg_racke(k, v, nos_pkt, yta, stolpar, hl_x, start="snacka", **kw):
    return racke.bygg(k, linje=nos_pkt, yta=yta, stolpar=stolpar, handledare_x=hl_x, hojd=v["Hojd"], under=v["Under"],
                      mellan=v["Mellan"], start=start, **dict(UTFORANDE, **kw))


def ritning(k, info, noter_):
    racke.ritval(k, info, noter_)


def noter(beskr, v, info, start, slut_text, extra=()):
    rader = ["PRELIMINÄR RITNING – OFFERTUNDERLAG, EJ FÖR TILLVERKNING",
             "UNDERLAG: FOTON OCH MÅTT I MAIL FRÅN P. HELLSTONE 2026-10-17, UTFÖRANDE EFTER KUNDENS FÖREBILDER",
             beskr,
             "STEGHÖJD %g, STEGDJUP %g/%g ÄR ANTAGNA UR FOTON – ALLA MÅTT KONTROLLMÄTS PÅ PLATS FÖRE TILLVERKNING"
             % (T.R, T.G_OVRE, T.G_NEDRE)]
    utf = racke.noter(info)
    utf[0] += ", ±0 = GÅNGEN VID TRAPPANS FOT"
    return rader + utf[:-1] + [slut_text] + list(extra) + utf[-1:] + \
        ["YTBEHANDLING: VARMFÖRZINKAD OCH PULVERLACKAD SVART RAL 9005 (ANTAGET, ENLIGT BESTÄLLNING)"]
