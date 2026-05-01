import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
GNEWS_URL = "https://gnews.io/api/v4/search"

# Each ticker has multiple query fallbacks tried in order until one returns results
TICKER_QUERIES = {
    "BTC":     ["Bitcoin price", "Bitcoin crypto", "BTC market"],
    "ETH":     ["Ethereum price", "Ethereum crypto", "ETH market"],
    "GOLD":    ["Gold price market", "Gold commodity", "XAUUSD"],
    "NIFTY50": ["Nifty 50 index", "NSE Nifty", "Indian stock market"],
    "SENSEX":  ["Sensex BSE", "Indian stock market", "BSE index"],
    "SPX":     ["S&P 500 index", "US stock market", "SPX"],
    "AAPL":    ["Apple stock AAPL", "Apple Inc shares"],
    "MSFT":    ["Microsoft stock MSFT", "Microsoft shares"],
    "TSLA":    ["Tesla stock TSLA", "Tesla shares"],
    "OIL":     ["Crude oil price", "WTI oil market", "Brent crude"],
}


def _fetch_gnews(query: str, max_articles: int = 1) -> list[str]:
    """
    Fetch headlines from GNews for a given query.
    Returns a list of title strings, or [] on any failure.
    """
    if not GNEWS_API_KEY:
        logger.error("GNEWS_API_KEY not set in .env file.")
        return []

    params = {
        "q":      query,
        "token":  GNEWS_API_KEY,
        "lang":   "en",
        "sortby": "publishedAt",
        "max":    max_articles,
    }

    try:
        resp = requests.get(GNEWS_URL, params=params, timeout=8)
        resp.raise_for_status()

        articles = resp.json().get("articles", [])
        return [
            a["title"].strip()
            for a in articles
            if a.get("title", "").strip()
        ]

    except requests.exceptions.Timeout:
        logger.warning(f"GNews timeout for query: {query!r}")
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        if status in (401, 403):
            logger.error("GNews: invalid or missing API key — check GNEWS_API_KEY in .env")
        elif status == 429:
            logger.warning("GNews: rate limit hit (100 req/day on free tier).")
        else:
            logger.warning(f"GNews HTTP {status} for {query!r}: {e}")
    except Exception as e:
        logger.warning(f"GNews unexpected error for {query!r}: {e}")

    return []


def _fetch_with_fallbacks(name: str) -> str | None:
    """
    Try each query fallback for a ticker until one returns a result.
    Returns a single headline string, or None if all queries fail.
    """
    queries = TICKER_QUERIES.get(name.upper())

    # Unknown ticker — build two generic fallbacks on the fly
    if not queries:
        queries = [f"{name} stock price", f"{name} market"]

    for query in queries:
        time.sleep(0.4)  # polite gap — avoids burst 429
        logger.info(f"[{name}] Trying query: {query!r}")
        titles = _fetch_gnews(query, max_articles=1)
        if titles:
            logger.info(f"[{name}] → {titles[0]}")
            return titles[0]

    logger.warning(f"[{name}] No headlines found after all fallbacks.")
    return None


def fetch_news_for_portfolio(portfolio: dict) -> str:
    """
    Fetches ONE recent headline per non-cash asset in the portfolio.
    Tries multiple query fallbacks per asset so every asset gets coverage.

    Returns plain text, one line per asset:
        BTC: Bitcoin ETF inflows hit record $500M
        GOLD: Gold climbs as dollar weakens ahead of Fed decision
        NIFTY50: Nifty 50 gains 1.2% on strong FII buying
    """
    final_lines: list[str] = []

    assets = [
        a for a in portfolio.get("assets", [])
        if a.get("name", "").strip() and a.get("name", "").strip().upper() != "CASH"
    ]

    for asset in assets:
        name = asset["name"].strip()
        headline = _fetch_with_fallbacks(name)
        if headline:
            final_lines.append(f"{name}: {headline}")

    return "\n".join(final_lines) if final_lines else "No recent relevant market news found."