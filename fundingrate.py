import argparse, time, datetime, math, talib, yaml
from collections import defaultdict
from typing import List, Tuple
import pandas as pd
import numpy as np
from termcolor import cprint

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
    "STMX-PERP",
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
"1INCH", "AAVE", "BCH", "BNB", "BTC", "CEL", "DOGE", "ETH", "LEO", "LINK", "LTC", "MATIC",  "OMG", "PAXG",
"PENN", "PFE", "REN", "RSR", "RUNE", "SLV", "SNX", "SOL", "SUSHI", "SXP",  "TRX", "UNI", "WBTC", "XAUT", "XRP", "YFI",
]

MIN_LOT_SIZE={
    "XAUT-PERP":    20,
    "BNB-PERP":     40,
}


def section(name: str):
    cprint(f"{name}", 'white', attrs=['bold'])

def convert_symbol_futures_spot(symbol: str):
    return symbol.replace("-PERP", "/USD")

conf = yaml.safe_load(open('config/fundingrate.yml', 'r'))


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

    def get_market(self, market: str):
        if self._markets is None:
            self._markets = self._api.get_markets()
        market = [m for m in self._markets if m['name'] ==  market][0]
        return market

    def has_market(self, market: str) -> bool:
        if self._markets is None:
            self._markets = self._api.get_markets()
        return len( [m for m in self._markets if m['name'] ==  market] ) != 0

    def get_future_data(self, market: str):
        return self._api.get_future_stats(market)

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
            if not self.has_market(convert_symbol_futures_spot(k)): #does not have corresponding spot market for this future market
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
        order_id1 = self._api.place_order(market1, side1, None, "market", size)
        order_id2 = self._api.place_order(market2, side2, None, "market", size)

        for _ in range(10):
            time.sleep(0.5)
            r1 = self._api.get_order_status(order_id1)
            r2 = self._api.get_order_status(order_id2)
            if r1['status'] == "closed" and r2['status'] == "closed":
                break

        self._account = None
        self._balances = None



class Db:
    def __init__(self):
        import sqlite3
        self.con = sqlite3.connect('config/fundingrate.db')
        self.con.execute('''CREATE TABLE IF NOT EXISTS historical_frs (date text, market text, fr real, is_gainer integer)''')
        self.con.execute('''CREATE TABLE IF NOT EXISTS payments (date text, account_value real, net_profit real)''')
        self.con.commit()

    def add_fr(self, market: str, fr: float, is_gainer: bool ):
        now = datetime.datetime.now()
        self.con.execute("INSERT INTO historical_frs VALUES (?,?,?,?)", (now, market, fr, is_gainer))
        self.con.commit()

    def add_net_profit(self, account_value: float, net_profit: float):
        now = datetime.datetime.now()
        self.con.execute("INSERT INTO payments VALUES (?,?,?)", (now, account_value, net_profit))
        self.con.commit()

    def get_markets(self) -> List[str]:
        return [ row[0] for row in self.con.execute(f"SELECT DISTINCT market FROM historical_frs") ]

    def get_market_historical_frs(self, market: str) -> List[Tuple[float, bool]]:
        return [ {'fr': row[0], 'is_gainer': row[1] > 0} for row in self.con.execute(f"SELECT fr, is_gainer FROM historical_frs WHERE market = '{market}' ORDER BY date") ]

    def get_payments(self) -> List[Tuple[float, float]]:
        return [ {'account_value': row[0], 'net_profit': row[1]} for row in self.con.execute(f"SELECT account_value, net_profit FROM payments ORDER BY date") ]


