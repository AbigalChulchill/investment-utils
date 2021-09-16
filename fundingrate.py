import argparse, time
from collections import defaultdict
from termcolor import colored
import pandas as pd

from lib.trader import api_keys_config
from lib.trader import ftx_api

FUTURE_IGNORE=[
    "DMG-PERP",
    "SHIB-PERP",
    "HUM-PERP",
    "CUSDT-PERP",
    "TRYB-PERP",
    "MER-PERP",
    "DENT-PERP",
]

NON_USD_COLLATERAL=[
"1INCH", "AAPL", "AAVE", "ABNB", "ACB","ALPHA", "AMC", "AMD", "AMZN", "APHA","ARKK", "AUD",
"BABA", "BADGER", "BAND", "BAO", "BB", "BCH", "BILI", "BITW", "BNB", "BNT", "BNTX", "BRL", "BRZ", "BTC", "BTMX", "BUSD", "BVOL", "BYND",
"CAD", "CEL", "CGC", "CHF", "COIN", "COMP", "COPE", "CRON", "CUSDT",
"DAI", "DOGE", "ETH", "ETHE", "EUR", "FB", "FIDA", "FTM", "FTT",
"GBP", "GBTC", "GDX", "GDXJ", "GLD", "GLXY", "GME", "GOOGL", "GRT", "HKD", "HOLY", "HOOD", "HT", "HUSD", "HXRO",
"IBVOL", "KIN", "KNC", "LEO", "LINK", "LRC", "LTC", "MATIC", "MKR", "MOB", "MRNA", "MSTR", "NFLX", "NIO", "NOK", "NVDA",
"OKB", "OMG", "USDP", "PAXG", "PENN", "PFE", "PYPL", "RAY", "REN", "RSR", "RUNE",
"SECO", "SGD", "SLV", "SNX", "SOL", "SPY", "SQ", "SRM", "SUSHI", "SXP",
"TLRY", "TOMO", "TRX", "TRY", "TRYB", "TSLA", "TSM", "TUSD", "TWTR",
"UBER", "UNI", "USD", "USDC", "USDT", "USO", "WBTC", "WUSDC", "WUSDT", "XAUT", "XRP", "YFI", "ZAR", "ZM", "ZRX",
]

def convert_symbol_futures_spot(symbol: str):
    return symbol.replace("-PERP", "/USD")


class Client:
    def __init__(self, restrict_non_usd_collateral=False):
        cfg = api_keys_config.ApiKeysConfig()
        self._api = ftx_api.Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], cfg.get_ftx_subaccount_fundingratefarm())
        self._restrict_non_usd_collateral = restrict_non_usd_collateral
        self._markets = None
        self._funding_rates = None
        self._account = None
        self._balances = None

    @property
    def markets(self):
        if self._markets is None:
            self._markets = self._api.get_markets()
        return self._markets

    @property
    def funding_rates(self):
        if self._funding_rates is None:
            self._funding_rates =  self._convert_funding_rates(self._api.get_funding_rates())
        return self._funding_rates

    @property
    def account(self):
        if self._account is None:
            self._account =  self._api.get_account_information()
        return self._account

    @property
    def positions(self):
        if self._account is None:
            self._account =  self._api.get_account_information()
        return self._account['positions']

    @property
    def balances(self):
        if self._balances is None:
            self._balances = self._api.get_balances()
        return self._balances

    def get_orderbook(self, market: str):
        return self._api.get_orderbook(market)

    def get_future_data(self, market: str):
        return self._api.get_future_stats(market)

    def get_ticker(self, market: str):
        return self._api.get_ticker(market)

    def _convert_funding_rates(self, rates_list):
        rates = defaultdict(list)
        for row in rates_list:
            rates[row['future']] .append(row)
        for v in rates.values():
            v.sort(key=lambda x: x['time'],reverse=True)
        futures_data = list()
        for k,v in rates.items():
            if k in FUTURE_IGNORE:
                continue
            if self._restrict_non_usd_collateral and k.replace("-PERP","") not in NON_USD_COLLATERAL:
                continue
            if len([m for m in self.markets if m['name'] ==  convert_symbol_futures_spot(k) ]) == 0:
                continue
            future_data = {
                'future': k
            }
            index = 0
            for timestamp in v:
                future_data[f'rate_{index}'] = timestamp['rate'] * 100
                index += 1
                if index > 2:
                    break
            futures_data.append(future_data)
        return futures_data

    def execute_hedge_order(self, market1: str, side1: str, market2: str, side2: str, size: float):
        order_id1 = self._api.place_order(market1, side1, 0, "market", size)
        order_id2 = self._api.place_order(market2, side2, 0, "market", size)

        for _ in range(10):
            time.sleep(0.5)
            r1 = self._api.get_order_status(order_id1)
            r2 = self._api.get_order_status(order_id2)
            if r1['status'] == "closed" and r2['status'] == "closed":
                break

        self._account = None
        self._balances = None


