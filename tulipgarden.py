import argparse, yaml, time
from typing import Any
from math import isclose
from pandas.core.frame import DataFrame
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from lib.common.msg import *
from lib.trader import api_keys_config
from lib.trader import ftx_api
from lib.defi.solscan_api import Solscan
from lib.common.sound_notification import SoundNotification

conf: dict[str, Any] = {}


def reread_conf():
    global conf
    conf = yaml.safe_load(open('config/tulipgarden.yml', 'r'))


class FtxClient:
    def __init__(self):
        cfg = api_keys_config.ApiKeysConfig()
        self._api = ftx_api.Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], cfg.get_ftx_subaccount_tuliphedgedshorts())

    def get_account_value(self):
        return sum([x['usdValue'] for x in self.balances]) + sum([x['unrealizedPnl'] for x in self.positions])

    def get_positions_pnl(self):
        pnl = {}
        for p in self.positions:
            if not isclose(p['netSize'], 0):
                pnl[p['future'].replace('-PERP','')] = p['recentPnl']
        return pnl

    @property
    def account(self):
        return self._api.get_account_information()

    @property
    def positions(self):
        return self._api.get_positions()

    @property
    def balances(self):
        return self._api.get_balances()


class TulipClient:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("user-data-dir=cache/tulipgarden/selenium")
        options.add_extension("data/tulipgarden/Phantom.crx")
        self._driver = webdriver.Chrome(options=options)
        self._driver.get("https://tulip.garden/your-positions")

    def get_lyf_positions(self):
        d =[]
        for e in WebDriverWait(self._driver,60).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "your-positions-table__row-item"))):
            data_cols = e.find_elements_by_class_name("your-positions-table__row-item__cell")
            lp_name = e.find_element_by_class_name("your-positions-table__row-item__asset__text-name").text
            equity_value = data_cols[2].find_element_by_xpath("./div").text
            kill_buffer = data_cols[3].find_element_by_xpath("./div").text
            
            d.append({
                'LP': lp_name,
                'tulip_equity_value': float(equity_value.replace("$","").replace(",","")),
                'tulip_kill_buffer': float(kill_buffer.replace("%","").strip()),
            })
        return d
        
 


def list_positions():
    cl = FtxClient()
    tulip = TulipClient()
    solscan = Solscan(conf['lyf_account'])
    kill_thr = conf['kill_buffer_alert_threshold'] if 'kill_buffer_alert_threshold' in conf else 10

    while True:

        reread_conf()

        print("Positions:")
        print()

        hedged_short_positions_pnl = cl.get_positions_pnl()

        df_tulip_long_lyf_positions = DataFrame.from_dict(tulip.get_lyf_positions())
        main_token_of_lp = lambda x: x.replace("LP","").replace("-USDT","").replace("-USDC","").replace("we","").strip()
        df_tulip_long_lyf_positions['ftx_hedged_short_pnl'] = [ hedged_short_positions_pnl[ main_token_of_lp(x) ] if main_token_of_lp(x) in hedged_short_positions_pnl else 0 for x in df_tulip_long_lyf_positions['LP']]
        df_tulip_long_lyf_positions['ftx_kill_buffer'] = (cl.account['marginFraction'] - cl.account['maintenanceMarginRequirement'])*100 
        df_tulip_long_lyf_positions['net_value'] = df_tulip_long_lyf_positions['tulip_equity_value'] + df_tulip_long_lyf_positions['ftx_hedged_short_pnl']
        if "lyf_position_entry_value" in conf:
            df_tulip_long_lyf_positions['pnl'] = df_tulip_long_lyf_positions['net_value'] -  [ conf['lyf_position_entry_value'][x] for x in df_tulip_long_lyf_positions['LP'] ]
        print(df_tulip_long_lyf_positions.sort_values('LP').to_string(index=False,float_format=lambda x: f"{x:.2f}"))
        print()

        lyf_account_stablecoins_balance = solscan.get_token_qty('USDC') + solscan.get_token_qty('USDT')

        print(f"Combined Accounts Value: {df_tulip_long_lyf_positions['tulip_equity_value'].sum() + lyf_account_stablecoins_balance + cl.get_account_value():.2f} USD")
        print(f"FTX Free Collateral:     {cl.account['freeCollateral']:.2f} USD")
        print()


        if df_tulip_long_lyf_positions['tulip_kill_buffer'].min() < kill_thr or df_tulip_long_lyf_positions['ftx_kill_buffer'].min() < kill_thr:
            for i in range(3):
                SoundNotification().error()
                time.sleep(0.5)

        time.sleep(60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list',action='store_const', const='True', help='display LYF and hedged positions')
    args = parser.parse_args()

    reread_conf()

    if args.list:
        list_positions()


if __name__ == '__main__':
    main()
