"""Rendera PDF-sidor till PNG för granskning (vanlig Python med PyMuPDF).
  python rendera_pdf.py <fil.pdf> <utprefix> [dpi] [x0 y0 x1 y1 som andelar av sidan för ett utsnitt]
"""
import sys
try:
    import pymupdf as fitz
except ImportError:
    import fitz
pdf, pre = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 110
doc = fitz.open(pdf)
print("sidor:", len(doc), "format:", [tuple(round(v) for v in p.rect) for p in doc])
for i, p in enumerate(doc):
    clip = None
    if len(sys.argv) > 7:
        r = p.rect
        f = [float(v) for v in sys.argv[4:8]]
        clip = fitz.Rect(r.x0 + f[0] * r.width, r.y0 + f[1] * r.height, r.x0 + f[2] * r.width, r.y0 + f[3] * r.height)
    pix = p.get_pixmap(dpi=dpi, clip=clip)
    ut = "%s_s%d.png" % (pre, i + 1)
    pix.save(ut)
    print(ut, pix.width, "x", pix.height)
