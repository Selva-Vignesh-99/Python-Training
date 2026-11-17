"""Rounding helpers. Money is handled as int yen; rates as Decimal (never float)."""
from decimal import ROUND_FLOOR, ROUND_HALF_DOWN, Decimal


def round_half_down(value: Decimal | int | str) -> int:
    """50銭以下切り捨て・50銭超切り上げ.

    The rule used when an employee's share of social insurance is deducted
    from salary (0.50 yen rounds down, 0.51 yen rounds up).
    """
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_DOWN))


def floor_to(value: int, unit: int) -> int:
    """Truncate to a multiple of `unit` (e.g. 1,000 yen for taxable income)."""
    return value // unit * unit


def floor_mul(amount: int, rate: Decimal) -> int:
    """amount * rate, truncated to whole yen."""
    return int((Decimal(amount) * rate).to_integral_value(rounding=ROUND_FLOOR))
