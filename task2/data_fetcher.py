
import time
import logging
from datetime import datetime, timezone, timedelta

import requests
import yfinance as yf
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text



logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
CONSOLE = Console()



STOCK_ASSETS = [
    {"symbol": "^NSEI", "name": "NIFTY 50", "currency": "INR"},
    {"symbol": "GC=F",  "name": "Gold (COMEX)", "currency": "USD"},
]

CRYPTO_ASSETS = [
    {"coin_id": "bitcoin", "name": "Bitcoin (BTC)", "currency": "usd"},
    {"coin_id": "ethereum", "name": "Ethereum (ETH)", "currency": "usd"},
]



def fetch_stock_price(symbol: str, name: str, currency: str) -> dict:
    """Fetch latest price for a stock/index using yfinance."""
    t0 = time.monotonic()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info

        price = info.last_price
        prev_close = info.previous_close

        if price is None:
            raise ValueError("Invalid symbol or no data")

        pct_change = ((price - prev_close) / prev_close * 100) if prev_close else None
        latency_ms = (time.monotonic() - t0) * 1000

        return {
            "status": "OK",
            "name": name,
            "currency": currency,
            "price": price,
            "pct_change": pct_change,
            "latency_ms": latency_ms,
        }

    except Exception as exc:
        logger.error("Stock fetch failed for %s: %s", symbol, exc)
        return {
            "status": "FAILED",
            "name": name,
            "currency": currency,
            "price": None,
            "pct_change": None,
            "latency_ms": (time.monotonic() - t0) * 1000,
        }


def fetch_crypto_price(coin_id: str, name: str, currency: str) -> dict:
    
    t0 = time.monotonic()
    try:
        params = {
            "ids": coin_id,
            "vs_currencies": currency,
            "include_24hr_change": "true",
        }

        resp = requests.get(COINGECKO_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if coin_id not in data:
            raise ValueError("Invalid coin id")

        coin_data = data[coin_id]
        price = coin_data.get(currency)
        pct_change = coin_data.get(f"{currency}_24h_change")

        latency_ms = (time.monotonic() - t0) * 1000

        return {
            "status": "OK",
            "name": name,
            "currency": currency.upper(),
            "price": price,
            "pct_change": pct_change,
            "latency_ms": latency_ms,
        }

    except Exception as exc:
        logger.error("Crypto fetch failed for %s: %s", coin_id, exc)
        return {
            "status": "FAILED",
            "name": name,
            "currency": currency.upper(),
            "price": None,
            "pct_change": None,
            "latency_ms": (time.monotonic() - t0) * 1000,
        }




def _fmt_price(price, currency) -> Text:
    if price is None:
        return Text("—", style="red")
    symbol = "₹" if currency == "INR" else "$"
    return Text(f"{symbol}{price:,.2f}", style="bold white")


def _fmt_pct(pct) -> Text:
    if pct is None:
        return Text("—", style="dim")
    arrow = "▲" if pct >= 0 else "▼"
    style = "green" if pct >= 0 else "red"
    return Text(f"{arrow} {abs(pct):.2f}%", style=style)


def _fmt_latency(ms) -> Text:
    if ms is None:
        return Text("—", style="dim")
    style = "yellow" if ms > 2000 else "cyan"
    return Text(f"{ms:.0f} ms", style=style)


def _fmt_status(status) -> Text:
    if status == "OK":
        return Text("OK", style="bold green")
    return Text("FAILED", style="bold red")


def format_and_print_table(data: list) -> None:
    timestamp = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

    table = Table(
        title=f"Asset Prices — {timestamp}",
        box=box.ROUNDED,
        header_style="bold magenta",
        border_style="bright_black",
        padding=(0, 1),
    )

    table.add_column("Asset", style="bold")
    table.add_column("Price", justify="right", min_width=14)
    table.add_column("Currency", justify="center")
    table.add_column("24h Change", justify="right")
    table.add_column("Latency", justify="right")
    table.add_column("Status", justify="center")

    ok_count = 0
    for row in data:
        if row["status"] == "OK":
            ok_count += 1
        table.add_row(
            row["name"],
            _fmt_price(row["price"], row["currency"]),
            row["currency"],
            _fmt_pct(row["pct_change"]),
            _fmt_latency(row["latency_ms"]),
            _fmt_status(row["status"]),
        )

    CONSOLE.print(table)

    total = len(data)
    color = "green" if ok_count == total else ("yellow" if ok_count > 0 else "red")
    CONSOLE.print(
        f"[{color}]Summary:[/{color}] {ok_count}/{total} assets fetched successfully.\n"
    )


def main():
    CONSOLE.print("[bold cyan]Fetching live market data...[/bold cyan]\n")
    results = []

    for asset in STOCK_ASSETS:
        CONSOLE.print(f"  ↳ {asset['name']}…")
        row = fetch_stock_price(asset["symbol"], asset["name"], asset["currency"])
        results.append(row)

    for asset in CRYPTO_ASSETS:
        CONSOLE.print(f"  ↳ {asset['name']}…")
        row = fetch_crypto_price(asset["coin_id"], asset["name"], asset["currency"])
        results.append(row)

    CONSOLE.print()
    format_and_print_table(results)


if __name__ == "__main__":
    main()