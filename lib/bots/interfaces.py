from typing import Tuple
import numpy as np
import pandas as pd
from lib.common import pnl

class Broker:
    def buy(self, qty: float)->Tuple[float,float]:
        '''
        returns [value, qty]
        '''
        raise NotImplementedError()

    def sell(self, qty: float)->Tuple[float,float]:
        '''
        returns [value, qty]
        '''
        raise NotImplementedError()

    @property
    def account_size_usd(self) -> float:
        raise NotImplementedError()

    @property
    def account_size_token(self) -> float:
        raise NotImplementedError()

    @property
    def pnl(self) -> pnl.PnL:
        raise NotImplementedError()


class Ticker:
    @property
    def market_price(self) -> float:
        raise NotImplementedError()

    @property
    def timestamp(self) -> pd.DatetimeIndex:
        raise NotImplementedError()

    @property
    def open(self) -> np.ndarray:
        raise NotImplementedError()

    @property
    def close(self) -> np.ndarray:
        raise NotImplementedError()

    @property
    def high(self) -> np.ndarray:
        raise NotImplementedError()

    @property
    def low(self) -> np.ndarray:
        raise NotImplementedError()

    @property
    def volume(self) -> np.ndarray:
        raise NotImplementedError()


class Strategy:
    def tick(self, ticker: Ticker, broker: Broker):
        raise NotImplementedError()


class Conductor:
    def run(self):
        raise NotImplementedError()
