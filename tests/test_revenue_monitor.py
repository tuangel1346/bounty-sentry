import datetime as dt
import unittest

from scripts.check_revenue import render


class RevenueMonitorTests(unittest.TestCase):
    def test_zero_receipts_are_not_reported_as_income(self):
        data = {
            "chain_stats": {"funded_txo_sum": 0, "funded_txo_count": 0},
            "mempool_stats": {"funded_txo_sum": 0},
        }
        report = render("bc1test", data, dt.datetime(2026, 6, 27, tzinfo=dt.timezone.utc))
        self.assertIn("NO CONFIRMED RECEIPTS", report)
        self.assertIn("0 sats", report)

    def test_confirmed_receipt_is_reported(self):
        data = {
            "chain_stats": {"funded_txo_sum": 12_345, "funded_txo_count": 1},
            "mempool_stats": {"funded_txo_sum": 500},
        }
        report = render("bc1test", data, dt.datetime(2026, 6, 27, tzinfo=dt.timezone.utc))
        self.assertIn("CONFIRMED RECEIPT DETECTED", report)
        self.assertIn("12,345 sats", report)

    def test_confirmed_usdc_balance_is_reported(self):
        data = {
            "chain_stats": {"funded_txo_sum": 0, "funded_txo_count": 0},
            "mempool_stats": {"funded_txo_sum": 0},
        }
        report = render(
            "bc1test",
            data,
            dt.datetime(2026, 6, 27, tzinfo=dt.timezone.utc),
            "0x1234",
            1_250_000,
        )
        self.assertIn("CONFIRMED RECEIPT DETECTED", report)
        self.assertIn("1.250000 USDC", report)
