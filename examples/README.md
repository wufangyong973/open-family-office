# Synthetic demonstration

All values, households, dates of future receipts, preferences and target weights are invented.
No real person, account, investment product or institution is represented. Use this data for public recordings.

`household.synthetic.json`: AUD 2.5m gross assets, 0.7m mortgage, 1.8m net worth and 120k spendable cash.
The pension's 180k equity holdings are inside the 400k total equity exposure, not added again as a new asset class.
Baseline after-tax receipts are 8k fixed-labelled plus 5k variable per month. Regular outflows are 11k.
A 24k school payment and a 50k capital-call assumption occur once. Baseline 24-month cash ends at 94k.

Business sale: receive 900k after-tax household equity proceeds in month six; remove 600k of existing
business equity in the event bridge and stop the 5k monthly business receipt. Closing cash is 899k.
The event-only wealth change is 300k, not 900k; no full future balance-sheet forecast is claimed.

Recession: explicit asset markdowns and business income multiplied by 0.40. Immediate net worth falls
578k under those assumptions; closing cash is 22k. These are neither market forecasts nor estimated probabilities.

`policy.synthetic.json` contains arbitrary test weights. They are not allocation advice.
`expected/` contains actual engine-generated outputs. Regenerate with `python scripts/build_demo.py`.

`household.superannuation.synthetic.json` is a focused Australian superannuation example: the super fund is
one wrapper around its equities, bonds and cash. It shows the balance counted in net worth, excluded from
near-term spendable liquidity, never double-counted, and never turned into a new asset class. See
[`docs/superannuation-example.md`](../docs/superannuation-example.md) for the plain-language explanation and
`tests/test_superannuation.py` for the deterministic checks.
