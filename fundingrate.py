import argparse, time
from collections import defaultdict
from termcolor import colored
import pandas as pd

from lib.trader import api_keys_config
from lib.trader import ftx_api

 # not sure why but FTX does not allow to trade this future however it is returned in the list
FUTURE_IGNORE_LIST=[
    "DMG-PERP",
]

USES_AS_COLLATERAL_LIST=[
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
    def __init__(self):
        cfg = api_keys_config.ApiKeysConfig()
        self._api = ftx_api.Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], cfg.get_ftx_subaccount_fundingratefarm())
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

    def _convert_funding_rates(self, rates_list):
        rates = defaultdict(list)
        for row in rates_list:
            rates[row['future']] .append(row)
        for v in rates.values():
            v.sort(key=lambda x: x['time'],reverse=True)
        futures_data = list()
        for k,v in rates.items():
            if k in FUTURE_IGNORE_LIST:
                continue
            #if k.replace("-PERP","") not in USES_AS_COLLATERAL_LIST:
            #    continue
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

    def place_hedge_order(self, market1: str, side1: str, market2: str, side2: str, size: float):
        order_id1 = self._api.place_order(market1, side1, 0, "market", size)
        order_id2 = self._api.place_order(market2, side2, 0, "market", size)

        retries = 10
        while retries > 0:
            time.sleep(0.5)
            response = self._api.get_order_status(order_id1)
            if response['status'] == "closed":
                break
            retries = retries - 1

        retries = 10
        while retries > 0:
            time.sleep(0.5)
            response = self._api.get_order_status(order_id2)
            if response['status'] == "closed":
                break
            retries = retries - 1

        self._account = None
        self._balances = None


class App:
    def __init__(self):
        self.cl = Client()

    def list_markets(self):
        cl = self.cl

        arrow_up = colored("↑",color="green",attrs=["bold"])
        arrow_down= colored("↓",color="red",attrs=["bold"])
        df = pd.DataFrame.from_dict(cl.funding_rates)
        df['change'] = df.apply(axis='columns', func=lambda x: f"{arrow_up if x['rate_2'] < x['rate_1'] else arrow_down}{arrow_up if x['rate_1'] < x['rate_0'] else arrow_down}")
        print("\nhighest positive funding rates\n")
        df_positives = df.sort_values("rate_0", ascending=False)
        df_positives = df_positives[:10]
        print(df_positives.to_string(index=False))

        print("\nhighest negative funding rates↑\n")
        df_negatives = df.sort_values("rate_0", ascending=True)
        df_negatives = df_negatives[:10]
        print(df_negatives.to_string(index=False))


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
        print(f"USD Balance:      {spot_usd_data['total']}")
        print("\nPositions:\n")
        positions_data = list()
        for x in cl.positions:
            spot_coin_name = x['future'].replace("-PERP","")
            spot_coin_data = [a for a in cl.balances if a['coin'] == spot_coin_name][0]
            fr_data = [a for a in cl.funding_rates if a['future'] == x['future']][0]
            position_data = {
                'future': x['future'],
                'fr': fr_data['rate_0'],
                'side': "SHORT" if x['side'] == "sell" else "LONG",
                'qty': x['netSize'],
                'value': x['cost'],
                'entry price': x['entryPrice'],
                'liq price': x['estimatedLiquidationPrice'],
                'spot qty': spot_coin_data['total'],
                'spot value': spot_coin_data['usdValue'],
                'net qty': spot_coin_data['total'] + x['netSize'],
                'net value': spot_coin_data['usdValue'] + x['cost'],
                'profitable': (x['side'] == "sell" and fr_data['rate_0'] > 0) or(x['side'] == "buy" and fr_data['rate_0'] < 0),
            }
            positions_data.append(position_data)
        df = pd.DataFrame.from_dict(positions_data)
        print(df.to_string(index=False))


    def add_position(self, market: str, qty: float):
        market_spot = convert_symbol_futures_spot(market)
        self.cl.place_hedge_order(market, "buy", market_spot, "sell", qty)
        self.list_positions()


    def sub_position(self, market: str, qty: float):
        market_spot = convert_symbol_futures_spot(market)
        self.cl.place_hedge_order(market, "sell", market_spot, "buy", qty)
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
