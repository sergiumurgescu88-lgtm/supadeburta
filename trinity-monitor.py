#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║         TRINITY FUND - PREMIUM LIVE MONITOR v2.0             ║
║    Real-time Multi-Bot Dashboard with Color Coding          ║
╚═══════════════════════════════════════════════════════════════╝
"""

import subprocess
import time
import sys
from datetime import datetime

# ANSI Color Codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Bot Colors
    ALPHA = '\033[94m'    # Bright Blue
    BETA = '\033[92m'     # Bright Green
    GAMMA = '\033[93m'    # Bright Yellow
    SERGIU = '\033[95m'   # Bright Magenta
    EPSILON = '\033[96m'  # Bright Cyan
    
    # Status Colors
    INFO = '\033[36m'     # Cyan
    WARNING = '\033[33m'  # Yellow
    ERROR = '\033[91m'    # Bright Red
    SUCCESS = '\033[92m'  # Green
    
    # UI Colors
    BORDER = '\033[90m'   # Gray
    TIMESTAMP = '\033[37m' # White

# Bot configuration
BOTS = {
    'ALPHA': {
        'color': Colors.ALPHA,
        'symbol': '🎯',
        'file': '/root/.pm2/logs/alpha-sniper-engine-error.log'
    },
    'BETA': {
        'color': Colors.BETA,
        'symbol': '📈',
        'file': '/root/.pm2/logs/beta-trend-engine-error.log'
    },
    'GAMMA': {
        'color': Colors.GAMMA,
        'symbol': '⚡',
        'file': '/root/.pm2/logs/gamma-scalp-engine-error.log'
    },
    'SERGIU': {
        'color': Colors.SERGIU,
        'symbol': '🏆',
        'file': '/root/.pm2/logs/sergiu-strategy-engine-error.log'
    },
    'EPSILON': {
        'color': Colors.EPSILON,
        'symbol': '💎',
        'file': '/root/.pm2/logs/epsilon-strategy-engine-error.log'
    }
}

def clear_screen():
    print('\033[2J\033[H', end='')

def print_header():
    print(f"{Colors.BOLD}{Colors.BORDER}{'═' * 80}")
    print(f"{'═' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}  🏛️  TRINITY FUND - LIVE MONITORING DASHBOARD{Colors.RESET}")
    print(f"{Colors.BORDER}  {'─' * 76}{Colors.RESET}")
    print(f"  {Colors.INFO}⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}  │  "
          f"{Colors.SUCCESS}● LIVE{Colors.RESET}  │  "
          f"{Colors.TIMESTAMP}Auto-refresh: 1s{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BORDER}{'═' * 80}")
    print(f"{'═' * 80}{Colors.RESET}")
    print()

def format_log_line(line, bot_name, bot_config):
    """Format a single log line with colors"""
    line = line.strip()
    if not line:
        return None
    
    # Parse timestamp and message
    if ' - ' in line:
        parts = line.split(' - ', 1)
        timestamp = parts[0]
        message = parts[1] if len(parts) > 1 else ''
    else:
        timestamp = ''
        message = line
    
    # Determine message color based on content
    if '❌' in message or 'ERROR' in message:
        msg_color = Colors.ERROR
    elif '✅' in message or '🟢' in message or 'SUCCESS' in message:
        msg_color = Colors.SUCCESS
    elif '⚠️' in message or 'WARNING' in message:
        msg_color = Colors.WARNING
    elif '📥' in message:
        msg_color = Colors.INFO
    else:
        msg_color = Colors.RESET
    
    # Format the output
    bot_prefix = f"{bot_config['color']}{bot_config['symbol']} {bot_name:8}{Colors.RESET}"
    time_prefix = f"{Colors.TIMESTAMP}{timestamp:23}{Colors.RESET}"
    
    return f"{bot_prefix} │ {time_prefix} │ {msg_color}{message}{Colors.RESET}"

def tail_file(filename, bot_name, bot_config, num_lines=15):
    """Read last N lines from a file"""
    try:
        result = subprocess.run(
            ['tail', '-n', str(num_lines), filename],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return [format_log_line(line, bot_name, bot_config) for line in lines if line.strip()]
    except:
        pass
    return []

def main():
    clear_screen()
    print_header()
    
    # Collect logs from all bots
    all_logs = []
    
    for bot_name, bot_config in BOTS.items():
        logs = tail_file(bot_config['file'], bot_name, bot_config, num_lines=8)
        all_logs.extend(logs)
    
    # Sort by timestamp (simple string sort works for ISO format)
    all_logs.sort(key=lambda x: x if x else '')
    
    # Display logs
    print(f"{Colors.BORDER}{'─' * 80}{Colors.RESET}")
    for log in all_logs[-40:]:  # Show last 40 entries
        if log:
            print(log)
    
    print(f"{Colors.BORDER}{'─' * 80}{Colors.RESET}")
    
    # Legend
    print(f"\n{Colors.BOLD}📊 BOT LEGEND:{Colors.RESET}")
    for bot_name, bot_config in BOTS.items():
        print(f"  {bot_config['color']}{bot_config['symbol']} {bot_name:8}{Colors.RESET} "
              f"- {bot_config['file'].split('/')[-1]}")
    
    print(f"\n{Colors.BORDER}Press Ctrl+C to exit{Colors.RESET}")

if __name__ == '__main__':
    try:
        while True:
            main()
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.SUCCESS}✓ Monitor stopped. Goodbye!{Colors.RESET}\n")
        sys.exit(0)
