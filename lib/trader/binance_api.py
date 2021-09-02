import hashlib, hmac, time, random, requests
from typing import Optional, Dict, Any

BINANCE_API_ENDPOINTS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com"
]


def get_api_endpoint():
    return random.choice(BINANCE_API_ENDPOINTS)



class Binance:
    def __init__(self) -> None:
        self._session = requests.Session()

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = requests.Request(method, get_api_endpoint() + path, **kwargs)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _process_response(self, response: requests.Response) -> Any:
        response.raise_for_status()
        return response.json()

    def get_orderbook(self, pair: str) -> dict:
        return self._get("/api/v3/depth", {'symbol': pair })

    def get_current_price(self, pair: str) -> dict:
        return float(self._get("/api/v3/avgPrice", {'symbol': pair})['price'])

    def get_24h_change_percent(self, pair: str) -> dict:
        return float(self._get("/api/v3/ticker/24hr", {'symbol': pair})['priceChangePercent'])


    def get_candles(self, pair: str, interval: str, ts_start: int=None, ts_end: int=None, limit=None) -> dict:
        params={
            'symbol':      pair,
            'interval':    interval,
        }
        if ts_start:
            params['startTime'] = ts_start
        if ts_end:
            params['endTime'] = ts_end
        if limit:
            params['limit'] = limit
        klines = self._get("/api/v3/klines", params)
        candles = [ {'timestamp': x[0], 'open': x[1] , 'high': x[2], 'low': x[3], 'close': x[4], } for x in klines]
        return candles

