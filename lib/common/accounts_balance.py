from pandas.core.frame import DataFrame
from ..trader.poloniex_api import Poloniex
from ..trader.ftx_api import Ftx
from ..trader.okex_api import Okex
from ..trader.bitrue_api import Bitrue
from ..trader.mexc_api import Mexc

from ..trader.api_keys_config import ApiKeysConfig

def roundx(x: float):
    return round(x, 2)

def round_qty(x: float):
    return round(x, 3)

def get_poloniex(api: Poloniex) -> float:
    bal = api.returnCompleteBalances()['USDT']
    return roundx(float(bal['available']) + float(bal['onOrders'])  )

def get_ftx(api: Ftx) -> float:
    balances = api.get_balances()
    free = [float(x['free']) for x in balances if x['coin'] in ["USD"] ]
    return roundx(sum(free))
def get_ftx_borrowed(api: Ftx) -> float:
    balances = api.get_balances()
    borrowed = [float(x['spotBorrow']) for x in balances if x['coin'] in ["USD","USDT"] ]
    return -roundx(sum(borrowed))

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

def get_available_usd_balances_dca() -> DataFrame:
    cfg = ApiKeysConfig()
    poloniex_api = Poloniex(cfg.get_poloniex_ks()[0], cfg.get_poloniex_ks()[1])
    ftx_api = Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], cfg.get_ftx_subaccount_dca())
    okex_api = Okex(cfg.get_okex_ksp()[0], cfg.get_okex_ksp()[1], cfg.get_okex_ksp()[2])
    mexc_api = Mexc(cfg.get_mexc_ks()[0], cfg.get_mexc_ks()[1])
    df = DataFrame.from_dict(
        [
            {'cex_name': 'Poloniex',  'available': get_poloniex(poloniex_api)},
            {'cex_name': 'FTX',       'available': get_ftx(ftx_api), 'borrowed': get_ftx_borrowed(ftx_api)},
            {'cex_name': 'OKX',       'available': get_okex(okex_api)},
            {'cex_name': 'MEXC',      'available': get_mexc(mexc_api)},
        ]
    )
    return df

