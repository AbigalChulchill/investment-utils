# PancakeSwap CAKE staking management

import argparse, yaml, time, datetime
from lib.trader.poloniex_trader import PoloniexTrader
from lib.trader.poloniex_api import Poloniex as PoloniexAPI
from lib.trader.api_keys_config import ApiKeysConfig
from lib.common.msg import err

conf = yaml.safe_load(open('config/pancakeswap.yml', 'r'))


def _create_poloniex_trader(asset_id: str):
    api_key, secret = ApiKeysConfig().get_poloniex_ks()
    return PoloniexTrader(asset_id, api_key, secret)


def _create_poloniex_private_api():
    api_key, secret = ApiKeysConfig().get_poloniex_ks()
    return PoloniexAPI(api_key, secret)


def buy_cake():
    print('buying CAKE...')
    price, qty = _create_poloniex_trader('pancakeswap-token').buy_market(conf['quota'],qty_in_usd=True)
    print(f'exchanged {qty*price:.2f} USD for {qty:.6f} CAKE at rate {price:.6f})')


def transfer_cake():
    api = _create_poloniex_private_api()
    qty_held = float(api.returnBalances()['CAKE'])
    wallet_addr = conf['wallet']
    print(f'moving {qty_held} CAKE to BSC wallet {wallet_addr}')
    withdraw_response = api.withdraw('CAKE', qty_held,  wallet_addr)
    if 'error' in withdraw_response.keys():
        err(withdraw_response['error'])
        return

    print(f'withdrawal request status: {withdraw_response["response"]}')
    withdrawal_id = withdraw_response['withdrawalNumber']
    while True:
        t = datetime.datetime.now().timestamp()
        withdrawals_list = api.returnDepositsWithdrawals(t - 3600, t)['withdrawals']
        # matching_withdrawals = [x for x in withdrawals_list if x['withdrawalNumber'] == withdrawal_id ]
        # if len(matching_withdrawals) > 0: # this may or not be needed...
        #     status = matching_withdrawals[0]['status']
        #     if 'COMPLETE' in status:
        #         print(status)
        #         break
        # else:
        #     warn('cannot find withdrawal by id. Will retry later anyway')
        status = [x for x in withdrawals_list if x['withdrawalNumber'] == withdrawal_id][0]['status']
        if 'COMPLETE' in status:
            print(status)
            break
        print('waiting for withdrawal...')
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--buy-cake',action='store_const', const='True', help='buy daily amount of CAKE')
    parser.add_argument('--move-cake-to-chain', action='store_const', const='True', help='transfer CAKE from exchange to BSC')
    args = parser.parse_args()

    if args.buy_cake:
        buy_cake()
    elif args.move_cake_to_chain:
        transfer_cake()


if __name__ == '__main__':
    main()
