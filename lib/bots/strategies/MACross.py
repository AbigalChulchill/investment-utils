from lib.bots.interfaces import Strategy, Ticker, Broker
from lib.common import ta
from lib.common import position_size
import talib

class TraderMACross(Strategy):
    def __init__(self):
        self._position = 0
        self._risk = 1
        self._long_enabled = True
        self._short_enabled = True

    def tick(self, ticker: Ticker, broker: Broker):
        c = ticker.close
        o = ticker.open
        h = ticker.high
        l = ticker.low
        v = ticker.volume
        
        ma1 = talib.SMA(c, 5)
        ma2 = talib.SMA(c, 20)

        mid = ta.hlc3(h, l, c)

        buy = ta.crossover(ma1,ma2)
        sell = ta.crossunder(ma1,ma2)

        atrmult = 1.5
        atr = talib.ATR(h, l, c, timeperiod=14)*atrmult
        atr_l = mid - atr
        atr_h = mid + atr

       
        if self._position > 0:
            if c[-1] < self._stop or sell:
                print(ticker.timestamp)
                print(">> long TP")
                broker.sell(self._position)
                self._position = 0
                print("")
            else:
                self._stop = max(self._stop, atr_l[-1])

        if self._position < 0:
            if c[-1] > self._stop or buy:
                print(ticker.timestamp)
                print(">> short TP")
                broker.buy(-self._position)
                self._position = 0
                print("")
            else:
                self._stop = min(self._stop, atr_h[-1])

        if self._position == 0:
            if buy and self._long_enabled:
                print(ticker.timestamp)
                pos_size =  position_size.calculate_position_size(broker.account_size_usd, c[-1], atr_l[-1], self._risk)
                pos_size = min( broker.account_size_usd / c[-1], pos_size)
                print(">> long ENTER")
                value,qty = broker.buy(pos_size)
                self._position = qty
                self._stop = atr_l[-1]
                print("")
            if sell and self._short_enabled:
                print(ticker.timestamp)
                pos_size =  position_size.calculate_position_size(broker.account_size_usd, c[-1], atr_h[-1], self._risk)
                pos_size = min( broker.account_size_usd / c[-1], pos_size)
                print(">> short ENTER")
                value,qty = broker.sell(pos_size)
                self._position = -qty
                self._stop = atr_h[-1]
                print("")

