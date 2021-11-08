from abc import abstractmethod
from typing import Tuple

class Trader(object):
    @abstractmethod
    def buy_market(self, qty: float, qty_in_usd: bool) -> Tuple[float,float]:
        """returns [average fill price, filled qty in tokens]"""

    @abstractmethod
    def sell_market(self, qty_tokens: float) -> Tuple[float,float]:
        """ [average fill price, filled qty in tokens] """
