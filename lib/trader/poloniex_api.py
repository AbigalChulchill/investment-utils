import hashlib, hmac, time, urllib, requests
from lib.common.convert import timeframe_to_interval_ms
from typing import Optional


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
        self._session = requests.Session()


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
        return self._check_resp(self._session.post(POLONIEX_PRIVATE_API, data=post_data, headers=headers))

    def _get(self, command: str, data: dict={}) -> dict:
        params = {
            "command": command,
            **data
        }
        return self._check_resp(self._session.get(POLONIEX_PUBLIC_API, params=params))

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

    def returnCompleteBalances(self) -> dict:
        '''
        Returns all of your balances, including available balance, balance on orders,
        and the estimated BTC value of your balance. By default, this call is limited
        to your exchange account; set the "account" POST parameter to "all" to include
        your margin and lending accounts.

        Please note that this call will not return balances for your futures account.
        Please refer to https://futures-docs.poloniex.com/ for information on how to access your futures balance.
        { 
            "1CR":
            {"available":"0.00000000",
                "onOrders":"0.00000000",
                "btcValue":"0.00000000"},
            "ABY":
            {"available":"0.00000000",
                "onOrders":"0.00000000",
                "btcValue":"0.00000000"},
            ...
            }
        https://docs.poloniex.com/#returncompletebalances
        '''
        return self._post("returnCompleteBalances", {"account": "all"})


    def returnAvailableAccountBalances(self, account: Optional[str]) -> dict:
        '''
        Returns your balances sorted by account. You may optionally specify the "account" POST parameter
        if you wish to fetch only the balances of one account. Please note that balances in your margin account
        may not be accessible if you have any open margin positions or orders.

        Please note that this call will not return balances for your futures account.
        Please refer to https://futures-docs.poloniex.com/ for information on how to access your futures balance.
        { "exchange":
            { "BTC": "0.10000000",
                "EOS": "5.18012931",
                "ETC": "3.39980734",
                "SC": "120.00000000",
                "USDC": "23.79999938",
                "ZEC": "0.02380926" },
            "margin":
            { "BTC": "0.50000000" },
            "lending":
            { "BTC": "0.14804126",
                "ETH": "2.69148073",
                "LTC": "1.75862721",
                "XMR": "5.25780982" } }
        https://docs.poloniex.com/#returnavailableaccountbalances
        '''
        params = {}
        if account:
            params['account'] = account
        return self._post("returnAvailableAccountBalances", params)


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

    def returnLoanOrders(self, currency: str) -> dict:
        '''
        Returns the list of loan offers and demands for a given currency, specified by the "currency" GET parameter. 
        {
            "offers": [
                {
                "rate": "0.00001600",
                "amount": "4.29410375",
                "rangeMin": 2,
                "rangeMax": 2
                },
                {
                "rate": "0.00001694",
                "amount": "0.06896614",
                "rangeMin": 2,
                "rangeMax": 2
                },
                ...

            ],
            "demands": [
                {
                "rate": "0.00001000",
                "amount": "40.11028911",
                "rangeMin": 2,
                "rangeMax": 60
                },
                ...
            ]
        }

        https://docs.poloniex.com/#returnloanorders
        '''
        return self._get("returnLoanOrders",{'currency':currency})

    def createLoanOffer(self, currency: str, amount: float, duration: int, autoRenew: bool, lendingRate: float) -> dict:
        '''
        Creates a loan offer for a given currency.
        Args:
            currency 	Denotes the currency for this loan offer.
            amount 	    The total amount of currency offered.
            duration 	The maximum duration of this loan in days. (from 2 to 60, inclusive)
            autoRenew 	Denotes if this offer should be reinstated with the same settings after having been taken.
            lendingRate Lending interest rate
        Output Fields:
            success 	Denotes whether a success (1) or a failure (0) of this operation.
            message 	A human-readable message summarizing the activity.
            orderID 	The identification number of the newly created loan offer.

        {   "success": 1,
            "message": "Loan order placed.",
            "orderID": 1002013188 }

        https://docs.poloniex.com/#createloanoffer
        '''
        return self._post("createLoanOffer",{
            'currency':currency,
            'amount': amount,
            'duration': duration,
            'autoRenew': 1 if autoRenew else 0,
            'lendingRate': lendingRate,
            })

    def cancelLoanOffer(self, orderID: int) -> dict:
        '''
        Cancels a loan offer
        Args:
            orderID 	The identification number of the offer to be canceled.
            
        Output Fields:
            success 	Denotes whether a success (1) or a failure (0) of this operation.
            message 	A human-readable message summarizing the activity.
            amount 	    The amount of the offer that was canceled.

        {   "success": 1,
            "message": "Loan offer canceled.",
            "amount": "0.10000000" }

        https://docs.poloniex.com/#cancelloanoffer
        '''
        return self._post("cancelLoanOffer",{
            'orderNumber':orderID,
            })

    def returnOpenLoanOffers(self) -> dict:
        '''
        Returns your open loan offers for each currency.
        Args:
            None
            
        Output Fields:
            id	        The identification number of this offer.
            rate	    Daily lending rate.
            amount	    The total amount offered for this loan.
            duration	The maximum number of days offered for this loan.
            autoRenew	Denotes if this offer will be reinstated with the same settings after having been taken.
            date	    The UTC date at which this loan offer was created.

        { "BTC":
            [ { "id": 1002015083,
                "rate": "0.01500000",
                "amount": "0.10000000",
                "duration": 2,
                "autoRenew": 0,
                "date": "2018-10-26 20:26:46" } ] }

        https://docs.poloniex.com/#returnopenloanoffers
        '''
        return self._post("returnOpenLoanOffers")
