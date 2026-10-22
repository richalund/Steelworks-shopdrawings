"""Svetsad hattbalk (HSQ) på två pelare och en kepsbalk (FSQ) - exempel på k.ladbalk.

Hattbalken HSQ H270:B200x450 ligger på två stöd c/c 7200 med 200 utstick: underfläns PL15*450, liv 2 x PL10*255
(200 över liven), överfläns PL25*180 mellan liven, ändplåtar och livplåtar över pelarnas väggar (VKR 200), och
4 hål Ø22 för M20 i underflänsen vid varje stöd. Bjälklaget (t.ex. KL-trä 270) vilar på underflänsen. Kepsbalken
FSQ H240:B100x240 ligger parallellt 1200 bredvid, med brättet mot hattbalken och 2 hål i brättet vid stöden.
Plåttjocklekarna är exempel: konstruktören anger dem.

Koordinater: X längs balkarna, Y tvärs, Z uppåt med Z = 0 = underkant balk.
"""
NAMN = "Hattbalk och kepsbalk"
MARKE = "SB/1"
VARIABLER = []
RITNING = dict(
    vyer=["fram", "plan"],
    snitt=[dict(namn="A", axel="x", varde=320, mot="-"),
           dict(namn="B", axel="x", varde=3800, mot="-")],
    stomnat="1-2/A",
    noter=["PRELIMINÄR RITNING – EJ FÖR TILLVERKNING",
           "TESTRITNING UR FREECAD: k.ladbalk",
           "UTFÖRANDE: PLÅTTJOCKLEKAR ENLIGT KONSTRUKTÖR",
           "SVETS: LIV MOT UNDERFLÄNS a5 DUBBELSIDIG, ÖVERFLÄNS MOT LIV a5, ÄND- OCH LIVPLÅTAR a4 RUNT OM",
           "MONTAGE: UNDERFLÄNS BULTAS MOT PELARENS TOPPPLÅT, M20 8.8",
           "YTBEHANDLING ENLIGT BESTÄLLNING"],
)


def bygg(k, v):
    L, c = 7600, 7200
    k.ladbalk((0, 0, 0), (L, 0, 0), H=270, Bo=200, Bu=450, tu=15, tw=10, to=25, stod=(200, 200 + c),
              hal=dict(bult="M20x60", dx=120, dy=165))
    k.ladbalk((0, -1200, 0), (L, -1200, 0), H=240, Bo=100, Bu=240, tu=12, tw=8, to=15, keps=1, stod=(200, 200 + c),
              hal=dict(bult="M20x60", dx=120), pos=("b/2", "pl/5", "pl/6", "pl/7", "pl/8"), huvuddel=False)
    k.ritning(**RITNING)
