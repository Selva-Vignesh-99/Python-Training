from decimal import Decimal

import pytest

from jp_salary.rules import get_rules
from jp_salary.social_insurance import (
    _GRADES,
    annual_social_insurance,
    bonus_premiums,
    monthly_premiums,
    standard_monthly_remuneration,
)

R2026 = get_rules(2026).social


def test_grade_table_has_50_grades():
    assert len(_GRADES) == 50


@pytest.mark.parametrize(
    "pay, expected",
    [
        (0, 58_000),
        (62_999, 58_000),
        (63_000, 68_000),
        (299_999, 300_000),
        (309_999, 300_000),
        (310_000, 320_000),
        (1_354_999, 1_330_000),
        (5_000_000, 1_390_000),
    ],
)
def test_standard_monthly_remuneration(pay, expected):
    assert standard_monthly_remuneration(pay) == expected


def test_monthly_premiums_age_30():
    p = monthly_premiums(300_000, 30, R2026)
    assert p.health == 14_850  # 300,000 x 9.90% / 2
    assert p.nursing == 0
    assert p.child_support == 345  # 300,000 x 0.23% / 2
    assert p.pension == 27_450  # 300,000 x 18.3% / 2
    assert p.employment == 1_500  # 300,000 x 0.5%


def test_nursing_care_only_for_40_to_64():
    assert monthly_premiums(300_000, 39, R2026).nursing == 0
    assert monthly_premiums(300_000, 40, R2026).nursing == 2_430
    assert monthly_premiums(300_000, 64, R2026).nursing == 2_430
    assert monthly_premiums(300_000, 65, R2026).nursing == 0


def test_pension_standard_is_capped():
    # standard remuneration 1,390,000 -> pension base capped at 650,000
    p = monthly_premiums(1_500_000, 30, R2026)
    assert p.pension == round(650_000 * 0.183 / 2)


def test_bonus_premiums_and_pension_cap():
    p, used = bonus_premiums(600_000, 0, 30, R2026)
    assert (p.health, p.pension, p.employment) == (29_700, 54_900, 3_000)
    assert used == 600_000
    big, _ = bonus_premiums(2_000_000, 0, 30, R2026)
    assert big.pension == 137_250  # capped at 1.5M x 18.3% / 2


def test_bonus_health_annual_cap():
    # 5.73M annual cap: the third 2.5M bonus only has 730k left
    p, used = bonus_premiums(2_500_000, 5_000_000, 30, R2026)
    assert used == 5_730_000
    assert p.health == round(730_000 * 0.099 / 2)


def test_annual_total_matches_months_plus_bonuses():
    total = annual_social_insurance(300_000, (600_000, 600_000), 30, R2026)
    assert total.health == 14_850 * 12 + 29_700 * 2
    assert total.total == total.health + total.nursing + total.child_support + total.pension + total.employment


def test_custom_health_rate():
    custom = type(R2026)(**{**R2026.__dict__, "health": Decimal("0.1000")})
    assert monthly_premiums(300_000, 30, custom).health == 15_000
