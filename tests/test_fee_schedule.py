"""Synthetic checks for the public fee-calculation excerpt."""

from datetime import date
import unittest

import pandas as pd

from fee_schedule import FeeRates, daily_trade_costs, fee_rates_for_date


class FeeScheduleTests(unittest.TestCase):
    def test_stamp_duty_cutover_is_sell_only(self):
        before = fee_rates_for_date(date(2023, 8, 27))
        after = fee_rates_for_date("2023-08-28")

        self.assertEqual(before, FeeRates(10.0, 2.5, 0.1, 0.2))
        self.assertEqual(after, FeeRates(5.0, 2.5, 0.1, 0.2))
        self.assertAlmostEqual(before.buy_bps(), 2.8)
        self.assertAlmostEqual(after.buy_bps(), 2.8)
        self.assertAlmostEqual(before.sell_bps(), 12.8)
        self.assertAlmostEqual(after.sell_bps(), 7.8)

    def test_components_reconcile_and_align_by_date(self):
        dates = pd.DatetimeIndex(["2023-08-27", "2023-08-28", "2024-01-02"])
        buys = pd.Series([0.20, 0.15], index=dates[[0, 2]])
        sells = pd.Series([0.05, 0.30], index=dates[[2, 1]])

        total, components = daily_trade_costs(buys, sells, dates)

        pd.testing.assert_series_equal(
            total,
            pd.Series([0.000056, 0.000234, 0.000081], index=dates),
        )
        pd.testing.assert_series_equal(
            components["cost_stamp"],
            pd.Series([0.0, 0.000150, 0.000025], index=dates),
        )
        self.assertEqual(
            set(components),
            {"cost_stamp", "cost_broker", "cost_exchange", "cost_sec_mgmt"},
        )
        pd.testing.assert_series_equal(total, sum(components.values()))

    def test_missing_turnover_dates_are_zero(self):
        dates = pd.DatetimeIndex(["2023-08-27", "2023-08-28"])
        buys = pd.Series([0.10], index=dates[:1])
        sells = pd.Series(dtype=float)

        total, _ = daily_trade_costs(buys, sells, dates)

        pd.testing.assert_series_equal(
            total, pd.Series([0.000028, 0.0], index=dates)
        )

    def test_unsupported_date_and_invalid_turnover_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "outside this sample"):
            fee_rates_for_date("2022-12-31")

        dates = pd.DatetimeIndex(["2023-08-28"])
        zero = pd.Series([0.0], index=dates)
        for bad in (-0.1, float("nan"), float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "finite, nonnegative"):
                    daily_trade_costs(pd.Series([bad], index=dates), zero, dates)

        duplicated = pd.DatetimeIndex(["2023-08-28", "2023-08-28"])
        with self.assertRaisesRegex(ValueError, "duplicate dates"):
            daily_trade_costs(zero, zero, duplicated)


if __name__ == "__main__":
    unittest.main()
