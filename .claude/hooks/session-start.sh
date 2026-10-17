#!/bin/bash
# SessionStart-hook för Claude Code-molnsessioner (claude.ai/code, även från mobilappen).
# Installerar FreeCAD 1.1.3, SheetMetal, Xvfb, PyMuPDF och ezdxf i bakgrunden så att skillen
# kan rita direkt. Första gången i en ny container tar det 5–10 minuter; därefter är det klart
# på några sekunder. Lokalt (på en egen dator) gör hooken ingenting.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo '{"async": true, "asyncTimeout": 1800000}'

cd "$CLAUDE_PROJECT_DIR"
bash .claude/skills/freecad-styrning/scripts/installera_linux.sh
echo "freecad-styrning: FreeCAD och beroenden installerade"
