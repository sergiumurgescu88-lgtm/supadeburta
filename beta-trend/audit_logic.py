import os

print("\n=== 🧠 G4TRADE SYSTEM AUDIT - LOGICA STRATEGIEI ===")
files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'audit_logic.py']

keywords_to_check = {
    "Macro/Calendar": ["nfp", "cpi", "forexfactory", "news", "calendar", "lockdown"],
    "Whale/Volume": ["volume", "delta", "spike", "absorption", "liquidity", "whale"],
    "Tehnic/Structură": ["adx", "choch", "bos", "vwap", "atr", "structure"],
    "Consens/Decizie": ["consensus", "score", "evaluate_trade", "macro_score", "whale_score"]
}

for file in files:
    print(f"\n📄 Analiză: {file}")
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            
        for category, words in keywords_to_check.items():
            matches = [word for word in words if word in content]
            if matches:
                print(f"  ✅ {category}: Găsit ({', '.join(matches)})")
            else:
                print(f"  ⚠️ {category}: Lipsă sau denumit diferit")
    except Exception as e:
        print(f"  ❌ Eroare la citire: {e}")

print("\n🔒 NOTĂ: Acest script doar caută cuvinte cheie. Nu expune logica matematică sau API keys.")
