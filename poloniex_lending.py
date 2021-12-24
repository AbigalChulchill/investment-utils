import argparse, time, yaml
from pandas import DataFrame

from lib.common.msg import *
from lib.trader import api_keys_config
from lib.trader import poloniex_api


conf = yaml.safe_load(open('config/poloniex_lending.yml', 'r'))


def aprp_to_dpr(x: float) -> float:
    return x / 365 / 100

def dpr_to_aprp(x: float) -> float:
    return x * 365 * 100

class Client:
    def __init__(self):
        cfg = api_keys_config.ApiKeysConfig()
        self._api = poloniex_api.Poloniex(cfg.get_poloniex_ks()[0], cfg.get_poloniex_ks()[1])
        self._loan_offer_id = 0
        self._loan_offer_expiration = 0
        self._loan_offer_cooldown = 0

    def get_available_balance_lending(self) -> float:
        """ unused lend USDT balance"""
        r = self._api.returnAvailableAccountBalances(account="lending")["lending"]
        qty = float(r['USDT' ]) if 'USDT' in r else 0
        return qty

    def get_APR(self) -> tuple[float,float]:
        """  current lend rates """
        r = self._api.returnLoanOrders("USDT")['offers']
        df = DataFrame.from_dict(r,dtype=float)
        max_r = dpr_to_aprp(df['rate'][:3].max())
        min_r = dpr_to_aprp(df['rate'][:3].min())
        return min_r,max_r

    def _cancel_offer(self) -> bool:
        """ 
        Return:
            True if offer has been canceled successfully.
            False if offer not existing or if it has been already accepted.
        """
        if self._loan_offer_id:
            cancel_result = self._api.cancelLoanOffer(self._loan_offer_id)
            if 'success' in cancel_result and cancel_result['success']:
                print(f"canceled an existing offer")
                return True
            else:
                return False
            self._loan_offer_id = 0


    def check_expired_loan_offer(self):
        if time.time() > self._loan_offer_expiration:
            self._loan_offer_expiration = 0
            if self._cancel_offer():
                # also reset cooldown if we canceled an open offer
                self._loan_offer_cooldown = 0


    def create_loan_offer(self, rate: float):
        if time.time() > self._loan_offer_cooldown:
            self._cancel_offer()
            self._loan_offer_cooldown = 0


            lot_size = min(self.get_available_balance_lending(), conf['lot_size'])
            create_result = self._api.createLoanOffer('USDT', lot_size, 2, False, rate)
            if 'orderID' in create_result:
                print(f"created an offer at {dpr_to_aprp(rate):.2f}%")
                self._loan_offer_id = create_result['orderID']
                self._loan_offer_expiration = time.time() + conf['offer_expiration']
                self._loan_offer_cooldown = time.time() + conf['offer_cooldown']

    def get_timeout_expiration(self) -> float:
        return self._loan_offer_expiration - time.time()

    def get_timeout_cooldown(self) -> float:
        return self._loan_offer_cooldown - time.time()


def status():
    cl = Client()

    while True:
        cl.check_expired_loan_offer()

        unused_balance = cl.get_available_balance_lending()        
        min_r,max_r = cl.get_APR()

        t_expiration = cl.get_timeout_expiration()
        t_cooldown = cl.get_timeout_cooldown()

        print(f"{unused_balance:.0f} USDT not on orders, current APR {min_r:.2f}% to {max_r:.2f}%", end='')
        if t_expiration > 0:
            print(f", offer expires in {t_expiration/60:.1f} minutes", end='')
        if t_cooldown > 0:
            print(f", cooldown to next offer {t_cooldown/60:.1f} minutes", end='')
        print()

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
