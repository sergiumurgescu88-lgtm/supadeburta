from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import subprocess
import re

app = Flask(__name__)
CORS(app)

LOG_DIR = "/var/log/trinity"
LOG_FILES = {
    "alpha": "alpha-engine.log",
    "beta": "beta-engine.log",
    "gamma": "gamma-engine.log"
}

@app.route('/api/logs')
def get_combined_logs():
    lines_per_strategy = int(request.args.get('lines', 50))
    combined_logs = []
    for strategy, filename in LOG_FILES.items():
        log_path = os.path.join(LOG_DIR, filename)
        if os.path.exists(log_path):
            try:
                result = subprocess.run(['tail', f'-n{lines_per_strategy}', log_path], capture_output=True, text=True)
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        combined_logs.append({"strategy": strategy, "line": line, "timestamp": line[:23] if len(line) > 23 else ""})
            except Exception as e:
                pass
    combined_logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify({"success": True, "logs": combined_logs[:lines_per_strategy * 3]})

@app.route('/api/trading/logs')
def trading_logs_text():
    """TEXT SIMPLU pentru terminalul verde - SORTAT CRONOLOGIC"""
    logs = []
    timestamp_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})')
    for strategy, filename in LOG_FILES.items():
        log_path = os.path.join(LOG_DIR, filename)
        if os.path.exists(log_path):
            try:
                result = subprocess.run(['tail', '-n', '60', log_path], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if line.strip():
                        match = timestamp_pattern.search(line)
                        ts = match.group(1) if match else "0000-00-00 00:00:00,000"
                        logs.append((ts, f"[{strategy.upper()}] {line}"))
            except Exception:
                pass
    # Sortare cronologica (ascendent - vechi la inceput, nou la final)
    logs.sort(key=lambda x: x[0])
    return "\n".join([line for ts, line in logs[-180:]]) + "\n"

@app.route('/api/status')
def get_status():
    status = {}
    for strategy, filename in LOG_FILES.items():
        log_path = os.path.join(LOG_DIR, filename)
        status[strategy] = {"active": os.path.exists(log_path)}
    return jsonify({"success": True, "status": status})



@app.route('/api/trading/status')
def trading_status():
    """Returnează statusul și prețul real al aurului"""
    import requests
    import time
    
    # Preț real de la API extern
    try:
        response = requests.get('https://api.gold-api.com/price/XAU', timeout=5)
        data = response.json()
        price = data.get('price', 2650.00)
        prev_close = data.get('prev_close_price', price - 5)
        change = price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close else 0
        
        return jsonify({
            'status': 'active',
            'current_price': price,
            'price_change': change,
            'price_change_percent': change_percent,
            'timestamp': int(time.time())
        })
    except Exception as e:
        # Fallback dacă API-ul extern nu răspunde
        return jsonify({
            'status': 'active',
            'current_price': 2650.00,
            'price_change': 0,
            'price_change_percent': 0,
            'timestamp': int(time.time())
        })

@app.route('/api/trading/whales')
def trading_whales():
    """Returnează alertele whale (simulare pentru moment)"""
    return jsonify({
        'whales': [],
        'whale_stats': {
            'total_whales': 0,
            'total_volume': 0
        }
    })

@app.route('/api/trading/delta')
def trading_delta():
    """Returnează delta volume pressure (simulare pentru moment)"""
    return jsonify({
        'deltaData': {
            'signal': 'WAITING FOR DATA',
            'delta': {
                'buy_volume': 0,
                'sell_volume': 0
            }
        }
    })

@app.route('/api/trading/smart-levels')
def smart_levels():
    """Returnează nivelele smart (suport/rezistență)"""
    import requests
    try:
        response = requests.get('https://api.gold-api.com/price/XAU', timeout=5)
        data = response.json()
        price = data.get('price', 2650.00)
        
        return jsonify({
            'sl': round(price - 10, 2),  # Stop Loss: 10$ sub preț
            'tp': round(price + 30, 2)   # Take Profit: 30$ peste preț
        })
    except:
        return jsonify({
            'sl': 2640.00,
            'tp': 2680.00
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=False)
