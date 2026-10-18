# Smidesritningar: klassiska svenska tillverkningsritningar (konventioner)

Konventionerna nedan är uttagna ur ett fyrtiotal svenska tillverkningsritningar (GA och sammanställningar) från ett
smidesföretag, 2026-10: räcken och grindar, balkonger, avväxlingar, pelare och balkar, trappor samt stagningar.
Använd dem som facit för hur en smidesritning ska se ut när en ritning görs i FreeCAD eller granskas.
Exempelnummer i texten (`2026-001`, `B/1`) är bara exempel på format.

## Ritningstyper
| Typ | Format | Skala | Innehåll |
|---|---|---|---|
| **GA – översikt/montage** (`GA_1_R-101`, `A-02`, `STG-101`) | A1 liggande | 1:20 (1:10–1:100) | Fasad/plan med alla sammanställningar märkta (R/1, G/1, S/1), måttkedjor till systemlinjer/nivåer, infästningar (kemankare, bultar) märkta, allmänna noter i versaler under vyn. Inga materiallistor. |
| **Sammanställning – tillverkning** (`B/1`, `R/1`, `SP1/1`) | A2 liggande | 1:5–1:20 | En sammanställning per blad: huvudvy med positionsbubblor, snitt A–A, B–B … med egen skala, ofta isometri (t.ex. 1:25), måttkedjor + totalmått, hålangivelser, materiallista, allmänna noteringar, noter. |

Ritningsnummer: GA-blad har serienummer per typ (`R-101`, `R-201` … per plan/etapp, `A-02`, `STG-101`).
Sammanställningar numreras efter märket (`B/1`, `SP1/1`); flera blad av samma märke `.1`, `.2`.

## Positionsnummer (stycklitterering) – prefix/löpnummer
Märks på ritningen i en avlång bubbla, t.ex. `(pl/3)`, `3x pl/2 NS` (antal och sida: NS/FS = när-/fjärrsida),
huvuddelen med sammanställningsmärke och profil: `B/1 b/1 UPE140`, `SP1/1 c/5 VKR100*6.3`.

| Prefix | Del | Typiska profiler |
|---|---|---|
| `b` | balk | UPE140–240, IPE100, VKR150–250 |
| `u` | UPE-balk (golv/fot) | UPE300–330 |
| `c` | pelare | VKR80–100 |
| `st` | stolpe (räcke) | VKR50–100, PL12*50 |
| `l` | liggare (räcke) | VKR40*3, plattstång 30–50*8 |
| `sp` | spjäla | RHS20*20*2, plattstång 8*25 |
| `ek` | handledare i ek | 70*30 |
| `pl` / `p` | plåt (fotplåt, toppplåt, ändplåt, däckplåt) | PL4–PL15 |
| `k` | knut-/konsolplåt | PL10 |
| `v` | vangstycke (trappa) | PL12 |
| `s` | steg (trappa) | PL3 |
| `r` | rundstång | D80 |

Sammanställningens prefix (versal): B balkong/balk, R räcke, G grind, S stolpe/stöd, SP stålpelare, SB stålbalk,
V vägg-/vangfäste, L trapplopp, K konsol, T, F, E. Formen är `<prefix><löpnr>/<nr>`.

## Materiallista (nere i mitten, ovanför titelblocket)
Rubrik `MATERIALLISTA FÖR ETT GODS MÄRKT: B/1` och `1 st. TILLVERKAS`. Kolumner:
`STYCKLIT. | PROFIL | MATERIAL | ANT. | LÄNGD | AREA/st | VIKT/st`, sorterad efter vikt (tyngst först), sista raden
`TOTALT` med area (m²) och vikt (kg). Profilnamn som i svenska profilkataloger: `VKR70*5`, `VKR100*6.3`,
`UPE140`, `IPE100`, `PL10*150` (tjocklek*bredd), `RHS20*20*2`, `D80`.
Ovanför listan **ALLMÄNNA NOTERINGAR**: `ALLA HÅL ÄR 22 mm OM EJ ANNAT ANGES` och
`ALLA SVETSAR ÄR 3.0 mm OM EJ ANNAT ANGES` (a-mått 2, 3 eller 4 mm beroende på godstjocklek).

