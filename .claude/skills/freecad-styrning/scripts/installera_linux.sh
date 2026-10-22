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

# Fungerar i Claude Code, Codex, Copilot (GitHub Actions), Jules och Cursor: som root eller med sudo. Utan
# skrivrätt i /opt (och utan sudo) hamnar allt i ~/.local/opt; fcapi.py och export.py letar på båda ställena.
if [ "$(id -u)" = "0" ]; then SUDO=""; elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then SUDO="sudo"; else SUDO="ingen"; fi
OPT=/opt
if [ ! -w /opt ]; then
  if [ "$SUDO" = "sudo" ]; then sudo mkdir -p /opt/freecad /opt/micromamba /opt/freecad-extra && sudo chown -R "$(id -u):$(id -g)" /opt/freecad /opt/micromamba /opt/freecad-extra
  else OPT="$HOME/.local/opt"; mkdir -p "$OPT"; fi
fi
apt_installera() {   # paket...
  [ "$SUDO" = "ingen" ] && { echo "OBS: kan inte installera $* (varken root eller sudo)" >&2; return 1; }
  $SUDO apt-get update -qq >/dev/null && $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@" >/dev/null
}
PREFIX="${FREECAD_PREFIX:-$OPT/freecad}"
FREECAD_VERSION="1.1.3"
SHEETMETAL_TAG="V0.7.24-beta"
SHEETMETAL_URL="${SHEETMETAL_URL:-https://github.com/richalund/Steelworks-shopdrawings/releases/download/verktyg/FreeCAD_SheetMetal-$SHEETMETAL_TAG.tar.gz}"
MAMBA_DIR="${MAMBA_DIR:-$OPT/micromamba}"
export MAMBA_ROOT_PREFIX="$MAMBA_DIR/root"

steg() { echo "== $*"; }

# 1. FreeCAD
if [ -x "$PREFIX/bin/freecad" ]; then
  steg "FreeCAD finns redan i $PREFIX"
else
  if [ ! -x "$MAMBA_DIR/bin/micromamba" ]; then
    steg "Hämtar micromamba"
    mkdir -p "$MAMBA_DIR"
    mkdir -p "$MAMBA_DIR/bin"
    # GitHub-releasen först (ingår i Claude Codes standardnät "Trusted"), micro.mamba.pm som reserv
    curl -sSfL --retry 3 -o "$MAMBA_DIR/bin/micromamba" \
         https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64 \
      && chmod +x "$MAMBA_DIR/bin/micromamba" && "$MAMBA_DIR/bin/micromamba" --version >/dev/null 2>&1 \
      || curl -sSfL https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C "$MAMBA_DIR" bin/micromamba
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
  # 1) oförändrad kopia av taggens källkod som release-fil i det här repot (GitHub-releaser ingår i standardnätet
  #    "Trusted"; källarkiv från andra repon släpps inte alltid igenom), 2) jsDelivr-spegeln av repot
  if curl -sSfL --retry 3 "$SHEETMETAL_URL" -o "$SM.tmp.tar.gz" \
     && tar -xzf "$SM.tmp.tar.gz" -C "$SM.tmp" --strip-components=1 --exclude='*/SMTests' --exclude='*/.github' --exclude='*.pdf'; then
    rm -f "$SM.tmp.tar.gz"
  else
    rm -rf "$SM.tmp" "$SM.tmp.tar.gz" && mkdir -p "$SM.tmp"
    lista=$(curl -sSf "https://data.jsdelivr.com/v1/package/gh/shaise/FreeCAD_SheetMetal@$SHEETMETAL_TAG/flat")
    echo "$lista" | python3 -c 'import json,sys; [print(f["name"]) for f in json.load(sys.stdin)["files"]]' \
      | grep -vE '^/(\.github|SMTests)/|\.pdf$' | while read -r f; do
        mkdir -p "$SM.tmp$(dirname "$f")"
        curl -sSf --retry 3 "https://cdn.jsdelivr.net/gh/shaise/FreeCAD_SheetMetal@$SHEETMETAL_TAG$f" -o "$SM.tmp$f"
      done
  fi
  grep -q "<version>0.7.24<" "$SM.tmp/package.xml" || { echo "SheetMetal-nedladdningen är ofullständig" >&2; exit 1; }
  rm -rf "$SM" && mv "$SM.tmp" "$SM"
fi

# 3. Xvfb (TechDraw kräver GUI; fcapi.py startar FreeCAD via xvfb-run när DISPLAY saknas)
if command -v xvfb-run >/dev/null 2>&1; then
  steg "Xvfb finns redan"
else
  steg "Installerar Xvfb"
  apt_installera xvfb
fi
# bibliotek som FreeCADs GUI behöver i en ren Ubuntu-bild (finns oftast redan)
if ! ldconfig -p 2>/dev/null | grep -q "libxcb-cursor.so"; then
  steg "Installerar X- och OpenGL-bibliotek"
  apt_installera libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 libfontconfig1 libdbus-1-3 || true
fi

# 4. System-Python: PyMuPDF (PDF-blad, PNG), ezdxf (DXF), Pillow (bilder, underlag.py, testa.py) och openpyxl
#    (kalkylunderlag i Excel, mangder.py samla)
if python3 -c "import pymupdf, ezdxf, PIL, openpyxl" >/dev/null 2>&1; then
  steg "PyMuPDF, ezdxf, Pillow och openpyxl finns redan"
else
  steg "Installerar PyMuPDF, ezdxf, Pillow och openpyxl"
  python3 -m pip install -q pymupdf ezdxf pillow openpyxl 2>/dev/null || python3 -m pip install -q --break-system-packages pymupdf ezdxf pillow openpyxl
fi

# 5. ifcopenshell (IFC-export) i en egen mapp: conda-paketet kräver en annan OCCT än FreeCAD 1.1.3, pip-hjulet
#    har sin egen och läggs utanför FreeCADs miljö (export.py lägger mappen i sys.path)
EXTRA="${FREECAD_EXTRA:-$OPT/freecad-extra}"
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
  apt_installera fonts-wqy-zenhei || \
    echo "OBS: typsnittet kunde inte installeras (kinesiska ritningar visar rutor)" >&2
fi

"$PREFIX/bin/freecadcmd" --version 2>/dev/null | head -1 || true
steg "Klart. Exempel: python3 .claude/skills/freecad-styrning/scripts/partdesign.py bygg .claude/skills/freecad-styrning/delar/fotplatta.py /tmp/Fotplatta.FCStd"
