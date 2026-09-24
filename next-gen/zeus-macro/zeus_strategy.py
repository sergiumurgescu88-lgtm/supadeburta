import yfinance as yf
import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime

log_dir = "/root/trinity-fund/next-gen/zeus-macro/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, "zeus_shadow.log"), level=logging.INFO, format='%(asctime)s - %(message)s')

def calculate_zeus_signal():
    print("🧠 ZEUS (Macro Swing) - Calculare Strategie Shadow...")
    
    try:
        # 1. Preluare date istorice aliniate automat pe aceleași zile (1 an)
        print("⏳ Descărcare date istorice (Gold, DXY, 10Y)...")
        data = yf.download(["GC=F", "DX-Y.NYB", "^TNX"], period="1y", progress=False)
        
        if data.empty:
            print("❌ Nu s-au putut descărca datele istorice de la Yahoo Finance.")
            return

        # Extragem doar coloanele 'Close' (yf.download returnează MultiIndex)
        gold = data['Close']['GC=F']
        dxy = data['Close']['DX-Y.NYB']
        tnx = data['Close']['^TNX']
        
        # Creăm un DataFrame curat și eliminăm rândurile cu NaN (zile de sărbătoare diferite)
        df = pd.DataFrame({'Gold': gold, 'DXY': dxy, 'TNX': tnx}).dropna()
        
        # PROTECȚIE: Dacă nu există date comune valide, oprim execuția elegant
        if df.empty:
            print("⚠️ Nu există date comune valide între Gold, DXY și 10Y Yield în acest interval.")
            return

        # 2. Calcul Z-Score pe 20 de zile
        df['DXY_Z'] = (df['DXY'] - df['DXY'].rolling(20).mean()) / df['DXY'].rolling(20).std()
        df['TNX_Z'] = (df['TNX'] - df['TNX'].rolling(20).mean()) / df['TNX'].rolling(20).std()
        
        # Scorul Macro: Aurul crește când DXY și Yields scad (inversăm semnul Z)
        df['Macro_Score'] = (-df['DXY_Z']) + (-df['TNX_Z'])

        # 3. Filtrul de Regim (Corelație pe 250 zile)
        df['Correlation'] = df['Gold'].rolling(250).corr(df['TNX'])
        
        # 4. Trigger Tehnic (EMA 50 și EMA 20)
        df['EMA50'] = df['Gold'].rolling(50).mean()
        df['EMA20'] = df['Gold'].rolling(20).mean()

        # Luăm ultima zi completă
        last_row = df.iloc[-1]
        
        print(f"\n📊 Status Macro Actual:")
        print(f"   - Scor Macro: {last_row['Macro_Score']:.2f} (Peste 1.0 = Bullish pentru Aur)")
        print(f"   - Corelație Gold/TNX (250z): {last_row['Correlation']:.2f} (Trebuie să fie < -0.2)")
        print(f"   - Preț Gold: {last_row['Gold']:.2f} | EMA50: {last_row['EMA50']:.2f} | EMA20: {last_row['EMA20']:.2f}")
        
        # 5. Logica de Decizie
        if pd.isna(last_row['Correlation']) or last_row['Correlation'] > -0.2:
            signal = "STANDBY (Regim macro rupt / Corelație invalidă)"
        elif last_row['Macro_Score'] < 1.0:
            signal = "WAIT (Scor macro insuficient)"
        elif last_row['Gold'] < last_row['EMA50']:
            signal = "WAIT (Preț sub trendul major EMA50)"
        elif last_row['Gold'] > last_row['EMA20']:
            signal = "WAIT (Așteptăm pullback la EMA20)"
        else:
            signal = "🚀 SHADOW LONG SIGNAL (Macro + Tehnic aliniate perfect)"

        print(f"\n🎯 DECIZIE ZEUS: {signal}")
        logging.info(f"Scor: {last_row['Macro_Score']:.2f} | Corelație: {last_row['Correlation']:.2f} | Semnal: {signal}")
        
    except Exception as e:
        print(f"❌ Eroare critică în calculul strategiei: {e}")
        logging.error(f"Eroare critică: {e}")

if __name__ == "__main__":
    calculate_zeus_signal()
