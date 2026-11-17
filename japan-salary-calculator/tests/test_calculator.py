import json
from decimal import Decimal

import pytest

from jp_salary import SalaryInput, calculate
from jp_salary.cli import main


def test_reference_case_300k_monthly_2026():
    """Hand-calculated: see README 'How the calculation works'."""
    r = calculate(SalaryInput(monthly_salary=300_000))
    assert r.gross_annual == 3_600_000
    assert r.social_insurance.total == 529_740
    assert r.employment_income_deduction == 1_160_000
    assert r.employment_income == 2_440_000
    assert r.basic_deduction == 1_040_000
    assert r.taxable_income == 870_000
    assert r.income_tax == 44_400
    assert r.resident_taxable_income == 1_480_000
    assert r.adjustment_credit == 2_500
    assert r.resident_tax == 150_500
    assert r.net_annual == 3_600_000 - 529_740 - 44_400 - 150_500


def test_no_income_tax_below_the_wall():
    assert calculate(SalaryInput(monthly_salary=100_000)).income_tax == 0
    assert calculate(SalaryInput(monthly_salary=100_000, tax_year=2025)).income_tax == 0


def test_2026_is_never_worse_than_2025_for_same_pay():
    for monthly in (150_000, 250_000, 400_000, 600_000):
        old = calculate(SalaryInput(monthly_salary=monthly, tax_year=2025))
        new = calculate(SalaryInput(monthly_salary=monthly, tax_year=2026))
        assert new.income_tax <= old.income_tax


def test_dependents_and_spouse_reduce_tax():
    base = calculate(SalaryInput(monthly_salary=400_000, bonuses=(800_000, 800_000)))
    family = calculate(SalaryInput(monthly_salary=400_000, bonuses=(800_000, 800_000), spouse=True, dependents=2))
    assert family.spouse_deduction == 380_000
    assert family.dependent_deduction == 760_000
    assert family.income_tax < base.income_tax
    assert family.resident_tax < base.resident_tax


def test_commuting_allowance_insured_but_tax_free():
    plain = calculate(SalaryInput(monthly_salary=300_000))
    with_commute = calculate(SalaryInput(monthly_salary=300_000, commuting_allowance=20_000))
    assert with_commute.gross_annual == plain.gross_annual + 240_000
    assert with_commute.taxable_gross == plain.taxable_gross  # tax-free
    assert with_commute.social_insurance.total > plain.social_insurance.total


def test_age_45_pays_nursing_care():
    assert calculate(SalaryInput(monthly_salary=300_000, age=45)).social_insurance.nursing == 2_430 * 12


def test_custom_health_rate_changes_premium():
    default = calculate(SalaryInput(monthly_salary=300_000))
    pricier = calculate(SalaryInput(monthly_salary=300_000, health_rate=Decimal("0.1124")))
    assert pricier.social_insurance.health > default.social_insurance.health


def test_net_pay_is_consistent():
    r = calculate(SalaryInput(monthly_salary=500_000, bonuses=(1_000_000, 1_000_000)))
    assert r.net_annual == r.gross_annual - r.social_insurance.total - r.income_tax - r.resident_tax
    assert 0 < r.deduction_rate < Decimal("0.4")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"monthly_salary": -1},
        {"monthly_salary": 300_000, "bonuses": (-1,)},
        {"monthly_salary": 300_000, "age": 10},
        {"monthly_salary": 300_000, "dependents": -1},
        {"monthly_salary": 300_000, "health_rate": Decimal("9.9")},  # percent by mistake
    ],
)
def test_invalid_input_rejected(kwargs):
    with pytest.raises(ValueError):
        SalaryInput(**kwargs)


def test_unsupported_year_rejected():
    with pytest.raises(ValueError):
        calculate(SalaryInput(monthly_salary=300_000, tax_year=1999))


def test_cli_json(capsys):
    assert main(["300000", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["income_tax"] == 44_400
    assert data["social_insurance"]["total"] == 529_740


def test_cli_report(capsys):
    assert main(["300000", "--bonus", "600000", "--bonus", "600000", "--year", "2025"]) == 0
    assert "tax year 2025" in capsys.readouterr().out
