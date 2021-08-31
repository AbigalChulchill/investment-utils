import hashlib, hmac, time, urllib, requests


POLONIEX_PUBLIC_API = "https://poloniex.com/public"
POLONIEX_PRIVATE_API = "https://poloniex.com/tradingApi"


class PoloniexQueryError(Exception):
    def __init__(self, status_code: int = 0, data: str = ""):
        self.status_code = status_code
        if data:
            self.msg = data['error']
        else:
            self.msg = None
        message = f"{status_code} {self.msg}"

        super().__init__(message)


class Poloniex:
    def __init__(self, api_key: str, secret: str) -> None:
        self.api_key = str(api_key)
        self.secret = str(secret)

    def _api_query(self, api: str, command: str, data: dict = {}) -> dict:
        resp: requests.Response = None

        if api == POLONIEX_PUBLIC_API:
            params = {"command": command, **data}
            resp = requests.get(f"{api}", params=params)

        elif api == POLONIEX_PRIVATE_API:
            post_data = {"command": command, "nonce": int(time.time() * 1000), **data}
            post_data_quote = urllib.parse.urlencode(post_data)

            sign = hmac.new(str.encode(self.secret, "utf-8"), str.encode(post_data_quote, "utf-8"),
                            hashlib.sha512).hexdigest()

            headers = {"Sign": sign, "Key": self.api_key}

            resp = requests.post(f"{api}", data=post_data, headers=headers)
        else:
            assert (True, "Wat?")

        if resp.status_code != 200:
            raise PoloniexQueryError(status_code=resp.status_code, data=resp.json())

        return resp.json()

    def returnTicker(self, currencyPair: str) -> str:
        # https://docs.poloniex.com/#returnticker

        data = self._api_query(POLONIEX_PUBLIC_API, "returnTicker")
        return data.get(currencyPair, {}).get("last")

    def return24hVolume(self) -> dict:
        # https://docs.poloniex.com/#return24hvolume
        return self._api_query(POLONIEX_PUBLIC_API, "return24hVolume")

    def returnOrderBook(self, currencyPair: str) -> dict:
        # https://docs.poloniex.com/#returnorderbook
        params = {"currencyPair": currencyPair}
        return self._api_query(POLONIEX_PUBLIC_API, "returnOrderBook", params)

    def returnMarketTradeHistory(self, currencyPair: str) -> dict:
        # https://docs.poloniex.com/#returntradehistory-public
        params = {"currencyPair": currencyPair}
        return self._api_query(POLONIEX_PUBLIC_API, "returnTradeHistory", params)

    def returnBalances(self) -> dict:
        # Returns all of your balances available for trade after having deducted all open orders.
        # { '1CR': '0.00000000', ABY: '0.00000000', ...}

        # https://docs.poloniex.com/#returnbalances
        return self._api_query(POLONIEX_PRIVATE_API, "returnBalances")

    def returnOpenOrders(self, currencyPair: str) -> dict:
        # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_ETH".
        #  Set "currencyPair" to "all" to return open orders for all markets.

        # https://docs.poloniex.com/#returnopenorders
        params = {"currencyPair": currencyPair}
        return self._api_query(POLONIEX_PRIVATE_API, "returnOpenOrders", params)

    def returnTradeHistory(self, currencyPair: str) -> dict:
        # Returns your trade history for a given market, specified by the "currencyPair" POST parameter.
        # You may specify "all" as the currencyPair to receive your trade history for all markets.

        # https://docs.poloniex.com/#returntradehistory-private
        params = {"currencyPair": currencyPair}
        return self._api_query(POLONIEX_PRIVATE_API, "returnTradeHistory", params)

    def buy(self, currencyPair: str, rate: float, amount: float, timeInForce: dict[str, bool]) -> dict:
        # Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        # If successful, the method will return the order number.

        # https://docs.poloniex.com/#buy
        params = {"currencyPair": currencyPair, "rate": rate, "amount": amount}
        for mode, status in timeInForce.items():
            params[mode] = int(status)

        return self._api_query(POLONIEX_PRIVATE_API, "buy", params)

    def sell(self, currencyPair: str, rate: float, amount: float, timeInForce: dict[str, bool]) -> dict:
        # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        # If successful, the method will return the order number.

        # https://docs.poloniex.com/#sell
        params = {"currencyPair": currencyPair, "rate": rate, "amount": amount}
        for mode, status in timeInForce.items():
            params[mode] = int(status)

        return self._api_query(POLONIEX_PRIVATE_API, "sell", params)

    def cancelOrder(self, currencyPair: str, orderNumber: int) -> dict:
        # Cancels an order you have placed in a given market. Requires exactly one of "orderNumber" or "clientOrderId" POST parameters.
        # If successful, the method will return a success of 1.

        # https://docs.poloniex.com/#cancelorder
        params = {"currencyPair": currencyPair, "orderNumber": orderNumber}
        return self._api_query(POLONIEX_PRIVATE_API, "cancelOrder", params)