## Material och infästning som återkommer
- Stål: S355J2 (balkar, plåt), S355J2H (VKR), S235JR (räcken), S355N. Aluminium 6060-T6 för räcken/grindar.
- Noterna avslutas med var profilmåtten (standard, databas, datum) och materialkvaliteten (fy/fu enligt
  EN 1993-1-1 tab. 3.1, källa, datum) är verifierade; raderna kommer från `scripts/kallor.py`.
  Trä C24, ek för handledare.
- Bultar: `M12 8.8 FZV`, hålangivelse `4*Ø14 - M12x44` (antal*håldiameter - bult). Kemankare M12 i Ø14.
  Avlånga hål för montageglapp anges i not.
- Svets i not: `UPE-HÖRN a4 RUNT OM`, `PÅSVETSADE PLÅTAR … a4`, `DÄCKPLÅT … a3`.
- Ytbehandling i not: `PULVERLACK MATT SVART RAL 9005`, `YTBEHANDLING ENLIGT BESTÄLLNING`.

## Noter (versaler, under eller bredvid vyerna)
Ordning: status → underlag → material/ytbehandling → nivåer → svets/bult → avvikelser/antaganden.
- Status: `PRELIMINÄR RITNING – KOMPLETTERAR FÖRSLAGSSKISS A-01 (OFFERT <uppdragsnr>)`,
  `PRELIMINÄR – EJ FÖR TILLVERKNING FÖRRÄN K33:32 ÄR MÄRKT BYGGHANDLING`,
  `EJ FÖR TILLVERKNING FÖRRÄN MÅTT OCH UTFÖRANDE ÄR GODKÄNDA`.
- Underlag: `UNDERLAG: K33:32 SD PROJECT 2026-10-07 (FÖRHANDSKOPIA), BALKONG 107 ALT. 2`.
- Mått: `ALLA MÅTT ÄR ANTAGNA OCH FASTSTÄLLS VID INMÄTNING PÅ PLATS`, `… SKALMÄTTA/ANTAGNA – KONTROLLERAS MED KONSTRUKTÖR`.
- Nivåer: `±0 = GÅNGYTA VID GRIND, +800 = MURKRÖN (ANTAGET)`, lutningar `IPE100 I FALL 1:100 UTÅT`.
- Det som inte ritas: `GRINDBESLAG ENL. LEVERANTÖR, EJ RITADE`.

## Vyer och mått
- Huvudvy med måttkedjor på båda sidor och totalmått ytterst (t.ex. 550-550-550-550 / 2200, c/c 110 för spjälor).
  Hålmått från kant i kedja (55-55, 75-75). Vinklar som lutning i grader (`0.57°`).
- Snitt markeras med pilar och bokstav (A, B, G) i huvudvyn; snittvyn får rubrik `A - A` och skala under.
- Isometri utan mått i ledig yta, egen skala.
- **Placering i stomnät** (ruta uppe till vänster): NUMMER + SYSTEMLINJE, t.ex. `B/1 | A-B/2`, `R/1 | 2-7/A`.
- **Etapp/Antal** (ruta uppe till höger).

