from lib.common.position_size import calculate_position_size
from math import isclose

def test_calculate_position_size():
    assert isclose(calculate_position_size(1000, 1, 0, 1), 10)
    assert isclose(calculate_position_size(3000, 1, 0, 2), 60)
    assert isclose(calculate_position_size(1000, 1, 0.99, 1), 1000)
    assert isclose(calculate_position_size(1000, 1, 0.5, 1), 20)


