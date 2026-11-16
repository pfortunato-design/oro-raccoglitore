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
| Cambio euro/dollaro | Banca Centrale Europea (`data-api.ecb.europa.eu`), ripiego frankfurter.dev |
| Serie giornaliera | **nessun fornitore: solo le misure di questo raccoglitore**, dal 07/09/2026 |
| Storia lunga (mensile, dal 1960) | World Bank Commodity Price Data (Pink Sheet), **CC-BY 4.0** |
| Cambio mensile per la storia lunga | Banca Centrale Europea, serie mensile dal 1999 |
| Tassi, inflazione attesa, dollaro, VIX | FRED, Federal Reserve Bank of St. Louis |
| Rischio geopolitico | Indice GPR, Caldara & Iacoviello, Federal Reserve Board |

## Tre regole scritte nel codice

1. **La serie giornaliera contiene solo ciò che abbiamo misurato noi.** Fino al 16/11/2026 si
   ricostruiva a ogni giro dal future COMEX di Yahoo Finance e arrivava al 2021; i termini di
   Yahoo vietano la raccolta automatica e la ridistribuzione in un'applicazione, quindi quei
   1.258 giorni sono stati **tolti**, non solo smesso di aggiungerne. La profondità la dà ora la
   serie mensile della Banca Mondiale, ridistribuibile con attribuzione.
2. **A mercato chiuso non si scrive un giorno nuovo.** Nel fine settimana la fonte continua a
   rispondere «aggiornato pochi secondi fa» servendo la chiusura di venerdi': contarla come
   misura aggiungerebbe alla serie giorni piatti che nessuno ha misurato.
3. **Un `serie.json` illeggibile ferma il giro** invece di essere sovrascritto. Meglio
   un'esecuzione fallita che una serie storica cancellata.
