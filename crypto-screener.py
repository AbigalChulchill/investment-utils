import os
import json
import termcolor
from pycoingecko import CoinGeckoAPI



def pretty_json(s):
    print(json.dumps(s, indent=4, sort_keys=True))



cg = CoinGeckoAPI()

trade_coin_list ="BAT BCH BEAM BNT BTC BTT CAKE DASH DOGE DOT EGLD ENJ ETC ETH FIL HBAR ICX IOST KSM LTC LUNA "\
                 "MANA MATIC ONE ONT RSR RVN STX THETA TRX UMA XEM XMR XRP ZEC ZEN ZIL SC ZRX"


syms = trade_coin_list.split()
coin_data = cg.get_coins_list()


# build map CoinGecko internal coin ID -> coin Symbol
coin_id_map = {}
for c in syms:
    for x in coin_data:
        if x["symbol"] == c.lower():
            coin_id_map[x["id"]] = c

#print(coin_id_map)

coin_ids = list(coin_id_map.keys())


price_data = None


price_data_filename:str = "cached_price_data.json"
if os.path.exists(price_data_filename):
    price_data_fp = open(price_data_filename)
    price_data = json.load(price_data_fp)
    print('using cached stock price data')
else:
    price_data = cg.get_price(ids=coin_ids, vs_currencies='usd', include_24hr_change='true')
    price_data_fp = open(price_data_filename, "w")
    json.dump(price_data, price_data_fp)

#pretty_json(price_data)


for coin_id,price_entry in price_data.items():
    chg24h = float(price_entry["usd_24h_change"])
    #print(coin_id,chg24h)
    inc = 0
    div = 1
    if chg24h > 0.01:
        if chg24h < 1:
            inc = 50
        elif chg24h < 5:
            inc = 100
        elif chg24h < 10:
            inc = 300
        else:
            inc = 1000
    elif chg24h < -0.001:
        if chg24h > -0.5:
            div = 0.10
        elif chg24h > -1:
            div = 0.25
        elif chg24h > -5:
            div = 0.50
        else:
            div = 0.75
    if inc > 0:
        print(f"{coin_id_map[coin_id]} stock increasing by ${inc} "+ "({:.2f}% market 24h change)".format(chg24h))
    elif div < 1:
        print(f"{coin_id_map[coin_id]} stock decreasing {div} times " + "({:.2f}% market 24h change)".format(chg24h))
    else:
        print(f"{coin_id_map[coin_id]} stock not changed " + "({:.2f}% market 24h change)".format(chg24h))

