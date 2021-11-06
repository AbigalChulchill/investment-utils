from typing import List, NamedTuple

class PnL(NamedTuple):
    realized_pnl: float
    realized_pnl_percent: float
    break_even_price: float
    unrealized_sell_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float

INVALID_PERCENT = -999

class Order(NamedTuple):
    side:   str
    value:  float
    qty:    float

def calculate_inc_pnl(orders: List[Order], market_price_now: float) -> PnL:

    position_qty = 0
    average_buying_rate = None

    cumulative_initial_buy_value = 0
    cumulative_sell_value = 0

    for o in orders:
        if o.side == "BUY":

            if average_buying_rate:
                average_buying_rate = (average_buying_rate * position_qty + o.value)  / (position_qty + o.qty)
            else:
                average_buying_rate = o.value / o.qty
            position_qty += o.qty

        elif o.side == "SELL":
            initial_buy_value = o.qty * average_buying_rate
            cumulative_initial_buy_value += initial_buy_value
            cumulative_sell_value += o.value
            position_qty -= o.qty


    unrealized_sell_value = position_qty * market_price_now
    average_buying_value = position_qty * average_buying_rate if average_buying_rate else 0
    unrealized_pnl = unrealized_sell_value - average_buying_value
    unrealized_pnl_percent = unrealized_pnl / average_buying_value * 100 if average_buying_value > 1e-5 else INVALID_PERCENT

    realized_pnl = cumulative_sell_value - cumulative_initial_buy_value
    realized_pnl_percent = realized_pnl / cumulative_initial_buy_value * 100 if cumulative_initial_buy_value > 1e-5 else INVALID_PERCENT

    return PnL(
        realized_pnl,
        realized_pnl_percent,
        average_buying_rate,
        unrealized_sell_value,
        unrealized_pnl,
        unrealized_pnl_percent
    )
