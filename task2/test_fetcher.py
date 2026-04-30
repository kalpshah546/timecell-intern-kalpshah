"""
Tests for fetcher.py

Strategy:
- Mock external APIs (yfinance, requests) so tests run offline and are fast.
- Cover happy paths, failure paths, and edge cases (None values, bad input).
- Smoke-test the renderer to make sure it doesn't crash on mixed results.
"""

from unittest.mock import patch, MagicMock

import pytest
import requests

from data_fetcher import (
    fetch_stock_price,
    fetch_crypto_price,
    format_and_print_table,
    _fmt_price,
    _fmt_pct,
    _fmt_latency,
    _fmt_status,
)


# ============================================================
# Stock fetcher tests
# ============================================================

@patch("data_fetcher.yf.Ticker")
def test_stock_fetch_success(mock_ticker_cls):
    """Happy path: yfinance returns valid price + previous close."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 22500.50
    mock_ticker.fast_info.previous_close = 22250.00
    mock_ticker_cls.return_value = mock_ticker

    result = fetch_stock_price("^NSEI", "NIFTY 50", "INR")

    assert result["status"] == "OK"
    assert result["name"] == "NIFTY 50"
    assert result["currency"] == "INR"
    assert result["price"] == 22500.50
    assert result["pct_change"] == pytest.approx(1.1258, rel=1e-3)
    assert result["latency_ms"] >= 0


@patch("data_fetcher.yf.Ticker")
def test_stock_fetch_missing_price_marks_failed(mock_ticker_cls):
    """If yfinance returns last_price=None, function should mark it FAILED."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = None
    mock_ticker.fast_info.previous_close = 100.0
    mock_ticker_cls.return_value = mock_ticker

    result = fetch_stock_price("BAD", "Bad Stock", "USD")

    assert result["status"] == "FAILED"
    assert result["price"] is None
    assert result["pct_change"] is None
    assert result["latency_ms"] is not None  # latency captured even on failure


@patch("data_fetcher.yf.Ticker", side_effect=Exception("Network unreachable"))
def test_stock_fetch_network_error(_mock_ticker_cls):
    """When yfinance itself raises, we should catch and return FAILED."""
    result = fetch_stock_price("^NSEI", "NIFTY 50", "INR")
    assert result["status"] == "FAILED"
    assert result["price"] is None


@patch("data_fetcher.yf.Ticker")
def test_stock_fetch_zero_prev_close_no_division_error(mock_ticker_cls):
    """If previous_close is 0, pct_change should be None — no ZeroDivisionError."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 100.0
    mock_ticker.fast_info.previous_close = 0
    mock_ticker_cls.return_value = mock_ticker

    result = fetch_stock_price("X", "X", "USD")
    assert result["status"] == "OK"
    assert result["pct_change"] is None  # safe fallback


# ============================================================
# Crypto fetcher tests
# ============================================================

@patch("data_fetcher.requests.get")
def test_crypto_fetch_success(mock_get):
    """Happy path: CoinGecko returns price + 24h change."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "bitcoin": {"usd": 62341.20, "usd_24h_change": -2.45}
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_crypto_price("bitcoin", "Bitcoin (BTC)", "usd")

    assert result["status"] == "OK"
    assert result["name"] == "Bitcoin (BTC)"
    assert result["currency"] == "USD"  # uppercased
    assert result["price"] == 62341.20
    assert result["pct_change"] == -2.45


@patch("data_fetcher.requests.get")
def test_crypto_fetch_unknown_coin(mock_get):
    """If coin_id missing in response, function marks it FAILED."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_crypto_price("notacoin", "Fake Coin", "usd")

    assert result["status"] == "FAILED"
    assert result["price"] is None


@patch("data_fetcher.requests.get", side_effect=requests.exceptions.Timeout("timeout"))
def test_crypto_fetch_timeout(_mock_get):
    """Request timeout should not crash the program."""
    result = fetch_crypto_price("bitcoin", "Bitcoin", "usd")
    assert result["status"] == "FAILED"
    assert result["price"] is None


@patch("data_fetcher.requests.get")
def test_crypto_fetch_http_error_propagates_to_failed(mock_get):
    """A 429 / 500 from raise_for_status should land in the except block."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429")
    mock_get.return_value = mock_response

    result = fetch_crypto_price("bitcoin", "Bitcoin", "usd")
    assert result["status"] == "FAILED"


# ============================================================
# Formatter helper tests
# ============================================================

def test_fmt_price_inr_uses_rupee_symbol():
    out = _fmt_price(1234567.89, "INR").plain
    assert "₹" in out
    assert "1,234,567.89" in out


def test_fmt_price_usd_uses_dollar_symbol():
    out = _fmt_price(99.5, "USD").plain
    assert "$" in out
    assert "99.50" in out


def test_fmt_price_none_renders_dash():
    out = _fmt_price(None, "USD").plain
    assert out == "—"


def test_fmt_pct_positive_has_up_arrow():
    out = _fmt_pct(2.5).plain
    assert "▲" in out
    assert "2.50%" in out


def test_fmt_pct_negative_has_down_arrow():
    out = _fmt_pct(-1.07).plain
    assert "▼" in out
    assert "1.07%" in out  # absolute value


def test_fmt_pct_none_renders_dash():
    assert _fmt_pct(None).plain == "—"


def test_fmt_latency_slow_call_marked_yellow():
    text = _fmt_latency(2500)
    assert text.style == "yellow"


def test_fmt_latency_fast_call_marked_cyan():
    text = _fmt_latency(120)
    assert text.style == "cyan"


def test_fmt_status_ok_and_failed():
    assert _fmt_status("OK").plain == "OK"
    assert _fmt_status("FAILED").plain == "FAILED"


# ============================================================
# Renderer smoke tests
# ============================================================

def test_format_and_print_table_renders_mixed_results(capsys):
    """Renderer should not crash with a mix of OK and FAILED rows."""
    rows = [
        {
            "status": "OK", "name": "NIFTY 50", "currency": "INR",
            "price": 22500.0, "pct_change": 1.2, "latency_ms": 350,
        },
        {
            "status": "FAILED", "name": "Bitcoin", "currency": "USD",
            "price": None, "pct_change": None, "latency_ms": 80,
        },
    ]
    format_and_print_table(rows)
    out = capsys.readouterr().out
    assert "NIFTY 50" in out
    assert "Bitcoin" in out
    assert "1/2" in out  # summary line


def test_format_and_print_table_all_failed_summary_red(capsys):
    """If everything fails, summary should still print and not crash."""
    rows = [
        {
            "status": "FAILED", "name": "X", "currency": "USD",
            "price": None, "pct_change": None, "latency_ms": 50,
        }
    ]
    format_and_print_table(rows)
    out = capsys.readouterr().out
    assert "0/1" in out


def test_format_and_print_table_empty_input_does_not_crash(capsys):
    """Edge case: empty list shouldn't crash; summary shows 0/0."""
    format_and_print_table([])
    out = capsys.readouterr().out
    assert "0/0" in out