## Titelblock (nere till höger, liggande)
Företagets logga eller namn med adressrader; fält UPPDRAG NR (t.ex. `2026-001`), RITAD/KONSTR AV (signatur),
DATUM, HANDLÄGGARE, ANSVARIG, objekt i tre rader (fastighet/projekt, kund, adress), SKALA (flera skalor om
snitten har annan: `1:10 1:20`), NUMMER (märket), BET (revisionsbokstav). Revisionstabell ovanför:
`BET | ANT | ÄNDRINGEN AVSER | DATUM | SIGN` (t.ex. `A | Bultad anslutning ram–väggfäste, noter | 2026-10-07 | AB`).
FreeCAD-mallen `mallar/A3.svg` har ett enklare titelblock för enstaka delar (plåt, Part Design). A2-blocket
ovan finns som `mallar/A2.svg` (med stomnät- och etapprutorna och en revisionsrad) och används av
`scripts/sammanstallning.py`, som också gör materiallistan, ALLMÄNNA NOTERINGAR, positionsbubblorna, snitten
och hålangivelserna enligt det här dokumentet (se SKILL.md). Företag, adress och signaturer fylls i med
`--foretag`, `--adress`, `--ritad-av`, `--handlaggare`, `--ansvarig` eller miljövariablerna `FC_FORETAG`,
`FC_ADRESS`, `FC_RITAD_AV`, `FC_HANDLAGGARE`, `FC_ANSVARIG`; vill man ha en logga byts Foretag-texten i mallen
mot en `<image>`. Det som inte görs automatiskt: bultar och svetssymboler ritas inte (skriv dem i noterna),
bara en revisionsrad, varje positionsnummer får en bubbla (förlagorna upprepar dem och skriver `3x pl/2 NS`).

## Räcken och trappräcken
Uttaget ur räckesritningarna ovan och ett offertuppdrag på en entrétrappa (2026-10). Måtten är vanliga
utgångsvärden, inte regelverket: kontrollera alltid mot gällande regler (BBR, avsnittet om skydd mot fall) och
beställarens krav, och skriv i noterna vad som är antaget.
- Höjd: handledarens överkant **900** lodrätt över stegframkant (nos) i trappor; högre räcken där fallhöjden
  är större (balkong, loftgång) enligt reglerna. Mät lodrätt, även på plana partier.
- **Fri öppning < 100 mm** mellan spjälor och mellan räckets nederkant och steg/plan yta (en sfär Ø100 ska inte
  gå igenom). Kontrollera även springan under underliggaren på podest/vilplan, där linjen mot stegnosarna inte
  längre gäller.
- Stolpar: **c/c högst ca 1300** (räknas på handledarens styvhet och infästningen), en stolpe i varje sektionsände
  och **en gemensam stolpe i innerhörn** där två räcken möts. Handledarens knäck (trappa → plant) läggs **mitt
  över en stolpe**, minst ca 60 mm in från stenkanten; mellanstolpar på stegmitt.
- Infästning: ingjutning 100 mm i kärnborrat hål (Ø40 för FS20) i sten, kemankare M10–M12 genom fotplåt
  (PL8*100 med 4 hål) i betong, eller sidomontage. Skriv infästningen i noterna och på översikten.
- Följare under handledaren och underliggare nedtill: plattstång liggande (FL30*8) eller två plattstål på högkant
  (2 st PL5*20, ett på var sida om spjälorna). Spjälor FS12, D12 eller plattstång; prefix `l` för följare/liggare,
  `sp` för spjälor, `st` för stolpar, `hl` för handledare.
- Handledaren: plattstång (gärna med rundad översida), rör Ø42,4 eller ek. Ändarna avslutas raka (proppade),
  nedböjda eller med smidd snäcka – ta med det kunden visat, men gör inte snäcka till standard.
- Ritningar för ett räcksuppdrag: en sammanställning per räcke (R/1, R/2 …) med detaljblad (.1, .2), en
  planritning/GA (`R-101`) med alla räcken märkta, stolparnas c/c och nivåer, och 3D-bilder till offerten.

## Kontrollfrågor när en smidesritning granskas
1. Har varje del ett positionsnummer som finns i materiallistan, och stämmer antal och längd?
2. Finns totalmått, måttkedjor som summerar och mått till alla hål från samma referens?
3. Är hål angivna med antal, diameter och bult (`4*Ø14 - M12x44`) och avviker de från standardhålet 22 mm?
4. Står svets (a-mått, runt om), material, ytbehandling och status (preliminär/för tillverkning) i noterna?
5. Är placeringen i stomnätet och antalet att tillverka angivet?
