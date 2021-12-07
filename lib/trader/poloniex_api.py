import hashlib, hmac, time, urllib, requests
from lib.common.convert import timeframe_to_interval_ms


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
        self._api_key = api_key
        self._secret = secret

    def _post(self, command: str, data: dict={}) -> dict:
        post_data = {
            "command": command,
            "nonce": int(time.time() * 1000),
            **data
        }
        post_data_quote = urllib.parse.urlencode(post_data)
        sign = hmac.new(str.encode(self._secret, "utf-8"), str.encode(post_data_quote, "utf-8"), hashlib.sha512).hexdigest()
        headers = {
            "Sign": sign,
            "Key": self._api_key
        }
        return self._check_resp(requests.post(POLONIEX_PRIVATE_API, data=post_data, headers=headers))

    def _get(self, command: str, data: dict={}) -> dict:
        params = {
            "command": command,
            **data
        }
        return self._check_resp(requests.get(POLONIEX_PUBLIC_API, params=params))

    def _check_resp(self, resp: requests.Response) -> dict:
        if resp.status_code != 200:
            raise PoloniexQueryError(status_code=resp.status_code, data=resp.json())
        return resp.json()

    def returnTicker(self, currencyPair: str) -> float:
        '''
        https://docs.poloniex.com/#returnticker
        '''
        data = self._get("returnTicker")
        return float(data.get(currencyPair, {})["last"])

    def return24hVolume(self) -> dict:
        '''
        # https://docs.poloniex.com/#return24hvolume
        '''
        return self._get("return24hVolume")

    def returnOrderBook(self, currencyPair: str) -> dict:
        '''
        https://docs.poloniex.com/#returnorderbook
        '''
        ob = self._get("returnOrderBook", {"currencyPair": currencyPair,"depth": 20})
        to_float_lists = lambda ob:list(map(lambda e: [float(e[0]), float(e[1])] , ob))
        ob['bids'] = to_float_lists(ob['bids'])
        ob['asks'] = to_float_lists(ob['asks'])
        return ob

    def returnMarketTradeHistory(self, currencyPair: str) -> dict:
        '''
        https://docs.poloniex.com/#returntradehistory-public
        '''
        return self._get("returnTradeHistory", {"currencyPair": currencyPair})

    def returnChartData(self, currencyPair: str, period: str, ts_start: int, ts_end: int) -> dict:
        '''
        Returns candlestick chart data. Required GET parameters are "currencyPair", "period"
        (candlestick period in seconds; valid values are 300, 900, 1800, 7200, 14400, and 86400),
        "start", and "end". "Start" and "end" are given in UNIX timestamp format and used to specify
        the date range for the data returned.

        Fields include:
        currencyPair	A string that defines the market, "USDT_BTC" for example.
        period	        Candlestick period in seconds. Valid values are 300, 900, 1800, 7200, 14400, and 86400.
        start	        The start of the window in seconds since the unix epoch.
        end	            The end of the window in seconds since the unix epoch.

        https://docs.poloniex.com/#returnchartdata
        '''
        return self._get("returnChartData", {
            "currencyPair": currencyPair,
            "period": timeframe_to_interval_ms[period] / 1000,
            "start": ts_start,
            "end": ts_end,
        })

    def returnBalances(self) -> dict:
        '''
        Returns all of your balances available for trade after having deducted all open orders.
        { '1CR': '0.00000000', ABY: '0.00000000', ...}
        https://docs.poloniex.com/#returnbalances
        '''
        return self._post("returnBalances")

    def returnOpenOrders(self, currencyPair: str) -> dict:
        '''
        Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_ETH".
        Set "currencyPair" to "all" to return open orders for all markets.
        https://docs.poloniex.com/#returnopenorders
        '''
        return self._post("returnOpenOrders", {"currencyPair": currencyPair})

    def returnTradeHistory(self, currencyPair: str) -> dict:
        '''
        Returns your trade history for a given market, specified by the "currencyPair" POST parameter.
        You may specify "all" as the currencyPair to receive your trade history for all markets.
        https://docs.poloniex.com/#returntradehistory-private
        '''
        return self._post("returnTradeHistory", {"currencyPair": currencyPair})

    def buy(self, currencyPair: str, rate: float, amount: float, timeInForce: dict[str, bool]) -> dict:
        '''
        Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        If successful, the method will return the order number.
        https://docs.poloniex.com/#buy
        '''
        params = {"currencyPair": currencyPair, "rate": rate, "amount": amount}
        for mode, status in timeInForce.items():
            params[mode] = int(status)
        return self._post("buy", params)

    def sell(self, currencyPair: str, rate: float, amount: float, timeInForce: dict[str, bool]) -> dict:
        '''
        Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        If successful, the method will return the order number.
        https://docs.poloniex.com/#sell
        '''
        params = {"currencyPair": currencyPair, "rate": rate, "amount": amount}
        for mode, status in timeInForce.items():
            params[mode] = int(status)
        return self._post("sell", params)

    def cancelOrder(self, currencyPair: str, orderNumber: int) -> dict:
        '''
        Cancels an order you have placed in a given market. Requires exactly one of "orderNumber" or "clientOrderId" POST parameters.
        If successful, the method will return a success of 1.
        https://docs.poloniex.com/#cancelorder
        '''
        return self._post("cancelOrder", {"currencyPair": currencyPair, "orderNumber": orderNumber})

    def withdraw(self, currency: str, amount: float, address: str) -> dict:
        '''
        Immediately places a withdrawal for a given currency, with no email confirmation.
        In order to use this method, withdrawal privilege must be enabled for your API key.
        Required POST parameters are "currency", "amount", and "address".

        For withdrawals which support payment IDs, (such as XMR) you may optionally specify a "paymentId" parameter.

        For currencies where there are multiple networks to choose from (like USDT or BTC), you can specify the chain
        by setting the "currency" parameter to be a multiChain currency name, like USDTTRON, USDTETH, or BTCTRON.
        You can get information on these currencies, like fees or if they"re disabled, by adding
        the "includeMultiChainCurrencies" optional parameter to the returnCurrencies endpoint.
        The previous method of choosing a network using the optional "currencyToWithdrawAs" parameter will continue
        to function as it used to, but is no longer recommended.

        https://docs.poloniex.com/#withdraw
        '''
        return self._post("withdraw", {
            "currency": currency,
            "amount": amount,
            "address": address
            })

    def returnDepositsWithdrawals(self, ts_start: int, ts_end: int) -> dict:
        '''
        Returns your adjustment, deposit, and withdrawal history within a range window,
        specified by the "start" and "end" POST parameters, both of which should be given as UNIX timestamps.
        Note that only adjustments intended to be shown in the UI will be returned

        https://docs.poloniex.com/#returndepositswithdrawals
        '''
        return self._post("returnDepositsWithdrawals", {
            "start": ts_start,
            "end": ts_end,
            })
