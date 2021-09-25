from lib.bots.interfaces import Strategy, Ticker, Broker

class StrategyImpl(Strategy):
    '''
      A strategy to backtest the average buy price when using constant DCA quota in tokens
    '''
    def __init__(self, args: dict):
        self._dca_base_quota = float(args['dca_base_quota'])

    def tick(self, ticker: Ticker, broker: Broker):
        c = ticker.close
        buy_qty = self._dca_base_quota
        print(f"{ticker.timestamp} buy {buy_qty}")
        broker.buy(buy_qty)
