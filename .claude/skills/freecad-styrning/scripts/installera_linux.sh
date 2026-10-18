#!/bin/bash
# Installerar det freecad-styrning behöver på Linux (t.ex. en Claude Code-molnsession):
#   FreeCAD 1.1.3 från conda-forge (via micromamba) i /opt/freecad med CalculiX (FEM, hallfasthet.py),
#   SheetMetal 0.7.24 (samma version som skillen är testad med på Windows), Xvfb för TechDraw utan skärm,
#   ifcopenshell i /opt/freecad-extra (IFC-export, export.py), ett typsnitt med kinesiska tecken (ritningar på
#   kinesiska), och PyMuPDF + ezdxf + Pillow i system-Python för PDF, DXF och bilder.
#
# Tar 5–10 minuter första gången och ca 4 GB disk. Idempotent: redan installerat hoppas över.
# Körs vid behov, inte vid varje sessionsstart:
#   bash .claude/skills/freecad-styrning/scripts/installera_linux.sh
# fcapi.py hittar FreeCAD i /opt/freecad/bin; annan plats: sätt FREECAD_PREFIX här och
# FREECAD_BIN=<prefix>/bin när skripten körs.
set -euo pipefail

PREFIX="${FREECAD_PREFIX:-/opt/freecad}"
FREECAD_VERSION="1.1.3"
SHEETMETAL_TAG="V0.7.24-beta"
MAMBA_DIR="${MAMBA_DIR:-/opt/micromamba}"
export MAMBA_ROOT_PREFIX="$MAMBA_DIR/root"

steg() { echo "== $*"; }

# 1. FreeCAD
if [ -x "$PREFIX/bin/freecad" ]; then
  steg "FreeCAD finns redan i $PREFIX"
else
  if [ ! -x "$MAMBA_DIR/bin/micromamba" ]; then
    steg "Hämtar micromamba"
    mkdir -p "$MAMBA_DIR"
    curl -sSfL https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C "$MAMBA_DIR" bin/micromamba
  fi
  steg "Installerar FreeCAD $FREECAD_VERSION i $PREFIX (tar några minuter)"
  "$MAMBA_DIR/bin/micromamba" create -y -q -p "$PREFIX" -c conda-forge \
    "freecad=$FREECAD_VERSION" calculix python=3.11 networkx defusedxml
  "$MAMBA_DIR/bin/micromamba" clean -a -y -q >/dev/null 2>&1 || true
fi

# 1b. CalculiX i en äldre installation. FreeCAD-versionen låses i samma kommando: annars kan lösaren byta
#     FreeCAD mot en utvecklingsversion som inte fungerar med skripten.
if [ ! -x "$PREFIX/bin/ccx" ]; then
  steg "Installerar CalculiX i $PREFIX"
  "$MAMBA_DIR/bin/micromamba" install -y -q -p "$PREFIX" -c conda-forge "freecad=$FREECAD_VERSION" calculix || \
    echo "OBS: CalculiX kunde inte installeras (hallfasthet.py fem fungerar inte)" >&2
fi

# FreeCAD 1.1 visar en modal migreringsdialog vid start om en annan versions konfiguration finns
# men inte den egna – den blockerar jobben (inget svar under xvfb). En tom egen konfigmapp räcker.
VERDIR="v$(echo "$FREECAD_VERSION" | cut -d. -f1-2 | tr . -)"
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/FreeCAD/$VERDIR" "${XDG_DATA_HOME:-$HOME/.local/share}/FreeCAD/$VERDIR"

# 2. SheetMetal (GitHub nås inte direkt från molnsessionen; jsDelivr speglar repot per tagg)
SM="$PREFIX/Mod/SheetMetal"
if grep -q "<version>0.7.24<" "$SM/package.xml" 2>/dev/null; then
  steg "SheetMetal 0.7.24 finns redan"
else
  steg "Installerar SheetMetal $SHEETMETAL_TAG"
  rm -rf "$SM.tmp" && mkdir -p "$SM.tmp"
  lista=$(curl -sSf "https://data.jsdelivr.com/v1/package/gh/shaise/FreeCAD_SheetMetal@$SHEETMETAL_TAG/flat")
  echo "$lista" | python3 -c 'import json,sys; [print(f["name"]) for f in json.load(sys.stdin)["files"]]' \
    | grep -vE '^/(\.github|SMTests)/|\.pdf$' | while read -r f; do
      mkdir -p "$SM.tmp$(dirname "$f")"
      curl -sSf --retry 3 "https://cdn.jsdelivr.net/gh/shaise/FreeCAD_SheetMetal@$SHEETMETAL_TAG$f" -o "$SM.tmp$f"
    done
  grep -q "<version>0.7.24<" "$SM.tmp/package.xml" || { echo "SheetMetal-nedladdningen är ofullständig" >&2; exit 1; }
  rm -rf "$SM" && mv "$SM.tmp" "$SM"
fi

# 3. Xvfb (TechDraw kräver GUI; fcapi.py startar FreeCAD via xvfb-run när DISPLAY saknas)
if command -v xvfb-run >/dev/null 2>&1; then
  steg "Xvfb finns redan"
else
  steg "Installerar Xvfb"
  apt-get update -qq >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq xvfb >/dev/null
fi

# 4. System-Python: PyMuPDF (PDF-blad, PNG), ezdxf (DXF) och Pillow (bilder, underlag.py, testa.py)
if python3 -c "import pymupdf, ezdxf, PIL" >/dev/null 2>&1; then
  steg "PyMuPDF, ezdxf och Pillow finns redan"
else
  steg "Installerar PyMuPDF, ezdxf och Pillow"
  python3 -m pip install -q pymupdf ezdxf pillow 2>/dev/null || python3 -m pip install -q --break-system-packages pymupdf ezdxf pillow
fi

# 5. ifcopenshell (IFC-export) i en egen mapp: conda-paketet kräver en annan OCCT än FreeCAD 1.1.3, pip-hjulet
#    har sin egen och läggs utanför FreeCADs miljö (export.py lägger mappen i sys.path)
EXTRA="${FREECAD_EXTRA:-/opt/freecad-extra}"
if [ -d "$EXTRA/ifcopenshell" ]; then
  steg "ifcopenshell finns redan"
else
  steg "Installerar ifcopenshell i $EXTRA"
  "$PREFIX/bin/pip" install -q --no-deps --target "$EXTRA" ifcopenshell 2>/dev/null || \
    echo "OBS: ifcopenshell kunde inte installeras (export.py --format ifc fungerar inte)" >&2
fi

# 6. Typsnitt med kinesiska tecken (ritningar med --sprak zh)
if fc-list :lang=zh 2>/dev/null | grep -q .; then
  steg "Typsnitt med kinesiska tecken finns redan"
else
  steg "Installerar typsnittet WenQuanYi Zen Hei"
  (apt-get update -qq >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fonts-wqy-zenhei >/dev/null) || \
    echo "OBS: typsnittet kunde inte installeras (kinesiska ritningar visar rutor)" >&2
fi

"$PREFIX/bin/freecadcmd" --version 2>/dev/null | head -1 || true
steg "Klart. Exempel: python3 .claude/skills/freecad-styrning/scripts/partdesign.py bygg .claude/skills/freecad-styrning/delar/fotplatta.py /tmp/Fotplatta.FCStd"
