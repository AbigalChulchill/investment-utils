import os, json, time, datetime
from typing import List, Tuple

from lib.common import pnl
from lib.common import convert
from lib.trader import api_keys_config
from lib.trader import ftx_api
from lib.trader import binance_api
from lib.bots.interfaces import Broker, Ticker, Strategy, Conductor
import pandas as pd
import numpy as np




class DummyBroker(Broker):
    def __init__(self, ticker: Ticker, initial_account: float = 1000, commission: float=0.0007):
        self._ticker = ticker
        self._account_usd = initial_account
        self._account_token = 0
        self._commission = commission

    def _print_balance(self):
        print(f"**balance** usd={self._account_usd} token={self._account_token}")

    def buy(self, qty: float)->Tuple[float,float]:
        price = self._ticker.market_price
        print(f"buying {qty} at {price}")
        self._account_token += qty*(1-self._commission)
        self._account_usd -= qty*price
        self._print_balance()
        return [qty*price, qty*(1-self._commission)]

    def sell(self, qty: float)->Tuple[float,float]:
        price = self._ticker.market_price
        print(f"selling {qty} at {price}")
        self._account_token -= qty
        self._account_usd +=  qty*(1-self._commission)*price
        self._print_balance()
        return [qty*(1-self._commission)*price, qty]

    @property
    def account_size_usd(self) -> float:
        return self._account_usd
    @property
    def account_size_token(self) -> float:
        return self._account_token


class BrokerAdapterPnL(Broker):
    def __init__(self, ticker: Ticker, broker: Broker):
        self._broker = broker
        self._ticker = ticker
        self._orders:List[pnl.Order] = list()
        self._pnl = None

    def _print_pnl(self):
        pnl_data = pnl.calculate_inc_pnl(self._orders, self._ticker.market_price)
        stats_data = []
        stats_data.append({
            'break_even_price': pnl_data.break_even_price,
            'r pnl': round(pnl_data.realized_pnl,1),
            'r pnl %': round(pnl_data.realized_pnl_percent,1) if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
            'u pnl': round(pnl_data.unrealized_pnl,1),
            'u pnl %': round(pnl_data.unrealized_pnl_percent,1) if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
        })
        df_pnl = pd.DataFrame.from_dict(stats_data)
        print(df_pnl.to_string(index=False))
        self._pnl = pnl_data


    def buy(self, qty: float)->Tuple[float,float]:
        [value,qty] = self._broker.buy(qty)
        #print(f"buying {fill_qty} at {price}")
        self._orders.append(pnl.Order("BUY", value, qty))
        self._print_pnl()
        return [value,qty]

    def sell(self, qty: float)->Tuple[float,float]:
        [value,qty] = self._broker.sell(qty)
        #print(f"selling {fill_qty} at {price}")
        self._orders.append(pnl.Order("SELL", value, qty))
        self._print_pnl()
        return [value,qty]

    @property
    def account_size_usd(self) -> float:
        return self._broker.account_size_usd

    @property
    def account_size_token(self) -> float:
        return self._broker.account_size_token

    @property
    def pnl(self) -> pnl.PnL:
        return self._pnl


class TickerRealtime(Ticker):
    '''
     Ticker using current market data, updated in realtime (not candlestick based)
    '''
    def __init__(self, market: str, update_rate_s: float = 5.0):
        cfg = api_keys_config.ApiKeysConfig()
        api_key, secret = cfg.get_ftx_ks()
        subaccount = cfg.get_ftx_subaccount_trade()
        self._update_rate = update_rate_s
        self._market = market
        self._api = ftx_api.Ftx(api_key, secret, subaccount)

    @property
    def market_price(self) -> float:
        return self._api.get_ticker(convert.coingecko_id_to_ftx[ self._market ])

    @property
    def timestamp(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex(datetime.datetime.utcnow())

    @property
    def update_rate(self) -> float:
        return self._update_rate



class TickerLive(Ticker):
    '''
     Ticker using live candlestick chart data
    '''
    def __init__(self, market: str, timeframe: str):      
        self._market = market
        self._timeframe = timeframe

    @property
    def timeframe(self) -> str:
        return self._timeframe

    def update(self):
        '''
        called by the conductor to update ticker candlestick data
        '''
        api = binance_api.Binance()
        candles = api.get_candles_by_limit(convert.coingecko_id_to_binance[self._market], self._timeframe, limit=500)
        self._df = pd.DataFrame.from_dict(candles)
        self._df = self._df[:-1] # remove last item as it corresponds to just opened candle (partial)
        self._df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(self._df['timestamp'], unit="ms"))

    @property
    def market_price(self) -> float:
        return self.close[-1]

    @property
    def timestamp(self) -> pd.DatetimeIndex:
        return self._df['timestamp'][len(self._df['timestamp'])-1]

    def _get_array(self, elem: str):
        return self._df[elem].to_numpy(dtype=np.double)

    @property
    def open(self):
        return self._get_array('open')

    @property
    def close(self):
        return self._get_array('close')

    @property
    def high(self):
        return self._get_array('high')

    @property
    def low(self):
        return self._get_array('low')

    @property
    def volume(self):
        return self._get_array('volume')


