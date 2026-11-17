from decimal import Decimal

from jp_salary.rounding import floor_mul, floor_to, round_half_down


def test_round_half_down_boundary():
    assert round_half_down(Decimal("14850.50")) == 14850  # 50銭以下は切り捨て
    assert round_half_down(Decimal("14850.51")) == 14851  # 50銭超は切り上げ


def test_floor_helpers():
    assert floor_to(870_260, 1_000) == 870_000
    assert floor_mul(572_500, Decimal("0.021")) == 12_022
