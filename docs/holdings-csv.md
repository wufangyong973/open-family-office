# Normalized fund holdings CSV

`ofo import-holdings` ingests a flat, normalized holdings CSV and returns a
deterministic record set. It is an **import boundary**: it checks the shape of
your file and preserves what you did not classify — it never prices holdings,
runs a brokerage login, scrapes a ticker, or guesses live market data.

The canonical example in this repo is
[`examples/holdings.synthetic.csv`](../../examples/holdings.synthetic.csv).
Every value in it is invented; it contains no real account, security, or
ownership data, and it is safe to use in public recordings and demos.

## The exact command

```bash
# Installed entry point (also `open-family-office import-holdings ...`):
ofo import-holdings examples/holdings.synthetic.csv

# Source-checkout fallback:
python scripts/ofo.py import-holdings examples/holdings.synthetic.csv
```

The command is part of the `documents` integration and needs the
`open_family_office` package with the `documents` extra. Output is a JSON
envelope printed to stdout, or written to a file with `--out`:

```bash
ofo import-holdings examples/holdings.synthetic.csv --out reports/holdings.json
```

## Required columns

The file must have **exactly** these five columns, in any order, with a
`utf-8-sig` header (a BOM is tolerated, so it round-trips from Excel):

| Column | Meaning | Rule |
|--------|---------|------|
| `asset_id` | The account / wrapper / fund this row belongs to | Required, non-empty |
| `underlying_id` | The concrete underlying position inside that asset | Required, non-empty |
| `weight` | The fraction of the asset this underlying represents, as a decimal string | Must be a finite number in `[0, 1]` |
| `as_of` | The valuation date of the row | Must parse as an ISO date (`YYYY-MM-DD`) |
| `source` | Where the figure came from | Required, non-empty |

Any missing, extra, or renamed column is rejected outright — the command fails
with `Use agent/templates/holdings.csv exact columns` rather than guessing. The
blank template is [`agent/templates/holdings.csv`](../../agent/templates/holdings.csv)
(header row only).

## How `weight` is interpreted

- `weight` is the fraction of **one `asset_id`** that a row's `underlying_id`
  accounts for, not of the whole household. Weights are grouped by `asset_id`.
- Within a single `asset_id`, the weights may total less than, or exactly up
  to, `1`. The sum must **not** exceed `1`: when it does, the import stops
  with `Underlying weights exceed 100%; leverage needs explicit model`.
  Leverage is therefore never silently modeled — it must be declared explicitly.
- `as_of` and `source` are carried through to every record verbatim; they are
  the provenance a reviewer reads later.

## Unknown / unclassified weight is preserved, not normalized

This is the behavior that most often gets a holdings file wrong, so it is
documented explicitly:

- For each `asset_id`, Open Family Office reports the residual
  `1 - (sum of that asset's weights)` as `unclassified_weight`, **per asset**,
  as a string.
- That residual is **kept**, not silently stretched to make each asset total
  to `1`. If `equity-fund` is 60% + 40% = 100%, its `unclassified_weight` is
  `"0.0"`. If `cash-fund` is 75%, its `unclassified_weight` is `"0.25"` — the
  25% you have not yet classified stays visible instead of being absorbed into
  one line.

The fixture shows both cases: `equity-fund` fully classified (0.6 + 0.4) and
`cash-fund` partially classified (0.75).

## Duplicate underlyings are rejected

The pair `(asset_id, underlying_id)` must be unique. Two rows that name the
same underlying inside the same asset fail with `Duplicate underlying holding`
— the import does not merge, average, or drop one of them, because silently
choosing would hide a data error.

## `as_of` / `source` metadata expectations

- `as_of` must be a valid ISO 8601 calendar date; anything else fails with a
  `ValueError` from the date parse.
- `source` is free text (e.g. `synthetic-statement`, `broker-export-2026-02`).
  The import does not fetch, verify, or follow it.
- The envelope always sets `verified: false` and carries a standing note:
  extraction is not verification, and no household record is edited by the
  import. A holding in the output is evidence, not a claim of current value.

## Reading the envelope

`ofo import-holdings` returns:

```json
{
  "kind": "holdings",
  "records": [
    { "asset_id": "equity-fund", "underlying_id": "equity-fund.underlying.dca",
      "weight": "0.6", "as_of": "2026-02-01", "source": "synthetic-statement" }
  ],
  "unclassified_weight": { "cash-fund": "0.25", "equity-fund": "0.0" },
  "verified": false
}
```

- `records` is the file's rows, echoed back in order with the exact column
  values.
- `unclassified_weight` is a map of `asset_id -> "residual"` for every asset
  that appears.
- `verified: false` is fixed by design; downstream tools must treat these
  records as imported evidence, not verified truth.

## What this is not

- Not a universal ETF/brokerage website scraper and not a live holdings sync.
- Not a price engine — `weight` is a fraction of an asset, not a market value.
- No tax, contribution-cap, preservation-age, or jurisdiction logic is applied.
- No household JSON is read, written, or mutated by the command.
