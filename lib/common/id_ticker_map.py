import os, pathlib, pycoingecko, yahoo_fin.stock_info, pickledb


class CryptoNameDb:
    def __init__(self):
        is_uninitialized = not os.path.exists("cache/cg/names.db")
        pathlib.Path("cache/cg").mkdir(parents=True, exist_ok=True)
        self.db = pickledb.load("cache/cg/names.db", auto_dump=False)
        if is_uninitialized:
            cg = pycoingecko.CoinGeckoAPI()
            coins_list = cg.get_coins_list()
            for entry in coins_list:
                self.db.set(entry['id'], {'name': entry['name'],'sym': entry['symbol'].upper() })
            self.db.dump()

    def get_name(self, ticker: str) -> str:
        entry = self.db.get(ticker)
        return entry['name'] if entry else None

    def get_sym(self, ticker: str) -> str:
        entry = self.db.get(ticker)
        return entry['sym'] if entry else None

    def get_id_to_ticker_map(self) -> dict:
        m = {}
        all_ids = self.db.getall()
        for k in all_ids:
            m[k] = self.get_sym(k)
        return m


class StockNameDb:
    def __init__(self):
        pathlib.Path("cache/yf").mkdir(parents=True, exist_ok=True)
        self.db = pickledb.load("cache/yf/names.db", auto_dump=True)
    def get_name(self, ticker: str) -> str:
        existing_name = self.db.get(ticker)
        if existing_name:
            return existing_name
        else:
            try:
                name = yahoo_fin.stock_info.get_quote_data(ticker)["longName"]
            except:
                name = ticker
            self.db.set(ticker, name)
            return name

_crypto_name_db = CryptoNameDb()
_stock_name_db = StockNameDb()


# DEPRECATED, use get_id_sym
class TickerDict (dict):
    # if id is not listed below its ticker is assumed to be equal to id
    def __missing__(self,k):
        return k
id_to_ticker = TickerDict(_crypto_name_db.get_id_to_ticker_map())



def get_id_sym(asset_id: str) -> str:
    sym = _crypto_name_db.get_sym(asset_id)
    if sym is None:
        sym = asset_id
    return sym

def get_id_name(asset_id: str) -> str:
    name = _crypto_name_db.get_name(asset_id)
    if name is None:
        name = _stock_name_db.get_name(asset_id)
    return name

def get_id_name_shorter(asset_id: str) -> str:
    removes = [
        'ETF',
        ', Inc.',
        'Inc.',
        'Corp.',
        'Corporation',
        'N.V.',
        'Company',
        'Limited',
        'PLC',
        'plc',
    ]
    replaces = [
        # ('VanEck Vectors', 'VanEck'),
        ('International', 'Intl'),
        # ('Standard', 'Std'),
        # ('Physical', 'Phys'),
    ]
    s = get_id_name(asset_id)
    for x in removes:
        s = s.replace(x,'')
    for x,y in replaces:
        s = s.replace(x,y)
    return s.strip()

# def get_id_sym_name_concat(id: str) -> str:
#     return f"{get_id_sym(id)}: {get_id_name(id)}"