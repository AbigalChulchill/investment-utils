from abc import abstractmethod, abstractproperty
from typing import Tuple
import numpy as np
import pandas as pd
from lib.common import pnl

class Broker:
    @abstractmethod
    def buy(self, qty: float)->Tuple[float,float]:
        """returns [value, qty]"""

    @abstractmethod
    def sell(self, qty: float)->Tuple[float,float]:
        """returns [value, qty]"""

    @abstractproperty
    def account_size_usd(self) -> float:
        """returns account size in USD"""

    @abstractproperty
    def account_size_token(self) -> float:
        """returns account size in token"""

    @abstractproperty
    def pnl(self) -> pnl.PnL:
        """returns PnL"""


class Ticker:
    @abstractproperty
    def market_price(self) -> float:
        """returns current market price of instrument"""

    @abstractproperty
    def timestamp(self) -> pd.DatetimeIndex:
        """returns open timestamps of bars"""

    @abstractproperty
    def open(self) -> np.ndarray:
        """returns open values of bars"""

    @abstractproperty
    def close(self) -> np.ndarray:
        """returns close values of bars"""

    @abstractproperty
    def high(self) -> np.ndarray:
        """returns high values of bars"""

    @abstractproperty
    def low(self) -> np.ndarray:
        """returns low values of bars"""

    @abstractproperty
    def volume(self) -> np.ndarray:
        """returns volume values of bars"""


class Strategy:
    @abstractmethod
    def tick(self, ticker: Ticker, broker: Broker):
        """strategy update"""


class Conductor:
    @abstractmethod
    def run(self):
        """conductor logic"""
