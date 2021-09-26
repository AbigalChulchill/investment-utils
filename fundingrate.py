import argparse, time, datetime, math
from collections import defaultdict
import pandas as pd

from lib.trader import api_keys_config
from lib.trader import ftx_api
from lib.common.sound_notification import SoundNotification
from lib.common.misc import get_decimal_count


FUTURE_IGNORE=[
    "AMPL-PERP",
    "DMG-PERP",
    "SHIB-PERP",
    "HUM-PERP",
    "CUSDT-PERP",
    "TRYB-PERP",
    "MER-PERP",
    "DENT-PERP",
    "MTA-PERP",
    "BAO-PERP",
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

MIN_LOT_SIZE={
    "XAUT-PERP":    20,
    "BNB-PERP":     40,
}


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
        self._alert = None

    @property
    def alert_state(self):
        return self._alert is not None

    @property
    def alert_message(self):
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

        print(f"Account Value:    {sum([x['usdValue'] for x in cl.balances]) + sum([x['unrealizedPnl'] for x in cl.positions]) :.2f}")
        print(f"Free Collateral:  {cl.account['freeCollateral']:.2f}")
        print(f"Margin:           {cl.account['marginFraction']*100:.1f}%/{cl.account['maintenanceMarginRequirement']*100:.1f}%")
        print(f"Fees:             Taker {cl.account['takerFee']*100}%, Maker {cl.account['makerFee']*100}%")
        spot_usd_data = [a for a in cl.balances if a['coin'] == "USD"][0]
        print(f"USD Balance:      {spot_usd_data['total']:.2f} ({spot_usd_data['total']/cl.account['collateral']:.1f}x of net collateral)")
        ####
        if cl.account['marginFraction'] / cl.account['maintenanceMarginRequirement'] < 2:
            self._alert = "margin"
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
                value = x['netSize']*future_close_price
                net_qty = spot_coin_data['total'] + x['netSize']
                floor_net_qty = math.floor(abs(spot_coin_data['total'] + x['netSize']))
                get_fr_profitable = lambda x: x > 0 if pos_side == "SHORT" else x < 0
                is_profitable = get_fr_profitable(fr)
                profit_per_hour = -value*fr*0.01
                stability = [ get_fr_profitable(historical_frs['rate_0']), get_fr_profitable(historical_frs['rate_1']), get_fr_profitable(historical_frs['rate_2']) ]
                ####
                # use rounded diff of qties because sometimes qty may not be exactly 0
                # due to extra amount borrowed when market-short-selling
                if floor_net_qty > 0:
                    self._alert = "net qty"
                ##
                if not is_profitable and datetime.datetime.now().minute > 50 and not stability[0]:
                    self._alert = "profitable"
                ####
                position_data = {
                    'future': future_name,
                    'fr': fr,
                    'side': pos_side,
                    'qty': x['netSize'],
                    'value': round(value,2),
                    'future cl p': future_close_price,
                    'spot cl p': spot_close_price,
                    'cl spread %': round( (future_close_price - spot_close_price)/future_close_price * 100 * [1,-1][pos_side == "SHORT"] ,2),
                    'net qty': net_qty,
                    'profit/h': round(profit_per_hour,2),
                    'stability': f"{['-','+'][stability[2]]}{['-','+'][stability[1]]}{['-','+'][stability[0]]}",
                }
                positions_data.append(position_data)
        df = pd.DataFrame.from_dict(positions_data)
        df.sort_values('value', ascending=True, inplace=True)
        print(df.to_string(index=False))
        net_profit_per_hour = sum(df['profit/h'])
        print(f"net profit/h: {net_profit_per_hour:.2f}")



    def update_pos(self, market: str, qty: float, limit_spread: float):
        lot_qty0, lot_count = self._calc_lot_qty_and_count(market, abs(qty))
        future_market = [m for m in self.cl.markets if m['name'] ==  market ][0]
        spot_market = [m for m in self.cl.markets if m['name'] ==  convert_symbol_futures_spot(market)][0]
        future_size_increment = future_market['sizeIncrement']
        spot_size_increment = spot_market['sizeIncrement']
        future_min_decimals = get_decimal_count(future_size_increment)
        spot_min_decimals = get_decimal_count(spot_size_increment)
        lot_qty = round(lot_qty0, min(future_min_decimals,spot_min_decimals))
        print(f"rounded lot size {lot_qty0} -> {lot_qty} future market min decimals: {future_min_decimals},  spot market min decimals: {spot_min_decimals}")
        for ilot in range(lot_count):
            print(f"** LOT {ilot+1} of {lot_count} qty={lot_qty} **")
            if qty > 0:
               self._long_pos(market, lot_qty, limit_spread)
            elif qty < 0:
               self._short_pos(market, lot_qty, limit_spread)
        self.list_positions()

    def _calc_lot_qty_and_count(self,  market: str, qty: float):
        '''
        returns [lot_qty, count]
        '''
        max_value_per_lot =  MIN_LOT_SIZE[market] if market in MIN_LOT_SIZE else 15
        price = self.cl.get_orderbook(market)['asks'][0][0]
        lot_qty = max_value_per_lot / price
        count = max(1,math.floor(qty / lot_qty))
        return lot_qty, count


    def _long_pos(self, market: str, qty: float, limit_spread: float):
        cl = None
        if limit_spread is not None:
            while True:
                cl = Client()
                buy_price = cl.get_orderbook(market)['asks'][0][0]
                sell_price = cl.get_orderbook(convert_symbol_futures_spot(market))['bids'][0][0]
                spread= round((sell_price - buy_price )/ sell_price * 100,2)
                print(f"current spread: {spread}%, required: >{limit_spread}%", end="\r", flush=True)
                if spread > limit_spread:
                    break
                time.sleep(5.0)
        print(f"\nadd long: {qty}")
        self.cl.execute_hedge_order(market, "buy", convert_symbol_futures_spot(market), "sell", qty)

    def _short_pos(self, market: str, qty: float, limit_spread: float):
        cl = None
        if limit_spread is not None:
            while True:
                cl = Client()
                sell_price = cl.get_orderbook(market)['bids'][0][0]
                buy_price = cl.get_orderbook(convert_symbol_futures_spot(market))['asks'][0][0]
                spread= round((sell_price - buy_price )/ sell_price * 100,2)
                print(f"current spread: {spread}%, required: >{limit_spread}%", end="\r", flush=True)
                if spread > limit_spread:
                    break
                time.sleep(5.0)
        print(f"\nadd short: {qty}")
        self.cl.execute_hedge_order(market, "sell", convert_symbol_futures_spot(market), "buy", qty)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-markets', type=int, help='Display list of top futures markets sorted by last funding rate. Argument: n: limit displayed results to top n markets')
    parser.add_argument('--list-positions', action='store_const', const='True',  help='Display list of opened positions')
    parser.add_argument('--update', type=float,  help='add long/short position. Argument: add qty in tokens. Positive qty adds to long, negative qty adds to short. Requires --market')
    parser.add_argument('--market', type=str,  help='Futures market symbol, to use with --update')
    parser.add_argument('--limit-spread', type=float,  help='Does not create order right away, waits until open spread percent is greater than limit value. '
                                                    'When placing orders it is important that spread is kept positive to minimize losses on price difference between hedge pair. '
                                                    ' spread >0:  selling higher and hedge buying lower'
                                                    ' spread <0:  buying higher and hedge selling lower'
                                                    ' spread =0:  buying and hedge selling at same price'   )

    args = parser.parse_args()

    app = App()

    if args.list_positions:
        app.list_positions()
    if args.list_markets:
        app.list_markets(args.list_markets)

    if args.update:
        if args.market:
            app.update_pos(args.market, args.update, args.limit_spread)
        else:
            print("error: --market not specified")

    if app.alert_state:
        sn = SoundNotification()
        for _ in range(3):
            print(f"****************** ALERT {app.alert_message} ******************")
            sn.info()
            time.sleep(0.6)

if __name__ == '__main__':
    main()
