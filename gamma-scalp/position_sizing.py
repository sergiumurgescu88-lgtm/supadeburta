class PositionSizer:
    def __init__(self, account_balance=10000.0, risk_per_trade=0.01):
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade  # 1% risc implicit

    def calculate_lot_size(self, current_price, sl_price, symbol='XAUUSD'):
        """
        Calculează volumul (loturi) bazat pe risc dinamic.
        Pentru XAUUSD: 1 lot standard = 100 uncii. 
        O mișcare de 1.00 în preț (ex: 2350 -> 2351) = 100 USD profit/pierdere per lot.
        """
        risk_amount = self.account_balance * self.risk_per_trade
        price_distance = abs(current_price - sl_price)
        
        if price_distance == 0:
            return 0.01 # Fallback minim de siguranță
            
        contract_size = 100.0 
        
        lot_size = risk_amount / (price_distance * contract_size)
        
        # Rotunjim la 2 zecimale și limităm între 0.01 și 10.0 loturi
        lot_size = max(0.01, min(10.0, round(lot_size, 2)))
        
        return lot_size
