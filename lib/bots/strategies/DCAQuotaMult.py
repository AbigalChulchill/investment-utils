from lib.bots.interfaces import Strategy, Ticker, Broker

class StrategyImpl(Strategy):
    '''
      A strategy to backtest the average buy price when using quota multiplier for DCA
      based on level ratio
    '''
    def __init__(self, args: dict):
        self._dca_base_quota = float(args['dca_base_quota'])
        self._base_price = float(args['dca_base_price'])

    def tick(self, ticker: Ticker, broker: Broker):
        c = ticker.close
        quota_mult = self._base_price / c[-1]
        buy_qty = self._dca_base_quota * quota_mult /  c[-1]
        print(f"{ticker.timestamp} buy {buy_qty}  mult={quota_mult:.2f}")
        broker.buy(buy_qty)
