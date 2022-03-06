import time
from lib.common.id_ticker_map import get_id_sym
from lib.trader.trader import Trader
from lib.common.msg import info, warn

import kucoin.client as kucl


class KucoinTrader(Trader):

    @staticmethod
    def handles_sym(asset_id: str) -> bool:
        return True

    def __init__(self, asset_id: str, api_key: str, secret: str, passphrase: str):
        self._symbol = get_id_sym(asset_id) + "-USDT"
        self._market_api = kucl.Market(url="https://api.kucoin.com")
        self._trade_api = kucl.Trade(key=api_key, secret=secret, passphrase=passphrase, is_sandbox=False, url="")
        self._user_api = kucl.User(key=api_key, secret=secret, passphrase=passphrase, is_sandbox=False, url="")
        self._symbol_list = None

    def buy_market(self, qty: float, qty_in_usd: bool) -> tuple[float,float]:
        self._check_kcs_balance()
        parms ={}
        if qty_in_usd:
            parms['funds'] = qty # amount in quote currency
        else:
            parms['size'] = qty # amount in base currency
        return self._finalize_order(self._trade_api.create_market_margin_order(symbol=self._symbol, side="buy", **parms)['orderId'])

    def sell_market(self, qty_tokens: float) -> tuple[float,float]:
        self._check_kcs_balance()
        return self._finalize_order(self._trade_api.create_market_margin_order(symbol=self._symbol, side="sell", size=qty_tokens)['orderId'])

    def _finalize_order(self, order_id: str) -> tuple[float,float]:
        fill_qty = 0
        fill_price = 0
        for _ in range(10):
            r = self._trade_api.get_order_details (order_id)
            if r['isActive'] == False:
                fill_qty = float(r['dealSize'])
                fill_price = float(r['dealFunds']) / fill_qty
                break
        return fill_price, fill_qty,

    def _check_kcs_balance(self):
        def get_kcs_balance():
            account_list = self._user_api.get_account_list(currency="KCS", account_type="main")
            return float(account_list[0]['available'])

        if get_kcs_balance() < 0.1:
            add_qty = 1
            info(f"kucoin_trader: buying {add_qty:.1f} KCS")
            self._trade_api.create_market_margin_order(symbol="KCS-USDT", side="buy", size=add_qty)
            time.sleep(1)
            self._user_api.inner_transfer(currency="KCS", from_payer="margin", to_payee="main", amount=add_qty)
            new_qty = get_kcs_balance()
            if new_qty < add_qty:
                warn("kucoin_trader: failed to buy KCS")
