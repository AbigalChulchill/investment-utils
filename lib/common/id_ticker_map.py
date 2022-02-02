class TickerDict (dict):
    # if id is not listed below its ticker is assumed to be equal to id
    def __missing__(self,k):
        return k

from lib.common.yaml_id_maps import get_id_map_by_key

id_to_ticker = TickerDict(get_id_map_by_key("id_to_ticker"))
