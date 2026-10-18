"""Mall för ett projekts gemensamma noteringar (noteringsritningen N-01). Kopiera till egna/<uppdrag>_noter.py,
skriv om raderna för uppdraget och kör:

  python3 scripts/sammanstallning.py noteringar egna/<uppdrag>_noter.py ut/N-01.FCStd --nummer N-01 \\
          --uppdrag <uppdragsnr> --objekt "<projekt>" "<beställare>"

Varje sammanställning ritas sedan med `--noter-ref N-01` och bara sina egna noter. Rubrikerna är de i
scripts/noter.py; egna rubriker går också bra. Raderna nedan är exempel att ändra, inga krav.
"""
NOTER = {
    "STATUS": ["PRELIMINÄR – OFFERTUNDERLAG, EJ FÖR TILLVERKNING FÖRRÄN MÅTT OCH UTFÖRANDE ÄR GODKÄNDA"],
    "UNDERLAG": ["UNDERLAG: <RITNINGAR, FOTON ELLER MAIL MED DATUM>",
                 "MÅTT SOM INTE STÅR I UNDERLAGET ÄR ANTAGNA OCH KONTROLLMÄTS PÅ PLATS FÖRE TILLVERKNING"],
    "MONTAGE": ["INFÄSTNING ENLIGT RESPEKTIVE SAMMANSTÄLLNING; KEMANKARE OCH BULTAR ENL. LEVERANTÖRENS ANVISNING"],
    "SVETS": ["SVETSAR a3 OM EJ ANNAT ANGES", "SYNLIGA SVETSAR SLIPAS"],
    "YTBEHANDLING": ["ENLIGT BESTÄLLNING"],
}
