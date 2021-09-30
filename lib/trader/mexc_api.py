import hmac, time, requests
from urllib.parse import urlencode
from typing import Optional, Dict, Any

class MexcQueryError(Exception):
    def __init__(self, status_code: int, data: dict):
        super().__init__(f"{status_code} [{data['code']}] {data['msg']}")



class Mexc:
    API_URI = "https://www.mexc.com"

    def __init__(self, api_key: str, secret: str) -> None:
        self._api_key = api_key
        self._secret = secret
        self._session = requests.Session()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = requests.Request(method, Mexc.API_URI + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: requests.Request) -> None:
        request.headers['ApiKey'] = self._api_key
        timestamp = str(int(time.time())*1000)
        request.headers['Request-Time'] = str(timestamp)
        request.headers['Recv-Window'] = str(5000)
        prepared = request.prepare()
        signature_payload = f"{self._api_key}{timestamp}".encode('utf-8')
        if request.params:
            signature_payload += urlencode(request.params).encode('utf-8')
        if prepared.body:
            signature_payload += prepared.body
        request.headers['Signature'] = hmac.new(self._secret.encode('utf-8'), signature_payload, 'sha256').hexdigest()

    def _process_response(self, response: requests.Response) -> Any:
        if response.status_code != 200:
            raise MexcQueryError(status_code=response.status_code, data=response.json())
        return response.json()['data']

    def get_ticker(self, symbol: str) -> dict:
        return self._get("/open/api/v2/market/ticker", {
            'symbol': symbol,
        })[0]

    def place_order(self, symbol: str, price: float, qty: float, trade_type: str, order_type: str) -> str:
        return self._post("/open/api/v2/order/place", {
            'symbol': symbol,
            'price': price,
            'quantity': qty,
            'trade_type': trade_type,
            'order_type': order_type,
        })

    def query_order(self, symbol: str, order_id: str) -> Dict:
        # Attention:
        # Keys must be in alphabetical order otherwise signature verification fails.
        # This restriction applies only to GET requests.
        return self._get("/open/api/v2/order/query", {
            'order_ids': order_id,
            'symbol': symbol,
        })[0]
    
    def get_balances(self) -> Dict:
        return self._get("/open/api/v2/account/info")
