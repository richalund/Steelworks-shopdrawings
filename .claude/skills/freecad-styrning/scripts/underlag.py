"""Läser in kundens underlag så att det går att rita efter: PDF-ritningar (vektor eller scannade), foton och
bilder, DXF. Körs med system-Python (ingen FreeCAD).

  python3 underlag.py las <fil> [<fil> ...] [--ut ut/underlag] [--zoom-dpi 300] [--sidor 1-3]
  python3 underlag.py zoom <fil> --ruta x0,y0,x1,y1 [--sida 1] [--dpi 400] [--rotera 90] [--forstora 2] [--ut ...]
  python3 underlag.py skala [<bild>] --ref x1,y1:x2,y2=4800 [--punkt x,y ...] [--avstand x1,y1:x2,y2 ...]

`las` gör för varje fil:
  - en översiktsbild per sida (`<namn>_s1.png`, långsidan högst ca 2000 px) och rutor i hög upplösning
    (`<namn>_s1_r2-1.png`, rad-kolumn, 10 % överlapp) så att små måttsiffror i en scannad ritning går att läsa;
  - för en PDF med text (vektor-PDF, utskriven ur CAD): all text med läge på papperet (`<namn>_s1_text.txt`),
    sorterad i läsordning, och talen som ser ut som mått; sidans storlek och skala om den står i texten;
  - för en scannad PDF eller ett foto: bilden rätvänd (EXIF), gråskala med höjd kontrast i rutorna;
  - för en DXF: enheter, utsträckning, lager med antal objekt, alla texter och måttens värden
    (`<namn>_dxf.txt`) och en bild av ritningen (`<namn>_dxf.png` med rutor);
  - en sammanställning `underlag.md` i utmappen med vad som finns och vilka bilder som ska läsas.
`zoom` gör ett utsnitt i hög upplösning: rutan i bråkdelar av sidan (0,0 = övre vänstra hörnet), t.ex.
`--ruta 0.55,0.70,1,1` för titelblocket nere till höger. Fotade ritningar ligger ofta på tvären: `--rotera 90`
(eller 180, 270, moturs) vänder utsnittet efter klippningen (rutan anges i originalets läge) så att texten blir
läsbar, och `--forstora 2` förstorar ett foto så att små siffror går att läsa.
`skala` räknar om pixlar i en bild till mm när ett mått saknas men ritningen är skalenlig: `--ref` är två punkter
med känt avstånd (t.ex. två stomlinjer, 4800 mm), `--punkt` ger en punkts läge längs referensen (mm från första
referenspunkten) och vinkelrätt mot den, `--avstand` avståndet mellan två punkter. Koordinaterna läses i den bild
som visas (översikt eller utsnitt). Skalade mått är ungefärliga (fotots perspektiv, papperets veck): skriv dem som
SKALAT/ANTAGET på ritningen och fråga efter de mått som avgör utförandet.

Läs bilderna med Read-verktyget (översikten först, sedan rutorna där måtten står) och skriv upp måtten med
källa (sida, ruta). Mått som inte går att läsa säkert ska frågas efter, inte gissas. DWG läses inte: be om DXF
eller PDF. Kräver PyMuPDF och Pillow (finns efter installera_linux.sh), ezdxf för DXF.
"""
import os, re, sys, math, argparse

MAX_PX = 2000            # översiktsbildens långsida
RUTA_PX = 1600           # ungefärlig storlek på en ruta
OVERLAPP = 0.10
MATT = re.compile(r"^(?:[ØøR⌀]|M)?\d{1,5}(?:[.,]\d{1,2})?(?:[x×*]\d{1,5}(?:[.,]\d{1,2})?)*$")
SKALA = re.compile(r"\b1\s*:\s*(\d{1,4})\b")


def _pil():
    from PIL import Image, ImageOps
    return Image, ImageOps


