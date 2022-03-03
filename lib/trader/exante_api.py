import logging
from typing import Any
from xnt.http_api import HTTPApi, AuthMethods
from xnt.models.http_api_models import OrderMarketV2, Reject, FeedLevel

API_URI_DEMO="https://api-demo.exante.eu"
API_URI_LIVE="https://api-live.exante.eu"


class ExanteRejectError(Exception):
    def __init__(self, reject: Reject):
        super().__init__(f"[{reject.group}] {reject.message}")



class Exante:
    def __init__(self, appid: str, clientid: str, sharedkey: str,  accountid: str, demo: bool=False) -> None:
        self._api = HTTPApi(auth=AuthMethods.JWT, appid=appid, clientid=clientid, sharedkey=sharedkey, ttl=86400, url=API_URI_DEMO if demo else API_URI_LIVE, log_level=logging.WARNING)
        self._accountid = accountid

    def get_account_summary(self):
        return self._api.get_account_summary(account=self._accountid, currency="USD")

    def get_last_quote(self, sym: str):
        last_quote = self._api.get_last_quote(sym, level=FeedLevel.BEST_PRICE)
        return { 'bid': last_quote[0].bid[0].value, 'ask': last_quote[0].ask[0].value }

    def get_min_qty(self, sym: str) -> float:
        return self._api.get_symbol_spec(sym).lot_size

    def place_market_order(self, sym: str, side: str, size: float, duration: str) -> str:
        result = self._api.place_order(OrderMarketV2(account_id=self._accountid, instrument=sym, side=side, quantity=size, duration=duration))
        result = result[0]
        if isinstance(result, Reject):
            raise ExanteRejectError(result)
        return result.id_

    def get_order(self, order_id: str) -> Any:
        return self._api.get_order(order_id)

    def cancel_order(self, order_id: str) -> None:
        return self._api.cancel_order(order_id)

    def is_valid_symbol(self, sym: str) -> bool:
        log_level = self._api.logger.level          # save current log level
        self._api.logger.setLevel(logging.CRITICAL) # prevent 404 response spam on failed get_symbol
        r = self._api.get_symbol(sym) is not None
        self._api.logger.setLevel(log_level)        # restore saved log level
        return r