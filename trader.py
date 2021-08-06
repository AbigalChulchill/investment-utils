class Trader(object):

    def buy_market(self, qty_usd: float) -> float:
        #
        # returns [average fill price, filled qty in tokens]
        #
        raise NotImplementedError()

    def sell_market(self, qty_tokens: float) -> float:
        #
        # returns [average fill price, filled qty in tokens]
        #
        raise NotImplementedError()
