import yfinance as yf
import sqlite3
from datetime import datetime, timezone
import logging
import os

log_dir = "/root/trinity-fund/next-gen/shared/data_pipeline"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, "data_pipeline.log"), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"

def fetch_and_save_macro_data():
    try:
        logging.info("🔄 Preluare date macro (Metodă robustă yf.Ticker)...")
        # Folosim yf.Ticker().history() care returnează un DataFrame simplu, evitând erorile de MultiIndex
        dxy_hist = yf.Ticker("DX-Y.NYB").history(period="5d")
        tnx_hist = yf.Ticker("^TNX").history(period="5d")
        
        if dxy_hist.empty or tnx_hist.empty:
            logging.warning("⚠️ Date lipsă de la Yahoo Finance.")
            return

        # Extragem ultima valoare de închidere (Close) ca float simplu
        dxy_value = float(dxy_hist['Close'].iloc[-1])
        tnx_value = float(tnx_hist['Close'].iloc[-1])
        
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        available_at_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO macro_data (date, tips_10y, dxy_proxy, us10y_nominal, available_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                tips_10y = excluded.tips_10y, dxy_proxy = excluded.dxy_proxy, 
                us10y_nominal = excluded.us10y_nominal, available_at = excluded.available_at
        """, (today_str, 0.0, dxy_value, tnx_value, available_at_str)) 
        conn.commit()
        conn.close()
        logging.info(f"✅ Date salvate: DXY={dxy_value:.2f}, 10Y={tnx_value:.2f}")
        print(f"✅ SUCCES: DXY={dxy_value:.2f}, 10Y Yield={tnx_value:.2f}%")
    except Exception as e:
        logging.error(f"❌ Eroare: {e}")
        print(f"❌ Eroare: {e}")

if __name__ == "__main__":
    fetch_and_save_macro_data()
