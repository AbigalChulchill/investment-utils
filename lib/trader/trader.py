from abc import abstractmethod
from lib.common.orderbook import FillPriceEstimate


class Trader(object):
    @abstractmethod
    def buy_market(self, qty: float, qty_in_usd: bool) -> tuple[float,float]:
        """ returns [average fill price, filled qty in tokens]"""

    @abstractmethod
    def sell_market(self, qty_tokens: float) -> tuple[float,float]:
        """ returns [average fill price, filled qty in tokens] """

    @abstractmethod
    def sell_limit(self, qty_tokens: float, limit_price: float, auto_top_up_commission_tokens: bool = False) -> tuple[float,float]:
        """ 
        Create a limit order for selling
        Args:
            qty_tokens      qty to sell
            limit_price     limit price
            auto_top_up_commission_tokens   if true check that there are enough commission tokens available and buy more if not
        Return:
            [average fill price, filled qty in tokens]
        """

    @abstractmethod
    def estimate_fill_price(self, qty: float, side: str) -> FillPriceEstimate:
        """
        Estimate fill price for buying or selling qty amount of the instrument
        Args:
            qty     amount of tokens or shares of instrument
            side    buy or sell
        Return:
            estimated fill price
        """

    @abstractmethod
    def get_available_qty(self) -> float:
        """get available qty of token"""