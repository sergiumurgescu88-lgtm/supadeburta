from flask import jsonify
from trading_engine import engine

def register_trading_api(app):
    
    @app.route('/api/trading/status')
    def trading_status():
        """Returnează statusul complet al trading engine"""
        return jsonify(engine.get_status())
    
    @app.route('/api/trading/smart-levels')
    def smart_levels():
        """Returnează nivelurile inteligente TP/SL"""
        from trading_engine import engine
        if engine.last_price:
            levels = engine.tp_sl_calculator.calculate_smart_levels(engine.last_price, 'BUY')
            return jsonify(levels)
        return jsonify({'error': 'No price data yet'})
    
    @app.route('/api/trading/whales')
    def whale_alerts():
        """Returnează ultimele alerte whale"""
        return jsonify({
            'whales': engine.whale_detector.get_recent_alerts(10),
            'stats': engine.whale_detector.get_stats()
        })
    
    @app.route('/api/trading/delta')
    def delta_analysis():
        """Returnează analiza delta volume"""
        delta = engine.delta_analyzer.calculate_delta()
        signal = engine.delta_analyzer.get_pressure_signal()
        return jsonify({
            'delta': delta,
            'signal': signal
        })
