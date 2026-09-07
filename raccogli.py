#!/usr/bin/env python3
"""Raccoglitore in cloud. Gira tre volte al giorno su GitHub Actions e pubblica un file
che l'app iPhone legge.

⛔ QUI NON ENTRA NULLA DI PERSONALE. Si pubblicano prezzi e indicatori macroeconomici, che
non sono dati di nessuno. Grammi posseduti, importi pagati e guadagno restano sul telefono
e non passano di qui: e' la ragione per cui questo file puo' stare su un indirizzo pubblico.

Perche' esiste: iOS non garantisce esecuzioni in background a orari fissi, e un Mac che
dorme non misura. Un lavoro pianificato in cloud misura sempre, e il telefono legge.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

from oro import fonti

USCITA = Path(__file__).parent / "pubblico" / "serie.json"
ANNI_DI_STORIA = 5

# Le fasce sono bande larghe, non orari al minuto: cosi' il passaggio fra ora legale e
# ora solare non sposta una rilevazione da una fascia all'altra. Il cron e' in UTC.
FASCE = {"mattino": (6, 11), "mezzogiorno": (11, 16), "sera": (16, 23)}


def fascia(m: datetime) -> str:
    for nome, (da, a) in FASCE.items():
        if da <= m.hour < a:
            return nome
    return "notte"


def taglia(serie: dict[str, float], anni: int = ANNI_DI_STORIA) -> dict[str, float]:
    limite = (date.today() - timedelta(days=365 * anni)).isoformat()
    return {g: round(v, 6) for g, v in serie.items() if g >= limite}


def carica_precedente() -> dict:
    if USCITA.exists():
        try:
            with USCITA.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            # ⛔ Un file illeggibile non si sovrascrive in silenzio: si ferma il giro.
            # Meglio un'esecuzione fallita che una serie storica cancellata.
            print(f"::error::serie.json esistente non leggibile: {e}")
            sys.exit(1)
    return {}


def main() -> int:
    precedente = carica_precedente()
    ora_utc = datetime.now(timezone.utc)
    # ⛔ Fuso DICHIARATO, non «quello della macchina». `astimezone()` senza argomento usa
    # il fuso locale di chi esegue: sul Mac e' Roma, sui server di GitHub e' UTC. Il
    # 07/09/2026 una misura delle 12:41 di Roma e' finita nella fascia «mattino» per
    # questo. Le fasce descrivono la giornata di chi guarda l'app, non del server.
    ora_roma = ora_utc.astimezone(ZoneInfo("Europe/Rome"))
    copertura: list[str] = []

    spot = fonti.oro_spot_usd_oncia()
    cambio = fonti.eur_per_usd()
    aperto = fonti.mercato_oro_aperto(ora_utc)
    copertura.append(f"oro spot {'OK' if spot.ok else 'NON RILEVATO: ' + str(spot.errore)}")
    copertura.append(f"cambio {'OK' if cambio.ok else 'NON RILEVATO: ' + str(cambio.errore)}")

    rilevazioni = precedente.get("rilevazioni", [])
    corrente = None
    if spot.ok and cambio.ok:
        corrente = {
            "momento": ora_utc.isoformat(),
            "data": ora_utc.date().isoformat(),
            "fascia": fascia(ora_roma),
            "oro_usd_oncia": round(spot.valore, 4),
            "eur_per_dollaro": cambio.valore,
            "oro_eur_grammo": round(fonti.eur_grammo(spot.valore, cambio.valore), 4),
            "mercato_aperto": aperto,
            "fonte_oro": spot.fonte,
            "fonte_cambio": cambio.fonte,
        }
        rilevazioni.append(corrente)
        rilevazioni = rilevazioni[-400:]
    else:
        print("::warning::prezzo non rilevato in questa esecuzione")

    # Serie giornaliera: si RICOSTRUISCE dai fornitori a ogni giro, cosi' un'esecuzione
    # saltata non lascia un buco permanente. I giorni a mercato chiuso non entrano.
    giornaliero = {g: v for g, v in precedente.get("giornaliero", {}).items()}
    storico = fonti.oro_storico_usd_oncia("5y")
    if storico.ok:
        usd = storico.extra["serie"]
        cambi = fonti.eur_per_usd_storico(min(usd))
        if cambi.ok:
            k = cambi.extra["serie"]
            giorni_k = sorted(k)
            for g, u in usd.items():
                c = k.get(g) or next((k[x] for x in reversed(giorni_k) if x <= g), None)
                if c:
                    giornaliero[g] = round(fonti.eur_grammo(u, c), 4)
            copertura.append(f"serie oro OK {len(usd)} giorni")
        else:
            copertura.append(f"serie cambio NON RILEVATA: {cambi.errore}")
    else:
        copertura.append(f"serie oro NON RILEVATA: {storico.errore}")

    # La chiusura di oggi vale solo a mercato aperto (v. sopra: altrimenti e' la copia
    # della chiusura precedente, e diventerebbe un giorno piatto mai misurato).
    if corrente and aperto:
        giornaliero[corrente["data"]] = corrente["oro_eur_grammo"]

    fattori = precedente.get("fattori", {})
    meta = precedente.get("fattori_meta", {})
    for chiave in fonti.SERIE_FRED:
        lettura = fonti.fred(chiave)
        if lettura.ok:
            fattori[chiave] = taglia(lettura.extra["serie"])
            codice, descrizione, unita = fonti.SERIE_FRED[chiave]
            meta[chiave] = {"codice": codice, "descrizione": descrizione,
                            "unita": unita, "fonte": lettura.fonte, "al": lettura.momento}
            copertura.append(f"{chiave} OK (al {lettura.momento})")
        else:
            copertura.append(f"{chiave} NON RILEVATO: {lettura.errore}")

    gpr = fonti.rischio_geopolitico()
    if gpr.ok:
        fattori["rischio_geopolitico"] = taglia(gpr.extra["serie"])
        meta["rischio_geopolitico"] = {
            "codice": "GPRD", "descrizione": "Indice di rischio geopolitico",
            "unita": "indice",
            "fonte": "Caldara & Iacoviello, Federal Reserve Board", "al": gpr.momento}
        copertura.append(f"rischio geopolitico OK (al {gpr.momento})")
    else:
        copertura.append(f"rischio geopolitico NON RILEVATO: {gpr.errore}")

    fuori = {
        "versione": 1,
        "generato": ora_utc.isoformat(),
        "avvertenza": ("Prezzi e indicatori pubblici. Nessun dato personale: il portafoglio "
                       "resta sul dispositivo di chi usa l'app e non passa mai di qui."),
        "corrente": corrente,
        "rilevazioni": rilevazioni,
        "giornaliero": dict(sorted(giornaliero.items())),
        "fattori": fattori,
        "fattori_meta": meta,
        "copertura": copertura,
    }
    USCITA.parent.mkdir(parents=True, exist_ok=True)
    USCITA.write_text(json.dumps(fuori, ensure_ascii=False, separators=(",", ":")),
                      encoding="utf-8")

    peso = USCITA.stat().st_size / 1024
    stato = "mercato aperto" if aperto else "MERCATO CHIUSO (chiusura precedente riproposta)"
    print(f"{corrente['oro_eur_grammo'] if corrente else 'n/r'} EUR/g · {stato}")
    print(f"{len(giornaliero)} giorni · {len(rilevazioni)} rilevazioni · {peso:.0f} kB")
    print("Fonti: " + " · ".join(copertura))
    return 0 if corrente else 2


if __name__ == "__main__":
    sys.exit(main())
