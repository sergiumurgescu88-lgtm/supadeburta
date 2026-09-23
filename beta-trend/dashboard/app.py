import os
import time
import json
from flask import Flask, jsonify, request, render_template
from auth_cTrader import auth_bp
from flask_socketio import SocketIO

app = Flask(__name__)

app.register_blueprint(auth_bp, url_prefix="/auth")
socketio = SocketIO(app, cors_allowed_origins="*")

# Încercăm să încărcăm API-ul de Trading Intelligence
try:
    import sys
    sys.path.append('/root/ctrader-g4trade-bot')
    from api_trading import register_trading_api
    register_trading_api(app)
    print("✅ Trading API încărcat cu succes!")
except Exception as e:
    print(f"⚠️ Trading API nu a putut fi încărcat: {e}")

@app.route('/api/trade', methods=['POST'])
def api_trade():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Date lipsă'}), 400
        
        side = str(data.get('side', 'UNKNOWN'))
        volume = float(data.get('volume', 0.01))
        sl = float(data.get('sl', 0)) if data.get('sl') else None
        tp = float(data.get('tp', 0)) if data.get('tp') else None

        static_dir = '/root/ctrader-g4trade-bot/dashboard/static'
        os.makedirs(static_dir, exist_ok=True)

        trade_data = {
            'side': side,
            'volume': volume,
            'sl': sl,
            'tp': tp,
            'symbol': 'XAUUSD',
            'timestamp': time.time(),
            'status': 'PENDING_EXECUTION'
        }

        file_path = os.path.join(static_dir, 'trade_request.json')
        with open(file_path, 'w') as f:
            json.dump(trade_data, f, indent=4)

        print(f"✅ COMANDĂ SCRISĂ ÎN FIȘIER: {file_path}")
        return jsonify({'message': f'Comanda {side} a fost înregistrată și trimisă către bot!', 'data': trade_data})
    except Exception as e:
        print(f"❌ EROARE CRITICĂ ÎN api_trade: {str(e)}")
        return jsonify({'error': 'Eroare internă', 'details': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/trading/logs')
def trading_logs():
    import subprocess
    p = "/var/log/trinity/beta-engine.log"
    try:
        out = subprocess.run(["tail", "-n", "120", p], capture_output=True, text=True).stdout
        lines = ["[BETA] " + l for l in out.splitlines() if l.strip()]
    except Exception:
        lines = ["[BETA] log indisponibil"]
    return "\n".join(lines) + "\n"






@app.route('/api/current')
def current_price():
    import random, time
    price = 2350.50 + (random.random() - 0.5) * 10
    return jsonify({
        'price': round(price, 2),
        'bid': round(price - 0.5, 2),
        'ask': round(price + 0.5, 2),
        'timestamp': int(time.time() * 1000)
    })

if __name__ == '__main__':
    print("🚀 DASHBOARD PORNIT PE PORTUL 5050")
    
@app.route('/api/system/status')
def get_system_status():
    import json
    try:
        with open('static/system_status.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Status file not found"}, 404

@app.route('/architecture')
def architecture_page():
    return send_from_directory('static', 'architecture.html')

def get_trading_logs():
    try:
        with open('/var/log/g4trade-strategy.log', 'r') as f:
            return "".join(f.readlines()[-200:])
    except Exception as e:
        return str(e), 500






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5102, debug=False)
