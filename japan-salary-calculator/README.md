# jp-salary — Japan take-home pay calculator

A small, dependency-free Python library and CLI that estimates what is deducted from a salary in Japan and what ends up in your bank account:

- **Social insurance** (employee share): health (健康保険), nursing care (介護保険), child support levy (子ども・子育て支援金), employee pension (厚生年金), employment insurance (雇用保険)
- **Income tax** (所得税 + 復興特別所得税) with 給与所得控除 and 基礎控除
- **Resident tax** (住民税) estimate, including 調整控除 and 均等割
- Spouse / dependent / other deductions, commuting allowance, bonuses
- Tax-year rule sets for **2025** and **2026** (令和8年度税制改正 included)

## Quick start

```bash
pip install -e ".[dev]"
pytest

jp-salary 300000                                  # ¥300,000/month, 2026 rules
jp-salary 400000 --bonus 800000 --bonus 800000 --commuting 15000 --spouse --dependents 1
jp-salary 300000 --year 2025 --json               # compare years / machine-readable
jp-salary 300000 --health-rate 9.9                # your prefecture's rate, in percent
```

```
Japan salary breakdown (tax year 2026)
==============================================
Gross annual pay            ¥   6,580,000

Social insurance (employee share)
  Health insurance          ¥     322,740
  Nursing care (40-64)      ¥           0
  Child support levy        ¥       7,492
  Pension (厚生年金)        ¥     596,580
  Employment insurance      ¥      32,900
  Subtotal                  ¥     959,712

Income tax (所得税)
  Employment income         ¥   4,680,000  (after 給与所得控除 1,720,000)
  Basic deduction           ¥   1,040,000
  Spouse / dependents       ¥     760,000
  Other deductions          ¥           0
  Taxable income            ¥   1,920,000
  Tax incl. 復興特別所得税   ¥      98,000

Resident tax (住民税, estimate)
  Taxable income            ¥   2,630,000
  Annual amount             ¥     265,500

----------------------------------------------
Total deductions            ¥   1,323,212  (20.1%)
Net annual                  ¥   5,256,788
Net monthly (average)       ¥     438,065
```

As a library:

```python
from jp_salary import SalaryInput, calculate

result = calculate(SalaryInput(monthly_salary=300_000, bonuses=(600_000, 600_000), age=45))
print(result.net_annual, result.income_tax, result.social_insurance.total)
```

## Project layout

```
src/jp_salary/
  rules.py             statutory parameters per tax year (data only)
  models.py            immutable SalaryInput / SalaryResult / SocialInsurance
  rounding.py          Decimal-based rounding helpers (50銭 rule, floor to 100/1000 yen)
  social_insurance.py  標準報酬月額 grade lookup, monthly + bonus premiums, caps
  income_tax.py        給与所得控除, 基礎控除, 速算表, 復興特別所得税
  resident_tax.py      住民税 income levy, 調整控除, 均等割
  calculator.py        pipeline orchestration
  report.py / cli.py   presentation
tests/                 58 tests incl. hand-calculated reference cases
```

## How the calculation works

Reference case: ¥300,000/month, no bonus, age 30, 2026 rules.

1. **Social insurance.** 標準報酬月額 = ¥300,000 → health 9.90% ÷ 2 = ¥14,850, child support 0.23% ÷ 2 = ¥345, pension 18.3% ÷ 2 = ¥27,450, employment 0.5% = ¥1,500 per month → **¥529,740/year**.
2. **給与所得** = ¥3,600,000 − 給与所得控除 (30% + ¥80,000 = ¥1,160,000) = ¥2,440,000.
3. **課税所得** = ¥2,440,000 − ¥529,740 (社会保険料控除) − ¥1,040,000 (基礎控除) = ¥870,260 → truncated to **¥870,000**.
4. **所得税** = ¥870,000 × 5% = ¥43,500, + 復興特別所得税 2.1% (¥913) = ¥44,413 → truncated to 100 yen = **¥44,400**.
5. **住民税** = (¥2,440,000 − ¥529,740 − ¥430,000 → ¥1,480,000) × 10% − 調整控除 ¥2,500 + 均等割 ¥5,000 = **¥150,500**.

## Design decisions

- **Rules are data, logic is code.** A new tax year is a new `TaxYearRules` entry; the 2025 → 2026 reform (basic deduction up to ¥1,040,000, minimum 給与所得控除 ¥740,000, "178万円の壁") needed no calculation changes.
- **Money is `int` yen, rates are `Decimal`.** No floats, so no drift. Each statutory rounding rule is explicit and tested (employee insurance share: 50銭以下切り捨て; taxable income floored to ¥1,000; final tax floored to ¥100).
- **Immutable dataclasses** for input and output, validation in `__post_init__`.
- **Small, single-purpose modules** with a thin orchestrator, so each piece is unit-testable.

## Assumptions and limitations

This is an estimator, not tax advice or a payroll system.

- Computes the **annual liability** (what 年末調整 settles), not each month's 源泉徴収 from the 月額表. Under the 2026 reform the higher deductions reach actual withholding only at the December 2026 年末調整.
- Health insurance defaults to the **協会けんぽ national average**; premiums differ by prefecture, so pass your own with `--health-rate`. Company health societies (組合健保) have their own rates.
- Rates are assumed constant for the whole year (in reality health/nursing changed in March 2026 and employment insurance and the child support levy in April 2026).
- Resident tax is billed on the *previous* year's income; this estimates the steady-state amount from the same year's income and ignores 非課税 thresholds and locality differences in 均等割.
- Not modelled: 配偶者特別控除, 特定扶養/老人扶養, 障害者・ひとり親・寡婦 deductions, 住宅ローン控除, 医療費控除, 所得金額調整控除, ふるさと納税, 特定支出控除, multiple employers.
- 給与所得 uses the formula, not the NTA 年末調整 lookup table, so results can differ by a few hundred yen.

## Updating for a new year

1. Income tax: 国税庁 — 基礎控除 / 給与所得控除 for the year → `basic_deduction_income_tax`, `EmploymentDeductionRule`.
2. 協会けんぽ 都道府県単位保険料率, 介護保険料率, 子ども・子育て支援金率 → `SocialInsuranceRates`.
3. 厚生労働省 雇用保険料率 (一般の事業, 労働者負担) and 厚生年金 18.3%.
4. Add a hand-calculated test case, then run `pytest`.

Sources used for the 2026 values: Ministry of Finance 令和8年度税制改正 summary (<https://www.mof.go.jp/public_relations/finance/202604/202604c.html>), 協会けんぽ 令和8年度 rates (<https://www.kyoukaikenpo.or.jp/about/business/insurance_rate/rate_prefectures/r08>), MHLW 令和8年度 雇用保険料率.

## License

MIT (add a LICENSE file if you publish this).