def _spara_rutor(bild, bas, kontrast=False):
    """Delar bilden i rutor om ca RUTA_PX med överlapp. Returnerar filnamnen."""
    Image, ImageOps = _pil()
    w, h = bild.size
    nx, ny = max(1, math.ceil(w / RUTA_PX - 0.3)), max(1, math.ceil(h / RUTA_PX - 0.3))
    if nx == ny == 1:
        return []
    bw, bh = w / nx, h / ny
    ox, oy = bw * OVERLAPP, bh * OVERLAPP
    ut = []
    for r in range(ny):
        for k in range(nx):
            box = (int(max(0, k * bw - ox)), int(max(0, r * bh - oy)), int(min(w, (k + 1) * bw + ox)), int(min(h, (r + 1) * bh + oy)))
            ruta = bild.crop(box)
            if kontrast:
                ruta = ImageOps.autocontrast(ImageOps.grayscale(ruta), cutoff=1)
            fil = "%s_r%d-%d.png" % (bas, r + 1, k + 1)
            ruta.save(fil)
            ut.append(fil)
    return ut


def _oversikt(bild, bas):
    b = bild.copy()
    b.thumbnail((MAX_PX, MAX_PX))
    b.save(bas + ".png")
    return bas + ".png"


def _sidor(spec, n):
    if not spec:
        return list(range(n))
    ut = []
    for del_ in spec.split(","):
        if "-" in del_:
            a, b = del_.split("-")
            ut += list(range(int(a) - 1, min(int(b), n)))
        else:
            ut.append(int(del_) - 1)
    return [i for i in ut if 0 <= i < n]


def _textrader(sida):
    """Ord grupperade i rader (y), sorterade uppifrån och vänster till höger, med läge i mm från övre vänstra hörnet."""
    ord_ = sida.get_text("words")                       # x0, y0, x1, y1, ord, block, rad, nr
    rader = {}
    for x0, y0, x1, y1, w, b, l, _ in ord_:
        rader.setdefault((b, l), []).append((x0, y0, w))
    mm = 25.4 / 72
    ut = []
    for lst in rader.values():
        lst.sort()
        ut.append((round(lst[0][1] * mm), round(lst[0][0] * mm), " ".join(w for _, _, w in lst)))
    ut.sort()
    return ut, [w for *_, w, _, _, _ in ord_]


def las_pdf(fil, ut, a):
    import pymupdf
    Image, _ = _pil()
    doc = pymupdf.open(fil)
    namn = os.path.splitext(os.path.basename(fil))[0]
    rapport = ["## %s (PDF, %d sidor)" % (os.path.basename(fil), len(doc))]
    for i in _sidor(a.sidor, len(doc)):
        s = doc[i]
        bas = os.path.join(ut, "%s_s%d" % (namn, i + 1))
        rader, ord_ = _textrader(s)
        bilder = s.get_images()
        vektorer = len(s.get_drawings())
        tecken = sum(len(w) for w in ord_)
        scannad = tecken < 30 and bool(bilder)
        w_mm, h_mm = s.rect.width * 25.4 / 72, s.rect.height * 25.4 / 72
        format_ = next((f for f, (fw, fh) in (("A4", (210, 297)), ("A3", (297, 420)), ("A2", (420, 594)), ("A1", (594, 841)),
                                               ("A0", (841, 1189))) if abs(min(w_mm, h_mm) - fw) < 8 and abs(max(w_mm, h_mm) - fh) < 8), "")
        # översikt och rutor
        pix = s.get_pixmap(dpi=a.zoom_dpi if scannad else min(a.zoom_dpi, 200))     # vektortext läses också som text
        bild = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        _oversikt(bild, bas)
        rutor = _spara_rutor(bild, bas, kontrast=scannad)
        typ = "scannad (bild utan text)" if scannad else "vektor-PDF med text" if tecken else "vektor-PDF utan text"
        rapport.append("- Sida %d: %.0f x %.0f mm %s, %s, %d vektorobjekt, %d bilder. Översikt `%s`%s" % (
            i + 1, w_mm, h_mm, format_, typ, vektorer, len(bilder), os.path.basename(bas + ".png"),
            ", rutor " + ", ".join("`%s`" % os.path.basename(r) for r in rutor) if rutor else ""))
        if tecken:
            matt = [w for w in ord_ if MATT.match(w.strip("()[],;:"))]
            skalor = sorted({m.group(1) for _, _, t in rader for m in SKALA.finditer(t)}, key=int)
            with open(bas + "_text.txt", "w", encoding="utf-8") as f:
                f.write("# %s sida %d: text med läge (y, x i mm från övre vänstra hörnet)\n" % (os.path.basename(fil), i + 1))
                for y, x, t in rader:
                    f.write("%4d %4d  %s\n" % (y, x, t))
            rapport.append("  Text: %d rader i `%s`; %d tal som ser ut som mått (t.ex. %s)%s" % (
                len(rader), os.path.basename(bas + "_text.txt"), len(matt), ", ".join(list(dict.fromkeys(matt))[:12]),
                "; skala " + ", ".join("1:" + x for x in skalor) if skalor else ""))
    return rapport


