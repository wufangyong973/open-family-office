"""Deterministic checks for the synthetic Australian superannuation example.

The fixture (examples/household.superannuation.synthetic.json) shows, in plain
money, that a superannuation fund is a *wrapper* around its underlying
holdings: the holdings are counted once (by their own class), the locked
balance raises net worth but not near-term spendable cash, and the wrapper
view never adds a new asset class on top.

No contribution caps, preservation-age or tax figures are modelled.
"""
from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from open_family_office.core import snapshot, cashflow, validate  # noqa: E402
from open_family_office.io import read_json  # noqa: E402


def load() -> dict:
    return read_json(ROOT / "examples" / "household.superannuation.synthetic.json")


class SuperannuationExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = load()
        cls.s = snapshot(cls.h)

    # --- validity / all synthetic (also swept by test_artifacts) ---------
    def test_validate_is_clean(self):
        self.assertEqual(validate(self.h), [])

    def test_fixture_is_marked_synthetic(self):
        self.assertIs(self.h["synthetic"], True)

    # --- super is counted in net worth -----------------------------------
    def test_super_balance_is_in_net_worth(self):
        # 60k cash + 120k direct shares + (160k + 70k + 20k) super holdings - 400k mortgage
        self.assertEqual(self.s["gross_assets"], "430000.00")
        self.assertEqual(self.s["liabilities"], "400000.00")
        self.assertEqual(self.s["net_worth"], "30000.00")

    # --- super is excluded from near-term spendable liquidity -----------
    def test_super_cash_is_not_spendable_today(self):
        # Only the direct 60k cash (class=cash, restriction=none, liquidity_days=0)
        # counts; the 20k cash *inside* super is locked and does not.
        self.assertEqual(self.s["spendable_cash"], "60000.00")
        self.assertNotEqual(self.s["spendable_cash"], "80000.00")

    def test_locked_super_is_not_investable_or_liquid(self):
        # investable+accessible = direct cash 60k + direct shares 120k = 180k;
        # every locked super holding is excluded from the allocation pool.
        self.assertEqual(self.s["eligible_allocation_capital"], "180000.00")
        # 7-day view: direct cash 60k + direct shares 120k * (1 - 0.05) = 174k.
        self.assertEqual(self.s["available_within_7_days_after_haircuts"], "174000.00")

    # --- no double counting between wrapper and underlying assets --------
    def test_no_super_asset_class_is_created(self):
        self.assertNotIn("super", self.s["asset_classes"])

    def test_wrapper_view_reconciles_with_class_view(self):
        # The super wrapper is a SEPARATE VIEW of the same holdings, not an
        # addition: wrapper totals, class totals and gross assets all agree.
        self.assertEqual(self.s["wrappers"]["super"], "250000.00")
        self.assertEqual(self.s["wrappers"]["direct"], "180000.00")
        wrapper_sum = sum((Decimal(v) for v in self.s["wrappers"].values()), Decimal("0"))
        class_sum = sum((Decimal(v) for v in self.s["asset_classes"].values()), Decimal("0"))
        gross = Decimal(self.s["gross_assets"])
        self.assertEqual(wrapper_sum, class_sum)
        self.assertEqual(class_sum, gross)

    def test_super_holdings_split_by_their_own_class(self):
        # Underlying super holdings aggregate into their real classes:
        # equity = 120k direct + 160k super = 280k, bond = 70k, cash = 80k.
        self.assertEqual(self.s["asset_classes"]["equity"], "280000.00")
        self.assertEqual(self.s["asset_classes"]["bond"], "70000.00")
        self.assertEqual(self.s["asset_classes"]["cash"], "80000.00")

    # --- no invented forward tax / preservation figures -----------------
    def test_no_tax_or_preservation_cashflows_invented(self):
        for f in self.h["cashflows"]:
            self.assertNotIn(f["category"], {"super_tax", "contribution_cap", "preservation_benefit"})
        # The only monthly net is salary 5k - living 4k = +1k; ending cash grows
        # from the 60k spendable base, not from any release of locked super.
        self.assertEqual(cashflow(self.h)["ending_cash"], "84000.00")


if __name__ == "__main__":
    unittest.main()
