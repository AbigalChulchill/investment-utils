import argparse
from lib.bots.framework import *

def get_strategy_class(name: str):
    import importlib
    for sub in ".", ".custom.":
        try:
            strategy_module = importlib.import_module(f"lib.bots.strategies{sub}{name}")
        except:
            next
    strategy_class = getattr(strategy_module, f"Trader{name}")
    return strategy_class


def create_conductor_backtesting(strategy: str, sym, low, high, account, split, stop, risk):
    ticker = TickerHistorical(sym, "4h", "2021-03-04", "2021-09-04")
    broker = DummyBroker(ticker=ticker)
    #broker = BrokerAdapterPnL(ticker=ticker, broker=broker)
    #strategy = RangeTrader(low=low, high=high, account=account, split=split, stop=stop, risk=risk)
    strategy = get_strategy_class(strategy)()
    return BacktestingConductor(strategy=strategy, ticker=ticker, broker=broker)


def create_conductor_live(strategy: str, sym, low, high, account, split, stop, risk):
    ticker = TickerLive(sym, "1m")
    broker = DummyBroker(ticker=ticker)
    #broker = BrokerAdapterPnL(ticker=ticker, broker=broker)
    strategy = get_strategy_class(strategy)()
    return LiveConductor(strategy=strategy, ticker=ticker, broker=broker)



# def create_conductor_realtime(sym, low, high, account, split, stop, risk):
#     ticker = TickerRealtime(sym)
#     #broker = BrokerAdapterPnL(ticker=ticker, broker=DummyBroker(ticker=ticker))
#     broker = DummyBroker(ticker=ticker)
#     strategy = RangeTrader(low=low, high=high, account=account, split=split, stop=stop, risk=risk)
#     return RealtimeConductor(strategy=strategy, ticker=ticker, broker=broker)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy',  nargs='+', type=str,  help='Name of the strategy to use')
    parser.add_argument('--backtest', action='store_const', const='True', help='Run in backtesting mode. Without this parameter run in live mode (default)')
    parser.add_argument('--sym',  nargs='+', type=str,  help='symbol to trade')
    parser.add_argument('--low',  nargs='+', type=float,  help='range low')
    parser.add_argument('--high',  nargs='+', type=float,  help='range high')
    parser.add_argument('--account',  nargs='+', type=float,  help='total money available for trading session')
    parser.add_argument('--split',  nargs='?', type=int, default=5,  help='number of splits of lot per half-period')
    parser.add_argument('--stop',  nargs='?', type=float, default=10,  help='stop placement, below or above the range, in percent of range height')
    parser.add_argument('--risk',  nargs='?', type=float, default=1,  help='max risk in percent of account size')
    args = parser.parse_args()

    if args.backtest:
        factory = create_conductor_backtesting
    else:
        factory = create_conductor_live

    conductor = factory(strategy=args.strategy[0], sym=args.sym[0], low=args.low, high=args.high, account=args.account, split=args.split, stop=args.stop, risk=args.risk)
    conductor.run()

if __name__ == '__main__':
    main()
