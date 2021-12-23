import argparse, time, yaml
from pandas import DataFrame

from lib.common.msg import *
from lib.trader import api_keys_config
from lib.trader import poloniex_api


conf = yaml.safe_load(open('config/poloniex_lending.yml', 'r'))


def aprp_to_dpr(x):
    return x / 365 / 100

def dpr_to_aprp(x):
    return x * 365 * 100

class Client:
    def __init__(self):
        cfg = api_keys_config.ApiKeysConfig()
        self._api = poloniex_api.Poloniex(cfg.get_poloniex_ks()[0], cfg.get_poloniex_ks()[1])
        self._loan_offer_id = 0
        self._loan_offer_expiration = 0
        self._loan_offer_cooldown = 0

    def get_available_balance_lending(self):
        """ unused lend USDT balance"""
        r = self._api.returnAvailableAccountBalances(account="lending")["lending"]
        qty = float(r['USDT' ]) if 'USDT' in r else 0
        return qty

    def get_APR(self):
        """  current lend rates """
        r = self._api.returnLoanOrders("USDT")['offers']
        df = DataFrame.from_dict(r,dtype=float)
        max_r = dpr_to_aprp(df['rate'][:3].max())
        min_r = dpr_to_aprp(df['rate'][:3].min())
        return min_r,max_r

    def create_loan_offer(self, rate: float):
        if self._loan_offer_id and (time.time() > self._loan_offer_expiration):
            cancel_result = self._api.cancelLoanOffer(self._loan_offer_id)
            if cancel_result['success']:
                print(f"canceled an existing offer")
                self._loan_offer_id = 0
                self._loan_offer_expiration = 0
                self._loan_offer_cooldown = 0

        if time.time() > self._loan_offer_cooldown:
            lot_size = min(self.get_available_balance_lending(), conf['lot_size'])
            create_result = self._api.createLoanOffer('USDT', lot_size, 2, False, rate)
            if 'orderID' in create_result:
                print(f"created an offer at {dpr_to_aprp(rate):.2f}%")
                self._loan_offer_id = create_result['orderID']
                self._loan_offer_expiration = time.time() + conf['offer_expiration']
                self._loan_offer_cooldown = time.time() + conf['offer_cooldown']


def status():
    cl = Client()

    while True:
        unused_balance = cl.get_available_balance_lending()        
        min_r,max_r = cl.get_APR()

        print(f"{unused_balance:.0f} USDT not on orders, current APR {min_r:.2f}% to {max_r:.2f}%")

        if unused_balance >= 50:
            test_apr = max_r
            if test_apr >= conf['min_apr']:
                cl.create_loan_offer(aprp_to_dpr(test_apr))

        time.sleep(conf['delay'])

def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--check',action='store_const', const='True', help='check unused lending balance')
    # args = parser.parse_args()

    status()

if __name__ == '__main__':
    main()
