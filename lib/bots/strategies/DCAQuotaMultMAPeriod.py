

from lib.bots.interfaces import Strategy, Ticker, Broker
from lib.common import ta
import talib

class TraderDCAQuotaMultMAPeriod(Strategy):
    '''
    A strategy to backtest the period of MA from which the quota multiplier for DCA is derived
      quota_multiplier = MA(close, period) / close 
    '''
    def __init__(self, args: dict):
        self._dca_base_quota = float(args['dca_base_quota'])
        self._ma_period = int(args['ma_period'])
        self._remove_percent  = float(args['remove_percent'])
        print(f"Strategy: using DCA base quota : {self._dca_base_quota}   MA period : {self._ma_period}  remove percent: {self._remove_percent}")

    def tick(self, ticker: Ticker, broker: Broker):
        c = ticker.close
        macd, macdsignal, macdhist = talib.MACD(c, fastperiod=12, slowperiod=26, signalperiod=9)

        pnl = broker.pnl

        sell = macd[-1] > 0 and ta.crossunder(macd, macdsignal) and pnl and pnl.unrealized_pnl_percent > 5

        if sell:
            sell_qty = broker.account_size_token * self._remove_percent/100
            print(f"{ticker.timestamp} sell {sell_qty}")
            broker.sell(sell_qty)

        else:
        
            quota_mult = 1
            if self._ma_period != 0:
                ma = talib.SMA(c, self._ma_period)

                quota_mult = ma[-1] / c[-1]
                #quota_mult = min(1, ma[-1] / c[-1])
                
                if quota_mult != quota_mult: # workaround for NaN if not enough data available for full SMA period
                    quota_mult = 1
            
            buy_qty = self._dca_base_quota * quota_mult /  c[-1]

            print(f"{ticker.timestamp} buy {buy_qty}  mult={round(quota_mult,2)}")
            broker.buy(buy_qty)
