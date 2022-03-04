import pickledb

class BlacklistDb:
    def __init__(self):
        self._db = pickledb.load("cache/blacklist.db", auto_dump=True)

    def add_blacklist(self, ticker: str) -> None:
        self._db.set(ticker, True)
    
    def is_blacklisted(self, ticker: str) -> bool:
        return True == self._db.get(ticker)