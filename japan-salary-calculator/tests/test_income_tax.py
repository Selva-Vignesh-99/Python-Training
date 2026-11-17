import pytest

from jp_salary.income_tax import basic_deduction, employment_income_deduction, income_tax
from jp_salary.rules import get_rules

R25, R26 = get_rules(2025), get_rules(2026)


@pytest.mark.parametrize(
    "gross, expected",
    [
        (1_780_000, 740_000),
        (2_200_000, 740_000),  # continuous with 30% + 80,000 at the boundary
        (3_600_000, 1_160_000),
        (5_000_000, 1_440_000),
        (7_000_000, 1_800_000),
        (10_000_000, 1_950_000),
        (500_000, 500_000),  # deduction can't exceed the pay itself
    ],
)
def test_employment_deduction_2026(gross, expected):
    assert employment_income_deduction(gross, R26.employment_deduction) == expected


def test_employment_deduction_2025():
    assert employment_income_deduction(1_600_000, R25.employment_deduction) == 650_000
    assert employment_income_deduction(2_500_000, R25.employment_deduction) == 830_000


@pytest.mark.parametrize(
    "income, expected",
    [(1_040_000, 1_040_000), (4_890_000, 1_040_000), (4_891_000, 670_000),
     (6_550_000, 670_000), (7_000_000, 620_000), (24_000_001, 320_000), (26_000_000, 0)],
)
def test_basic_deduction_2026(income, expected):
    assert basic_deduction(income, R26) == expected


@pytest.mark.parametrize("income, expected", [(1_320_000, 950_000), (2_000_000, 880_000), (4_000_000, 680_000)])
def test_basic_deduction_2025(income, expected):
    assert basic_deduction(income, R25) == expected


def test_zero_tax_threshold_matches_government_figures():
    """年収の壁: 160万円 (2025) and 178万円 (2026) with no other deductions."""
    income_25 = 1_600_000 - employment_income_deduction(1_600_000, R25.employment_deduction)
    income_26 = 1_780_000 - employment_income_deduction(1_780_000, R26.employment_deduction)
    assert income_25 - basic_deduction(income_25, R25) == 0
    assert income_26 - basic_deduction(income_26, R26) == 0


def test_income_tax_lowest_bracket():
    assert income_tax(870_000, R26) == (43_500, 913, 44_400)


def test_income_tax_middle_bracket():
    assert income_tax(5_000_000, R26) == (572_500, 12_022, 584_500)


def test_income_tax_truncates_taxable_income_to_1000():
    assert income_tax(870_999, R26) == income_tax(870_000, R26)


def test_income_tax_zero_and_negative():
    assert income_tax(0, R26) == (0, 0, 0)
    assert income_tax(-5, R26) == (0, 0, 0)


def test_income_tax_top_bracket():
    base, _, _ = income_tax(50_000_000, R26)
    assert base == 50_000_000 * 45 // 100 - 4_796_000
