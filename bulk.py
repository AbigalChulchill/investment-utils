import argparse

from lib.trader import api_keys_config
from lib.trader import ftx_api


class Client:
    def __init__(self, subaccount: str):
        cfg = api_keys_config.ApiKeysConfig()
        self._api = ftx_api.Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], subaccount)

    def get_account(self):
        return self._api.get_account_information()

    def get_balances(self):
        return self._api.get_balances()

    def get_ticker(self, market: str):
        return self._api.get_ticker(market)

    def place_limit_order(self, market: str, side: str, qty: float, limit_price: float):
        self._api.place_order(market, side, limit_price, "limit", qty)

    def cancel_all_orders(self, market: str):
        self._api.cancel_all_orders(market)


class App:
    def __init__(self, subaccount: str):
        self.cl = Client(subaccount)

    def create_orders(self, market: str, side: str, total_value: float, lots: int, min_price: float, max_price: float, scale: float, rounding: bool, dry: bool):
        assert lots > 0
        assert total_value > 0
        assert min_price > 0
        assert max_price > 0
        assert scale >= 1
        avg_price = (max_price + min_price) / 2
        qty = total_value / avg_price
        step = (max_price - min_price) / (lots - 1)

        lots_value = lambda lots: sum([x[0]*x[1] for x in lots])

        # fitting
        base_lot_qty = qty / lots
        orders = []
        while True:
            lot_qty = base_lot_qty

            orders = []
            if side == "sell":
                price = min_price
                for i in range(lots):
                    orders.append([price,lot_qty])
                    price += step
                    lot_qty *= scale
            else:
                price = max_price
                for i in range(lots):
                    orders.append([price,lot_qty])
                    price -= step
                    lot_qty *= scale
            if round(lots_value(orders)) <= total_value:
                break
            base_lot_qty *= 0.99

        if rounding:
            orders = list( map(lambda o: [round(o[0],1),round(o[1],1)], orders ))

        for i in range(len(orders)):
            price,lot_qty = orders[i]
            print(f"[{i+1:2}] add {side} order limit={price:.6} qty={lot_qty:.6}")
            if not dry:
                self.cl.place_limit_order(market, side, lot_qty, price)
        print(f"combined value of all orders: {round(lots_value(orders))} USD")


    def cancel_orders(self, market: str):
        self.cl.cancel_all_orders(market)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subaccount', type=str, default="Trade", help='Subaccount name')
    parser.add_argument('--market', type=str,  help='Market symbol')
    parser.add_argument('--buy', action='store_const', const='True',  help='Buy limit order')
    parser.add_argument('--sell', action='store_const', const='True',  help='Sell limit order')
    parser.add_argument('--value', type=float,  help='Total USD value of the orders')
    parser.add_argument('--min', type=float,  help='Min price of the range')
    parser.add_argument('--max', type=float,  help='Max price of the range')
    parser.add_argument('--lots', type=int,  help='Number of orders')
    parser.add_argument('--scale', type=float, default=1, help='qty factor for every next lot such as lot_qty(i+1) = lot_qty(i) * scale')
    parser.add_argument('--round', action='store_const', const='True',  help='Round price and size values. This step is unnecessary but helps if entering orders manually.')
    parser.add_argument('--dry', action='store_const', const='True',  help='Do not do anythng, only print')
    parser.add_argument('--cancel-all-orders', action='store_const', const='True',  help='Cancel all orders')
    args = parser.parse_args()

    app = App(args.subaccount)

    if args.buy or args.sell:
        if args.buy and args.sell:
            raise argparse.ArgumentError("specify either --buy or --sell, not both")
        app.create_orders(
            side=["buy","sell"][args.sell is not None],
            market=args.market,
            total_value=args.value,
            lots=args.lots,
            min_price=args.min,
            max_price=args.max,
            scale=args.scale,
            rounding=args.round,
            dry=args.dry)
    elif args.cancel_all_orders:
        app.cancel_orders(market=args.market)


if __name__ == '__main__':
    main()