class TickerHistorical(Ticker):
    '''
     Ticker using historical candlestick chart data 
    '''

    def _load_candles_live(self, market: str, timeframe: str, dt_start: str, dt_end: str ):
        api = binance_api.Binance()
        return api.get_candles_by_range(convert.coingecko_id_to_binance[market], timeframe, dt_start, dt_end)

    def _load_candles(self, market: str, timeframe: str, dt_start: str, dt_end: str ) -> str:
        cache_dir:str ="cache"
        cache_file:str = f"{cache_dir}/cache_candles-{market}-{timeframe}-{dt_start}-{dt_end}.json"
        if os.path.exists(cache_file):
            data = json.load(open(cache_file))
            print("loading cached candle data")
        else:
            data = self._load_candles_live(market, timeframe, dt_start, dt_end)
            if not os.path.exists(cache_dir):
                os.mkdir(cache_dir)
            with open(cache_file, "w") as f:
                json.dump(data, f)
        return data


    def __init__(self, market: str, timeframe: str, dt_start: str, dt_end: str ):
        #api = binance_api.Binance()
        #candles = api.get_candles_by_range(convert.coingecko_id_to_binance[market], timeframe, dt_start, dt_end)
        candles = self._load_candles(market, timeframe, dt_start, dt_end)
        self._df = pd.DataFrame.from_dict(candles)
        self._df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(self._df['timestamp'], unit="ms"))
        #self._df.set_index('timestamp', inplace=True)
        #print(self._df.to_string())
        self._p = 0

    def advance(self):
        self._p += 1

    def ended(self)->bool:
        return self._p >= len(self._df)

    @property
    def timestamp(self) -> pd.DatetimeIndex:
        return self._df['timestamp'][self._p]

    @property
    def market_price(self) -> float:
        assert not self.ended()
        return float(self._df['close'][self._p])

    def _get_array(self, elem: str):
        assert not self.ended()
        #return np.flip(self._df[elem][:self._p+1].to_numpy(dtype=np.double))
        return self._df[elem][:self._p+1].to_numpy(dtype=np.double)

    @property
    def open(self):
        return self._get_array('open')

    @property
    def close(self):
        return self._get_array('close')

    @property
    def high(self):
        return self._get_array('high')

    @property
    def low(self):
        return self._get_array('low')

    @property
    def volume(self):
        return self._get_array('volume')




class RealtimeConductor(Conductor):
    def __init__(self, strategy: Strategy, ticker: TickerRealtime, broker: Broker):
        self._ticker = ticker
        self._broker = broker
        self._strategy = strategy

    def run(self):
        while True:
            # update at fixed rate as per ticker property
            self._strategy.tick(self._ticker, self._broker)
            time.sleep(self._ticker.update_rate)


class LiveConductor(Conductor):
    def __init__(self, strategy: Strategy, ticker: TickerLive, broker: Broker):
        self._ticker = ticker
        self._broker = broker
        self._strategy = strategy

    def run(self):
        while True:
            # only update when crossed next interval as per ticker tf
            interval_s = int(convert.timeframe_to_interval_ms[ self._ticker.timeframe ] * 0.001)
            current = int(datetime.datetime.utcnow().timestamp())
            remainder = current % interval_s
            wait_s = interval_s - remainder
            time.sleep(wait_s+1) # extra second to ensure current candle has closed
            self._ticker.update()
            print(f"tick : {datetime.datetime.utcnow()}")
            self._strategy.tick(self._ticker, self._broker)


class BacktestingConductor(Conductor):
    def __init__(self, strategy: Strategy, ticker: TickerHistorical, broker: Broker):
        self._ticker = ticker
        self._broker = broker
        self._strategy = strategy

    def run(self):
        while not self._ticker.ended():
            #print(f"tick : {self._ticker.timestamp}")
            self._strategy.tick(self._ticker, self._broker)
            self._ticker.advance()
