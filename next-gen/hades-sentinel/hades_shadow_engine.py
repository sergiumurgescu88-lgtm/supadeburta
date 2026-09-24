import sqlite3
import uuid
import time
import logging
import os
import pandas as pd
from datetime import datetime, timezone

log_dir = "/root/trinity-fund/next-gen/hades-sentinel/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "hades_shadow_engine.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"

def analyze_cot_positioning():
    try:
        logging.info("⚖️ Ciclu Hades Positioning Engine început...")
        
        conn = sqlite3.connect(DB_PATH)
        # Citim toate datele COT disponibile pentru a calcula percentila
        df = pd.read_sql_query("SELECT report_date, gold_managed_net FROM cot_data ORDER BY report_date ASC", conn)
        conn.close()
        
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        if df.empty or len(df) < 52: # Avem nevoie de minim 1 an de date pentru o percentilă relevantă
            status = "WAIT"
            reason = "Date COT insuficiente în Cutia Neagră (minim 52 săptămâni necesare)."
            logging.info(f"⚖️ Hades Status: {status} | {reason}")
        else:
            # Luăm ultima valoare disponibilă
            latest_net_position = df['gold_managed_net'].iloc[-1]
            
            # Calculăm percentila poziției nete pe tot istoricul disponibil
            percentile = (df['gold_managed_net'].rank(pct=True).iloc[-1]) * 100
            
            status = "CLEAR"
            reason = f"Poziționare normală. Percentilă Hedge Funds: {percentile:.1f}%"
            
            # Reguli de VETO extreme
            if percentile >= 90.0:
                status = "VETO_MACRO_LONG"
                reason = f"⚠️ Trend Long epuizat! Hedge Funds sunt la percentila {percentile:.1f}% (peste 90%). Risc maxim de reversare."
            elif percentile <= 10.0:
                status = "VETO_MACRO_SHORT"
                reason = f"⚠️ Trend Short epuizat! Hedge Funds sunt la percentila {percentile:.1f}% (sub 10%). Risc maxim de reversare."
                
            logging.info(f"⚖️ Hades Status: {status} | {reason}")
        
        # Salvare în Cutia Neagră
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        signal_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO signals (signal_id, timestamp, bot_name, strategy_version, direction, status, rejection_reason, available_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal_id, now_str, 'HADES', 'v1.0_cot', 'N/A', status, reason, now_str))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logging.error(f"❌ Eroare Hades: {e}")

if __name__ == "__main__":
    logging.info("⚖️ HADES Shadow Engine a pornit NON-STOP.")
    print("⚖️ HADES Shadow Engine a pornit. Verifică poziționarea COT o dată pe zi.")
    while True:
        analyze_cot_positioning()
        time.sleep(86400) # 24 de ore (86400 secunde), deoarece COT se actualizează săptămânal
