import sys
sys.path.append('/root/ctrader-g4trade-bot')
from position_sizing import PositionSizer

# Inițializăm Position Sizer cu 10000 USD (aprox. 9800 EUR) și risc de 1%
sizer = PositionSizer(account_balance=10000.0, risk_per_trade=0.01)

def evaluate_trade_setup(engine, side: str) -> dict:
    score = 0
    reasons = []
    dynamic_volume = None

    # 1. Whale Detection (35%)
    recent_whales = engine.whale_detector.get_recent_alerts(1)
    if recent_whales and len(recent_whales) > 0:
        score += 35
        reasons.append("Whale/Volume anomaly detected")
    else:
        reasons.append("No institutional volume spike")

    # 2. Delta Volume (25%)
    pressure_signal = engine.delta_analyzer.get_pressure_signal()
    if pressure_signal and "INSUFFICIENT" not in str(pressure_signal).upper():
        if (side == 'BUY' and 'BUY' in str(pressure_signal).upper()) or (side == 'SELL' and 'SELL' in str(pressure_signal).upper()):
            score += 25
            reasons.append(f"Delta pressure confirms direction: {pressure_signal}")
        else:
            reasons.append(f"Delta pressure against direction: {pressure_signal}")
    else:
        if engine.last_price:
            score += 10
            reasons.append("Delta data warming up (valid price action)")
        else:
            reasons.append("No delta pressure signal")

    # 3. ADX M15 - Trend Filter (20%)
    is_trending = engine.adx_calculator.is_trending()
    adx_val = engine.adx_calculator.calculate_adx()
    if is_trending is True:
        score += 20
        reasons.append(f"M15 ADX confirms trend (ADX={adx_val:.1f})")
    elif is_trending is False:
        reasons.append(f"M15 ADX shows ranging market (ADX={adx_val:.1f})")
    else:
        if engine.last_price:
            score += 10
            reasons.append("M15 ADX warming up (collecting candles)")
        else:
            reasons.append("No price data for M15 ADX")

    # 4. Smart TP/SL & Dynamic Sizing (20%)
    if engine.last_price:
        smart_levels = engine.tp_sl_calculator.calculate_smart_levels(engine.last_price, side)
        if smart_levels and 'sl' in smart_levels and 'tp' in smart_levels:
            score += 20
            reasons.append(f"Smart TP/SL calculated (RR: {smart_levels.get('risk_reward', 'N/A')})")
            
            # Calculăm volumul dinamic dacă avem SL
            if smart_levels['sl'] != engine.last_price:
                dynamic_volume = sizer.calculate_lot_size(engine.last_price, smart_levels['sl'])
                reasons.append(f"Dynamic sizing: {dynamic_volume} lots (1% risk)")
        else:
            score += 10
            reasons.append("Risk management active (TP/SL warming up)")
    else:
        reasons.append("No price data available")

    # Pragul Instituțional: 70 pentru aprobare
    is_approved = score >= 70
    
    result = {
        "score": score, 
        "approved": is_approved, 
        "reasons": reasons
    }
    
    if dynamic_volume:
        result["dynamic_volume"] = dynamic_volume
        
    return result
