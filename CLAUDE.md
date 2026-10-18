@AGENTS.md

## Det som gäller just Claude Code
- Skillen `freecad-styrning` laddas från `.claude/skills/`; använd den för allt som rör ritningar och modeller.
- I en molnsession installerar SessionStart-hooken (`.claude/hooks/session-start.sh`) FreeCAD i bakgrunden
  (10–15 min första gången i en ny container). Vänta på att `/opt/freecad/bin/freecad` finns innan första
  ritningen, eller kör `bash .claude/skills/freecad-styrning/scripts/installera_linux.sh` själv.
- Frågorna till användaren (företagsuppgifter, leverans) ställs med AskUserQuestion-formuläret.
- Visa PNG:erna med Read och lägg upp filerna i chatten med verktyget för att skicka filer (många filer: en PDF
  och en zip med `paket.py samla`); `leverans/` behövs inte i Claude Code.
- Leveransmailet: är Gmail kopplat, lägg ett utkast med paketet som bilaga och skicka bara på uttryckligt ja.
