from pandas.core.frame import DataFrame
from ..trader.poloniex_api import Poloniex
from ..trader.ftx_api import Ftx
from ..trader.okex_api import Okex
from ..trader.bitrue_api import Bitrue
from ..trader.mexc_api import Mexc
from ..trader.exante_api import Exante
from kucoin.client import Margin as KucoinMargin
from ..trader.api_keys_config import ApiKeysConfig


def roundx(x: float):
    return round(x, 2)

def round_qty(x: float):
    return round(x, 3)

def get_poloniex(api: Poloniex) -> float:
    bal = api.returnCompleteBalances()['USDT']
    return roundx(float(bal['available']) + float(bal['onOrders'])  )

def get_ftx(api: Ftx) -> dict:
    balances = api.get_balances()
    
    return {
       'available_including_borrow':        roundx(sum([float(x['free']) for x in balances if x['coin'] in ["USD"] ])),
       'available_without_borrow':          roundx(sum([float(x['availableWithoutBorrow']) for x in balances if x['coin'] in ["USD"] ])),
       'borrow':                           -roundx(sum([float(x['spotBorrow']) for x in balances if x['coin'] in ["USD","USDT"] ])),   
    }

def get_kucoin(margin_api: KucoinMargin) -> dict:
    margin_account = [x for x in margin_api.get_margin_account()['accounts'] if x['currency'] == "USDT"][0]   
    return {
       'available_including_borrow':        float(margin_account['availableBalance']),
       'available_without_borrow':          float(margin_account['holdBalance']),
       'borrow':                           -float(margin_account['liability']),
    }

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

def get_exante(api: Exante) -> float:
    account_summary = api.get_account_summary()
    value = [float(x.converted_value) for x in account_summary.currencies if x.code in ["USD","EUR"] ]   
    return roundx(float(value[0]))


def get_available_usd_balances_dca() -> DataFrame:
    cfg = ApiKeysConfig()

    poloniex_data = get_poloniex(Poloniex(*cfg.get_poloniex_ks()))
    ftx_data = get_ftx(Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], cfg.get_ftx_subaccount_dca()))
    okex_data = get_okex(Okex(*cfg.get_okex_ksp()))
    kucoin_data = get_kucoin(KucoinMargin(*cfg.get_kucoin_ksp()))
    mexc_data = get_mexc(Mexc(*cfg.get_mexc_ks()))
    exante_data = get_exante(Exante(*cfg.get_exante()))
    df = DataFrame.from_dict(
        [
            {
                'cex_name':                     'FTX',
                'available_including_borrow':   ftx_data['available_including_borrow'],
                'borrow':                       ftx_data['borrow'],
                'available_without_borrow':     ftx_data['available_without_borrow'],
                'liquid':                       True,
            },
            {
                'cex_name':                     'Kucoin',
                'available_including_borrow':   kucoin_data['available_including_borrow'],
                'borrow':                       kucoin_data['borrow'],
                'available_without_borrow':     kucoin_data['available_without_borrow'],
                'liquid':                       True,
            },

            {'cex_name': 'Poloniex',  'available_including_borrow': poloniex_data,      'borrow': 0,    'available_without_borrow': poloniex_data,  'liquid': True,},
            {'cex_name': 'OKX',       'available_including_borrow': okex_data,          'borrow': 0,    'available_without_borrow': okex_data,      'liquid': True,},
            {'cex_name': 'MEXC',      'available_including_borrow': mexc_data,          'borrow': 0,    'available_without_borrow': mexc_data,      'liquid': True,},
            {'cex_name': 'Exante',    'available_including_borrow': exante_data,        'borrow': 0,    'available_without_borrow': exante_data,    'liquid': False,},
        ]
    )
    return df

