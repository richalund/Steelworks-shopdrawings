# Verktygen i detalj

Kort API för skillens byggare och kommandon. Docstringen i varje skript är den fullständiga beskrivningen.

## stal.Konstruktion (`k` i ett konstruktionsskript)
Koordinater i mm, globala, x/y/z; tal eller uttryck mot Variabler (`"Langd - 40"`). `rot` = delens x-, y- och
z-riktning som tre vektorer. Varje metod ger en del med Pos (positionsnummer), Profil (texten i materiallistan) och
Material; samma positionsnummer på flera delar = samma position (de ska vara lika).

| Metod | Ger |
|---|---|
| `k.balk(pos, profil, start, slut, upp=, oppning=)` | profil/stång längs linjen (UPE, IPE, HEA, HEB, VKR, KKR, RÖR, D, FL, FS, L) |
| `k.plat(pos, "PL10*110", mitt=, langd=, lriktning=, briktning=)` | rektangulär plåt |
| `k.skiva(pos, text, langd, bredd, t, mitt=, form="ellips"\|"rektangel")` | liggande skiva (bordsskiva, lock) |
| `k.egen(pos, text, bygg, mitt=, rot=, material=)` | egen Part Design-kropp, `bygg(d)` med pd-API:t |
| `k.hal(delar, punkter, riktning, bult="M12x44")` | hålgrupp genom delarna (hålangivelse på ritningen) |
| `k.gera(del, yttre, inre, riktning=)` | gering eller plant kap genom två punkter |
| `k.bockad(pos, t, punkter, langd, mitt=, rot=, radie=, sida="vanster")` | kantvikt plåt (SheetMetal) ur en öppen profil |
| `k.trag(pos, t, langd, bredd, kant, mitt=, rot=, sidor=("-x","+x","-y","+y"))` | plåttråg, uppbockade kanter, hörnurtag |
| `k.ladbalk(start, slut, H, Bo, Bu, tu, tw, to, keps=0, stod=, hal=, pos=)` | svetsad lådbalk av plåt: hattbalk (HSQ) eller kepsbalk (FSQ, `keps=±1` = brättets sida), ändplåtar, livplåtar och bulthål vid stöden |
| `k.glas(pos, horn1, horn2, normal=, t=8, glipa=5, djup=0, list_profil=, list_pos=)` | glasruta i en öppning (+ lister) |
| `k.inkop(pos, komponent="id" \| text, lada=(x,y,z) \| cylinder=(d,l), mitt=, rot=, vikt=)` | inköpt komponent som utrymmesmodell |
| `k.referens(namn, lada=(x0,x1,y0,y1,z0,z1) \| bygg=, farg=, transparens=)` | omgivning (inte i materiallistan) |
| `k.rorelse(namn, delar, axel=(punkt, riktning), fran=, till=, gangjarn=[...])` | rörlig del för rorelse.py |
| `k.utseende({"g/": "patinerad", "st/": "svart"})` | utseende i 3D-bilder och glb |
| `k.ritning(**val)` | ritningens val (annars skriptets RITNING): vyer, snitt, dolda, detaljer, delvyer, kedjor, noter, noter_blad, bubblor, sprak |

- `kedjor=[dict(pos="pi/1", vy="fram", axel="y")]` i ritningens val: måttkedja från vyns kant till varje dels mitt
  (bounding box) för positionen, i vyerna där delarnas mitt skiljer sig; `vy` = fram, plan ..., snittets bokstav.
  Används för pinnar, spjälor och regler som saknar hål (hålens kedjor kommer av sig själva).
- `k.bockad`: punkterna är plåtens ena sida; materialet ligger till vänster om profilens riktning (moturs profil =
  yttermått). Inre radien standard = t. Profiltext `PL<t> BOCKAD`, längd = utdragslängden.
- `k.trag`: yttermått langd x bredd x kant; `mitt` = bottens undersida i mitten; kanterna bockas uppåt längs delens
  +z. Justeras efter bygget så att yttermåtten stämmer (OBS-rad i loggen om inte), även med kanter på bara några
  sidor och med delens z i negativ riktning (lock och hyllor med kanterna nedåt: `rot=((1,0,0),(0,-1,0),(0,0,-1))`,
  `mitt` = ovansidan). Exempel med lock, gavlar, mellanväggar, hyllor, fronter och lådor: `konstruktioner/skap.py`.
- `k.glas`: rutan = öppningen minus glipan, centrerad i öppningens plan (+ `djup` längs normalen); vikt 2500 kg/m3.
- `k.inkop`: mått och vikt ur leverantörens datablad, helst via komponentregistret (`komponent="id"`, se
  komponenter.py). Material "INKÖP"; räknas inte i kap, yta eller laser men i vikten, krockar och rörelsen; listas
  under INKÖP i mängdunderlaget med benämning, tillverkare och artikelnummer, källan i ritningens noter.

Skriptets valfria `REGLER = [dict(villkor="600 <= Bredd <= 1500", text="...", niva="FEL"|"VARNING"), ...]` med
variablerna och VIKT, LANGD, BREDD, HOJD, DELAR, POSITIONER kontrolleras vid varje bygge (regler.py).

## noter.py (noteringarna på A2-ritningarna)
`gruppera(noter, kallor=, inkop=, kontroll=)` -> `[(rubrik, [noter])]` i fast ordning (STATUS, UNDERLAG OCH
ANTAGANDEN, UTFÖRANDE, MONTAGE OCH INFÄSTNING, SVETS, YTBEHANDLING, MATERIAL OCH KÄLLOR, INKÖPTA KOMPONENTER,
KONTROLL); `noter` är en lista (rubrik ur prefix `"SVETS: ..."` eller nyckelord) eller en dict {rubrik: [rader]}
(egna rubriker hamnar efter UTFÖRANDE). `spalter(grupper, antal, tecken)` fördelar raderna på spalter med hela
rubriker, `lagg_till_status(grupper, text)` lägger till en statusrad. Rubrikerna översätts med sprak.py.

