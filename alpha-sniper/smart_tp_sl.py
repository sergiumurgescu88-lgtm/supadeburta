import numpy as np
from collections import deque

class SmartTPSL:
    def __init__(self, lookback_period=50):
        self.price_history = deque(maxlen=lookback_period)
        self.atr_period = 14
        
    def add_price(self, price, timestamp):
        """Adaugă un preț nou în istoric"""
        self.price_history.append({
            'price': price,
            'timestamp': timestamp
        })
    
    def calculate_atr(self):
        """Calculează Average True Range"""
        if len(self.price_history) < self.atr_period:
            return None
        
        prices = [p['price'] for p in self.price_history]
        true_ranges = []
        
        for i in range(1, len(prices)):
            high = max(prices[i], prices[i-1])
            low = min(prices[i], prices[i-1])
            tr = high - low
            true_ranges.append(tr)
        
        return np.mean(true_ranges[-self.atr_period:])
    
    def find_support_resistance(self):
        """Găsește nivelurile de suport și rezistență"""
        if len(self.price_history) < 20:
            return None, None
        
        prices = [p['price'] for p in self.price_history]
        
        # Suport = minimul ultimelor 20 de prețuri
        support = min(prices[-20:])
        
        # Rezistență = maximul ultimelor 20 de prețuri
        resistance = max(prices[-20:])
        
        return support, resistance
    
    def calculate_smart_levels(self, current_price, trade_side='BUY'):
        """Calculează TP și SL inteligente"""
        atr = self.calculate_atr()
        support, resistance = self.find_support_resistance()
        
        if atr is None or support is None:
            return None, None
        
        if trade_side == 'BUY':
            # SL = 1.5x ATR sub prețul curent
            sl = current_price - (atr * 1.5)
            
            # TP = chiar înainte de rezistență
            tp = resistance - (atr * 0.2)
            
        else:  # SELL
            # SL = 1.5x ATR peste prețul curent
            sl = current_price + (atr * 1.5)
            
            # TP = chiar înainte de suport
            tp = support + (atr * 0.2)
        
        return {
            'sl': round(sl, 2),
            'tp': round(tp, 2),
            'atr': round(atr, 2),
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'risk_reward': round(abs(tp - current_price) / abs(current_price - sl), 2)
        }

# Test rapid
if __name__ == "__main__":
    calculator = SmartTPSL()
    
    # Simulăm câteva prețuri
    import time
    for i in range(30):
        price = 2000 + np.random.uniform(-5, 5)
        calculator.add_price(price, time.time())
    
    levels = calculator.calculate_smart_levels(2005, 'BUY')
    print(f"\nNiveluri inteligente pentru BUY la 2005:")
    print(f"  SL: {levels['sl']}")
    print(f"  TP: {levels['tp']}")
    print(f"  Risk/Reward: {levels['risk_reward']}")
