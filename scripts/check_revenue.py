#!/usr/bin/env python3
"""Write a public confirmation report for Bitcoin and Base USDC addresses."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.request
from pathlib import Path


BASE_RPC = "https://mainnet.base.org"
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"


def fetch_address(address: str) -> dict:
    request = urllib.request.Request(
        f"https://mempool.space/api/address/{address}",
        headers={"User-Agent": "bounty-sentry-revenue-monitor"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def fetch_usdc_balance(address: str) -> int:
    clean_address = address.lower().removeprefix("0x")
    call_data = "0x70a08231" + ("0" * 24) + clean_address
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": BASE_USDC, "data": call_data}, "latest"],
    }
    request = urllib.request.Request(
        BASE_RPC,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "bounty-sentry-revenue-monitor"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.load(response)
    return int(result["result"], 16)


def render(
    address: str,
    data: dict,
    checked_at: dt.datetime,
    base_address: str | None = None,
    usdc_atomic: int = 0,
) -> str:
    chain = data["chain_stats"]
    mempool = data["mempool_stats"]
    confirmed = chain["funded_txo_sum"]
    pending = mempool["funded_txo_sum"]
    status = "CONFIRMED RECEIPT DETECTED" if confirmed or usdc_atomic else "NO CONFIRMED RECEIPTS"
    usdc_section = ""
    if base_address:
        usdc_section = f"""
## USDC on Base

- Address: `{base_address}`
- Confirmed balance: {usdc_atomic / 1_000_000:,.6f} USDC
"""
    return f"""# Revenue monitor

**Status: {status}**

- Address: `{address}`
- Confirmed received (lifetime): {confirmed:,} sats
- Unconfirmed incoming: {pending:,} sats
- Confirmed incoming transactions: {chain['funded_txo_count']:,}
{usdc_section}
- Last checked: {checked_at.astimezone(dt.timezone.utc).isoformat(timespec='seconds')}

This verifies blockchain receipts only. It does not prove that a receipt was earned from a customer.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("address")
    parser.add_argument("--base-address")
    parser.add_argument("--output", type=Path, default=Path("REVENUE.md"))
    args = parser.parse_args()
    usdc_atomic = fetch_usdc_balance(args.base_address) if args.base_address else 0
    report = render(
        args.address,
        fetch_address(args.address),
        dt.datetime.now(dt.timezone.utc),
        args.base_address,
        usdc_atomic,
    )
    args.output.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
