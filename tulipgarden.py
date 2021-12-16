import argparse, yaml, time
from math import isclose
from pandas.core.frame import DataFrame
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from lib.common.msg import *
from lib.trader import api_keys_config
from lib.trader import ftx_api
from lib.common.sound_notification import SoundNotification

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
                'tulip_equity_value': float(equity_value.replace("$","")),
                'tulip_kill_buffer': float(kill_buffer.replace("%","").strip()),
            })
        return d
        
 


def list_positions():
    cl = FtxClient()
    tulip = TulipClient()

    while True:

        # print(f"FTX Account Value:    {cl.get_account_value():.2f}")
        print(f"FTX Free Collateral:  {cl.account['freeCollateral']:.2f}")
        print(f"FTX Margin Fraction:  {cl.account['marginFraction']*100:.1f}% (liquidation if < {cl.account['maintenanceMarginRequirement']*100:.1f}%)  {1/cl.account['marginFraction']:.1f}x leverage")

        hedged_short_positions_pnl = cl.get_positions_pnl()
        # df = DataFrame.from_dict([ {'ticker':k,'hedged short pnl':round(v,2)}  for k,v in hedged_short_positions_pnl.items()] )
        # print(df.to_string(index=False))

        df_tulip_long_lyf_positions = DataFrame.from_dict(tulip.get_lyf_positions())
        main_token_of_lp = lambda x: x.replace("LP","").replace("-USDT","").replace("-USDC","").replace("we","").strip()
        df_tulip_long_lyf_positions['ftx_hedged_short_pnl'] = [ hedged_short_positions_pnl[ main_token_of_lp(x) ] for x in df_tulip_long_lyf_positions['LP'] ]
        df_tulip_long_lyf_positions['ftx_kill_buffer'] = (cl.account['marginFraction'] - cl.account['maintenanceMarginRequirement'])*100 
        df_tulip_long_lyf_positions['net_value'] = df_tulip_long_lyf_positions['tulip_equity_value'] + df_tulip_long_lyf_positions['ftx_hedged_short_pnl']
        print(df_tulip_long_lyf_positions.sort_values('LP').to_string(index=False,float_format=lambda x: f"{x:.2f}"))
        print()

        if df_tulip_long_lyf_positions['tulip_kill_buffer'].min() < 5 or df_tulip_long_lyf_positions['ftx_kill_buffer'].min() < 5:
            for i in range(3):
                SoundNotification().error()
                time.sleep(0.5)            

        time.sleep(60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list',action='store_const', const='True', help='display LYF and hedged positions')
    args = parser.parse_args()

    if args.list:
        list_positions()


if __name__ == '__main__':
    main()
