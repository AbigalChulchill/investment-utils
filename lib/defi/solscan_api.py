import requests
from typing import Optional, Any

API_URI = 'https://public-api.solscan.io'

class Solscan:
    def __init__(self, account: str):
        self._account = account
        self._session = requests.Session()

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = requests.Request(method, API_URI + path, **kwargs)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _process_response(self, response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            response.raise_for_status()

    def get_token_qty(self, ticker: str) -> float:
        all_tokens = self._get("/account/tokens",{'account': self._account})
        matching_items = [x for x in all_tokens if 'tokenSymbol' in x and x['tokenSymbol'] == ticker]
        if len(matching_items) > 0:
            return matching_items[0]['tokenAmount']['uiAmount']
        else:
            raise ValueError("token not found")