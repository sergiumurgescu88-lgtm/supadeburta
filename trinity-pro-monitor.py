#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║    TRINITY FUND - TV PROMPTER v2.9 (Final with Scroll)        ║
║    No Flicker | 1 Line/Sec | Scroll UP/DOWN | G=Live          
╚═══════════════════════════════════════════════════════════════╝
"""
import os, time, sys, re, curses, json, urllib.request
from datetime import datetime
from collections import deque

BOTS = {
    'ALPHA':   {'icon': '🎯', 'file': '/root/.pm2/logs/alpha-sniper-engine-error.log', 'color': 8},
    'BETA':    {'icon': '📈', 'file': '/root/.pm2/logs/beta-trend-engine-error.log', 'color': 9},
    'GAMMA':   {'icon': '⚡', 'file': '/root/.pm2/logs/gamma-scalp-engine-error.log', 'color': 10},
    'SERGIU':  {'icon': '👑', 'file': '/root/.pm2/logs/sergiu-strategy-engine-error.log', 'color': 11},
    'EPSILON': {'icon': '💎', 'file': '/root/.pm2/logs/epsilon-strategy-engine-error.log', 'color': 12}
}
API_URL = 'http://127.0.0.1:5100/api/trading/status'

class BotState:
    def __init__(self, name, config):
        self.name = name; self.config = config; self.status = 'OFFLINE'; self.log_count = 0
    def update(self, line):
        self.log_count += 1
        if any(x in line for x in ['ONLINE', ' SNIPER ONLINE']): self.status = 'ONLINE'
        elif 'Deconectat' in line: self.status = 'DISCONNECTED'
        elif any(x in line for x in ['Așteptăm', 'Istoric', 'Whale']): self.status = 'SCANNING'

class Metrics:
    def __init__(self):
        self.start_time = datetime.now(); self.total_logs = 0; self.live_equity = 129710.60
        self.xauusd_price = 4150.0
    def fetch_live_data(self):
        try:
            req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode())
                if 'metrics' in data: self.live_equity = 129710.60 + data['metrics'].get('netProfit', 0)
                if 'current_price' in data: self.xauusd_price = data['current_price']
        except: pass
    def update_from_log(self, line): self.total_logs += 1
    @property
    def uptime(self): return datetime.now() - self.start_time

def get_system_metrics():
    try:
        with open('/proc/loadavg', 'r') as f: load = float(f.read().split()[0])
        with open('/proc/meminfo', 'r') as f:
            content = f.read()
            mem_total = int(re.search(r'MemTotal:\s+(\d+)', content).group(1))
            mem_free = int(re.search(r'MemFree:\s+(\d+)', content).group(1))
            mem_used = mem_total - mem_free
            mem_percent = (mem_used / mem_total) * 100
        return {'load': load, 'mem_percent': mem_percent, 'mem_used_mb': mem_used // 1024, 'mem_total_mb': mem_total // 1024}
    except: return {'load': 0, 'mem_percent': 0, 'mem_used_mb': 0, 'mem_total_mb': 0}

def safe_addstr(stdscr, y, x, text, attr=0):
    try:
        height, width = stdscr.getmaxyx()
        if 0 <= y < height and 0 <= x < width:
            max_len = width - x - 1
            if len(text) > max_len: text = text[:max_len-3] + "..."
            stdscr.addstr(y, x, text, attr)
    except: pass

def main(stdscr):
    curses.start_color(); curses.use_default_colors(); curses.curs_set(0)
    stdscr.nodelay(1); stdscr.keypad(True) # Activare taste speciale (Săgeți)
    
    for i in range(1, 14): curses.init_pair(i, i, -1)
    
    bot_states = {name: BotState(name, config) for name, config in BOTS.items()}
    metrics = Metrics()
    file_positions = {name: os.path.getsize(config['file']) if os.path.exists(config['file']) else 0 for name, config in BOTS.items()}
    
    pending_logs = deque()
    displayed_logs = []
    
    # SCROLL STATE
    scroll_offset = 0  # 0 = Live (jos), >0 = Derulat în sus
    
    last_refresh = time.time()
    last_api_fetch = time.time()
    last_line_time = time.time()
    last_clock_update = time.time()
    
    LINE_DELAY = 1.0  # 1 secundă per linie (Efect TV)
    
    while True:
        key = stdscr.getch()
        
        # --- CONTROALE SCROLL ---
        if key == curses.KEY_UP:
            scroll_offset += 5  # Urcă 5 linii
        elif key == curses.KEY_DOWN:
            scroll_offset = max(0, scroll_offset - 5)  # Coboară 5 linii
        elif key == ord('g') or key == ord('G'):
            scroll_offset = 0  # Salt direct la LIVE
        elif key == ord('q') or key == ord('Q'):
            break
            
        current_time = time.time()
        
        # 1. Citire fișiere
        if current_time - last_refresh >= 0.5:
            last_refresh = current_time
            for bot_name, config in BOTS.items():
                filepath = config['file']
                if not os.path.exists(filepath): continue
                current_size = os.path.getsize(filepath)
                last_size = file_positions[bot_name]
                
                if current_size > last_size:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_size)
                        for line in f.readlines():
                            line = line.strip()
                            if line:
                                bot_states[bot_name].update(line)
                                metrics.update_from_log(line)
                                pending_logs.append({
                                    'time': datetime.now().strftime('%H:%M:%S'),
                                    'bot': bot_name, 'icon': config['icon'],
                                    'line': line, 'color': config['color']
                                })
                                if len(pending_logs) > 2000: pending_logs.popleft()
                    file_positions[bot_name] = current_size
        
        # 2. API Fetch
        if current_time - last_api_fetch >= 10.0:
            last_api_fetch = current_time; metrics.fetch_live_data()
        
        # 3. Logică TV: Scoate 1 linie pe secundă din coadă
        needs_redraw = False
        if current_time - last_line_time >= LINE_DELAY:
            if pending_logs:
                new_log = pending_logs.popleft()
                displayed_logs.append(new_log)
                if len(displayed_logs) > 1000: displayed_logs.pop(0)
            last_line_time = current_time
            needs_redraw = True
        
        # 4. Update ceas la 2 secunde
        if not needs_redraw and (current_time - last_clock_update >= 2.0):
            needs_redraw = True
            last_clock_update = current_time
        
        # 5. Render
        if needs_redraw:
            height, width = stdscr.getmaxyx()
            
            # Header
            safe_addstr(stdscr, 0, 0, " " * width, curses.color_pair(2) | curses.A_BOLD)
            safe_addstr(stdscr, 0, (width-14)//2, " TRINITY FUND ", curses.color_pair(2) | curses.A_BOLD)
            
            scroll_status = "LIVE" if scroll_offset == 0 else f"SCROLL (-{scroll_offset})"
            safe_addstr(stdscr, 1, 0, f"  {datetime.now().strftime('%H:%M:%S')} │ {scroll_status} │ {metrics.uptime} │ Q=quit │ ↑↓=Scroll │ G=Live ", curses.color_pair(7))
            
            # Status
            row = 3
            safe_addstr(stdscr, row, 0, " BOT STATUS", curses.color_pair(2) | curses.A_BOLD)
            row += 1
            for bot_name, state in bot_states.items():
                config = BOTS[bot_name]
                color = curses.color_pair(config['color'])
                status = " SCANNING" if state.status == 'SCANNING' else "● ONLINE" if state.status == 'ONLINE' else "○ OFFLINE"
                safe_addstr(stdscr, row, 0, f"  {config['icon']} {bot_name:<8} {status}   Logs: {state.log_count}", color)
                row += 1
            
            # Metrics
            row += 1
            safe_addstr(stdscr, row, 0, " METRICS", curses.color_pair(2) | curses.A_BOLD)
            row += 1
            safe_addstr(stdscr, row, 0, f"   Equity: ${metrics.live_equity:,.2f}", curses.color_pair(9))
            safe_addstr(stdscr, row, 30, f"  🥇 XAUUSD: ${metrics.xauusd_price:.2f}", curses.color_pair(9))
            safe_addstr(stdscr, row, 60, f"   {metrics.total_logs}", curses.color_pair(1))
            sys_m = get_system_metrics()
            safe_addstr(stdscr, row+1, 0, f"  ⚙️ CPU: {sys_m['load']:.2f}", curses.color_pair(1))
            safe_addstr(stdscr, row+1, 30, f"  💾 RAM: {sys_m['mem_percent']:.1f}%", curses.color_pair(1))
            
            # Logs
            log_start_row = row + 3
            safe_addstr(stdscr, log_start_row - 1, 0, f" LIVE LOGS (TV Prompter: 1 line/sec | Total: {len(displayed_logs)})", curses.color_pair(2) | curses.A_BOLD)
            
            # Clear log area
            for r in range(log_start_row, height):
                stdscr.move(r, 0)
                stdscr.clrtoeol()
            
            max_visible = height - log_start_row - 1
            total_logs = len(displayed_logs)
            
            # Calculare indexuri pentru scroll
            if scroll_offset == 0:
                end_idx = total_logs
            else:
                end_idx = max(0, total_logs - scroll_offset)
            
            start_idx = max(0, end_idx - max_visible)
            visible_logs = displayed_logs[start_idx:end_idx]
            
            display_row = log_start_row
            for log in visible_logs:
                if display_row >= height: break
                line = log['line']
                
                if any(x in line for x in ['Whale insuficient', 'Deconectat', 'ERROR', 'Respingem']):
                    msg_color = curses.color_pair(3)
                elif any(x in line for x in ['✅', 'SUCCESS', 'TRADE', 'ONLINE']):
                    msg_color = curses.color_pair(9)
                else:
                    msg_color = curses.color_pair(log['color'])
                
                safe_addstr(stdscr, display_row, 0, f"[{log['time']}] {log['icon']} {log['bot']:<8} {line}", msg_color)
                display_row += 1
            
            stdscr.refresh()
        
        time.sleep(0.1)

if __name__ == '__main__':
    try: curses.wrapper(main)
    except KeyboardInterrupt: print("\n Monitor oprit.\n")
