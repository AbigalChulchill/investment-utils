import argparse, time

from lib.trader import api_keys_config
from lib.trader import ftx_api


class Client:
    def __init__(self):
        cfg = api_keys_config.ApiKeysConfig()
        self._api = ftx_api.Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], cfg.get_ftx_subaccount_trade())

    def get_account(self):
        return self._api.get_account_information()

    def get_balances(self):
        return self._api.get_balances()

    def get_ticker(self, market: str):
        return self._api.get_ticker(market)

    def place_limit_order(self, market: str, side: str, qty: float, limit_price: float):
        order_id = self._api.place_order(market, side, limit_price, "limit", qty)
        # for _ in range(10):
        #     time.sleep(0.5)
        #     r = self._api.get_order_status(order_id)
        #     if r['status'] == "closed":
        #         break

    def cancel_all_orders(self, market: str):
        self._api.cancel_all_orders(market)


def create_orders(market: str, side: str, qty: float, lots: int, min_price: float, max_price: float, dry: bool):
    cl = Client()
    
    lots = max(1, lots)
    lot_qty = round(qty / lots,3)
    value = 0

    if min_price and max_price:
        price = min_price
        step = round((max_price - min_price) / (lots-1))
        for i in range(lots):
            value += price * lot_qty
            print(f"[{i+1:2}] add {side} order limit={price} qty={lot_qty}")
            if not dry:
                cl.place_limit_order(market, side, lot_qty, price)
            price += step
        print(f"combined value of all orders: ${round(value)}")


def cancel_orders(market: str):
    cl = Client()
    cl.cancel_all_orders(market)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--market', type=str,  help='Market symbol')
    parser.add_argument('--buy', action='store_const', const='True',  help='Buy limit order')
    parser.add_argument('--sell', action='store_const', const='True',  help='Sell limit order')
    parser.add_argument('--qty', type=float,  help='Total qty')
    parser.add_argument('--min', type=float,  help='Min price of the range')
    parser.add_argument('--max', type=float,  help='Max price of the range')
    parser.add_argument('--lots', type=int,  help='Lots count')
    parser.add_argument('--cancel-all-orders', action='store_const', const='True',  help='Cancel all orders')
    parser.add_argument('--dry', action='store_const', const='True',  help='Do not do anythng, only print')
    args = parser.parse_args()

    if args.buy or args.sell:
        if args.buy and args.sell:
            raise argparse.ArgumentError("specify either --buy or --sell, not both")
        create_orders(side=["buy","sell"][args.sell is not None], market=args.market, qty=args.qty, lots=args.lots, min_price=args.min, max_price=args.max, dry=args.dry)
    elif args.cancel_all_orders:
        cancel_orders(market=args.market)


if __name__ == '__main__':
    main()
