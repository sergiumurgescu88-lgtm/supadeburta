from flask import jsonify
import sys
sys.path.append('/root/ctrader-g4trade-bot')
from trade_tracker import get_positions, get_history

def register_api_endpoints(app):
    @app.route('/api/positions')
    def api_positions():
        return jsonify({'positions': get_positions()})

    @app.route('/api/history')
    def api_history():
        return jsonify({'trades': get_history()})
