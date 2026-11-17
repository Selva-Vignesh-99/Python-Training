"""Command line interface: `jp-salary 300000 --bonus 600000 --bonus 600000`."""
from __future__ import annotations

import argparse
import json
from decimal import Decimal

from .calculator import calculate
from .models import SalaryInput
from .report import format_report
from .rules import RULES


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jp-salary", description="Estimate take-home pay in Japan.")
    p.add_argument("monthly_salary", type=int, help="monthly base pay in yen (before deductions)")
    p.add_argument("--bonus", type=int, action="append", default=[], help="a bonus payment; repeatable")
    p.add_argument("--commuting", type=int, default=0, help="monthly commuting allowance")
    p.add_argument("--age", type=int, default=30)
    p.add_argument("--year", type=int, default=max(RULES), choices=sorted(RULES), help="tax year")
    p.add_argument("--spouse", action="store_true", help="eligible spouse (配偶者控除)")
    p.add_argument("--dependents", type=int, default=0, help="number of general dependents (16+)")
    p.add_argument("--other-deductions", type=int, default=0, help="e.g. iDeCo / life insurance, yen/year")
    p.add_argument(
        "--health-rate",
        type=Decimal,
        help="total health insurance rate in percent for your prefecture, e.g. 9.9 (default: national average)",
    )
    p.add_argument("--json", action="store_true", help="print JSON instead of a report")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        inp = SalaryInput(
            monthly_salary=args.monthly_salary,
            bonuses=tuple(args.bonus),
            commuting_allowance=args.commuting,
            age=args.age,
            tax_year=args.year,
            spouse=args.spouse,
            dependents=args.dependents,
            other_deductions=args.other_deductions,
            health_rate=None if args.health_rate is None else args.health_rate / 100,
        )
    except ValueError as exc:
        build_parser().error(str(exc))
    result = calculate(inp)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) if args.json else format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
