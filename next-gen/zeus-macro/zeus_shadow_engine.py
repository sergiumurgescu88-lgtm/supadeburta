import yfinance as yf
import pandas as pd
import sqlite3
import uuid
import time
import logging
import os
from datetime import datetime, timezone

log_dir = "/root/trinity-fund/next-gen/zeus-macro/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "zeus_shadow_engine.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"

def run_zeus_shadow_cycle():
    try:
        logging.info("🔄 Ciclu de verificare Zeus (Mod Local Rapid) început...")
        
        # 1. CITIRE LOCALĂ INSTANTANEE din Cutia Neagră
        conn = sqlite3.connect(DB_PATH)
        # Luăm ultimele 300 de zile de date macro disponibile
        query = """
            SELECT date, tips_10y, dxy_proxy, us10y_nominal 
            FROM macro_data 
            WHERE tips_10y > 0 OR us10y_nominal > 0 
            ORDER BY date ASC 
            LIMIT 300;
        """
        macro_df = pd.read_sql_query(query, conn)
        conn.close()
        
        if macro_df.empty or len(macro_df) < 50:
            logging.warning("⚠️ Date macro insuficiente în Cutia Neagră. Se așteaptă.")
            return

        # 2. Descărcare DOAR a prețului Aurului (foarte rapid, ~1 secundă)
        gold_hist = yf.Ticker("GC=F").history(period="1y")
        if gold_hist.empty:
            logging.warning("⚠️ Nu s-au putut descărca datele pentru Aur.")
            return

        # Aliniem datele: folosim indexul de date din macro_df ca bază
        macro_df['date'] = pd.to_datetime(macro_df['date']).dt.date
        gold_hist.index = pd.to_datetime(gold_hist.index).date
        
        # Combinăm datele (Inner Join pe date)
        df = macro_df.set_index('date').join(gold_hist['Close'], how='inner').dropna()
        
        if len(df) < 50:
            logging.warning("⚠️ Nu există suficiente date comune între Macro și Aur.")
            return

        # 3. Calcule Matematice (Creierul)
        # Z-Score pe 20 de zile
        df['DXY_Z'] = (df['dxy_proxy'] - df['dxy_proxy'].rolling(20).mean()) / df['dxy_proxy'].rolling(20).std()
        df['TNX_Z'] = (df['us10y_nominal'] - df['us10y_nominal'].rolling(20).mean()) / df['us10y_nominal'].rolling(20).std()
        
        # Scor Macro: Aurul crește când DXY și Yields scad
        df['Macro_Score'] = (-df['DXY_Z'].fillna(0)) + (-df['TNX_Z'].fillna(0))
        
        # Corelație pe 50 de zile (250 e prea mult pentru 300 de rânduri, 50 e mai stabil pe acest subset)
        df['Correlation'] = df['Close'].rolling(50).corr(df['us10y_nominal'])
        
        # Trigger Tehnic (EMA 50 și EMA 20)
        df['EMA50'] = df['Close'].rolling(50).mean()
        df['EMA20'] = df['Close'].rolling(20).mean()

        # Luăm ultima zi completă
        last = df.iloc[-1]
        current_price = float(last['Close'])
        macro_score = float(last['Macro_Score'])
        correlation = float(last['Correlation']) if not pd.isna(last['Correlation']) else 0.0

        # 4. Logica de Decizie
        if correlation > -0.2:
            status = "STANDBY"
            reason = f"Corelație macro invalidă ({correlation:.2f} > -0.2)"
        elif macro_score < 1.0:
            status = "WAIT"
            reason = f"Scor macro insuficient ({macro_score:.2f} < 1.0)"
        elif current_price < float(last['EMA50']):
            status = "WAIT"
            reason = "Preț sub EMA50 (Trend major bearish)"
        elif current_price > float(last['EMA20']):
            status = "WAIT"
            reason = "Așteptăm pullback la EMA20"
        else:
            status = "SHADOW_LONG"
            reason = "Macro + Tehnic aliniate perfect"

        logging.info(f"📊 Scor: {macro_score:.2f} | Corelație: {correlation:.2f} | Decizie: {status}")

        # 5. SALVARE ÎN CUTIA NEAGRĂ
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        signal_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT INTO signals (signal_id, timestamp, bot_name, strategy_version, direction, status, rejection_reason, available_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal_id, now_str, 'ZEUS', 'v1.1_local_fast', 'LONG', status, reason, now_str))

        cursor.execute("""
            INSERT INTO snapshots (signal_id, price_usd, atr_usd, adx_value, spread_usd, session, macro_score, total_open_risk_usd, minutes_to_news)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal_id, current_price, 0.0, 0.0, 0.0, 'AUTO', macro_score, 0.0, 0.0))

        conn.commit()
        conn.close()
        logging.info(f"✅ Decizie salvată în Cutia Neagră: {status} (Citire Locală)")

    except Exception as e:
        logging.error(f"❌ Eroare în ciclul Zeus: {e}")

# 6. Bucla Non-Stop
if __name__ == "__main__":
    logging.info("🚀 ZEUS Shadow Engine (Local Fast) a pornit NON-STOP.")
    print("🚀 ZEUS rulează în mod ULTRA-RAPID (Citire Locală). Verifică la fiecare 4 ore.")
    
    # Rulăm o dată imediat pentru test
    run_zeus_shadow_cycle()
    
    while True:
        time.sleep(14400) # 4 ore
        run_zeus_shadow_cycle()
