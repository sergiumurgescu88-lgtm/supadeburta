import urllib.request
import xml.etree.ElementTree as ET
import sqlite3
import logging
import os
import time

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
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
        logging.info("📥 Descărcare Calendar Forex Factory...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(FF_URL, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        updated_count = 0

        for event in root.findall('event'):
            # Extragem datele exact conform structurii XML reale
            title_elem = event.find('title')
            event_name = title_elem.text.strip() if title_elem is not None and title_elem.text else "Unknown Event"
            
            country_elem = event.find('country')
            currency = country_elem.text.strip() if country_elem is not None and country_elem.text else "USD"
            
            date_elem = event.find('date')
            date_str = date_elem.text.strip() if date_elem is not None and date_elem.text else ""
            
            time_elem = event.find('time')
            time_str = time_elem.text.strip() if time_elem is not None and time_elem.text else ""
            
            impact_elem = event.find('impact')
            impact = impact_elem.text.strip().upper() if impact_elem is not None and impact_elem.text else "MEDIUM"
            
            forecast_elem = event.find('forecast')
            forecast = forecast_elem.text.strip() if forecast_elem is not None and forecast_elem.text else None
            
            actual_elem = event.find('actual')
            actual = actual_elem.text.strip() if actual_elem is not None and actual_elem.text else None
            
            # Formatăm data și ora
            event_time = f"{date_str} {time_str}:00" if date_str and time_str else date_str
            
            # Curățăm datele (eliminăm '%' etc. pentru calcule matematice viitoare)
            if forecast: forecast = forecast.replace('%', '').strip()
            if actual: actual = actual.replace('%', '').strip()

            cursor.execute("""
                INSERT OR REPLACE INTO economic_calendar 
                (event_name, event_time, forecast, actual, currency, impact)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_name, event_time, forecast, actual, currency, impact))
            updated_count += 1

        conn.commit()
        conn.close()
        logging.info(f"✅ Calendar actualizat cu succes: {updated_count} evenimente procesate.")

    except Exception as e:
        logging.error(f"❌ Eroare la procesarea calendarului: {e}")

if __name__ == "__main__":
    logging.info("🚀 Hermes Feed Calendar (Forex Factory) pornit.")
    fetch_and_update_calendar()
    # Actualizare la fiecare 6 ore
    while True:
        time.sleep(21600)
        fetch_and_update_calendar()
