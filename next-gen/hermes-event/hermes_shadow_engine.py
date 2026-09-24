import sqlite3
import uuid
import time
import logging
import os
from datetime import datetime, timezone

log_dir = "/root/trinity-fund/next-gen/hermes-event/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "hermes_shadow_engine.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"

def check_economic_calendar():
    try:
        logging.info("👟 Ciclu Hermes Event Engine început...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificăm dacă avem evenimente în calendarul economic
        cursor.execute("SELECT COUNT(*) FROM economic_calendar WHERE event_time >= ?", (now_str,))
        upcoming_events = cursor.fetchone()[0]
        
        conn.close()
        
        if upcoming_events == 0:
            status = "WAIT"
            reason = "Așteaptă integrarea sursei de date de consens (Forecast/Actual) în Calendarul Economic."
        else:
            status = "READY"
            reason = f"Sunt {upcoming_events} evenimente în așteptare. Motorul este gata să calculeze surpriza (Z-Score) la T+15m."
            
        logging.info(f"👟 Hermes Status: {status} | {reason}")
        
        # Salvare în Cutia Neagră
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        signal_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO signals (signal_id, timestamp, bot_name, strategy_version, direction, status, rejection_reason, available_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal_id, now_str, 'HERMES', 'v1.0_event', 'N/A', status, reason, now_str))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logging.error(f"❌ Eroare Hermes: {e}")

if __name__ == "__main__":
    logging.info("👟 HERMES Shadow Engine a pornit NON-STOP.")
    print("👟 HERMES Shadow Engine a pornit. Verifică calendarul economic la fiecare 15 minute.")
    while True:
        check_economic_calendar()
        time.sleep(900) # 15 minute (900 secunde)
