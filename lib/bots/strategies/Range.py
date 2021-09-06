from lib.bots.interfaces import Strategy, Ticker, Broker
from lib.common import position_size

class TraderRange(Strategy):
    def __init__(self, low: float, high: float, account: float, split: int, stop: float, risk: float):
        self._low = low
        self._high = high
        self._account = account
        self._split = split
        self._stop = stop
        self._risk = risk
        self._position = False

    def tick(self, ticker: Ticker, broker: Broker):
        c = ticker.close
        o = ticker.open
        h = ticker.high
        l = ticker.low
