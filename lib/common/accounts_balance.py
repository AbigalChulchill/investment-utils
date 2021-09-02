from ..trader.poloniex_api import Poloniex
from ..trader.ftx_api import Ftx
from ..trader.okex_api import Okex
from ..trader.bitrue_api import Bitrue

from ..trader.api_keys_config import ApiKeysConfig
from typing import Dict

def roundx(x: float):
    return round(x, 1)

def get_poloniex(api: Poloniex) -> float:
    return roundx(float(api.returnBalances()['USDT']))

def get_ftx(api: Ftx) -> float:
    balances = api.get_balances()
    free = [x['usdValue'] for x in balances if x['coin'] == "USD"]
    return roundx(float(free[0]))

def get_okex(api: Okex) -> float:
    balances = api.get_balances()
    free = [x['eqUsd'] for x in balances if x['ccy'] == "USDT"]
    return roundx(float(free[0]))

def get_bitrue(api: Bitrue) -> float:
    balances = api.get_balances()
    free = [x['free'] for x in balances if x['asset'] == "usdt"]
    return roundx(float(free[0]))

def get_available_usd_balances_dca() -> Dict[str,float]:
    cfg = ApiKeysConfig()
    return [
        {'exchange': 'Poloniex',  'USD': get_poloniex(  Poloniex(   cfg.get_poloniex_ks()[0],   cfg.get_poloniex_ks()[1]  ))},
        {'exchange': 'FTX',       'USD': get_ftx(       Ftx(        cfg.get_ftx_ks()[0],        cfg.get_ftx_ks()[1],        cfg.get_ftx_subaccount_dca()  ))},
        {'exchange': 'Okex',      'USD': get_okex(      Okex(       cfg.get_okex_ksp()[0],      cfg.get_okex_ksp()[1],      cfg.get_okex_ksp()[2]  ))},
        {'exchange': 'Bitrue',    'USD': get_bitrue(    Bitrue(     cfg.get_bitrue_ks()[0],     cfg.get_bitrue_ks()[1]  ))},
    ]

