import yaml
from typing import Tuple

class ApiKeysConfig:
    def __init__(self):
        self._cfg = dict()

        with open('config/keys.yml', 'r') as file:
            self._cfg = yaml.safe_load(file)

    def get_poloniex_ks(self) -> Tuple[str,str]:
        return self._cfg['poloniex']['API_KEY'], self._cfg['poloniex']['SECRET']

    def get_bitrue_ks(self) -> Tuple[str,str]:
        return self._cfg['bitrue']['API_KEY'], self._cfg['bitrue']['SECRET']

    def get_okex_ksp(self) -> Tuple[str,str,str]:
        return self._cfg['okex']['API_KEY'], self._cfg['okex']['SECRET'], self._cfg['okex']['PASS']

    def get_ftx_ks(self) -> Tuple[str,str]:
        return self._cfg['ftx']['API_KEY'], self._cfg['ftx']['SECRET']

    def get_ftx_subaccount_dca(self) -> str:
        return self._cfg['ftx']['SUBACCOUNT_DCA']

    def get_ftx_subaccount_trade(self) -> str:
        return self._cfg['ftx']['SUBACCOUNT_TRADE']
