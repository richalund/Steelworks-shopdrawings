# Leveranser från agenter utan filnedladdning

I Codex, Copilot och Cursor ser användaren bara det som committas. I användarens eget **privata** repo kopierar
agenten då det användaren ska ha (PDF, PNG, beställningspaketet `_bestallning.zip`, mailet `_mail.eml`) till
`leverans/<uppdrag>/`, committar det på uppdragets gren och ger länken. Leveranser läggs aldrig på `main`, aldrig i
en förbättrings-PR för skillen och aldrig i ett publikt repo (Steelworks-shopdrawings och forkar av det är
publika). Uppdraget sparas sedan i sin projektmapp (SKILL.md, "Spara uppdraget i projektmappen").
I Claude Code laddas filerna i `ut/` ner direkt ur sessionen och den här mappen behövs inte.