class App:
    def __init__(self):
        self.cl = Client(restrict_non_usd_collateral=False)

    def list_markets(self):
        cl = self.cl

        arrow_up = colored("↑",color="green",attrs=["bold"])
        arrow_down= colored("↓",color="red",attrs=["bold"])
        df = pd.DataFrame.from_dict(cl.funding_rates)
        print("\nmost positive funding rates " + arrow_up + "\n")
        df_positives = df.sort_values("rate_0", ascending=False)
        df_positives = df_positives[:10]
        df_positives['rate'] = df_positives.apply(axis='columns', func=lambda x: cl.get_future_data(x['future'])['nextFundingRate']*100)
        df_positives = df_positives.sort_values("rate", ascending=False)
        df_positives['change'] = df_positives.apply(axis='columns', func=lambda x: f"{arrow_up if x['rate_2'] < x['rate_1'] else arrow_down}{arrow_up if x['rate_1'] < x['rate_0'] else arrow_down}{arrow_up if x['rate_0'] < x['rate'] else arrow_down}")
        df_positives['future sell price'] = df_positives.apply(axis='columns', func=lambda x: cl.get_ticker(x['future']))
        df_positives['spot buy price'] = df_positives.apply(axis='columns', func=lambda x: cl.get_orderbook(convert_symbol_futures_spot(x['future']))['asks'][0][0])
        df_positives['%'] = round( abs( df_positives['future sell price'] -  df_positives['spot buy price'] )/ df_positives['future sell price'] * 100,2)
        print(df_positives.to_string(header=False, index=False, columns=["future","rate","change","future sell price","spot buy price","%"]))

        print("\nmost negative funding rates " + arrow_down + "\n")
        df_negatives = df.sort_values("rate_0", ascending=True)
        df_negatives = df_negatives[:10]
        df_negatives['rate'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_future_data(x['future'])['nextFundingRate']*100)
        df_negatives = df_negatives.sort_values("rate", ascending=True)
        df_negatives['change'] = df_negatives.apply(axis='columns', func=lambda x: f"{arrow_up if x['rate_2'] < x['rate_1'] else arrow_down}{arrow_up if x['rate_1'] < x['rate_0'] else arrow_down}{arrow_up if x['rate_0'] < x['rate'] else arrow_down}")
        df_negatives['future buy price'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_orderbook(x['future'])['asks'][0][0])
        df_negatives['spot sell price'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_orderbook(convert_symbol_futures_spot(x['future']))['bids'][0][0])
        df_negatives['%'] = round( abs( df_negatives['future buy price'] -  df_negatives['spot sell price'] )/ df_negatives['future buy price'] * 100,2)
        print(df_negatives.to_string(header=False, index=False, columns=["future","rate","change","future buy price","spot sell price","%"]))


    def list_positions(self):
        cl = self.cl

        #df = pd.DataFrame.from_dict(cl.balances)
        #print(df.to_string(index=False))
        #df = pd.DataFrame.from_dict(cl.positions)
        #print(df.to_string(index=False))
        print(f"Account Value:    {round(cl.account['totalAccountValue'],2)}")
        print(f"Total Collateral: {round(cl.account['collateral'],2)}")
        print(f"Free Collateral:  {round(cl.account['freeCollateral'],2)}")
        print(f"Margin:           {round(cl.account['marginFraction']*100,1)}%/{round(cl.account['maintenanceMarginRequirement']*100,1)}%")
        print(f"Fees:             Taker {cl.account['takerFee']*100}%, Maker {cl.account['makerFee']*100}%")
        spot_usd_data = [a for a in cl.balances if a['coin'] == "USD"][0]
        print(f"USD Balance:      {round(spot_usd_data['total'],2)} ({round(spot_usd_data['total']/cl.account['collateral'],1)}x of net collateral)")
        print("\nPositions:\n")
        positions_data = list()
        for x in cl.positions:
            future_name = x['future']
            spot_coin_data = [a for a in cl.balances if a['coin'] ==  future_name.replace("-PERP","")][0]
            if x['netSize'] > 0 or spot_coin_data['total'] > 0:
                future_data = cl.get_future_data(future_name)
                fr = future_data['nextFundingRate']*100
                historical_frs = [a for a in cl.funding_rates if a['future'] == future_name][0]
                pos_side = "SHORT" if x['side'] == "sell" else "LONG"
                orderbook_futures = cl.get_orderbook(future_name)
                orderbook_spot = cl.get_orderbook(convert_symbol_futures_spot(future_name))
                future_close_price =  orderbook_futures['asks'][0][0] if pos_side == "LONG" else orderbook_futures['bids'][0][0]
                spot_close_price =  orderbook_spot['bids'][0][0] if pos_side == "LONG" else orderbook_spot['asks'][0][0]
                position_data = {
                    'future': future_name,
                    'fr': fr,
                    'side': pos_side,
                    'qty': x['netSize'],
                    #'value': x['cost'],
                    'value': round(x['netSize']*future_close_price,2),
                    'entry price': x['entryPrice'],
                    'liq price': x['estimatedLiquidationPrice'],
                    'spot qty': spot_coin_data['total'],
                    #'spot value': spot_coin_data['usdValue'],
                    'spot value': round(spot_coin_data['total']*spot_close_price,2),
                    'net qty': spot_coin_data['total'] + x['netSize'],
                    'net value': round(x['netSize']*future_close_price + spot_coin_data['total']*spot_close_price,2),
                    'profitable': (pos_side == "SHORT" and fr > 0) or(pos_side == "LONG" and fr < 0),
                    'fr trend': f"{['+','-'][historical_frs['rate_2'] < 0]}{['+','-'][historical_frs['rate_1'] < 0]}{['+','-'][historical_frs['rate_0'] < 0]}",
                }
                positions_data.append(position_data)
        df = pd.DataFrame.from_dict(positions_data)
        print(df.to_string(index=False))


    def add_position(self, market: str, qty: float):
        market_spot = convert_symbol_futures_spot(market)
        self.cl.execute_hedge_order(market, "buy", market_spot, "sell", qty)
        self.list_positions()


    def sub_position(self, market: str, qty: float):
        market_spot = convert_symbol_futures_spot(market)
        self.cl.execute_hedge_order(market, "sell", market_spot, "buy", qty)
        self.list_positions()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-markets', action='store_const', const='True',  help='Display list of futures markets and their current funding rates')
    parser.add_argument('--list-positions', action='store_const', const='True',  help='Display list of opened positions')
    parser.add_argument('--add', type=float,  help='Add to position. Argument: add amount in tokens. Requires --market')
    parser.add_argument('--sub', type=float,  help='Remove from position. Argument: add amount in tokens. Requires --market')
    parser.add_argument('--market', type=str,  help='Futures market symbol, to use with --add or --sub')
    args = parser.parse_args()

    app = App()

    if args.list_markets:
        app.list_markets()
    elif args.list_positions:
        app.list_positions()
    elif args.add:
        if args.market:
            app.add_position(args.market, args.add)
        else:
            print("error: --market not specified")
    elif args.sub:
        if args.market:
            app.sub_position(args.market, args.sub)
        else:
            print("error: --market not specified")

if __name__ == '__main__':
    main()
