import sqlite3, datetime
from typing import Tuple
from . historical_order import HistoricalOrder

class Db:
    def __init__(self):
        self.con = sqlite3.connect('config/dca.db')
        self.con.execute('''CREATE TABLE IF NOT EXISTS dca (date text, sym text, qty real, price real)''')
        self.con.commit()

    def add(self, sym: str, qty: float, price: float, timestamp: datetime.datetime=None ):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        self.con.execute("INSERT INTO dca VALUES (?,?,?,?)", (timestamp, sym, qty, price))
        self.con.commit()

    def remove(self, sym: str, qty: float, price: float, timestamp: datetime.datetime=None ):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        self.con.execute("INSERT INTO dca VALUES (?,?,?,?)", (timestamp, sym, -qty, price))
        self.con.commit()

    def burn(self, sym: str, qty: float):
        now = datetime.datetime.now()
        self.con.execute("INSERT INTO dca VALUES (?,?,?,?)", (now, sym, -qty, 0))
        self.con.commit()

    def delete_all(self, sym: str):
        self.con.execute("DELETE FROM dca WHERE sym = ?", (sym,))
        self.con.commit()

    def get_syms(self) -> list:
        syms = []
        for row in self.con.execute(f"SELECT DISTINCT sym FROM dca"):
            syms.append(row[0])
        return syms

    def _get_sym_trades(self, sym: str) -> Tuple[float, float, str]:
        """returns [ [ [+-]coin_qty, price, date ] ]"""
        trades = list()
        for row in self.con.execute(f"SELECT qty,price,date FROM dca WHERE sym = '{sym}' ORDER BY date"):
            entry =(row[0], row[1], row[2] )
            trades.append(entry)
        return trades

    def get_sym_available_qty(self, sym:str) -> float:
        trades = self._get_sym_trades(sym)
        return sum([i[0] for i in trades])

    def get_sym_orders(self, sym:str) -> list[HistoricalOrder]:
        trades = self._get_sym_trades(sym)
        orders:list[HistoricalOrder] = []
        for i in trades:
            t = datetime.datetime.fromisoformat(i[2])
            if i[0] < 0:
                o = HistoricalOrder(side="SELL", value=-i[0]*i[1], qty=-i[0], timestamp=t)
            else:
                o = HistoricalOrder(side="BUY", value=i[0]*i[1], qty=i[0], timestamp=t)
            orders.append(o)
        return orders

    def get_last_buy_timestamp(self) -> datetime.datetime:
        ts = None
        for row in self.con.execute(f"SELECT date FROM dca WHERE qty > 0 ORDER BY date DESC LIMIT 1"):
            ts = datetime.datetime.fromisoformat(row[0])
        return ts