"""Resident tax (住民税 = municipal + prefectural), estimated.

Real resident tax is billed the *following* June based on the previous year's
income. This module estimates the steady-state annual amount using the same
year's income, which is what is useful for a take-home comparison.
"""
from __future__ import annotations

from dataclasses import dataclass

from .rounding import floor_to
from .rules import TaxYearRules, band_amount

INCOME_LEVY_RATE_PERCENT = 10  # 6% municipal + 4% prefectural
PER_CAPITA_LEVY = 5_000  # 均等割 incl. 森林環境税 (varies slightly by locality)


@dataclass(frozen=True)
class ResidentTax:
    taxable_income: int
    adjustment_credit: int
    total: int


def adjustment_credit(
    taxable_income: int, total_income: int, spouse: bool, dependents: int, rules: TaxYearRules
) -> int:
    """調整控除: compensates for resident-tax personal deductions being lower
    than income-tax ones. Uses the legislated difference amounts."""
    if total_income > 25_000_000:
        return 0
    basic_diff = band_amount(((24_000_000, 50_000), (24_500_000, 30_000), (25_000_000, 10_000)), total_income)
    spouse_diff = 0
    if spouse:
        spouse_diff = band_amount(rules.spouse_deduction_income_tax, total_income) - band_amount(
            rules.spouse_deduction_resident, total_income
        )
    diff = basic_diff + spouse_diff + dependents * 50_000
    if taxable_income <= 2_000_000:
        base = min(diff, taxable_income)
    else:
        base = max(diff - (taxable_income - 2_000_000), 50_000)
    return base * 5 // 100


def resident_tax(
    employment_income: int,
    social_insurance: int,
    spouse: bool,
    dependents: int,
    other_deductions: int,
    rules: TaxYearRules,
) -> ResidentTax:
    deductions = (
        social_insurance
        + band_amount(rules.basic_deduction_resident, employment_income)
        + (band_amount(rules.spouse_deduction_resident, employment_income) if spouse else 0)
        + dependents * rules.dependent_deduction_resident
        + other_deductions
    )
    taxable = floor_to(max(0, employment_income - deductions), 1_000)
    if taxable == 0:
        return ResidentTax(0, 0, 0)  # simplification: ignores 非課税 thresholds
    credit = adjustment_credit(taxable, employment_income, spouse, dependents, rules)
    income_levy = floor_to(max(0, taxable * INCOME_LEVY_RATE_PERCENT // 100 - credit), 100)
    return ResidentTax(taxable, credit, income_levy + PER_CAPITA_LEVY)
