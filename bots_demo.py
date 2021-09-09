import argparse
from lib.bots.framework import *

def get_strategy_class(name: str):
    import importlib
    strategy_module = None
    for subset in ".", ".custom.":
        try:
            strategy_module = importlib.import_module(f"lib.bots.strategies{subset}{name}")
        except:
            next
    if strategy_module is None:
        raise ValueError(f"strategy not found: {name}")
    strategy_class = getattr(strategy_module, f"StrategyImpl")
    return strategy_class


def create_conductor_backtesting(strategy: str, strategy_args: dict(), sym: str, tf: str, dt_start: str, dt_end: str, initial_account: float, with_pnl: bool):
    ticker = TickerHistorical(sym, tf, dt_start, dt_end)
    broker = DummyBroker(ticker=ticker, initial_account=initial_account)
    if with_pnl:
        broker = BrokerAdapterPnL(ticker=ticker, broker=broker)
    strategy = get_strategy_class(strategy)(strategy_args)
    return BacktestingConductor(strategy=strategy, ticker=ticker, broker=broker)


def create_conductor_live(strategy: str, strategy_args: dict(), sym: str, tf: str, with_pnl: bool):
    ticker = TickerLive(sym, tf)
    broker = DummyBroker(ticker=ticker)
    if with_pnl:
        broker = BrokerAdapterPnL(ticker=ticker, broker=broker)
    strategy = get_strategy_class(strategy)(strategy_args)
    return LiveConductor(strategy=strategy, ticker=ticker, broker=broker)



# def create_conductor_realtime(sym, low, high, account, split, stop, risk):
#     ticker = TickerRealtime(sym)
#     #broker = BrokerAdapterPnL(ticker=ticker, broker=DummyBroker(ticker=ticker))
#     broker = DummyBroker(ticker=ticker)
#     strategy = RangeTrader(low=low, high=high, account=account, split=split, stop=stop, risk=risk)
#     return RealtimeConductor(strategy=strategy, ticker=ticker, broker=broker)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backtest', action='store_const', const='True', help='Run in backtesting mode. Without this parameter run in live mode (default)')
    parser.add_argument('--pnl',      nargs='?', type=bool, const=True, default=False, help='Calculate and report PnL of each trade')
    parser.add_argument('--strategy', type=str, help='Name of the strategy to use')
    parser.add_argument('--sym',      type=str, help='symbol to trade')
    parser.add_argument('--account',  type=float, default=1000, help='total money available for trading session')
    parser.add_argument('--tf',       type=str, help='timeframe for strategy to operate on')
    parser.add_argument('--start',    type=str, help='timestamp of the start of backtesting region')
    parser.add_argument('--end',      type=str, help='timestamp of the end of backtesting region')
    parser.add_argument('--strategy-args', type=str, help='extra strategy arguments: list of k=v items separated by commas')
    # parser.add_argument('--low',   type=float, help='range low')
    # parser.add_argument('--high',  type=float, help='range high')
    # parser.add_argument('--split', type=int, default=5, help='number of splits of lot per half-period')
    # parser.add_argument('--stop',  type=float, default=10, help='stop placement, below or above the range, in percent of range height')
    # parser.add_argument('--risk',  type=float, default=1, help='max risk in percent of account size')
    args = parser.parse_args()

    strategy_args = {}
    if args.strategy_args:
        kv_tokens: List[str]= str(args.strategy_args).split(",")
        for kv in kv_tokens:
            k,v = kv.split("=")
            strategy_args[k] = v

    if args.backtest:
        conductor = create_conductor_backtesting(strategy=args.strategy, strategy_args=strategy_args, sym=args.sym, tf=args.tf, dt_start=args.start, dt_end=args.end, initial_account=args.account, with_pnl=args.pnl)
    else:
        conductor = create_conductor_live(strategy=args.strategy,strategy_args=strategy_args, sym=args.sym, tf=args.tf, with_pnl=args.pnl)

    conductor.run()

if __name__ == '__main__':
    main()