def las_bild(fil, ut, a):
    Image, ImageOps = _pil()
    namn = os.path.splitext(os.path.basename(fil))[0]
    bild = ImageOps.exif_transpose(Image.open(fil)).convert("RGB")
    bas = os.path.join(ut, namn)
    _oversikt(bild, bas)
    rutor = _spara_rutor(bild, bas, kontrast=False)
    return ["## %s (bild %d x %d px)" % (os.path.basename(fil), *bild.size),
            "- Översikt `%s`%s" % (os.path.basename(bas + ".png"), ", rutor " + ", ".join("`%s`" % os.path.basename(r) for r in rutor) if rutor else "")]


def las_dxf(fil, ut, a):
    import ezdxf
    from ezdxf import bbox
    namn = os.path.splitext(os.path.basename(fil))[0]
    bas = os.path.join(ut, namn + "_dxf")
    doc = ezdxf.readfile(fil)
    msp = doc.modelspace()
    enh = {0: "ospecificerad", 1: "tum", 2: "fot", 4: "mm", 5: "cm", 6: "m"}.get(doc.header.get("$INSUNITS", 0), "kod %s" % doc.header.get("$INSUNITS"))
    lager = {}
    texter, matt = [], []
    for e in msp:
        lager[e.dxf.layer] = lager.get(e.dxf.layer, 0) + 1
        t = e.dxftype()
        if t == "TEXT":
            texter.append((e.dxf.insert.x, e.dxf.insert.y, e.dxf.text))
        elif t == "MTEXT":
            texter.append((e.dxf.insert.x, e.dxf.insert.y, e.plain_text().replace("\n", " | ")))
        elif t == "DIMENSION":
            try:
                v = e.get_measurement()
                v = v if isinstance(v, (int, float)) else getattr(v, "magnitude", v)
                matt.append((e.dxf.layer, e.dxf.get("text", "") or "", v))
            except Exception:
                pass
    ext = bbox.extents(msp, fast=True)
    with open(bas + ".txt", "w", encoding="utf-8") as f:
        f.write("# %s: enheter %s\n" % (os.path.basename(fil), enh))
        if ext.has_data:
            f.write("Utsträckning: x %.1f..%.1f, y %.1f..%.1f (%.1f x %.1f)\n" % (ext.extmin.x, ext.extmax.x, ext.extmin.y, ext.extmax.y, ext.size.x, ext.size.y))
        f.write("\nLager (antal objekt):\n")
        for k, n in sorted(lager.items()):
            f.write("  %-30s %d\n" % (k, n))
        f.write("\nMått (lager, text, uppmätt värde):\n")
        for l, t, v in matt:
            f.write("  %-20s %-16s %s\n" % (l, t, ("%.2f" % v) if isinstance(v, (int, float)) else v))
        f.write("\nTexter (x, y, text):\n")
        for x, y, t in sorted(texter, key=lambda q: (-q[1], q[0])):
            f.write("  %10.1f %10.1f  %s\n" % (x, y, t))
    rapport = ["## %s (DXF, enheter %s)" % (os.path.basename(fil), enh),
               "- %d lager, %d texter, %d mått i `%s`%s" % (len(lager), len(texter), len(matt), os.path.basename(bas + ".txt"),
                                                         ", storlek %.0f x %.0f" % (ext.size.x, ext.size.y) if ext.has_data else "")]
    try:                                                  # bild av ritningen via ezdxf + PyMuPDF
        from ezdxf.addons.drawing import RenderContext, Frontend, layout, pymupdf as dxfpdf
        import pymupdf
        Image, _ = _pil()
        be = dxfpdf.PyMuPdfBackend()
        Frontend(RenderContext(doc), be).draw_layout(msp)
        pdf = be.get_pdf_bytes(layout.Page(0, 0, layout.Units.mm, margins=layout.Margins.all(5)),
                               settings=layout.Settings(fit_page=True))
        d = pymupdf.open("pdf", pdf)
        pix = d[0].get_pixmap(dpi=a.zoom_dpi if max(d[0].rect.width, d[0].rect.height) < 1200 else 150)
        bild = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        _oversikt(bild, bas)
        rutor = _spara_rutor(bild, bas)
        rapport.append("- Bild `%s`%s" % (os.path.basename(bas + ".png"), ", rutor " + ", ".join("`%s`" % os.path.basename(r) for r in rutor) if rutor else ""))
    except Exception as e:
        rapport.append("- Ingen bild (%s: %s)" % (type(e).__name__, e))
    return rapport


