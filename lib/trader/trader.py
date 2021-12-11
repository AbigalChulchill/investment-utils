from abc import abstractmethod
from typing import Tuple
from lib.common.orderbook import FillPriceEstimate


class Trader(object):
    @abstractmethod
    def buy_market(self, qty: float, qty_in_usd: bool) -> Tuple[float,float]:
        """returns [average fill price, filled qty in tokens]"""

    @abstractmethod
    def sell_market(self, qty_tokens: float) -> Tuple[float,float]:
        """ [average fill price, filled qty in tokens] """

    @abstractmethod
    def estimate_fill_price(self, qty: float, side: str) -> FillPriceEstimate:
        """estimate fill price for buying or selling qty amount of the instrument
            Args:
                qty     amount of tokens or shares of instrument
                side    buy or sell
            Return:
                estimated fill price
        """
