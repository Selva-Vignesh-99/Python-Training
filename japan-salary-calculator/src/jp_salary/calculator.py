"""Orchestrates the full pipeline: salary -> social insurance -> taxes -> net."""
from __future__ import annotations

from dataclasses import replace

from .income_tax import (
    COMMUTING_TAX_FREE_LIMIT,
    basic_deduction,
    employment_income_deduction,
    income_tax,
    spouse_deduction,
)
from .models import SalaryInput, SalaryResult
from .resident_tax import resident_tax
from .rules import get_rules
from .social_insurance import annual_social_insurance


def calculate(inp: SalaryInput) -> SalaryResult:
    rules = get_rules(inp.tax_year)
    rates = rules.social if inp.health_rate is None else replace(rules.social, health=inp.health_rate)

    # 1. Social insurance is based on everything paid, incl. commuting allowance.
    monthly_pay = inp.monthly_salary + inp.commuting_allowance
    bonus_total = sum(inp.bonuses)
    gross_annual = monthly_pay * 12 + bonus_total
    social = annual_social_insurance(monthly_pay, inp.bonuses, inp.age, rates)

    # 2. Taxable pay excludes the tax-free part of the commuting allowance.
    taxable_commuting = max(0, inp.commuting_allowance - COMMUTING_TAX_FREE_LIMIT) * 12
    taxable_gross = inp.monthly_salary * 12 + taxable_commuting + bonus_total

    # 3. 給与所得 = 収入 - 給与所得控除
    emp_deduction = employment_income_deduction(taxable_gross, rules.employment_deduction)
    employment_income = taxable_gross - emp_deduction

    # 4. Income tax deductions and tax.
    basic = basic_deduction(employment_income, rules)
    spouse = spouse_deduction(employment_income, rules) if inp.spouse else 0
    dependents = inp.dependents * rules.dependent_deduction_income_tax
    taxable_income = max(
        0, employment_income - (social.total + basic + spouse + dependents + inp.other_deductions)
    )
    base_tax, recon_tax, total_tax = income_tax(taxable_income, rules)

    # 5. Resident tax (estimate).
    resident = resident_tax(
        employment_income, social.total, inp.spouse, inp.dependents, inp.other_deductions, rules
    )

    return SalaryResult(
        tax_year=inp.tax_year,
        gross_annual=gross_annual,
        taxable_gross=taxable_gross,
        social_insurance=social,
        employment_income_deduction=emp_deduction,
        employment_income=employment_income,
        basic_deduction=basic,
        spouse_deduction=spouse,
        dependent_deduction=dependents,
        other_deductions=inp.other_deductions,
        taxable_income=(taxable_income // 1_000) * 1_000,
        income_tax_base=base_tax,
        reconstruction_tax=recon_tax,
        income_tax=total_tax,
        resident_taxable_income=resident.taxable_income,
        adjustment_credit=resident.adjustment_credit,
        resident_tax=resident.total,
    )
