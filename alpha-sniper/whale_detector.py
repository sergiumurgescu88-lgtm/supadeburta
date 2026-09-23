import time
from collections import deque

class WhaleDetector:
    def __init__(self, history_size=50, threshold_multiplier=3.0):
        self.tick_history = deque(maxlen=history_size)
        self.threshold_multiplier = threshold_multiplier
        self.whale_alerts = []
        
    def add_tick(self, volume, price, timestamp):
        """Adaugă un tick nou în istoric"""
        self.tick_history.append({
            'volume': volume,
            'price': price,
            'timestamp': timestamp
        })
        
        # Verifică dacă este whale
        if len(self.tick_history) >= 10:
            avg_volume = sum(t['volume'] for t in self.tick_history) / len(self.tick_history)
            
            if volume > avg_volume * self.threshold_multiplier:
                alert = {
                    'timestamp': timestamp,
                    'volume': volume,
                    'price': price,
                    'avg_volume': avg_volume,
                    'multiplier': volume / avg_volume,
                    'type': 'WHALE_DETECTED'
                }
                self.whale_alerts.append(alert)
                print(f"🐋 WHALE DETECTED! Volume: {volume} ({volume/avg_volume:.1f}x avg)")
                return alert
        
        return None
    
    def get_recent_alerts(self, count=10):
        """Returnează ultimele N alerte whale"""
        return self.whale_alerts[-count:]
    
    def get_stats(self):
        """Returnează statistici despre detecții"""
        if not self.whale_alerts:
            return {'total_whales': 0, 'avg_multiplier': 0}
        
        return {
            'total_whales': len(self.whale_alerts),
            'avg_multiplier': sum(a['multiplier'] for a in self.whale_alerts) / len(self.whale_alerts),
            'last_whale': self.whale_alerts[-1] if self.whale_alerts else None
        }

# Test rapid
if __name__ == "__main__":
    detector = WhaleDetector()
    
    # Simulăm câteva tick-uri
    for i in range(20):
        volume = 100 if i != 15 else 5000  # Tick-ul 15 este whale
        detector.add_tick(volume, 2000 + i*0.1, time.time())
    
    print(f"\nStatistici: {detector.get_stats()}")
