import datetime

from typing import NamedTuple

class HistoricalOrder(NamedTuple):
    side:   str
    value:  float
    qty:    float
    timestamp: datetime.datetime
