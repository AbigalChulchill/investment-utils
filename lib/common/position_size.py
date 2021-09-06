
def calculate_position_size(account: float, current_price: float, stop_price: float, risk_percent: float):
    risk_equity  = account * risk_percent * 0.01
    risk_trade   = abs(stop_price - current_price)
    return risk_equity / risk_trade
