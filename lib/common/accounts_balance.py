from ..trader.poloniex_api import Poloniex
from ..trader.ftx_api import Ftx
from ..trader.okex_api import Okex
from ..trader.bitrue_api import Bitrue
from ..trader.mexc_api import Mexc

from ..trader.api_keys_config import ApiKeysConfig
from typing import Dict

def roundx(x: float):
    return round(x, 2)

def round_qty(x: float):
    return round(x, 3)

def get_poloniex(api: Poloniex) -> float:
    return roundx(float(api.returnBalances()['USDT']))

def get_poloniex_fee_token(api: Poloniex) -> float:
    return round_qty(float(api.returnBalances()['TRX']))

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

def get_mexc(api: Mexc) -> float:
    balances = api.get_balances()
    return roundx(float(balances['USDT']['available'])) if 'USDT' in balances.keys() else 0

def get_mexc_fee_token(api: Mexc) -> float:
    balances = api.get_balances()
    return round_qty(float(balances['MX']['available'])) if 'MX' in balances.keys() else 0

def get_available_usd_balances_dca() -> Dict[str,float]:
    cfg = ApiKeysConfig()
    poloniex_api = Poloniex(cfg.get_poloniex_ks()[0], cfg.get_poloniex_ks()[1])
    ftx_api = Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], cfg.get_ftx_subaccount_dca())
    okex_api = Okex(cfg.get_okex_ksp()[0], cfg.get_okex_ksp()[1], cfg.get_okex_ksp()[2])
    mexc_api = Mexc(cfg.get_mexc_ks()[0], cfg.get_mexc_ks()[1])
    return [
        {'exchange': 'Poloniex',  'USD': get_poloniex(poloniex_api),  'fee token qty': get_poloniex_fee_token(poloniex_api)},
        {'exchange': 'FTX',       'USD': get_ftx(ftx_api), 'fee token qty': 0},
        {'exchange': 'Okex',      'USD': get_okex(okex_api), 'fee token qty': 0},
        {'exchange': 'MEXC',      'USD': get_mexc(mexc_api), 'fee token qty': get_mexc_fee_token(mexc_api)},
    ]

