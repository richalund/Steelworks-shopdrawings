# Leveranser från agenter utan filnedladdning

I Codex, Copilot och Cursor ser användaren bara det som committas. Agenten kopierar då det användaren ska ha
(PDF, PNG, beställningspaketet `_bestallning.zip`, mailet `_mail.eml`) till `leverans/<uppdrag>/`, committar det på
uppdragets gren och ger länken. Leveranser läggs aldrig på `main` och aldrig i en förbättrings-PR för skillen.
I Claude Code laddas filerna i `ut/` ner direkt ur sessionen och den här mappen behövs inte.
