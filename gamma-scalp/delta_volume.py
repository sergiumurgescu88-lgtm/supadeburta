from collections import deque

class DeltaVolumeAnalyzer:
    def __init__(self, history_size=100):
        self.tick_history = deque(maxlen=history_size)
        
    def add_tick(self, price_change, volume, timestamp):
        """
        Adaugă un tick nou
        price_change: pozitiv = prețul a crescut, negativ = a scăzut
        volume: volumul tranzacționat
        """
        self.tick_history.append({
            'price_change': price_change,
            'volume': volume,
            'timestamp': timestamp,
            'is_buy': price_change > 0
        })
    
    def calculate_delta(self, period=50):
        """
        Calculează delta volume pentru ultimele N tick-uri
        Returnează: buy_volume - sell_volume
        """
        if len(self.tick_history) < period:
            return None
        
        recent_ticks = list(self.tick_history)[-period:]
        
        buy_volume = sum(t['volume'] for t in recent_ticks if t['is_buy'])
        sell_volume = sum(t['volume'] for t in recent_ticks if not t['is_buy'])
        
        delta = buy_volume - sell_volume
        
        return {
            'delta': delta,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'buy_percentage': (buy_volume / (buy_volume + sell_volume) * 100) if (buy_volume + sell_volume) > 0 else 0,
            'pressure': 'BULLISH' if delta > 0 else 'BEARISH'
        }
    
    def get_pressure_signal(self):
        """Returnează semnalul de presiune"""
        delta_data = self.calculate_delta()
        
        if delta_data is None:
            return 'INSUFFICIENT_DATA'
        
        if delta_data['buy_percentage'] > 60:
            return 'STRONG_BUY_PRESSURE'
        elif delta_data['buy_percentage'] > 55:
            return 'BUY_PRESSURE'
        elif delta_data['buy_percentage'] < 40:
            return 'STRONG_SELL_PRESSURE'
        elif delta_data['buy_percentage'] < 45:
            return 'SELL_PRESSURE'
        else:
            return 'NEUTRAL'

# Test rapid
if __name__ == "__main__":
    import time
    analyzer = DeltaVolumeAnalyzer()
    
    # Simulăm tick-uri cu presiune cumpărătoare
    for i in range(60):
        price_change = 0.5 if i % 3 != 0 else -0.3  # Mai multe creșteri
        volume = 100
        analyzer.add_tick(price_change, volume, time.time())
    
    delta = analyzer.calculate_delta()
    signal = analyzer.get_pressure_signal()
    
    print(f"\nAnaliză Delta Volume:")
    print(f"  Buy Volume: {delta['buy_volume']}")
    print(f"  Sell Volume: {delta['sell_volume']}")
    print(f"  Delta: {delta['delta']}")
    print(f"  Buy %: {delta['buy_percentage']:.1f}%")
    print(f"  Signal: {signal}")
