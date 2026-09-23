from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import json
import logging
from datetime import datetime
import os

app = FastAPI()

# Configurare
FINNHUB_SECRET = "d6qhhg9r01qhcrmk7on0"
LOG_FILE = "/root/ctrader-g4trade-bot/news-site/webhook_log.json"

# Configurare logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_news_to_file(news_data):
    """Această funcție rulează în background, DUPĂ ce am răspuns lui Finnhub"""
    try:
        # Citim datele existente (dacă există)
        existing_data = []
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r") as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
        
        # Adăugăm noua știre cu timestamp
        new_entry = {
            "received_at": datetime.now().isoformat(),
            "finnhub_data": news_data
        }
        existing_data.append(new_entry)
        
        # Păstrăm doar ultimele 100 de știri ca să nu umplem discul
        existing_data = existing_data[-100:]
        
        with open(LOG_FILE, "w") as f:
            json.dump(existing_data, f, indent=2)
            
        logging.info(f"✅ Știre salvată cu succes. Total în log: {len(existing_data)}")
    except Exception as e:
        logging.error(f"❌ Eroare la salvarea știrii: {e}")

@app.post("/webhook")
async def finnhub_webhook(request: Request, background_tasks: BackgroundTasks):
    # 1. Verificăm secretul IMEDIAT
    secret = request.headers.get("x-finnhub-secret")
    if secret != FINNHUB_SECRET:
        logging.warning(f"⚠️ Tentativă de acces cu secret invalid: {secret}")
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    # 2. Citim datele (FastAPI le parsează rapid)
    try:
        news_data = await request.json()
    except Exception as e:
        logging.error(f"❌ Date JSON invalide: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # 3. Programăm salvarea în BACKGROUND (se va executa DUPĂ ce returnăm 200 OK)
    background_tasks.add_task(save_news_to_file, news_data)
    
    # 4. Returnăm 200 OK IMEDIAT (Finnhub este mulțumit, nu va da timeout)
    logging.info("📥 Webhook primit și procesat în background.")
    return {"status": "success", "message": "Acknowledged"}

@app.get("/health")
async def health_check():
    return {"status": "alive"}
