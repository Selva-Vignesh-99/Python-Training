"""Human-readable report."""
from __future__ import annotations

from .models import SalaryResult


def _yen(value: int) -> str:
    return f"¥{value:>12,}"


def format_report(r: SalaryResult) -> str:
    si = r.social_insurance
    lines = [
        f"Japan salary breakdown (tax year {r.tax_year})",
        "=" * 46,
        f"Gross annual pay            {_yen(r.gross_annual)}",
        "",
        "Social insurance (employee share)",
        f"  Health insurance          {_yen(si.health)}",
        f"  Nursing care (40-64)      {_yen(si.nursing)}",
        f"  Child support levy        {_yen(si.child_support)}",
        f"  Pension (厚生年金)        {_yen(si.pension)}",
        f"  Employment insurance      {_yen(si.employment)}",
        f"  Subtotal                  {_yen(si.total)}",
        "",
        "Income tax (所得税)",
        f"  Employment income         {_yen(r.employment_income)}  (after 給与所得控除 {r.employment_income_deduction:,})",
        f"  Basic deduction           {_yen(r.basic_deduction)}",
        f"  Spouse / dependents       {_yen(r.spouse_deduction + r.dependent_deduction)}",
        f"  Other deductions          {_yen(r.other_deductions)}",
        f"  Taxable income            {_yen(r.taxable_income)}",
        f"  Tax incl. 復興特別所得税   {_yen(r.income_tax)}",
        "",
        "Resident tax (住民税, estimate)",
        f"  Taxable income            {_yen(r.resident_taxable_income)}",
        f"  Annual amount             {_yen(r.resident_tax)}",
        "",
        "-" * 46,
        f"Total deductions            {_yen(r.total_deductions)}  ({r.deduction_rate:.1%})",
        f"Net annual                  {_yen(r.net_annual)}",
        f"Net monthly (average)       {_yen(r.net_monthly_average)}",
    ]
    return "\n".join(lines)
