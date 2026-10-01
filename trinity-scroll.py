#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║      TRINITY FUND - LIVE SCROLL MONITOR (Zero-Flicker)       ║
║    Afișează DOAR liniile noi, lin, pe măsură ce apar.        ║
╚═══════════════════════════════════════════════════════════════╝
"""
import os
import time
import sys
from datetime import datetime

# Coduri de culori ANSI
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    WHITE = '\033[37m'

    # Culori Bots
    ALPHA = '\033[94m'    # Albastru
    BETA = '\033[92m'     # Verde
    GAMMA = '\033[93m'    # Galben
    SERGIU = '\033[95m'   # Magenta
    EPSILON = '\033[96m'  # Cyan

    # Culori Mesaje
    RED = '\033[91m'      # Eroare / Deconectat
    GREEN = '\033[92m'    # Succes
    YELLOW = '\033[93m'   # Warning / Spread

BOTS = {
    'ALPHA':   {'color': C.ALPHA,   'icon': '🎯', 'file': '/root/.pm2/logs/alpha-sniper-engine-error.log'},
    'BETA':    {'color': C.BETA,    'icon': '📈', 'file': '/root/.pm2/logs/beta-trend-engine-error.log'},
    'GAMMA':   {'color': C.GAMMA,   'icon': '⚡', 'file': '/root/.pm2/logs/gamma-scalp-engine-error.log'},
    'SERGIU':  {'color': C.SERGIU,  'icon': '🏆', 'file': '/root/.pm2/logs/sergiu-strategy-engine-error.log'},
    'EPSILON': {'color': C.EPSILON, 'icon': '💎', 'file': '/root/.pm2/logs/epsilon-strategy-engine-error.log'}
}

# LA PORNIRE: Sărim la sfârșitul fișierului (ca tail -f)
file_positions = {}
for name, config in BOTS.items():
    if os.path.exists(config['file']):
        file_positions[name] = os.path.getsize(config['file'])
    else:
        file_positions[name] = 0

def format_line(line, bot_name, config):
    line = line.strip()
    if not line:
        return ""
    
    # Împărțim linia: "2026-09-29 09:35:52,290 - INFO - 📥 Istoric..."
    parts = line.split(' - ', 2)
    if len(parts) >= 3:
        ts, level, msg = parts[0], parts[1], parts[2]
    else:
        ts, level, msg = "Unknown", "INFO", line

    # Logică inteligentă de colorare a mesajului
    msg_color = config['color']
    if '❌' in msg or 'ERROR' in msg or 'Deconectat' in msg or 'REJECTED' in msg:
        msg_color = C.RED
    elif '✅' in msg or '🟢' in msg or 'SUCCES' in msg or 'ONLINE' in msg:
        msg_color = C.GREEN
    elif '⚠️' in msg or 'WARNING' in msg or 'Spread prea mare' in msg:
        msg_color = C.YELLOW
    elif '📥' in msg or 'Istoric' in msg:
        msg_color = C.WHITE # Alb pentru istoric, ca să fie curat

    # Formatare finală aliniată perfect
    return f"{config['icon']} {bot_name:<8} {C.GRAY}│{C.RESET} {C.WHITE}{ts:<23}{C.RESET} {C.GRAY}│{C.RESET} {msg_color}{level} - {msg}{C.RESET}"

def main():
    # Curățăm ecranul DOAR la început
    os.system('clear')
    
    print(f"{C.BOLD}{C.GRAY}{'═' * 85}")
    print(f"  🏛️  TRINITY FUND - LIVE SCROLL MONITOR")
    print(f"  ⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  │  ● LIVE  │  Poll: 2s (Zero CPU)")
    print(f"{'═' * 85}{C.RESET}")
    print(f"{C.GRAY}Aștept evenimente noi de la boți... (Apasă Ctrl+C pentru oprire){C.RESET}\n")
    
    try:
        while True:
            for bot_name, config in BOTS.items():
                filepath = config['file']
                
                # Dacă fișierul nu există încă, sărim peste
                if not os.path.exists(filepath):
                    continue
                
                current_size = os.path.getsize(filepath)
                last_size = file_positions[bot_name]
                
                # Dacă fișierul a crescut, înseamnă că sunt linii noi!
                if current_size > last_size:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_size) # Mergem direct la ultimul octet citit
                        new_lines = f.readlines()
                        
                        for line in new_lines:
                            formatted = format_line(line, bot_name, config)
                            if formatted:
                                print(formatted)
                                
                        # Actualizăm poziția pentru data viitoare
                        file_positions[bot_name] = current_size
            
            # Așteptăm 2 secunde. Este suficient de rapid pentru a fi "live", 
            # dar folosește 0.0% CPU deoarece doar verificăm dimensiunea fișierului.
            time.sleep(2)
            
    except KeyboardInterrupt:
        print(f"\n\n{C.GREEN}🛑 Monitor oprit. Sistemul continuă să ruleze în fundal.{C.RESET}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
