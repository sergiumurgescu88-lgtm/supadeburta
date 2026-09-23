import datetime

# Lista de evenimente de înaltă impact (Exemplu: se poate încărca dintr-un JSON extern sau API ForexFactory)
HIGH_IMPACT_EVENTS = [
    {"date": "2026-09-25", "time": "15:30", "event": "NFP"}, # Exemplu
    {"date": "2026-10-10", "time": "15:30", "event": "CPI"}
]

def is_safe_to_trade(minutes_buffer=30):
    """
    Verifică dacă suntem într-o fereastră de timp sigură, departe de știri majore.
    Returnează True dacă e sigur, False dacă activează 'Panic Button'.
    """
    now = datetime.datetime.utcnow()
    
    for event in HIGH_IMPACT_EVENTS:
        event_time_str = f"{event['date']} {event['time']}"
        event_dt = datetime.datetime.strptime(event_time_str, "%Y-%m-%d %H:%M")
        
        # Calculăm diferența în minute
        diff_minutes = abs((now - event_dt).total_seconds() / 60)
        
        if diff_minutes <= minutes_buffer:
            print(f"⚠️ MACRO FILTER: PANIC BUTTON ACTIVAT! Știre '{event['event']}' în {int(diff_minutes)} minute.")
            return False
            
    return True

if __name__ == "__main__":
    print("Test Macro Filter:", "SAFE" if is_safe_to_trade() else "LOCKDOWN")
