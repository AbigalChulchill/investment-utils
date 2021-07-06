import collections

PnL = collections.namedtuple('PnL', ['realized_pnl', 'realized_pnl_percent', 'unrealized_sell_value', 'unrealized_pnl', 'unrealized_pnl_percent'])

def calculate_pnl(buy_value: float, buy_qty: float, sell_value: float, sell_qty: float, market_price_now: float) -> PnL:
    average_buying_rate = buy_value / buy_qty

    sold_tokens_buy_value = sell_qty * average_buying_rate
    realized_pnl = sell_value - sold_tokens_buy_value
    realized_pnl_percent = round(realized_pnl / sold_tokens_buy_value * 100, 1) if sold_tokens_buy_value > 0 else '~'

    unrealized_sell_value = (buy_qty - sell_qty) * market_price_now
    unrealized_sold_tokens_buy_value = (buy_qty - sell_qty) * average_buying_rate
    unrealized_pnl = unrealized_sell_value - unrealized_sold_tokens_buy_value
    unrealized_pnl_percent = round(unrealized_pnl / unrealized_sold_tokens_buy_value * 100, 1) if unrealized_sold_tokens_buy_value > 0 else '~'

    return PnL(
        realized_pnl,
        realized_pnl_percent,
        unrealized_sell_value,
        unrealized_pnl,
        unrealized_pnl_percent
    )

