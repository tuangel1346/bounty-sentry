#!/usr/bin/env python3
"""Write a public confirmation report for a Bitcoin address."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.request
from pathlib import Path


def fetch_address(address: str) -> dict:
    request = urllib.request.Request(
        f"https://mempool.space/api/address/{address}",
        headers={"User-Agent": "bounty-sentry-revenue-monitor"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def render(address: str, data: dict, checked_at: dt.datetime) -> str:
    chain = data["chain_stats"]
    mempool = data["mempool_stats"]
    confirmed = chain["funded_txo_sum"]
    pending = mempool["funded_txo_sum"]
    status = "CONFIRMED RECEIPT DETECTED" if confirmed else "NO CONFIRMED RECEIPTS"
    return f"""# Revenue monitor

**Status: {status}**

- Address: `{address}`
- Confirmed received (lifetime): {confirmed:,} sats
- Unconfirmed incoming: {pending:,} sats
- Confirmed incoming transactions: {chain['funded_txo_count']:,}
- Last checked: {checked_at.astimezone(dt.timezone.utc).isoformat(timespec='seconds')}

This verifies blockchain receipts only. It does not prove that a receipt was earned from a customer.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("address")
    parser.add_argument("--output", type=Path, default=Path("REVENUE.md"))
    args = parser.parse_args()
    report = render(args.address, fetch_address(args.address), dt.datetime.now(dt.timezone.utc))
    args.output.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
