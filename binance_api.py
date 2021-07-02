import hashlib
import hmac
import random
import time
from urllib.parse import urlencode, urljoin

import requests

BINANCE_API_ENDPOINTS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com"
]


def get_api_endpoint():
    return random.choice(BINANCE_API_ENDPOINTS)


class BinanceQueryError(Exception):
    def __init__(self, status_code: int = 0, data: str = ""):
        self.status_code = status_code
        if data:
            self.code = data['code']
            self.msg = data['msg']
        else:
            self.code = None
            self.msg = None
        message = f"{status_code} [{self.code}] {self.msg}"

        super().__init__(message)


class Binance:
    def __init__(self, api_key: str, secret: str) -> None:
        self.api_key = str(api_key)
        self.secret = str(secret)


    def _api_query_public(self, command: str, data: dict = {}) -> dict:
        url = urljoin(get_api_endpoint(), command)
        resp = requests.get(url, params=data)
        return resp.json()


    def _api_query_private(self, operation: callable, command: str, data: dict = {}) -> dict:
        url = urljoin(get_api_endpoint(), command)

        headers = {'X-MBX-APIKEY': self.api_key}

        data['timestamp'] = int(time.time() * 1000)
        data['recvWindow'] = 5000
        query_string = urlencode(data)
        signature = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        data['signature'] = signature

        resp = operation(url, headers=headers, params=data)

        if resp.status_code != 200:
            raise BinanceQueryError(status_code=resp.status_code, data=resp.json())

        return resp.json()


    def get_orderbook(self, symbol: str) -> dict:
        return self._api_query_public("/api/v3/depth", {'symbol': symbol })


    def buy_market(self, symbol: str, quantity: float) -> dict:
        params = {
            'symbol': symbol,
            'side': "BUY",
            'type': "MARKET",
            'quantity': quantity
        }
        return self._api_query_private(requests.post, "/api/v3/order", params)
