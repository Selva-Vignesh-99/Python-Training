"""Immutable input/output value objects."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Optional


@dataclass(frozen=True)
class SalaryInput:
    monthly_salary: int  # taxable base pay per month (yen)
    bonuses: tuple[int, ...] = ()  # each bonus payment (yen)
    commuting_allowance: int = 0  # monthly; tax-free up to 150,000, but insured
    age: int = 30  # decides 介護保険 (40-64) and pension/health eligibility
    tax_year: int = 2026
    spouse: bool = False  # has a 同一生計配偶者 eligible for 配偶者控除
    dependents: int = 0  # 一般の扶養親族 (age 16+; 38万 income-tax deduction)
    other_deductions: int = 0  # e.g. life insurance, iDeCo (applied to both taxes)
    health_rate: Optional[Decimal] = None  # total 健康保険料率, e.g. Decimal("0.0990")

    def __post_init__(self) -> None:
        if self.monthly_salary < 0 or self.commuting_allowance < 0:
            raise ValueError("salary and allowance must be >= 0")
        if any(b < 0 for b in self.bonuses):
            raise ValueError("bonuses must be >= 0")
        if self.dependents < 0 or self.other_deductions < 0:
            raise ValueError("dependents and other_deductions must be >= 0")
        if not 15 <= self.age <= 100:
            raise ValueError("age must be between 15 and 100")
        if self.health_rate is not None and not Decimal(0) < self.health_rate < Decimal("0.2"):
            raise ValueError("health_rate must be a fraction, e.g. 0.099 for 9.9%")


@dataclass(frozen=True)
class SocialInsurance:
    """Employee share of 社会保険 (yen)."""

    health: int = 0
    nursing: int = 0
    child_support: int = 0
    pension: int = 0
    employment: int = 0

    @property
    def total(self) -> int:
        return self.health + self.nursing + self.child_support + self.pension + self.employment

    def __add__(self, other: SocialInsurance) -> SocialInsurance:
        return SocialInsurance(
            self.health + other.health,
            self.nursing + other.nursing,
            self.child_support + other.child_support,
            self.pension + other.pension,
            self.employment + other.employment,
        )


@dataclass(frozen=True)
class SalaryResult:
    tax_year: int
    gross_annual: int  # everything paid, incl. tax-free commuting
    taxable_gross: int  # 給与等の収入金額 used for tax
    social_insurance: SocialInsurance
    employment_income_deduction: int  # 給与所得控除
    employment_income: int  # 給与所得
    basic_deduction: int
    spouse_deduction: int
    dependent_deduction: int
    other_deductions: int
    taxable_income: int  # 課税所得 (income tax)
    income_tax_base: int
    reconstruction_tax: int
    income_tax: int  # incl. 復興特別所得税
    resident_taxable_income: int
    adjustment_credit: int  # 調整控除
    resident_tax: int  # 所得割 + 均等割

    @property
    def total_deductions(self) -> int:
        return self.social_insurance.total + self.income_tax + self.resident_tax

    @property
    def net_annual(self) -> int:
        return self.gross_annual - self.total_deductions

    @property
    def net_monthly_average(self) -> int:
        return self.net_annual // 12

    @property
    def deduction_rate(self) -> Decimal:
        if self.gross_annual == 0:
            return Decimal(0)
        return Decimal(self.total_deductions) / Decimal(self.gross_annual)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["social_insurance"]["total"] = self.social_insurance.total
        data["total_deductions"] = self.total_deductions
        data["net_annual"] = self.net_annual
        data["net_monthly_average"] = self.net_monthly_average
        data["deduction_rate"] = float(round(self.deduction_rate, 4))
        return data
