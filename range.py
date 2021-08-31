import argparse,asyncio
from lib.trader.trader_factory import TraderFactory

from lib.trader import api_keys_config
from lib.trader import ftx_api

class Ticker:
    async def get_price_tick(self) -> float:
        raise NotImplementedError()

class TickerSourceFtx(Ticker):
    TICKER_FIXED_DELAY = 10

    def __init__(self, market: str):
        cfg = api_keys_config.ApiKeysConfig()
        api_key, secret = cfg.get_ftx_ks()
        subaccount = cfg.get_ftx_subaccount_trade()
        self._market = market
        self._api = ftx_api.Ftx(api_key, secret, subaccount)
        self._t = 0

    async def get_price_tick(self) -> float:
        time_since_last = asyncio.get_running_loop().time() - self._t
        if time_since_last < TickerSourceFtx.TICKER_FIXED_DELAY:
            await asyncio.sleep(TickerSourceFtx.TICKER_FIXED_DELAY - time_since_last)
        price = self._api.get_ticker(self._market)
        self._t = asyncio.get_running_loop().time()
        print(f"ticker: {price}")
        return price

class RangeTrader:
    def __init__(self, ticker: Ticker, sym: str, low: float, high: float, account: float, split: int, stop: float, risk: float):
        self._trader = TraderFactory.create_dummy(sym)
        self._ticker = ticker
        self._low = low
        self._high = high
        self._account = account
        self._split = split
        self._stop = stop
        self._risk = risk

    async def run(self):
        while True:
            price = await self._ticker.get_price_tick()
        


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sym',  nargs='+', type=str,  help='symbol to trade')
    parser.add_argument('--low',  nargs='+', type=float,  help='range low')
    parser.add_argument('--high',  nargs='+', type=float,  help='range high')
    parser.add_argument('--account',  nargs='+', type=float,  help='total money available for trading session')
    parser.add_argument('--split',  nargs='?', type=int, default=5,  help='number of splits of lot per half-period')
    parser.add_argument('--stop',  nargs='?', type=float, default=10,  help='stop placement, below or above the range, in percent of range height')
    parser.add_argument('--risk',  nargs='?', type=float, default=1,  help='max risk in percent of account size')
    args = parser.parse_args([])

    market = "ETH-PERP"
    trader =RangeTrader( ticker=TickerSourceFtx(market), sym=market, low=args.low, high=args.high, account=args.account, split=args.split, stop=args.stop, risk=args.risk)
    asyncio.run(trader.run())

if __name__ == '__main__':
    main()
