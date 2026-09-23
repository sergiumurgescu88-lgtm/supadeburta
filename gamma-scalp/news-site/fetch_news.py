import requests
import json
from datetime import datetime

API_KEY = "dap7139r01qj9mnslupgdap7139r01qj9mnsluq0"
URL = f"https://finnhub.io/api/v1/news?category=general&token={API_KEY}"

try:
    response = requests.get(URL, timeout=10)
    data = response.json()
    
    if isinstance(data, dict) and "error" in data:
        print(f"❌ Eroare API: {data['error']}")
        data = [] 

    # FILTRU STRICT: Doar știri relevante pentru Aur/XAUUSD
    gold_keywords = [
        "gold", "xau", "xauusd", "aur",
        "fed", "federal reserve", "powell",
        "inflation", "cpi", "ppi",
        "interest rate", "rate hike", "rate cut",
        "dollar", "usd", "dxy",
        "treasury", "yield", "bond",
        "safe haven", "precious metal"
    ]
    
    filtered_news = []
    
    if isinstance(data, list):
        for item in data[:100]:  # Verificăm mai multe articole
            headline = item.get("headline", "").lower()
            summary = item.get("summary", "").lower()
            text = headline + " " + summary
            
            # Verificăm dacă se potrivește cu cel puțin un cuvânt cheie
            if any(kw in text for kw in gold_keywords):
                filtered_news.append({
                    "headline": item.get("headline"),
                    "source": item.get("source"),
                    "url": item.get("url"),
                    "datetime": datetime.fromtimestamp(item.get("datetime")).strftime("%d.%m.%Y %H:%M"),
                    "summary": item.get("summary", "")[:200]  # Primele 200 caractere
                })
        
        # Sortăm după dată (cele mai noi primele)
        filtered_news.sort(key=lambda x: x['datetime'], reverse=True)
        
        # Păstrăm doar primele 15 cele mai relevante
        filtered_news = filtered_news[:15]

    with open("/root/ctrader-g4trade-bot/news-site/news_data.json", "w", encoding="utf-8") as f:
        json.dump(filtered_news, f, indent=2, ensure_ascii=False)
    print(f"✅ Știri Aur actualizate! ({len(filtered_news)} articole relevante)")
except Exception as e:
    print(f"❌ Eroare: {e}")
