from lib.bots.interfaces import Strategy, Ticker, Broker
import talib

class StrategyImpl(Strategy):
    '''
      A strategy to backtest the period of MA from which the quota multiplier for DCA is derived
      quota_multiplier = MA(close, period) / close 
    '''
    def __init__(self, args: dict):
        self._dca_base_quota = float(args['dca_base_quota'])
        self._ma_period = int(args['ma_period'])
        print(f"Strategy: using DCA base quota : {self._dca_base_quota}  and MA period : {self._ma_period}")

    def tick(self, ticker: Ticker, broker: Broker):
        c = ticker.close
        
        quota_mult = 1

        # quota calculation
        if len(c) >= self._ma_period:
            ma = talib.SMA(c, self._ma_period)
            quota_mult = ma[-1] / c[-1]

        buy_qty = self._dca_base_quota * quota_mult /  c[-1]

        print(f"{ticker.timestamp} buy {buy_qty}  mult={round(quota_mult,2)}")
        broker.buy(buy_qty)
