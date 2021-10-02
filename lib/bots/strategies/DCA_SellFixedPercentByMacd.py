from lib.bots.interfaces import Strategy, Ticker, Broker
from lib.common import ta
import talib

class StrategyImpl(Strategy):
    '''
    A strategy to backtest the effect of selling a set amount of % of coin equity on each MACD crossunder
    '''
    def __init__(self, args: dict):
        self._quota = 100
        self._remove_percent  = float(args['remove_percent'])
        print(f"Strategy: using DCA quota {self._quota} remove percent: {self._remove_percent}")

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
            buy_qty = self._quota / c[-1]
            print(f"{ticker.timestamp} buy {buy_qty}")
            broker.buy(buy_qty)
