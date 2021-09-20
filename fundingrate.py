import argparse, time, datetime
from collections import defaultdict
import pandas as pd

from lib.trader import api_keys_config
from lib.trader import ftx_api
from lib.common.sound_notification import SoundNotification

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

SHORTABLE=[
"1INCH", "AAVE", "BCH", "BNB", "BTC", "CEL", "DOGE", "ETH", "LEO", "LINK", "LTC", "MATIC", "OKB", "OMG", "PAXG",
"PENN", "PFE", "REN", "RSR", "RUNE", "SLV", "SNX", "SOL", "SUSHI", "SXP", "TOMO", "TRX", "UNI", "WBTC", "XAUT", "XRP", "YFI",
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

        self._orderbook_cache = dict()

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
        if market not in self._orderbook_cache.keys():
            self._orderbook_cache[market] = self._api.get_orderbook(market, depth=1)
        return self._orderbook_cache[market]

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
        self._alert = False

    @property
    def is_alert_state(self):
        return self._alert

    def list_markets(self, limit_count: int):
        cl = self.cl

        arrow_up = "↑"
        arrow_down= "↓"
    
        df = pd.DataFrame.from_dict(cl.funding_rates)
    
        print("\nmost positive funding rates " + arrow_up + "\n")
        df_positives = df.sort_values("rate_0", ascending=False)
        df_positives = df_positives[:limit_count]
        df_positives['rate'] = df_positives.apply(axis='columns', func=lambda x: cl.get_future_data(x['future'])['nextFundingRate']*100)
        df_positives = df_positives.sort_values("rate", ascending=False)
        df_positives['change'] = df_positives.apply(axis='columns', func=lambda x: f"{arrow_up if x['rate_2'] < x['rate_1'] else arrow_down}{arrow_up if x['rate_1'] < x['rate_0'] else arrow_down}{arrow_up if x['rate_0'] < x['rate'] else arrow_down}")
        df_positives['stability'] = df_positives.apply(axis='columns', func=lambda x: f"{['+','-'][x['rate_2'] < 0]}{['+','-'][x['rate_1'] < 0]}{['+','-'][x['rate_0'] < 0]}{['+','-'][x['rate'] < 0]}")
        df_positives['future op p'] = df_positives.apply(axis='columns', func=lambda x: cl.get_orderbook(x['future'])['bids'][0][0])
        df_positives['spot op p'] = df_positives.apply(axis='columns', func=lambda x: cl.get_orderbook(convert_symbol_futures_spot(x['future']))['asks'][0][0])
        df_positives['future cl p'] = df_positives.apply(axis='columns', func=lambda x: cl.get_orderbook(x['future'])['asks'][0][0])
        df_positives['spot cl p'] = df_positives.apply(axis='columns', func=lambda x: cl.get_orderbook(convert_symbol_futures_spot(x['future']))['bids'][0][0])
        df_positives['op spread %'] = round( (df_positives['future op p'] -  df_positives['spot op p'] )/ df_positives['future op p'] * 100,2)
        df_positives['cl spread %'] = round( (df_positives['spot cl p'] -  df_positives['future cl p'] )/ df_positives['spot cl p'] * 100,2)
        print(df_positives.to_string(header=True, index=False, columns=["future","rate","change","stability","future op p","spot op p","op spread %","cl spread %"]))

        print("\nmost negative funding rates " + arrow_down + "\n")
        df_negatives = df.loc[ [ x.replace("-PERP", "") in SHORTABLE for x in df['future'] ] ] #only include those that can be shorted on spot market
        df_negatives = df_negatives.sort_values("rate_0", ascending=True)
        df_negatives = df_negatives[:limit_count]
        df_negatives['rate'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_future_data(x['future'])['nextFundingRate']*100)
        df_negatives = df_negatives.sort_values("rate", ascending=True)
        df_negatives['change'] = df_negatives.apply(axis='columns', func=lambda x: f"{arrow_up if x['rate_2'] < x['rate_1'] else arrow_down}{arrow_up if x['rate_1'] < x['rate_0'] else arrow_down}{arrow_up if x['rate_0'] < x['rate'] else arrow_down}")
        df_negatives['stability'] = df_negatives.apply(axis='columns', func=lambda x: f"{['+','-'][x['rate_2'] > 0]}{['+','-'][x['rate_1'] > 0]}{['+','-'][x['rate_0'] > 0]}{['+','-'][x['rate'] > 0]}")
        df_negatives['future op p'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_orderbook(x['future'])['asks'][0][0])
        df_negatives['spot op p'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_orderbook(convert_symbol_futures_spot(x['future']))['bids'][0][0])
        df_negatives['future cl p'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_orderbook(x['future'])['bids'][0][0])
        df_negatives['spot cl p'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_orderbook(convert_symbol_futures_spot(x['future']))['asks'][0][0])
        df_negatives['op spread %'] = round( ( df_negatives['spot op p'] - df_negatives['future op p'] )/ df_negatives['future op p'] * 100,2)
        df_negatives['cl spread %'] = round( ( df_negatives['future cl p'] - df_negatives['spot cl p'] )/ df_negatives['future cl p'] * 100,2)
        print(df_negatives.to_string(header=True, index=False, columns=["future","rate","change","stability","future op p","spot op p","op spread %","cl spread %"]))


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
        ####
        if cl.account['marginFraction'] / cl.account['maintenanceMarginRequirement'] < 2:
            self._alert = True
        ####
        print("\nHedged positions:\n")
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
                future_close_price =  orderbook_futures['bids'][0][0] if pos_side == "LONG" else orderbook_futures['asks'][0][0]
                spot_close_price =  orderbook_spot['asks'][0][0] if pos_side == "LONG" else orderbook_spot['bids'][0][0]
                net_qty = spot_coin_data['total'] + x['netSize']
                is_profitable = (pos_side == "SHORT" and fr > 0) or(pos_side == "LONG" and fr < 0)
                ####
                if abs(net_qty) > 0:
                    self._alert = True
                if not is_profitable and datetime.datetime.now().minute > 50:
                    self._alert = True
                ####
                position_data = {
                    'future': future_name,
                    'fr': fr,
                    'side': pos_side,
                    'qty': x['netSize'],
                    'value': round(x['netSize']*future_close_price,2),
                    'liq p': x['estimatedLiquidationPrice'],
                    'future cl p': future_close_price,
                    'spot cl p': spot_close_price,
                    'cl spread %': round( (future_close_price - spot_close_price)/future_close_price * 100 * [1,-1][pos_side == "SHORT"] ,2),
                    'net qty': net_qty,
                    'profitable': is_profitable,
                    'stability': f"{['+','-'][historical_frs['rate_2'] < 0]}{['+','-'][historical_frs['rate_1'] < 0]}{['+','-'][historical_frs['rate_0'] < 0]}",
                }
                positions_data.append(position_data)
        df = pd.DataFrame.from_dict(positions_data)
        print(df.to_string(index=False))


    def add_position(self, market: str, qty: float, limit_spread: float):
        cl = None
        if limit_spread is not None:
            while True:
                cl = Client()
                buy_price = cl.get_orderbook(market)['asks'][0][0]
                sell_price = cl.get_orderbook(convert_symbol_futures_spot(market))['bids'][0][0]
                open_spread= round((sell_price - buy_price )/ sell_price * 100,2)
                print(f"open_spread {open_spread}")
                if open_spread > limit_spread:
                    break
                time.sleep(5.0)
        print(f"adding {qty}")
        market_spot = convert_symbol_futures_spot(market)
        self.cl.execute_hedge_order(market, "buy", market_spot, "sell", qty)
        self.list_positions()


    def sub_position(self, market: str, qty: float, limit_spread: float):
        cl = None
        if limit_spread is not None:
            while True:
                cl = Client()
                sell_price = cl.get_orderbook(market)['bids'][0][0]
                buy_price = cl.get_orderbook(convert_symbol_futures_spot(market))['asks'][0][0]
                open_spread= round((sell_price - buy_price )/ sell_price * 100,2)
                print(f"open_spread {open_spread}")
                if open_spread > limit_spread:
                    break
                time.sleep(5.0)
        print(f"removing {qty}")
        market_spot = convert_symbol_futures_spot(market)
        self.cl.execute_hedge_order(market, "sell", market_spot, "buy", qty)
        self.list_positions()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-markets', type=int, help='Display list of futures markets and their current funding rates')
    parser.add_argument('--list-positions', action='store_const', const='True',  help='Display list of opened positions')
    parser.add_argument('--add', type=float,  help='Add to position. Argument: add amount in tokens. Requires --market')
    parser.add_argument('--sub', type=float,  help='Remove from position. Argument: add amount in tokens. Requires --market')
    parser.add_argument('--market', type=str,  help='Futures market symbol, to use with --add or --sub')

    parser.add_argument('--limit-spread', type=float,  help='Does not create order right away, waits until open spread percent is greater than limit value. '
                                                    'When placing orders it is important that spread is kept positive to minimize losses on price difference between hedge pair. '
                                                    ' spread >0:  selling higher and hedge buying lower'
                                                    ' spread <0:  buying higher and hedge selling lower'
                                                    ' spread =0:  buying and hedge selling at same price'   )

    args = parser.parse_args()

    app = App()

    if args.list_markets:
        app.list_markets(args.list_markets)
    elif args.list_positions:
        app.list_positions()
    elif args.add:
        if args.market:
            app.add_position(args.market, args.add, args.limit_spread)
        else:
            print("error: --market not specified")
    elif args.sub:
        if args.market:
            app.sub_position(args.market, args.sub, args.limit_spread)
        else:
            print("error: --market not specified")

    if app.is_alert_state:
        sn = SoundNotification()
        for _ in range(3):
            print("\n****************** ALERT ****************** ALERT ****************** ALERT ******************")
            sn.info()
            time.sleep(0.6)

if __name__ == '__main__':
    main()
