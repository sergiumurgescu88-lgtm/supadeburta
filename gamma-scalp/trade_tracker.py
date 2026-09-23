import json
import os
from datetime import datetime

TRADES_FILE = '/root/ctrader-g4trade-bot/trades.json'

def load_trades():
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return {'trades': [], 'positions': []}

def save_trades(data):
    with open(TRADES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_trade(side, volume, price, status='OPEN'):
    data = load_trades()
    trade = {
        'id': len(data['trades']) + 1,
        'time': int(datetime.now().timestamp()),
        'side': 'BUY' if side == 1 else 'SELL',
        'volume': volume,
        'price': price,
        'status': status,
        'profit': 0.0
    }
    data['trades'].append(trade)
    if status == 'OPEN':
        data['positions'].append(trade)
    save_trades(data)
    return trade

def get_positions():
    return load_trades()['positions']

def get_history():
    return load_trades()['trades']
