import sqlite3
import pandas as pd
import yfinance as yf
import logging
import os
import time
from datetime import datetime, timezone

log_dir = "/root/trinity-fund/next-gen/shared/data_pipeline/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "data_ingestion.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "/root/trinity-fund/next-gen/shared/black_box/context_db.sqlite"

def fetch_fred_and_proxies():
    """Descarcă TIPS și 10Y Yield folosind yfinance ca fallback sigur"""
    try:
        logging.info("📥 Descărcare date Macro (TIPS & 10Y Yield)...")
        print("   ⏳ Se preiau datele macro (poate dura 10-15 secunde)...")
        
        # Folosim yfinance pentru că este mult mai rapid și stabil decât requests către FRED
        # TIP = iShares TIPS Bond ETF (proxy excelent pentru TIPS 10Y)
        # ^TNX = CBOE 10-Year Treasury Yield
        tickers = ['TIP', '^TNX']
        data = yf.download(tickers, period="2y", progress=False)
        
        if data.empty:
            logging.warning("yfinance nu a returnat date macro.")
            print("   ❌ Nu s-au putut prelua datele macro.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        count_saved = 0
        
        # Iterăm prin date
        for date_idx in data.index:
            date_str = date_idx.strftime('%Y-%m-%d')
            available_at = date_idx.strftime('%Y-%m-%d 16:00:00')
            
            # Extragem valorile (gestionând cazurile unde un ticker lipsește într-o anumită zi)
            try:
                tip_close = float(data['Close']['TIP'].loc[date_idx]) if 'TIP' in data['Close'] else 0.0
                tnx_close = float(data['Close']['^TNX'].loc[date_idx]) if '^TNX' in data['Close'] else 0.0
            except (KeyError, TypeError):
                continue

            if tip_close > 0 or tnx_close > 0:
                cursor.execute("""
                    INSERT INTO macro_data (date, tips_10y, dxy_proxy, us10y_nominal, available_at)
                    VALUES (?, ?, 0.0, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET
                        tips_10y = excluded.tips_10y,
                        us10y_nominal = excluded.us10y_nominal,
                        available_at = excluded.available_at
                """, (date_str, tip_close, tnx_close, available_at))
                count_saved += 1
        
        conn.commit()
        conn.close()
        logging.info(f"✅ Date Macro salvate: {count_saved} înregistrări")
        print(f"   ✅ Macro (TIPS & 10Y): {count_saved} zile salvate cu succes.")
        
    except Exception as e:
        logging.error(f"Eroare Macro: {e}")
        print(f"   ❌ Eroare la preluarea datelor macro: {e}")

def fetch_yfinance_robust():
    """Descarcă date suplimentare individual pentru a evita erorile MultiIndex"""
    try:
        logging.info("📥 Descărcare date suplimentare (VIX, SPY, QQQ, BTC)...")
        tickers = {'^VIX': 'VIX', 'SPY': 'SPY', 'QQQ': 'QQQ', 'BTC-USD': 'BTC'}
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                date DATE, ticker TEXT, close_price REAL, available_at DATETIME,
                PRIMARY KEY (date, ticker)
            )
        """)
        
        count_saved = 0
        for ticker, name in tickers.items():
            try:
                # Descărcăm individual pentru fiecare
                df = yf.Ticker(ticker).history(period="1y")
                if not df.empty:
                    last_row = df.iloc[-1]
                    last_value = float(last_row['Close'])
                    last_date = last_row.name.strftime('%Y-%m-%d')
                    available_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    
                    cursor.execute("""
                        INSERT INTO market_data (date, ticker, close_price, available_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(date, ticker) DO UPDATE SET
                            close_price = excluded.close_price,
                            available_at = excluded.available_at
                    """, (last_date, name, last_value, available_at))
                    count_saved += 1
                    print(f"   ✅ {name}: {last_value:.2f} (Data: {last_date})")
                time.sleep(0.5) # Mică pauză pentru a nu fi blocați de yfinance
            except Exception as e:
                logging.warning(f"Eroare pentru {ticker}: {e}")
        
        conn.commit()
        conn.close()
        logging.info(f"✅ Date suplimentare salvate: {count_saved} tickere")
        
    except Exception as e:
        logging.error(f"Eroare YFinance robust: {e}")
        print(f"   ❌ Eroare YFinance: {e}")

if __name__ == "__main__":
    logging.info("🚀 Data Ingestion Engine (Ultra-Rezistent) pornit...")
    print("🧠 Începem hrănirea Creierului (Metodă Blindată)...\n")
    
    fetch_fred_and_proxies()
    print("")
    fetch_yfinance_robust()
    
    print("\n✅ Ingestie de date finalizată.")
