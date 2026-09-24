import sqlite3
import time
import logging
import os
from datetime import datetime, timezone

log_dir = "/root/trinity-fund/next-gen/shared/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "dispatcher.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"
LOT_SIZE_UNITS = 5000  # 0.05 loturi = 5000 unități cTrader

def dispatch_signals():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Căutăm semnale noi care nu au fost încă puse în coadă
        cursor.execute("""
            SELECT s.signal_id, s.bot_name, s.status
            FROM signals s
            LEFT JOIN executions e ON s.signal_id = e.signal_id
            LEFT JOIN order_queue oq ON s.signal_id = oq.signal_id
            WHERE s.status IN ('SHADOW_LONG', 'SHOCK_DETECTED')
            AND e.signal_id IS NULL
            AND oq.order_id IS NULL
            AND s.timestamp >= datetime('now', '-2 hour')
        """)
        signals = cursor.fetchall()
        
        for signal_id, bot_name, status in signals:
            logging.info(f"📥 Dispecer: Am primit semnal de la {bot_name}. Îl trimit la Coada de Așteptare.")
            cursor.execute("""
                INSERT INTO order_queue (signal_id, bot_name, volume, status)
                VALUES (?, ?, ?, 'PENDING')
            """, (signal_id, bot_name, LOT_SIZE_UNITS))
            
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Eroare dispecer: {e}")

if __name__ == "__main__":
    logging.info("🚀 DISPECER (live_executor) a pornit. Pune ordine în coadă.")
    while True:
        dispatch_signals()
        time.sleep(15) # Verifică la 15 secunde
