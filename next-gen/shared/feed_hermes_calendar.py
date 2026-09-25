import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import sqlite3
import logging
import os
import time
from datetime import datetime

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
        # User-Agent complet pentru a părea un browser real
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(FF_URL, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        updated_count = 0

        # Căutăm flexibil tag-ul 'event' sau 'calendar'
        for element in root.iter():
            if element.tag.endswith('event') or element.tag == 'event':
                country = element.find('country').text if element.find('country') is not None else "USD"
                date_str = element.find('date').text if element.find('date') is not None else ""
                time_str = element.find('time').text if element.find('time') is not None else ""
                
                # Uneori numele este în tag-ul 'title', alteori în 'event'
                name_elem = element.find('event')
                if name_elem is None:
                    name_elem = element.find('title')
                event_name = name_elem.text if name_elem is not None else "Unknown Event"
                
                impact = element.find('impact').text if element.find('impact') is not None else "Medium"
                forecast = element.find('forecast').text if element.find('forecast') is not None else None
                actual = element.find('actual').text if element.find('actual') is not None else None
                
                event_time = f"{date_str} {time_str}:00" if date_str and time_str else date_str
                
                if forecast: forecast = str(forecast).replace('%', '').strip()
                if actual: actual = str(actual).replace('%', '').strip()

                cursor.execute("""
                    INSERT OR REPLACE INTO economic_calendar 
                    (event_name, event_time, forecast, actual, currency, impact)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (event_name, event_time, forecast, actual, country, impact.upper()))
                updated_count += 1

        conn.commit()
        conn.close()
        logging.info(f"✅ Calendar actualizat: {updated_count} evenimente.")

    except urllib.error.HTTPError as e:
        if e.code == 429:
            logging.warning("⚠️ Forex Factory ne-a blocat temporar (429). Păstrăm datele anterioare și vom încerca din nou la următorul ciclu (12h).")
        else:
            logging.error(f"❌ Eroare HTTP: {e}")
    except Exception as e:
        logging.error(f"❌ Eroare procesare: {e}")

if __name__ == "__main__":
    logging.info("🚀 Hermes Feed Calendar (Mod Politicos) pornit.")
    fetch_and_update_calendar()
    
    # Actualizare la fiecare 12 ore (43200 secunde) pentru a nu fi blocați
    while True:
        time.sleep(43200)
        fetch_and_update_calendar()