def las(a):
    ut = os.path.abspath(a.ut)
    os.makedirs(ut, exist_ok=True)
    rapport = ["# Underlag", "", "Läs översikterna först, sedan rutorna där måtten står. Skriv upp varje mått med sida/ruta.", ""]
    for fil in a.filer:
        if not os.path.exists(fil):
            rapport.append("## %s: finns inte" % fil)
            continue
        slut = os.path.splitext(fil)[1].lower()
        try:
            if slut == ".pdf":
                rapport += las_pdf(fil, ut, a)
            elif slut in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".gif"):
                rapport += las_bild(fil, ut, a)
            elif slut == ".dxf":
                rapport += las_dxf(fil, ut, a)
            elif slut == ".dwg":
                rapport.append("## %s: DWG kan inte läsas, be om DXF eller PDF" % os.path.basename(fil))
            else:
                rapport.append("## %s: okänt format %s" % (os.path.basename(fil), slut))
        except Exception as e:
            rapport.append("## %s: kunde inte läsas (%s: %s)" % (os.path.basename(fil), type(e).__name__, e))
        rapport.append("")
    with open(os.path.join(ut, "underlag.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rapport) + "\n")
    print("\n".join(rapport))
    print("Sammanställning:", os.path.join(ut, "underlag.md"))


def zoom(a):
    Image, ImageOps = _pil()
    x0, y0, x1, y1 = (float(q) for q in a.ruta.split(","))
    ut = os.path.abspath(a.ut)
    os.makedirs(ut, exist_ok=True)
    namn = os.path.splitext(os.path.basename(a.filer[0]))[0]
    if a.filer[0].lower().endswith(".pdf"):
        import pymupdf
        s = pymupdf.open(a.filer[0])[a.sida - 1]
        r = s.rect
        klipp = pymupdf.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height, r.x0 + x1 * r.width, r.y0 + y1 * r.height)
        dpi = min(a.dpi, MAX_PX / (max(klipp.width, klipp.height) / 72))     # långsidan högst MAX_PX
        pix = s.get_pixmap(dpi=int(max(dpi, 72)), clip=klipp)
        bild = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        if not s.get_text("words"):
            bild = ImageOps.autocontrast(ImageOps.grayscale(bild), cutoff=1)
    else:
        b = ImageOps.exif_transpose(Image.open(a.filer[0])).convert("RGB")
        w, h = b.size
        bild = b.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    if a.forstora and a.forstora != 1:
        bild = bild.resize((int(bild.width * a.forstora), int(bild.height * a.forstora)), Image.LANCZOS)
    if a.rotera % 360:
        bild = bild.rotate(a.rotera % 360, expand=True)
    fil = os.path.join(ut, "%s_s%d_zoom_%s%s.png" % (namn, a.sida, "-".join("%02d" % round(100 * q) for q in (x0, y0, x1, y1)),
                                                   "_r%d" % (a.rotera % 360) if a.rotera % 360 else ""))
    bild.save(fil)
    print("Utsnitt: %s (%d x %d px)" % (fil, *bild.size))


def _xy(t):
    x, y = (float(q) for q in t.split(","))
    return x, y


def skala(a, logg=print):
    """Pixlar -> mm ur två referenspunkter med känt avstånd. Returnerar dict(mm_per_px, punkter, avstand)."""
    m = re.match(r"^\s*([\d.]+,[\d.]+)\s*:\s*([\d.]+,[\d.]+)\s*=\s*([\d.]+)\s*$", a.ref or "")
    if not m:
        raise SystemExit("--ref ska vara x1,y1:x2,y2=mm, t.ex. 120,340:520,340=4800")
    p1, p2, mm = _xy(m.group(1)), _xy(m.group(2)), float(m.group(3))
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    px = math.hypot(dx, dy)
    if px == 0:
        raise SystemExit("--ref: punkterna sammanfaller")
    k = mm / px
    ux, uy = dx / px, dy / px
    logg("Skala: %.2f mm/px (referens %.1f px = %g mm)" % (k, px, mm))
    res = dict(mm_per_px=k, punkter=[], avstand=[])
    for t in a.punkt or ():
        x, y = _xy(t)
        langs = ((x - p1[0]) * ux + (y - p1[1]) * uy) * k
        tvars = ((x - p1[0]) * -uy + (y - p1[1]) * ux) * k
        res["punkter"].append((t, round(langs), round(tvars)))
        logg("  punkt %-12s längs referensen %7.0f mm, vinkelrätt %7.0f mm" % (t, langs, tvars))
    for t in a.avstand or ():
        q1, q2 = (_xy(u) for u in t.split(":"))
        d = math.hypot(q2[0] - q1[0], q2[1] - q1[1]) * k
        res["avstand"].append((t, round(d)))
        logg("  avstånd %-20s %7.0f mm" % (t, d))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lage", choices=["las", "zoom", "skala"])
    ap.add_argument("filer", nargs="*")
    ap.add_argument("--ut", default=os.path.join(os.getcwd(), "ut", "underlag"))
    ap.add_argument("--dpi", type=int, default=400, help="zoom: upplösning")
    ap.add_argument("--zoom-dpi", dest="zoom_dpi", type=int, default=300, help="upplösning för rutorna (scannade ritningar: 300-400)")
    ap.add_argument("--sidor", default="", help="t.ex. 1-3,5 (standard alla)")
    ap.add_argument("--sida", type=int, default=1, help="zoom: sidan")
    ap.add_argument("--ruta", default="0,0,1,1", help="zoom: x0,y0,x1,y1 i bråkdelar av sidan")
    ap.add_argument("--rotera", type=int, default=0, help="zoom: vrid utsnittet 90/180/270 grader moturs")
    ap.add_argument("--forstora", type=float, default=1.0, help="zoom: förstoring av fotot (t.ex. 2)")
    ap.add_argument("--ref", default=None, help="skala: x1,y1:x2,y2=mm, två punkter med känt avstånd")
    ap.add_argument("--punkt", action="append", help="skala: x,y (flera)")
    ap.add_argument("--avstand", action="append", help="skala: x1,y1:x2,y2 (flera)")
    a = ap.parse_args(argv)
    if a.lage == "skala":
        skala(a)
    elif not a.filer:
        ap.error("ange minst en fil")
    elif a.lage == "las":
        las(a)
    else:
        zoom(a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
