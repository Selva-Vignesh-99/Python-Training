"""National income tax (所得税) building blocks."""
from __future__ import annotations

from .rounding import floor_mul, floor_to
from .rules import INCOME_TAX_BRACKETS, EmploymentDeductionRule, TaxYearRules, band_amount

COMMUTING_TAX_FREE_LIMIT = 150_000  # per month (非課税通勤手当)


def employment_income_deduction(gross: int, rule: EmploymentDeductionRule) -> int:
    """給与所得控除. Fractions of a yen are truncated."""
    if gross <= rule.flat_until:
        return min(gross, rule.minimum)
    if gross <= 3_600_000:
        return gross * 30 // 100 + 80_000
    if gross <= 6_600_000:
        return gross * 20 // 100 + 440_000
    if gross <= 8_500_000:
        return gross * 10 // 100 + 1_100_000
    return 1_950_000


def basic_deduction(total_income: int, rules: TaxYearRules) -> int:
    return band_amount(rules.basic_deduction_income_tax, total_income)


def spouse_deduction(total_income: int, rules: TaxYearRules) -> int:
    return band_amount(rules.spouse_deduction_income_tax, total_income)


def income_tax(taxable_income: int, rules: TaxYearRules) -> tuple[int, int, int]:
    """Returns (base tax, reconstruction surtax, total).

    Taxable income is truncated to 1,000 yen; the total (tax + 復興特別所得税
    2.1%) is truncated to 100 yen.
    """
    taxable = floor_to(max(0, taxable_income), 1_000)
    for bracket in INCOME_TAX_BRACKETS:
        if bracket.upper is None or taxable <= bracket.upper:
            base = floor_mul(taxable, bracket.rate) - bracket.deduction
            break
    base = max(0, base)
    recon = floor_mul(base, rules.reconstruction_rate)
    return base, recon, floor_to(base + recon, 100)
