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
CHRONOS_LOG_PATH = "/root/trinity-fund/next-gen/chronos-time/logs/chronos_shadow_engine.log"

def is_chronos_veto_active():
    """Verifică dacă Chronos a activat fereastra de VETO"""
    try:
        with open(CHRONOS_LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                # Citim ultimele 2 linii pentru a prinde cel mai recent status
                last_lines = "".join(lines[-2:])
                if "VETO_WINDOW" in last_lines:
                    return True
    except Exception:
        pass # Dacă logul nu există sau e blocat, presupunem că e sigur (fallback)
    return False

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

        # VERIFICARE DE SIGURANȚĂ: Este Chronos în VETO?
        veto_active = is_chronos_veto_active()

        for signal_id, bot_name, status in signals:
            if veto_active:
                logging.warning(f"🚫 VETO ACTIV: Semnal de la {bot_name} (ID: {signal_id}) IGNORAT. Chronos a detectat fereastră critică!")
                # Marcăm semnalul ca ignorat ca să nu-l tot citească la următorul ciclu
                cursor.execute("UPDATE signals SET status = 'IGNORED_VETO' WHERE signal_id = ?", (signal_id,))
                continue

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
