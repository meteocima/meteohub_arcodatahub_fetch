# Il dato nativo si conserva: una colonna per passo di cumulata, qualità come flag

Ogni uscita conserva il valore come arriva da MeteoHub accanto a quello orario derivato. La pioggia ha una colonna per passo di cumulata (`prec_300s`, `prec_3600s`…), perché una stazione può dare più passi nello stesso istante e una colonna unica `prec` con `prec_period_s` li sovrascriveva. I controlli di qualità aggiungono flag e non cancellano valori, a differenza di `clean_and_hourly.py` che azzera le temperature fuori soglia. La pioggia oraria si ricava dalla cumulata oraria nativa, se c'è, altrimenti dalla somma completa dei passi più brevi; per l'SRI radar dalla media delle intensità dell'ora, con almeno 2/3 delle misure attese.

## Consequences

Lo schema del CSV di `meteohub_download.py` e `filter_provincia.py` è cambiato il 2026-10-14 (commit d9b0af2): chi leggeva `prec` deve leggere le colonne `prec_<passo>s`.
