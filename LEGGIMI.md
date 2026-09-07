# Raccoglitore oro — misura in cloud

Misura il prezzo dell'oro e i fattori macroeconomici **tre volte al giorno** e pubblica
`pubblico/serie.json`, che l'app iPhone legge.

## Perche' esiste

iOS non garantisce esecuzioni in background a orari fissi, e un Mac che dorme non misura.
Un lavoro pianificato in cloud misura sempre — computer spento, telefono in tasca — e il
telefono si limita a leggere.

## ⛔ Qui non entra nulla di personale

Si pubblicano **prezzi e indicatori pubblici**, che non sono dati di nessuno. Grammi
posseduti, importi pagati e guadagno restano sul telefono e non passano mai di qui. E' la
ragione per cui questo file puo' stare su un indirizzo pubblico.

## Fonti

| Dato | Fonte |
|---|---|
| Prezzo spot dell'oro | gold-api.com |
| Cambio euro/dollaro | frankfurter.dev (tassi di riferimento BCE) |
| Serie storica | Yahoo Finance `GC=F` — future COMEX, **approssimazione** dello spot |
| Tassi, inflazione attesa, dollaro, VIX | FRED, Federal Reserve Bank of St. Louis |
| Rischio geopolitico | Indice GPR, Caldara & Iacoviello, Federal Reserve Board |

## Tre regole scritte nel codice

1. **La serie giornaliera si ricostruisce a ogni giro** dai fornitori: un'esecuzione saltata
   non lascia un buco permanente.
2. **A mercato chiuso non si scrive un giorno nuovo.** Nel fine settimana la fonte continua a
   rispondere «aggiornato pochi secondi fa» servendo la chiusura di venerdi': contarla come
   misura aggiungerebbe alla serie giorni piatti che nessuno ha misurato.
3. **Un `serie.json` illeggibile ferma il giro** invece di essere sovrascritto. Meglio
   un'esecuzione fallita che una serie storica cancellata.
