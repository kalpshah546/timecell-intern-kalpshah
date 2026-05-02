# Task 2 — Live Market Data Fetcher

Fetches current prices for three assets from free public APIs and renders them in a clean terminal table.

## What It Fetches

| Asset | Source | API |
|---|---|---|
| Bitcoin (BTC) | CoinGecko | `api.coingecko.com/api/v3/simple/price` |
| NIFTY 50 (^NSEI) | yfinance | Yahoo Finance |
| Gold (GC=F) | yfinance | Yahoo Finance |

CoinGecko gives BTC USD price + 24h change with no API key. yfinance gives NIFTY 50 and Gold COMEX futures via `fast_info.last_price` and `previous_close`.

## Run

```bash
cd task2
python data_fetcher.py
```

Output is a six-column rich table:

| Asset | Price | Currency | 24h Change | Latency | Status |
|---|---|---|---|---|---|
| NIFTY 50 | ₹22,500.50 | INR | ▲ 1.12% | 340 ms | OK |
| Gold (COMEX) | $2,341.20 | USD | ▼ 0.45% | 280 ms | OK |
| Bitcoin (BTC) | $62,341.20 | USD | ▲ 2.45% | 180 ms | OK |

Followed by a colored summary line: `Summary: 3/3 assets fetched successfully.`

## Three Enhancements (Beyond Spec)

**Latency column** — `time.monotonic()` wraps each fetch. In a wealth-management product, slow data feeds matter; this is observability you'd want from day one. Captured even on failure so you can distinguish fast-fail (auth error) from slow-fail (timeout).

**Status column** — Green "OK" / red "FAILED" tag per row. Makes failures visually obvious without reading log lines, which matters when you're scanning a 20-asset portfolio.

**Summary line** — `2/3 assets fetched successfully` colored green/yellow/red based on success ratio. Quick health check at a glance.

All three are stdlib (`time`) or already-imported (`rich`) — no new dependencies.

## Error Handling Design

- Each fetcher (`fetch_stock_price`, `fetch_crypto_price`) is wrapped in its own `try/except`. One failure cannot kill the others.
- Latency is captured even on failure (start time is taken before the try block).
- Failures log via `logging` with timestamp + level, so a reviewer can see what broke without rerunning.
- Failed rows render as `—` in the table with `FAILED` status. The table still renders.
- HTTP requests have an explicit 10-second timeout — no indefinite hangs.
- `raise_for_status()` catches 4xx/5xx HTTP errors (e.g., CoinGecko 429 rate-limits).

## Tests

```bash
pytest -v
```

Tests use `unittest.mock.patch` so they run offline and deterministically. Coverage:

- Stock fetcher: success path, missing-price path (yfinance returns None), network exception, zero-`previous_close` (no ZeroDivisionError)
- Crypto fetcher: success path, unknown coin in response, timeout, HTTP 4xx/5xx
- Formatter helpers: INR vs USD symbols, comma formatting, None → dash, positive/negative arrows
- Renderer smoke tests: mixed OK/FAILED rows, all-failed case, empty input

## Honest Failure Modes


1. **yfinance breaks every few months.** It scrapes Yahoo's HTML, which Yahoo changes without warning. If `fast_info.last_price` stops returning a value, fall back to `ticker.history(period="1d")["Close"].iloc[-1]`.
2. **CoinGecko rate limits at ~30 req/min** on the free tier. Spamming the script will hit `429 Too Many Requests`. The fetcher catches this; it surfaces as a FAILED row.
3. **Indian markets are closed on weekends** — NIFTY 50's "current" price is just the last close. Latency might also spike on the first cold call (yfinance cache).
4. **First-run yfinance call can take 3–5 seconds** as it builds its session. The latency column shows this honestly.
