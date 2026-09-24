import sqlite3
import uuid
import time
import logging
import os
from datetime import datetime, timezone

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
        hour = now.hour
        minute = now.minute
        current_time_minutes = hour * 60 + minute
        
        # Definiția ferestrelor critice (în minute de la miezul nopții UTC)
        # LBMA AM Fixing: 09:15 - 09:45 UTC (vara)
        # LBMA PM Fixing: 14:45 - 15:15 UTC (vara)
        # Rollover Bancar: 21:00 - 22:00 UTC (vara)
        # Notă: Iarna orele se shiftă cu +1 oră, dar pentru Shadow Mode folosim standardul de vară.
        
        windows = {
            "LBMA_AM_FIXING": (555, 585),   # 09:15 - 09:45
            "LBMA_PM_FIXING": (885, 915),   # 14:45 - 15:15
            "ROLLOVER_RISK": (1260, 1320)   # 21:00 - 22:00
        }
        
        active_window = None
        for name, (start, end) in windows.items():
            if start <= current_time_minutes <= end:
                active_window = name
                break
                
        status = "CLEAR"
        reason = "Piață normală, fără ferestre de manipulare."
        
        if active_window:
            status = "VETO_WINDOW"
            reason = f"⚠️ Fereastră critică activă: {active_window}. Spread-uri toxice, lichiditate artificială."
            
        logging.info(f"⏳ Chronos Status: {status} | {reason}")
        
        # Salvare în Cutia Neagră
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        signal_id = str(uuid.uuid4())
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO signals (signal_id, timestamp, bot_name, strategy_version, direction, status, rejection_reason, available_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal_id, now_str, 'CHRONOS', 'v1.0_time', 'N/A', status, reason, now_str))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logging.error(f"❌ Eroare Chronos: {e}")

if __name__ == "__main__":
    logging.info("⏳ CHRONOS Shadow Engine a pornit NON-STOP.")
    print("⏳ CHRONOS Shadow Engine a pornit. Verifică ora la fiecare 5 minute.")
    while True:
        check_time_windows()
        time.sleep(300) # 5 minute (300 secunde)
