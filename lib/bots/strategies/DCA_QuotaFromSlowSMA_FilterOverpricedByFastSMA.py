from lib.bots.interfaces import Strategy, Ticker, Broker
import talib

class StrategyImpl(Strategy):
    '''
      A strategy to backtest the period of MA from which the quota multiplier for DCA is derived

        quota_multiplier = SMA(close, quota_multiplier_ma_length) / close .

      Also not buying unless below SMA(close, overprice_filter_ma_length)
    '''
    def __init__(self, args: dict):
        self._dca_base_quota = float(args['dca_base_quota'])
        self._quota_multiplier_ma_length = int(args['quota_multiplier_ma_length'])
        self._overprice_filter_ma_length = int(args['overprice_filter_ma_length'])
        print(f"Strategy: using DCA base quota : {self._dca_base_quota},  Quota multiplier MA len : {self._quota_multiplier_ma_length}, overprice_filter MA len : {self._overprice_filter_ma_length}")

    def tick(self, ticker: Ticker, broker: Broker):
        c = ticker.close

        quota_mult = 1


        # quota calculation
        if len(c) >= self._quota_multiplier_ma_length:
            ma = talib.SMA(c, self._quota_multiplier_ma_length)
            quota_mult = ma[-1] / c[-1]

        # filtering
        if len(c) >= self._overprice_filter_ma_length:
            ma = talib.SMA(c, self._overprice_filter_ma_length)
            if c[-1] > ma[-1]:
                return
        else:
            return


        buy_qty = self._dca_base_quota * quota_mult /  c[-1]

        print(f"{ticker.timestamp} buy {buy_qty}  mult={round(quota_mult,2)}")
        broker.buy(buy_qty)
