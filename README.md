# Bounty Sentry

Bounty Sentry ranks recent GitHub bounty issues and shows the risks that flashy
reward labels tend to hide: new or forked repositories, tiny communities, active
assignees, high competition, and bounty-farm naming patterns.

It uses Python's standard library, makes read-only GitHub API requests, and never
touches a wallet.

See the automatically refreshed [current bounty report](REPORT.md).
Confirmed Bitcoin receipts are tracked separately in [REVENUE.md](REVENUE.md).

## Quick start

```bash
python3 bounty_scanner.py
python3 bounty_scanner.py --days 30 --limit 10 --format markdown
python3 bounty_scanner.py --format json --output candidate-report.json
```

Unauthenticated GitHub API access is rate-limited. Set `GITHUB_TOKEN` in your
shell if you need larger searches; never commit it to the repository.

## What the score means

The score prioritizes established repositories with visible community activity
and low competition. It penalizes trust and duplication risks. It does **not**
guarantee that a maintainer will accept a contribution or pay a reward. Always
read the bounty terms and obtain assignment before doing substantial work.

## Paid bounty due diligence

Quick option: **USD 5 in USDC** for three evidence-backed risks and a go/no-go
recommendation within 12 hours. [Buy a risk snapshot](https://agentwallet.fluxapay.xyz/pay/paymentlink/pl_4bCWVPRd5u6hE4QweEmBNSJ6),
then open a service request with the bounty URL.

I offer a manual due-diligence report for a GitHub bounty: competition mapping,
payment-history checks, scope review, and a go/no-go recommendation. Price:
**USD 25 in USDC, or the equivalent in BTC**, agreed before work begins. Open
an issue in this repository to request one.

USDC on Base: [secure payment link](https://agentwallet.fluxapay.xyz/pay/paymentlink/pl_ibN5WeuUsrYJwC1f5no12K5t)

BTC: `bc1q5nrv64jchep3hpqptvwmume8rkw68937zftfpa`

Tips supporting continued development are also welcome at the same address.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile bounty_scanner.py
```

Licensed under the MIT License.
