import numpy as np
from collections import deque

class ADXCalculator:
    def __init__(self, period=14, candle_size_minutes=15):  # SCHIMBAT la 15 minute pentru confirmare instituțională
        self.period = period
        self.candle_size_minutes = candle_size_minutes
        self.candles = deque(maxlen=100)
        self.current_candle = None
        self.last_adx = None

    def add_tick(self, price, timestamp):
        minute = int(timestamp // (self.candle_size_minutes * 60)) * (self.candle_size_minutes * 60)

        if self.current_candle is None or self.current_candle['minute'] != minute:
            if self.current_candle is not None:
                self.candles.append(self.current_candle)

            self.current_candle = {
                'minute': minute,
                'open': price,
                'high': price,
                'low': price,
                'close': price
            }
        else:
            self.current_candle['high'] = max(self.current_candle['high'], price)
            self.current_candle['low'] = min(self.current_candle['low'], price)
            self.current_candle['close'] = price

    def calculate_adx(self):
        if len(self.candles) < self.period + 1:
            return None

        highs = np.array([c['high'] for c in self.candles])
        lows = np.array([c['low'] for c in self.candles])
        closes = np.array([c['close'] for c in self.candles])

        tr1 = highs[1:] - lows[1:]
        tr2 = np.abs(highs[1:] - closes[:-1])
        tr3 = np.abs(lows[1:] - closes[:-1])
        tr = np.maximum(np.maximum(tr1, tr2), tr3)

        plus_dm = np.zeros(len(highs) - 1)
        minus_dm = np.zeros(len(highs) - 1)

        for i in range(len(highs) - 1):
            up_move = highs[i+1] - highs[i]
            down_move = lows[i] - lows[i+1]

            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            else:
                plus_dm[i] = 0

            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
            else:
                minus_dm[i] = 0

        atr = self._smooth(tr, self.period)
        plus_di = 100 * self._smooth(plus_dm, self.period) / atr
        minus_di = 100 * self._smooth(minus_dm, self.period) / atr

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = self._smooth(dx, self.period)

        self.last_adx = adx[-1] if len(adx) > 0 else None
        return self.last_adx

    def _smooth(self, data, period):
        result = np.zeros(len(data))
        result[period-1] = np.mean(data[:period])
        for i in range(period, len(data)):
            result[i] = (result[i-1] * (period - 1) + data[i]) / period
        return result[period-1:]

    def is_trending(self, threshold=25):
        adx = self.calculate_adx()
        if adx is None:
            return None
        return adx > threshold
