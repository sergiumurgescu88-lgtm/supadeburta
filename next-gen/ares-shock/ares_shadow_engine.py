import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
import uuid
import time
import logging
import os
from datetime import datetime, timezone

log_dir = "/root/trinity-fund/next-gen/ares-shock/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "ares_shadow_engine.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"

def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def run_ares_shadow_cycle():
    try:
        logging.info("⚔️ Ciclu Ares Shock Engine început...")
        
        # Preluare date M15 pentru ultimele 60 de zile
        data = yf.download("GC=F", period="60d", interval="15m", progress=False)
        if data.empty:
            logging.warning("⚠️ Date M15 lipsă.")
            return

        # Calcul ATR(M15) standard
        data['ATR_14'] = calculate_atr(data, 14)
        
        # ATR mediu pe ultimele 24h (96 de lumânări de 15 min)
        data['ATR_24h_avg'] = data['ATR_14'].rolling(window=96).mean()
        
        # Verificăm ultima lumânare completă (iloc[-2], pentru că -1 e cea curentă, incompletă)
        last_candle = data.iloc[-2]
        atr_avg = last_candle['ATR_24h_avg']
        candle_body = abs(last_candle['Close'] - last_candle['Open'])
        
        if pd.isna(atr_avg) or atr_avg == 0:
            logging.warning("⚠️ ATR invalid.")
            return

        # Condiția de Șoc: Corpul lumânării > 2.5 * ATR mediu pe 24h
        is_shock = candle_body > (2.5 * atr_avg)
        
        status = "WAIT"
        reason = f"Piață normală. Corp: {candle_body:.2f} vs Prag: {2.5 * atr_avg:.2f}"
        
        if is_shock:
            status = "SHOCK_DETECTED"
            reason = f"⚡ ȘOC DETECTAT! Corp ({candle_body:.2f}) > 2.5 * ATR ({2.5 * atr_avg:.2f})"
            
        logging.info(f"📊 ATR 24h: {atr_avg:.2f} | Status: {status}")
        
        # Salvare în Cutia Neagră
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        signal_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO signals (signal_id, timestamp, bot_name, strategy_version, direction, status, rejection_reason, available_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal_id, now_str, 'ARES', 'v1.0_shock', 'PENDING', status, reason, now_str))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logging.error(f"❌ Eroare Ares: {e}")

if __name__ == "__main__":
    logging.info("⚔️ ARES Shadow Engine a pornit NON-STOP.")
    print("⚔️ ARES Shadow Engine a pornit. Verifică piața la fiecare 15 minute.")
    while True:
        run_ares_shadow_cycle()
        time.sleep(900) # 15 minute (900 secunde)
