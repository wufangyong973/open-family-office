# Australian superannuation example, in plain language

This page explains, with one invented household, how Open Family Office treats an Australian
superannuation balance. It is paired with a deterministic fixture
([`examples/household.superannuation.synthetic.json`](../examples/household.superannuation.synthetic.json))
and the checks that lock its behaviour
([`tests/test_superannuation.py`](../tests/test_superannuation.py)). Every number below is synthetic;
no real person, fund or institution is represented.

## The household (all invented)

An Australian household with, as of 2026-09-21 in AUD:

| What it holds | Value (AUD) | Where it sits |
|---|---:|---|
| Cash reserve | 60,000 | Direct, spendable today |
| Direct shares | 120,000 | Direct, can sell within a week |
| Equities inside super | 160,000 | **Inside** the superannuation fund |
| Bonds inside super | 70,000 | **Inside** the superannuation fund |
| Cash inside super | 20,000 | **Inside** the superannuation fund |
| Home mortgage | −400,000 | Debt |

The superannuation fund holds 250,000 (160k + 70k + 20k). We do **not** add a fifth "super" asset of
250,000 on top of the three holdings — that would count the same money twice.

## The one idea this example makes concrete

**A superannuation fund is a wrapper, not an asset class.** The fund is the account; the equities, bonds
and cash *inside* it are its contents. Open Family Office counts the contents once, under their own
class, and shows the fund as a separate *view* that must reconcile to the same total — never an amount to
add.

- **It raises net worth.** Gross assets are 430,000 (including the 250,000 of super), debt is 400,000, so
  net worth is 30,000. The locked balance belongs to you and is part of your wealth.
- **It does not fund near-term spending.** The fund is `locked`, so the 20,000 of cash *inside* it is not
  spendable today. Spendable cash is only the 60,000 in the direct reserve.
- **It is not investable capital.** Because every super holding is locked, none of it counts toward the
  pool an allocation policy can redeploy. The investable pool is the 60,000 direct cash plus the 120,000
  direct shares.

## Why the fixture proves it, rather than asserting it

`tests/test_superannuation.py` runs the same engine (`snapshot`, `cashflow`, `validate`) the CLI uses and
locks these facts:

- `spendable_cash` is `60,000.00`, not `80,000.00` — the locked super cash is excluded.
- There is **no** `super` entry under the asset-class totals. The three underlying holdings aggregate into
  their real classes: equity 280,000 (120k direct + 160k super), bond 70,000, cash 80,000.
- The two parallel views agree: the wrapper totals (direct 180,000 + super 250,000) and the class totals
  both equal the 430,000 gross. That reconciliation is the "no double count" check.
- The only monthly net cashflow is salary 5,000 minus living 4,000; nothing in the cashflows invents a tax
  refund, a contribution cap, or a preservation-age release.

## What this example deliberately does **not** do

- No Australian contribution caps, co-contribution, preservation-age or tax outcomes are calculated. The
  fixture models a locked balance as *value in the household, unavailable for near-term spending*; it does
  not model when or how super might be released.
- No fund or product recommendation, and no target-return figure.
- The super value is a supplied statement figure, not a live price. A stale valuation is not a tradable price.

Run it yourself, no network or API key needed:

```bash
python scripts/ofo.py snapshot examples/household.superannuation.synthetic.json
python scripts/ofo.py validate examples/household.superannuation.synthetic.json
```

For field definitions and the wrapper/restriction semantics, see
[`docs/DATA-MODEL.md`](./DATA-MODEL.md). For the methodology behind locked wealth, see
[`agent/methodology/balance-sheet.md`](../agent/methodology/balance-sheet.md).
