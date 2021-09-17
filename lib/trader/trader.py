from typing import Tuple

class Trader(object):

    def buy_market(self, qty_usd: float) -> Tuple[float,float]:
        #
        # returns [average fill price, filled qty in tokens]
        #
        raise NotImplementedError()

    def sell_market(self, qty_tokens: float) -> Tuple[float,float]:
        #
        # returns [average fill price, filled qty in tokens]
        #
        raise NotImplementedError()
