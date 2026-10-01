import sys
sys.path.append('/root/ctrader-g4trade-bot')

from whale_detector import WhaleDetector
from smart_tp_sl import SmartTPSL
from delta_volume import DeltaVolumeAnalyzer
from adx_calculator import ADXCalculator
import time

class TradingEngine:
    def __init__(self):
        self.whale_detector = WhaleDetector()
        self.tp_sl_calculator = SmartTPSL()
        self.delta_analyzer = DeltaVolumeAnalyzer()
        self.adx_calculator = ADXCalculator(period=14, candle_size_minutes=1)
        self.last_price = None
        self.last_timestamp = None

    def process_tick(self, price, volume):
        timestamp = time.time()
        whale_alert = self.whale_detector.add_tick(volume, price, timestamp)
        self.tp_sl_calculator.add_price(price, timestamp)
        
        if self.last_price is not None:
            price_change = price - self.last_price
            self.delta_analyzer.add_tick(price_change, volume, timestamp)

        self.adx_calculator.add_tick(price, timestamp)
        self.last_price = price
        self.last_timestamp = timestamp

        return {
            'price': price,
            'volume': volume,
            'whale_alert': whale_alert,
            'smart_levels': self.tp_sl_calculator.calculate_smart_levels(price, 'BUY'),
            'delta': self.delta_analyzer.calculate_delta(),
            'pressure_signal': self.delta_analyzer.get_pressure_signal(),
            'adx': self.adx_calculator.calculate_adx(),
            'is_trending': self.adx_calculator.is_trending()
        }

    def get_status(self):
        return {
            'whale_stats': self.whale_detector.get_stats(),
            'recent_whales': self.whale_detector.get_recent_alerts(5),
            'pressure_signal': self.delta_analyzer.get_pressure_signal(),
            'delta': self.delta_analyzer.calculate_delta(),
            'adx': self.adx_calculator.calculate_adx(),
            'is_trending': self.adx_calculator.is_trending()
        }

engine = TradingEngine()
