import requests
import sqlite3
import logging
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"
log_dir = "/root/trinity-fund/next-gen/shared/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "hermes_feed.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

FF_XML_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def get_text(event, tag):
    el = event.find(tag)
    return el.text.strip() if el is not None and el.text else ""

def safe_float(val):
    if val in [None, "", "N/A"]:
        return None
    try:
        return float(str(val).replace('%', '').strip())
    except ValueError:
        return None

def fetch_and_update_calendar():
    try:
        logging.info("Interogare Forex Factory Calendar...")
        response = requests.get(FF_XML_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        updated_count = 0
        for event in root.findall('event'):
            title = get_text(event, 'title')
            date_str = get_text(event, 'date')
            time_str = get_text(event, 'time')
            impact = get_text(event, 'impact').upper()
            country = get_text(event, 'country')
            actual = get_text(event, 'actual')
            forecast = get_text(event, 'forecast')
            if not title or not date_str:
                continue
            try:
                if time_str:
                    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                else:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                event_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                event_time = f"{date_str} {time_str}".strip()
            impact_mapped = impact if impact in ["HIGH", "MEDIUM", "LOW"] else "MEDIUM"
            cursor.execute("""
                INSERT OR REPLACE INTO economic_calendar
                (event_name, event_time, forecast, actual, currency, impact)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, event_time, safe_float(forecast), safe_float(actual), country, impact_mapped))
            updated_count += 1
        conn.commit()
        conn.close()
        logging.info(f"Calendar actualizat: {updated_count} evenimente.")
    except Exception as e:
        logging.error(f"Eroare: {e}")

if __name__ == "__main__":
    logging.info("Hermes Feed Calendar pornit.")
    fetch_and_update_calendar()
    while True:
        time.sleep(3600)
        fetch_and_update_calendar()
