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
        
        # Preluare date M15 pentru ultimele 60 de zile (Folosim Ticker.history pentru a evita MultiIndex)
        ticker = yf.Ticker("GC=F")
        data = ticker.history(period="60d", interval="15m")
        if data.empty:
            logging.warning("⚠️ Date M15 lipsă.")
            return
        
        # Asigurăm că indexul este sortat corect
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()

        # Calcul ATR(M15) standard
        data['ATR_14'] = calculate_atr(data, 14)
        
        # ATR mediu pe ultimele 24h (96 de lumânări de 15 min)
        data['ATR_24h_avg'] = data['ATR_14'].rolling(window=96).mean()
        
        # Verificăm ultima lumânare completă (iloc[-2], pentru că -1 e cea curentă, incompletă)
        # Forțăm float() pentru a evita erorile de Series ambigue din yfinance MultiIndex
        try:
            last_close = float(data['Close'].iloc[-2])
            last_open = float(data['Open'].iloc[-2])
            atr_avg = float(data['ATR_24h_avg'].iloc[-2])
        except Exception as e:
            logging.warning(f"⚠️ Eroare la extragerea ultimei lumânări: {e}")
            logging.warning(f"📊 Date disponibile: {len(data)} rânduri. Coloane: {list(data.columns)[:5]}")
            return
        
        candle_body = abs(last_close - last_open)
        
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
        time.sleep(30) # 15 minute (900 secunde)
