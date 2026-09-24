import requests
import sqlite3
import logging
import os
import time
from datetime import datetime

# 🔧 CONFIGURARE API (ÎNLOCUIEȘTE CU DATELE TALE REALE)
API_URL = "https://news.g4trade.online/api/calendar"  # <-- URL-UL TĂU REAL
API_HEADERS = {
    "Accept": "application/json",
    # "Authorization": "Bearer YOUR_API_TOKEN"  # <-- DACĂ API-UL TĂU CEREAUTENTIFICARE
}

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"
log_dir = "/root/trinity-fund/next-gen/shared/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "hermes_feed.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fetch_and_update_calendar():
    try:
        logging.info("📥 Interogare API Calendar Economic...")
        response = requests.get(API_URL, headers=API_HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Dacă API-ul returnează o listă directă sau un câmp precum 'events'
        events = data if isinstance(data, list) else data.get("events", data.get("calendar", []))
        
        if not events:
            logging.warning("⚠️ API-ul nu a returnat evenimente. Verifică structura JSON.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        updated_count = 0

        for ev in events:
            # 🔧 MAPARE FLEXIBILĂ (Ajustează cheile în funcție de răspunsul tău API)
            event_name = ev.get("name", ev.get("title", ev.get("event", "")))
            event_time = ev.get("time", ev.get("date", ev.get("datetime", "")))
            forecast = ev.get("forecast", ev.get("estimate", None))
            actual = ev.get("actual", ev.get("result", None))
            currency = ev.get("currency", ev.get("ccy", "USD"))
            impact = ev.get("impact", ev.get("importance", "MEDIUM")).upper()

            if not event_name or not event_time:
                continue

            # Convertim forecast/actual în float dacă sunt șiruri
            try: forecast = float(forecast) if forecast not in [None, "", "N/A"] else None
            except: forecast = None
            try: actual = float(actual) if actual not in [None, "", "N/A"] else None
            except: actual = None

            # Formatăm ora în YYYY-MM-DD HH:MM:SS dacă e necesar
            if "T" in str(event_time):
                event_time = str(event_time).split(".")[0].replace("T", " ")

            cursor.execute("""
                INSERT OR REPLACE INTO economic_calendar 
                (event_name, event_time, forecast, actual, currency, impact)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_name, event_time, forecast, actual, currency, impact))
            updated_count += 1

        conn.commit()
        conn.close()
        logging.info(f"✅ Calendar actualizat: {updated_count} evenimente procesate.")

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Eroare rețea API: {e}")
    except Exception as e:
        logging.error(f"❌ Eroare procesare date: {e}")

if __name__ == "__main__":
    logging.info("🚀 Hermes Feed Calendar pornit. Se actualizează la fiecare oră.")
    while True:
        fetch_and_update_calendar()
        time.sleep(3600)  # Actualizare la 60 minute
