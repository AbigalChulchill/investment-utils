#python bots_demo.py --strategy=MACross --sym=ethereum --backtest --account=1000 --tf=4h --start=2021-03-04 --end=2021-09-04
python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=0 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period0.txt
python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=20 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period20.txt
python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=50 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period50.txt
python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=100 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period100.txt
python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period200.txt
