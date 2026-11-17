"""Employee share of social insurance (社会保険料).

Premiums are based on the 標準報酬月額 (standard monthly remuneration) grade,
not the exact salary. Bonuses use 標準賞与額 (truncated to 1,000 yen) with caps.
"""
from __future__ import annotations

from bisect import bisect_right
from decimal import Decimal

from .models import SocialInsurance
from .rounding import floor_to, round_half_down
from .rules import SocialInsuranceRates

# 健康保険 grades 1-50: (lower bound of monthly pay, 標準報酬月額)
_GRADES: tuple[tuple[int, int], ...] = (
    (0, 58_000), (63_000, 68_000), (73_000, 78_000), (83_000, 88_000), (93_000, 98_000),
    (101_000, 104_000), (107_000, 110_000), (114_000, 118_000), (122_000, 126_000), (130_000, 134_000),
    (138_000, 142_000), (146_000, 150_000), (155_000, 160_000), (165_000, 170_000), (175_000, 180_000),
    (185_000, 190_000), (195_000, 200_000), (210_000, 220_000), (230_000, 240_000), (250_000, 260_000),
    (270_000, 280_000), (290_000, 300_000), (310_000, 320_000), (330_000, 340_000), (350_000, 360_000),
    (370_000, 380_000), (395_000, 410_000), (425_000, 440_000), (455_000, 470_000), (485_000, 500_000),
    (515_000, 530_000), (545_000, 560_000), (575_000, 590_000), (605_000, 620_000), (635_000, 650_000),
    (665_000, 680_000), (695_000, 710_000), (730_000, 750_000), (770_000, 790_000), (810_000, 830_000),
    (855_000, 880_000), (905_000, 930_000), (955_000, 980_000), (1_005_000, 1_030_000), (1_055_000, 1_090_000),
    (1_115_000, 1_150_000), (1_175_000, 1_210_000), (1_235_000, 1_270_000), (1_295_000, 1_330_000),
    (1_355_000, 1_390_000),
)
_LOWER_BOUNDS = [lo for lo, _ in _GRADES]

PENSION_MIN_STANDARD = 88_000  # 厚生年金 grades are the health grades clamped
PENSION_MAX_STANDARD = 650_000  # to 88,000 .. 650,000
HEALTH_BONUS_ANNUAL_CAP = 5_730_000  # 標準賞与額, per fiscal year
PENSION_BONUS_CAP = 1_500_000  # 標準賞与額, per payment

NURSING_AGES = range(40, 65)  # 介護保険 second insured persons
HEALTH_MAX_AGE = 74  # 75+ moves to 後期高齢者医療
PENSION_MAX_AGE = 69  # 70+ stops 厚生年金 contributions


def standard_monthly_remuneration(monthly_pay: int) -> int:
    """標準報酬月額 for a monthly pay amount (incl. commuting allowance)."""
    return _GRADES[bisect_right(_LOWER_BOUNDS, monthly_pay) - 1][1]


def _employee_half(base: int, total_rate: Decimal) -> int:
    return round_half_down(Decimal(base) * total_rate / 2)


def monthly_premiums(monthly_pay: int, age: int, rates: SocialInsuranceRates) -> SocialInsurance:
    std = standard_monthly_remuneration(monthly_pay)
    pension_std = min(max(std, PENSION_MIN_STANDARD), PENSION_MAX_STANDARD)
    covered_health = age <= HEALTH_MAX_AGE
    return SocialInsurance(
        health=_employee_half(std, rates.health) if covered_health else 0,
        nursing=_employee_half(std, rates.nursing) if age in NURSING_AGES else 0,
        child_support=_employee_half(std, rates.child_support) if covered_health else 0,
        pension=_employee_half(pension_std, rates.pension) if age <= PENSION_MAX_AGE else 0,
        employment=round_half_down(Decimal(monthly_pay) * rates.employment_employee),
    )


def bonus_premiums(
    bonus: int, health_standard_used: int, age: int, rates: SocialInsuranceRates
) -> tuple[SocialInsurance, int]:
    """Premiums for one bonus. Returns (premiums, updated fiscal-year health base)."""
    std = floor_to(bonus, 1_000)
    health_std = min(std, max(0, HEALTH_BONUS_ANNUAL_CAP - health_standard_used))
    pension_std = min(std, PENSION_BONUS_CAP)
    covered_health = age <= HEALTH_MAX_AGE
    premiums = SocialInsurance(
        health=_employee_half(health_std, rates.health) if covered_health else 0,
        nursing=_employee_half(health_std, rates.nursing) if age in NURSING_AGES else 0,
        child_support=_employee_half(health_std, rates.child_support) if covered_health else 0,
        pension=_employee_half(pension_std, rates.pension) if age <= PENSION_MAX_AGE else 0,
        employment=round_half_down(Decimal(bonus) * rates.employment_employee),
    )
    return premiums, health_standard_used + health_std


def annual_social_insurance(
    monthly_pay: int, bonuses: tuple[int, ...], age: int, rates: SocialInsuranceRates
) -> SocialInsurance:
    """12 months of salary premiums plus premiums on every bonus."""
    month = monthly_premiums(monthly_pay, age, rates)
    total = SocialInsurance(
        month.health * 12,
        month.nursing * 12,
        month.child_support * 12,
        month.pension * 12,
        month.employment * 12,
    )
    health_used = 0
    for bonus in bonuses:
        premiums, health_used = bonus_premiums(bonus, health_used, age, rates)
        total = total + premiums
    return total
