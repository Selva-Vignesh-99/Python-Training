"""Statutory parameters for each tax year.

Everything that changes with legislation lives here as data, so supporting a
new year means adding a `TaxYearRules` entry -- no calculation code changes.

Always verify against the primary sources (NTA / 協会けんぽ / MHLW) before
relying on the numbers: see README "Updating for a new year".
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal as D
from typing import Optional

# (inclusive upper bound or None for "no limit", amount)
Band = tuple[Optional[int], int]


def band_amount(bands: tuple[Band, ...], value: int) -> int:
    for upper, amount in bands:
        if upper is None or value <= upper:
            return amount
    raise ValueError("bands must end with an open-ended entry")


@dataclass(frozen=True)
class IncomeTaxBracket:
    upper: Optional[int]  # taxable income, inclusive; None = no limit
    rate: D
    deduction: int


# 所得税の速算表 (unchanged for 2025 and 2026)
INCOME_TAX_BRACKETS: tuple[IncomeTaxBracket, ...] = (
    IncomeTaxBracket(1_950_000, D("0.05"), 0),
    IncomeTaxBracket(3_300_000, D("0.10"), 97_500),
    IncomeTaxBracket(6_950_000, D("0.20"), 427_500),
    IncomeTaxBracket(9_000_000, D("0.23"), 636_000),
    IncomeTaxBracket(18_000_000, D("0.33"), 1_536_000),
    IncomeTaxBracket(40_000_000, D("0.40"), 2_796_000),
    IncomeTaxBracket(None, D("0.45"), 4_796_000),
)


@dataclass(frozen=True)
class EmploymentDeductionRule:
    """給与所得控除. `minimum` applies flat up to `flat_until`; above that the
    standard 30% / 20% / 10% bands apply (identical in both years)."""

    minimum: int
    flat_until: int


@dataclass(frozen=True)
class SocialInsuranceRates:
    """Total rates (employee + employer) unless noted. Employee pays half."""

    health: D  # 健康保険 (prefecture-specific for 協会けんぽ)
    nursing: D  # 介護保険, ages 40-64
    child_support: D  # 子ども・子育て支援金 (from Apr 2026)
    pension: D  # 厚生年金
    employment_employee: D  # 雇用保険, employee share only


@dataclass(frozen=True)
class TaxYearRules:
    year: int
    employment_deduction: EmploymentDeductionRule
    basic_deduction_income_tax: tuple[Band, ...]  # keyed by 合計所得金額
    basic_deduction_resident: tuple[Band, ...]
    spouse_deduction_income_tax: tuple[Band, ...]  # keyed by taxpayer's income
    spouse_deduction_resident: tuple[Band, ...]
    dependent_deduction_income_tax: int  # 一般の扶養控除
    dependent_deduction_resident: int
    reconstruction_rate: D  # 復興特別所得税
    social: SocialInsuranceRates


_SPOUSE_IT: tuple[Band, ...] = ((9_000_000, 380_000), (9_500_000, 260_000), (10_000_000, 130_000), (None, 0))
_SPOUSE_RES: tuple[Band, ...] = ((9_000_000, 330_000), (9_500_000, 220_000), (10_000_000, 110_000), (None, 0))

# 住民税 basic deduction: not raised by the 2025/2026 reforms
_BASIC_RES: tuple[Band, ...] = ((24_000_000, 430_000), (24_500_000, 290_000), (25_000_000, 150_000), (None, 0))

RULES: dict[int, TaxYearRules] = {
    2025: TaxYearRules(
        year=2025,
        employment_deduction=EmploymentDeductionRule(minimum=650_000, flat_until=1_900_000),
        basic_deduction_income_tax=(
            (1_320_000, 950_000),
            (3_360_000, 880_000),
            (4_890_000, 680_000),
            (6_550_000, 630_000),
            (23_500_000, 580_000),
            (24_000_000, 480_000),
            (24_500_000, 320_000),
            (25_000_000, 160_000),
            (None, 0),
        ),
        basic_deduction_resident=_BASIC_RES,
        spouse_deduction_income_tax=_SPOUSE_IT,
        spouse_deduction_resident=_SPOUSE_RES,
        dependent_deduction_income_tax=380_000,
        dependent_deduction_resident=330_000,
        reconstruction_rate=D("0.021"),
        social=SocialInsuranceRates(
            health=D("0.1000"),  # national average of 協会けんぽ; override per prefecture
            nursing=D("0.0159"),
            child_support=D("0"),
            pension=D("0.183"),
            employment_employee=D("0.0055"),
        ),
    ),
    # 令和8年分. Note: the higher deductions reach actual withholding only at
    # the December 2026 year-end adjustment (年末調整); this models the annual
    # liability, i.e. the result after 年末調整.
    2026: TaxYearRules(
        year=2026,
        employment_deduction=EmploymentDeductionRule(minimum=740_000, flat_until=2_200_000),
        basic_deduction_income_tax=(
            (4_890_000, 1_040_000),  # 62万 + 特例42万
            (6_550_000, 670_000),  # 62万 + 特例5万
            (23_500_000, 620_000),
            (24_000_000, 480_000),
            (24_500_000, 320_000),
            (25_000_000, 160_000),
            (None, 0),
        ),
        basic_deduction_resident=_BASIC_RES,
        spouse_deduction_income_tax=_SPOUSE_IT,
        spouse_deduction_resident=_SPOUSE_RES,
        dependent_deduction_income_tax=380_000,
        dependent_deduction_resident=330_000,
        reconstruction_rate=D("0.021"),
        social=SocialInsuranceRates(
            health=D("0.0990"),  # national average of 協会けんぽ; override per prefecture
            nursing=D("0.0162"),
            child_support=D("0.0023"),
            pension=D("0.183"),
            employment_employee=D("0.005"),
        ),
    ),
}


def get_rules(year: int) -> TaxYearRules:
    try:
        return RULES[year]
    except KeyError:
        raise ValueError(f"No rules for {year}; supported: {sorted(RULES)}") from None