class App:
    def __init__(self):
        self.cl = Client(restrict_non_usd_collateral=False)

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
        df_positives['future op p'] = df_positives.apply(axis='columns', func=lambda x: cl.get_market(x['future'])['bid'])
        df_positives['spot op p'] = df_positives.apply(axis='columns', func=lambda x: cl.get_market(convert_symbol_futures_spot(x['future']))['ask'])
        df_positives['future cl p'] = df_positives.apply(axis='columns', func=lambda x: cl.get_market(x['future'])['ask'])
        df_positives['spot cl p'] = df_positives.apply(axis='columns', func=lambda x: cl.get_market(convert_symbol_futures_spot(x['future']))['bid'])
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
        df_negatives['future op p'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_market(x['future'])['ask'])
        df_negatives['spot op p'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_market(convert_symbol_futures_spot(x['future']))['bid'])
        df_negatives['future cl p'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_market(x['future'])['bid'])
        df_negatives['spot cl p'] = df_negatives.apply(axis='columns', func=lambda x: cl.get_market(convert_symbol_futures_spot(x['future']))['ask'])
        df_negatives['op spread %'] = round( ( df_negatives['spot op p'] - df_negatives['future op p'] )/ df_negatives['future op p'] * 100,2)
        df_negatives['cl spread %'] = round( ( df_negatives['future cl p'] - df_negatives['spot cl p'] )/ df_negatives['future cl p'] * 100,2)
        print(df_negatives.to_string(header=True, index=False, columns=["future","rate","change","stability","future op p","spot op p","op spread %","cl spread %"]))

    def _calc_account_value(self):
        return sum([x['usdValue'] for x in self.cl.balances]) + sum([x['unrealizedPnl'] for x in self.cl.positions]) - conf['airbag_collateral']

    def list_positions(self, silent_alert: bool = False):
        cl = self.cl
        alert_list = list()

        print(f"Account Value:    {self._calc_account_value():.2f}")
        print(f"Free Collateral:  {cl.account['freeCollateral']:.2f}")
        print(f"Margin:           {cl.account['marginFraction']*100:.1f}%/{cl.account['maintenanceMarginRequirement']*100:.1f}%")
        print(f"Fees:             Taker {cl.account['takerFee']*100}%, Maker {cl.account['makerFee']*100}%")
        spot_usd_data = [a for a in cl.balances if a['coin'] == "USD"][0]
        print(f"USD Balance:      {spot_usd_data['total']:.2f} ({spot_usd_data['total']/cl.account['collateral']:.1f}x of net collateral)")
        ####
        if cl.account['freeCollateral'] < 200:
            alert_list.append("collateral")
        if cl.account['marginFraction'] / cl.account['maintenanceMarginRequirement'] < 1.5:
            alert_list.append("margin")
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
                future_op_price =  cl.get_market(future_name)['ask'] if pos_side == "LONG" else cl.get_market(future_name)['bid']
                spot_op_price =  cl.get_market(convert_symbol_futures_spot(future_name))['bid'] if pos_side == "LONG" else cl.get_market(convert_symbol_futures_spot(future_name))['ask']
                future_close_price =  cl.get_market(future_name)['bid'] if pos_side == "LONG" else cl.get_market(future_name)['ask']
                spot_close_price =  cl.get_market(convert_symbol_futures_spot(future_name))['ask'] if pos_side == "LONG" else cl.get_market(convert_symbol_futures_spot(future_name))['bid']
                value = x['netSize']*future_close_price
                net_qty = spot_coin_data['total'] + x['netSize']
                floor_net_qty = math.floor(abs(spot_coin_data['total'] + x['netSize']))
                get_fr_profitable = lambda x: x > 0 if pos_side == "SHORT" else x < 0
                is_profitable = get_fr_profitable(fr)
                profit_per_hour = -value*fr*0.01
                stability = [ get_fr_profitable(historical_frs[k]) for k in ["rate_2","rate_1", "rate_0"] ]
                ####
                # use rounded diff of qties because sometimes qty may not be exactly 0
                # due to extra amount borrowed when market-short-selling
                if floor_net_qty > 0:
                    alert_list.append("net_qty")
                ##
                position_data = {
                    'future': future_name,
                    'fr': fr,
                    'side': pos_side,
                    'qty': x['netSize'],
                    'price': round((future_close_price+spot_close_price)/2,2),
                    'value': round(abs(value),2),
                    # 'f op p': round(future_op_price,2),
                    # 's op p': round(spot_op_price,2),
                    # 'f cl p': round(future_close_price,2),
                    # 's cl p': round(spot_close_price,2),
                    'op spread %': round( (future_op_price - spot_op_price)/future_op_price * 100 * [1,-1][pos_side == "LONG"] ,2),
                    'cl spread %': round( (future_close_price - spot_close_price)/future_close_price * 100 * [1,-1][pos_side == "SHORT"] ,2),
                    'net qty': net_qty,
                    'profit/h': round(profit_per_hour,2),
                    'stability': "".join([ ['-','+'][x]  for x in stability]),
                }
                positions_data.append(position_data)
        df = pd.DataFrame.from_dict(positions_data)
        df.sort_values('value', ascending=False, inplace=True)
        print(df.to_string(index=False))
        net_profit_per_hour = sum(df['profit/h'])
        print(f"net profit/h: {net_profit_per_hour:.2f}")
        if net_profit_per_hour < 0:
            alert_list.append("net_profit")

        if len(alert_list):
            if not silent_alert:
                sn = SoundNotification()
            for _ in range(3):
                print(f"****************** ALERT : {' '.join(alert_list)}! ******************")
                if not silent_alert:
                    sn.info()
                time.sleep(0.6)


    def update_pos(self, market: str, qty: float, limit_spread: float):
        future_size_increment = self.cl.get_market(market)['sizeIncrement']
        spot_size_increment = self.cl.get_market(convert_symbol_futures_spot(market))['sizeIncrement']
        future_decimals = get_decimal_count(future_size_increment)
        spot_decimals = get_decimal_count(spot_size_increment)
        lot_qty, lot_count = self._calc_lot_qty_and_count(market, abs(qty), min(future_decimals,spot_decimals))
        for ilot in range(lot_count):
            print(f"** LOT {ilot+1} of {lot_count} qty={lot_qty} **")
            if qty > 0:
               self._long_pos(market, lot_qty, limit_spread)
            elif qty < 0:
               self._short_pos(market, lot_qty, limit_spread)

    def _calc_lot_qty_and_count(self,  market: str, qty: float, round_decimals: int):
        '''
        returns [lot_qty, count]
        '''
        max_value_per_lot =  MIN_LOT_SIZE[market] if market in MIN_LOT_SIZE else 15
        price = self.cl.get_market(market)['ask']
        lot_qty0 = min(qty, max_value_per_lot / price)
        lot_qty = round(lot_qty0, round_decimals)
        count = max(1,math.floor(qty / lot_qty))
        print(f"rounded lot size {lot_qty0} -> {lot_qty} round_decimals: {round_decimals}")
        return lot_qty, count


    def _long_pos(self, market: str, qty: float, limit_spread: float):
        cl = None
        if limit_spread is not None:
            while True:
                cl = Client()
                buy_price = cl.get_market(market)['ask']
                sell_price = cl.get_market(convert_symbol_futures_spot(market))['bid']
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
                sell_price = cl.get_market(market)['bid']
                buy_price = cl.get_market(convert_symbol_futures_spot(market))['ask']
                spread= round((sell_price - buy_price )/ sell_price * 100,2)
                print(f"current spread: {spread}%, required: >{limit_spread}%", end="\r", flush=True)
                if spread > limit_spread:
                    break
                time.sleep(5.0)
        print(f"\nadd short: {qty}")
        self.cl.execute_hedge_order(market, "sell", convert_symbol_futures_spot(market), "buy", qty)


    def update_db(self):
        print("** press Ctrl-C to terminate! **")
        while True:
            ts = int(datetime.datetime.now().timestamp())
            remaining_seconds = max(0, 3600 - 55 - (ts % 3600))
            print(f"sleeping for {remaining_seconds} seconds")
            time.sleep(remaining_seconds)
            print("updating db")
            db = Db()
            net_profit_per_hour = 0
            for x in self.cl.positions:
                future_name = x['future']
                if x['size'] > 0:
                    future_data = self.cl.get_future_data(future_name)
                    fr = future_data['nextFundingRate']*100
                    pos_side = "SHORT" if x['side'] == "sell" else "LONG"
                    future_close_price =  self.cl.get_market(future_name)['bid'] if pos_side == "LONG" else self.cl.get_market(future_name)['ask']
                    value = x['netSize']*future_close_price
                    get_fr_profitable = lambda x: x > 0 if pos_side == "SHORT" else x < 0
                    is_profitable = get_fr_profitable(fr)
                    profit_per_hour = -value*fr*0.01
                    net_profit_per_hour += profit_per_hour
                    db.add_fr(future_name, fr, is_profitable)
            db.add_net_profit(account_value=round(self._calc_account_value()), net_profit=round(net_profit_per_hour,2))
            time.sleep(100)


    def stats(self):
        db = Db()
        markets = db.get_markets()
        market_info = []
        sma_period_days = 7
        print(f"Results below are {sma_period_days}-day averages")
        print()
        for m in markets:
            frs =  db.get_market_historical_frs(m)
            total_actions = len(frs)
            frs_signed = ([ abs(x['fr']) if  x['is_gainer'] else -abs(x['fr'])  for x in frs ] )
            avg_pnl = talib.SMA(np.array(frs_signed),min(sma_period_days*24,len(frs_signed)))[-1]
            wins_as_long  = sum([ 1 if x['is_gainer'] else 0 for x in frs if x['fr'] < 0 ] )
            wins_as_short = sum([ 1 if x['is_gainer'] else 0 for x in frs if x['fr'] > 0 ] )
            market_info.append( {
                'market': m,
                'pnl %': round(avg_pnl,4),
                '% wins as long': round(wins_as_long/total_actions*100,1),
                '% wins as short': round(wins_as_short/total_actions*100,1),
            })
        df = pd.DataFrame.from_dict(market_info)
        df.sort_values("pnl %", inplace=True, ascending=False)
        print(df.to_string(index=False))
        print()
        payments = db.get_payments()
        account_values = [x['account_value'] for x in payments]
        net_profits = [x['net_profit'] for x in payments]

        avg_account_value = talib.SMA(np.array(account_values),min(sma_period_days*24,len(account_values)))[-1]
        avg_net_profit = talib.SMA(np.array(net_profits),min(sma_period_days*24,len(net_profits)))[-1]
        
        df = pd.DataFrame.from_dict([
                { 'param' : f'account value MA{sma_period_days}', 'value': avg_account_value},
                { 'param' : f'net profit MA{sma_period_days}', 'value': avg_net_profit },
                { 'param' : f'APR %', 'value': round(avg_net_profit/avg_account_value * 24 * 365 * 100,1) },
                { 'param' : f'cumulative profit since {len(net_profits)/24:.1f} days', 'value': sum(net_profits)},
            ] )
        print(df.to_string(index=False, header=False))



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
    parser.add_argument('--update-db', action='store_const', const='True',  help='Collects stat data to db')
    parser.add_argument('--stats', action='store_const', const='True',  help='Print a performance report')
    parser.add_argument('--silent-alerts', action='store_const', const='True',  help='Do not play sound for alerts')

    args = parser.parse_args()

    app = App()

    if args.list_positions:
        app.list_positions(args.silent_alerts)
    if args.list_markets:
        app.list_markets(args.list_markets)

    if args.update:
        if args.market:
            app.update_pos(args.market, args.update, args.limit_spread)
        else:
            print("error: --market not specified")

    if args.update_db:
        app.update_db()
    
    if args.stats:
        app.stats()


if __name__ == '__main__':
    main()
