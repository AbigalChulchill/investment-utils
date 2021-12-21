import hmac, datetime, requests, codecs
from typing import Optional, Any


class OkexQueryError(Exception):
    def __init__(self, status_code:int, data: str):
        self.status_code = status_code
        if data:
            self.msg = data
        else:
            self.msg = None
        message = f"{status_code} {self.msg}"

        super().__init__(message)


class Okex:
    API_URI = "https://www.okex.com"

    def __init__(self, api_key: str, secret: str, passphrase: str) -> None:
        self._api_key = api_key
        self._secret = secret
        self._passphrase = passphrase
        self._session = requests.Session()

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = requests.Request(method, Okex.API_URI + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: requests.Request) -> None:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = codecs.encode(hmac.new(self._secret.encode(), signature_payload, "sha256").digest(), "base64").decode().rstrip()
        request.headers['OK-ACCESS-KEY'] = self._api_key
        request.headers['OK-ACCESS-SIGN'] = signature
        request.headers['OK-ACCESS-TIMESTAMP'] = ts
        request.headers['OK-ACCESS-PASSPHRASE'] = self._passphrase

    def _process_response(self, response: requests.Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if int(data['code']) != 0:
                raise OkexQueryError(status_code=response.status_code, data=response.json())
            return data['data']

    def get_ticker(self, market: str ) -> dict:
        return self._get(f"/api/v5/market/ticker", {
            'instId': market,
        })

    def get_orderbook(self, market: str, side: str) -> dict:
        r = self._get("/api/v5/market/books",{
            'instId': market,
            'sz': 20,
        })[0][side]
        #  return only  ( price,volume ), ignore other fields
        return [(float(d[0]),float(d[1])) for d in r]

    def get_min_qty(self, market: str ) -> float:
        return float(self._get(f"/api/v5/public/instruments", {
            'instType': 'SPOT',
            'instId': market,
        })[0]['minSz'])

    def place_order(self, market: str, side: str, size: float) -> int:
        response = self._post("/api/v5/trade/order", {
            'instId': market, #BTC-USD
            'tdMode': "cash",
            'side': side, #buy, sell
            'ordType': "market",
            'sz': size,
            'tgtCcy': "base_ccy",
        })
        return int(response[0]['ordId'])

    def get_order_details(self, market: str, order_id: int) -> dict:
        return self._get("/api/v5/trade/order", {
            'instId': market, #BTC-USD
            'ordId': order_id,
        })[0]

    def get_balances(self) -> dict:
        return self._get("/api/v5/account/balance")[0]['details']
