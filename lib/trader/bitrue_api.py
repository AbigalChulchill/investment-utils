import hmac, time, requests
from urllib.parse import urlencode
from typing import Optional, Dict, Any

ENDPOINT = "https://www.bitrue.com"


class BitrueQueryError(Exception):
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


class Bitrue:
    def __init__(self, api_key: str, secret: str) -> None:
        self._api_key = api_key
        self._secret = secret
        self._session = requests.Session()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, params=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, params=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = requests.Request(method, ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: requests.Request) -> None:
        request.headers['X-MBX-APIKEY'] = self._api_key
        request.params['timestamp'] = int(time.time() * 1000)
        request.params['recvWindow'] = 5000
        signature_payload = urlencode(request.params).encode('utf-8')
        request.params['signature'] = hmac.new(self._secret.encode('utf-8'), signature_payload, 'sha256').hexdigest()

    def _process_response(self, response: requests.Response) -> Any:
        if response.status_code != 200:
            raise BitrueQueryError(status_code=response.status_code, data=response.json())
        return response.json()

    def get_orderbook(self, symbol: str) -> dict:
        return self._get("/api/v1/depth", {
            'symbol': symbol,
        })

    def new_order(self, symbol: str, side: str, qty: float) -> int:
        return self._post("/api/v1/order", {
            'symbol': symbol,
            'side': side,
            'type': "MARKET",
            'quantity': qty
        })['orderId']

    def query_order(self, symbol: str, order_id: int) -> Dict:
        return self._get("/api/v1/order", {
            'symbol': symbol,
            'orderId': order_id,
        })
    
    def get_balances(self) -> Dict:
        return self._get("/api/v1/account")['balances']
