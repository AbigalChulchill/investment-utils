import hashlib, hmac, time, json, requests, urllib
from typing import Optional, Dict, Any, List


class FtxQueryError(Exception):
    def __init__(self, status_code: int = 0, data: str = ""):
        self.status_code = status_code
        if data:
            self.msg = data['error']
        else:
            self.msg = None
        message = f"{status_code} {self.msg}"

        super().__init__(message)


class FtxPublic:
    API_URI = "https://ftx.com/api"

    def __init__(self) -> None:
        pass

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        response = requests.get(FtxPublic.API_URI + path, params=params)
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise FtxQueryError(status_code=response.status_code, data=response.json())
            return data['result']

    def get_markets(self) -> dict:
        return self._get("/markets")

    def get_candles(self, market: str, resolution_seconds: int, ts_start: int=None, ts_end: int=None) -> dict:
        params={
            'resolution':  resolution_seconds,
            'start_time':  ts_start,
            'end_time':  ts_end,
        }
        candles = self._get(f"/markets/{market}/candles", params)
        return candles



class Ftx:
    API_URI = "https://ftx.com/api"

    def __init__(self, api_key: str, secret: str, subaccount: str = None) -> None:
        self._api_key = api_key
        self._secret = secret
        self._subaccount = subaccount
        self._session = requests.Session()


    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = requests.Request(method, Ftx.API_URI + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: requests.Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._subaccount)

    def _process_response(self, response: requests.Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise FtxQueryError(status_code=response.status_code, data=response.json())
            return data['result']

    def get_ticker(self, market: str) -> float:
        return self._get(f"/markets/{market}")['price']

    def get_min_qty(self, market: str) -> float:
        return self._get(f"/markets/{market}")['sizeIncrement']

    def get_orderbook(self, market: str, depth: int = 20) -> dict:
        return self._get(f"/markets/{market}/orderbook", params={'depth': depth})

    def place_order(self, market: str, side: str, price: float, limit_or_market: str, size: float, reduce_only: bool = False, ioc: bool = False, post_only: bool = False) -> int:
        response = self._post("/orders", {
            "market": market,
            "side": side,
            'price': price,
            'type': limit_or_market,
            'size': size,
            'reduceOnly': reduce_only,
            'ioc': ioc,
            'postOnly': post_only
        })
        return int(response['id'])

    def get_order_status(self, order_id: int) -> dict:
        return self._get(f"/orders/{order_id}")

    def get_account_information(self) -> dict:
        return self._get("/account")

    def get_balances(self) -> dict:
        return self._get("/wallet/balances")

    def get_positions(self) -> dict:
        return self._get("/positions")

    def get_markets(self) -> dict:
        return self._get("/markets")

    def get_future_stats(self, market: str) -> dict:
        return self._get(f"/futures/{market}/stats")

    def get_funding_rates(self) -> dict:
        return self._get("/funding_rates")

    def cancel_all_orders(self, market: str) -> dict:
        return self._delete("/orders", {
            "market": market,
        })