## ornament.py (i en pd-skiss)
`svg(sk, fil, bredd=|hojd=, mitt=)`, `text(sk, s, hojd, font=, mitt=, sparning=)`,
`solfjader(sk, r_inre, r_yttre, antal, fran=0, till=180, andel=0.5, mitt=)`, `sicksack(sk, langd, hojd, antal, bredd, mitt=)`,
`trappsteg(sk, bredd, hojd, steg, mitt=)`, `bagar(sk, r, bredd, antal, avstand, mitt=)`, `ring(sk, d_yttre, d_inre, mitt=)`,
`kanter(sk, kantlista)` för egna Part-kanter. Geometrin låses med Block. Slutna konturer = öar, konturer inuti =
hål. Pad (relief), Pocket med djup (gravyr) eller "genom" (genombrytning).

## Kommandon
| Kommando | Gör | Ger |
|---|---|---|
| `underlag.py las <filer>` / `zoom <fil> --ruta x0,y0,x1,y1 [--rotera 90]` / `skala --ref ...=mm` | läser PDF (vektor/scannad), bilder, DXF; vänder fotade blad; pixlar till mm | översikt, rutor, text, underlag.md |
| `sammanstallning.py bygg/ritning` | bygger, kontrollerar, A2-ritning (`--sprak sv\|en\|zh`, `--noter-blad`, `--noter-ref N-01`) | FCStd, PDF, PNG, CSV |
| `sammanstallning.py noteringar <noter.py\|json> <ut.FCStd> --nummer N-01` | projektets gemensamma noteringsritning | FCStd, PDF, PNG |
| `ritning.py <del.FCStd>` | A3-ritning för en del (`--sprak`) | PDF, PNG, DXF |
| `oversikt.py <modell> <ritskript>` | översikt/plan (`vy.stomnat(x=, y=)` för stomlinjer) | PDF, PNG |
| `rendera.py <modell>` | 3D-bilder med utseende | `_3d_<vy>.png` |
| `export.py <modell> --format glb,html,ifc,step,stl` | export, `html` = fristående 3D-vy (webbvy.py) | .glb .html .ifc .step .stl |
| `dxf.py <modell>` | DXF per plåtposition | `_<pos>_kontur.dxf`, `_utbredning.dxf` |
| `mangder.py <modell> [--antal]` | mängdunderlag (inga priser) | `_mangder.csv/.json` |
| `mangder.py samla <modell>:antal ... --namn` | kalkylunderlag för flera märken: mängdspec, kaplista, plåtlista | `<namn> kalkylunderlag.xlsx` |
| `komponenter.py visa/lagg-till/ta-bort` | register över inköpta komponenter med datablad och källa | `egna/komponenter.json` |
| `regler.py <modell>` | produktregler och verkstadsgränser | rad i loggen, not på ritningen |
| `paket.py skapa <modell>` / `kontrollera <zip>` / `skicka <zip> [--till]` | beställningspaket / mottagarens kontroll / mail till tillverkaren (skickas inte) | `_bestallning.zip`, `_mail.eml` |
| `paket.py samla <pdf:er> <filer/mapp> --namn <uppdrag> --skript <x.py>` | filerna till chatten: alla blad i en PDF, resten i en zip med LASMIG | `<uppdrag> ritningar.pdf`, `<uppdrag> underlag.zip` |
| `rorelse.py <modell> [--oppen v --ut fil]` | krock genom öppningen, tyngdpunkt, gångjärnslast | rad i loggen, öppen kopia |
| `hallfasthet.py balk/fem` | balköverslag / FEM med CalculiX | rad i loggen, `_fem.FCStd` |
| `kallor.py profil/material/motsvarighet` | profilmått, fy/fu, motsvarande kvaliteter | utskrift |
| `testa.py` | alla exempel genom alla verktyg, bildjämförelse | tabell, `ut/test/` |

## Filer som verkstaden äger (i `egna/`, aldrig i skillen)
- `egna/foretag.json`: titelblockets uppgifter och logga (foretag.py).
- `egna/verkstad.json`: lagerlängd, största längd, plåtformat, remslängd för svetsade balkar, lyft, förzinkningsbad, transport, hål mot tjocklek
  (mall `mallar/verkstad.json`).
- `egna/komponenter.json`: inköpta komponenter med databladets mått, vikt, last och källa (komponenter.py).
- `egna/leverans.json`: förifylld mottagare för `paket.py skicka` (mall `mallar/leverans.json`, anbud@smide.com).
- Priser finns inte i skillen eller i `egna/`: tillverkaren prissätter mängdunderlaget med ett eget verktyg.
- `egna/ornament/`: egna SVG-motiv och typsnitt (kontrollera licensen).

## Miljövariabler
`FREECAD_BIN`, `FC_TIMEOUT`, `FC_FELSOK` (fcapi); `FC_FORETAG*`, `FC_LOGGA` (foretag); `FC_KALLOR`,
`FC_KALLOR_CACHE`, `FC_KALLOR_DAGAR` (kallor); `FC_LAND` (foretag, komponenter); `FC_VERKSTAD_FIL`, `FC_KOMPONENT_FIL`; `FC_DATUM` och `FC_SKILLVERSION`
(låser datum och version, används av testa.py).
