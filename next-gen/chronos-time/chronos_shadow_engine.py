import sqlite3
import uuid
import time
import logging
import os
from datetime import datetime, timezone, timedelta

log_dir = "/root/trinity-fund/next-gen/chronos-time/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "chronos_shadow_engine.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"

def check_time_windows():
    try:
        now = datetime.now(timezone.utc)
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        future_str = (now + timedelta(minutes=45)).strftime('%Y-%m-%d %H:%M:%S')
        current_time_minutes = now.hour * 60 + now.minute

        dynamic_veto = False
        dynamic_reason = ""
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT event_name, event_time FROM economic_calendar 
                WHERE impact = 'HIGH' AND event_time >= ? AND event_time <= ?
                ORDER BY event_time ASC
                LIMIT 1
            """, (now_str, future_str))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                dynamic_veto = True
                event_name, event_time = row
                try:
                    dt = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')
                    time_str = dt.strftime('%H:%M UTC')
                except:
                    time_str = event_time
                dynamic_reason = f"⚠️ Eveniment economic major iminent: {event_name} la {time_str}."
        except Exception as e:
            logging.error(f"❌ Eroare la citirea calendarului dinamic: {e}")

        windows = {
            "LBMA_AM_FIXING": (555, 585),
            "LBMA_PM_FIXING": (885, 915),
            "ROLLOVER_RISK": (1260, 1320)
        }

        active_window = None
        for name, (start, end) in windows.items():
            if start <= current_time_minutes <= end:
                active_window = name
                break

        status = "CLEAR"
        reason = "Piață normală, fără ferestre de manipulare."

        if dynamic_veto:
            status = "VETO_WINDOW"
            reason = dynamic_reason
        elif active_window:
            status = "VETO_WINDOW"
            reason = f"⚠️ Fereastră critică activă: {active_window}. Spread-uri toxice, lichiditate artificială."

        logging.info(f"⏳ Chronos Status: {status} | {reason}")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        signal_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO signals (signal_id, timestamp, bot_name, strategy_version, direction, status, rejection_reason, available_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal_id, now_str, 'CHRONOS', 'v1.1_dynamic_time', 'N/A', status, reason, now_str))

        conn.commit()
        conn.close()

    except Exception as e:
        logging.error(f"❌ Eroare Chronos: {e}")

if __name__ == "__main__":
    logging.info("⏳ CHRONOS Shadow Engine a pornit NON-STOP.")
    print("⏳ CHRONOS Shadow Engine a pornit. Verifică ora și calendarul la fiecare 5 minute.")
    while True:
        check_time_windows()
        time.sleep(300)
