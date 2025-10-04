"""Utilities for downloading and persisting ASX market data."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf


LOGGER = logging.getLogger(__name__)

_EXPECTED_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
_COLUMN_ALIASES = {
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "adjclose": "Adj Close",
    "adjustedclose": "Adj Close",
    "adjclose*": "Adj Close",
    "volume": "Volume",
}


def _flatten_columns(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Return a frame with single-level columns."""
    if not isinstance(frame.columns, pd.MultiIndex):
        return frame

    frame = frame.copy()
    ticker_candidates = {
        ticker,
        ticker.upper(),
        ticker.lower(),
        ticker.replace(".", "-"),
        ticker.replace("-", "."),
    }

    for candidate in ticker_candidates:
        if candidate in frame.columns.get_level_values(0):
            try:
                return frame.xs(candidate, level=0, axis=1)
            except KeyError:
                continue

    # Fall back to concatenating all levels into a string.
    frame.columns = [" ".join(filter(None, map(str, col))).strip() for col in frame.columns]
    return frame


def _normalise_columns(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Return a frame with predictable column names."""

    flattened = _flatten_columns(frame, ticker)
    flattened = flattened.copy()

    canonical_names: dict[str, str] = {}
    for column in flattened.columns:
        key = "".join(ch for ch in str(column).lower() if ch.isalnum())
        canonical = _COLUMN_ALIASES.get(key)
        if canonical:
            canonical_names[column] = canonical

    flattened.rename(columns=canonical_names, inplace=True)

    for expected in _EXPECTED_COLUMNS:
        if expected not in flattened.columns:
            flattened[expected] = pd.NA

    return flattened[_EXPECTED_COLUMNS]


def _ensure_datetime_index(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a frame with a clean Date index."""

    frame = frame.copy()

    if not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.to_datetime(frame.index, errors="coerce")

    frame = frame[~frame.index.isna()].sort_index()

    if isinstance(frame.index, pd.DatetimeIndex) and frame.index.tz is not None:
        frame.index = frame.index.tz_localize(None)

    frame.index.name = "Date"
    return frame


def fetch_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download OHLCV data for *ticker* from Yahoo Finance."""

    LOGGER.info("Fetching data for %s from %s to %s", ticker, start, end)
    try:
        raw = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.exception("Failed to download data for %s", ticker)
        raise

    if raw is None or raw.empty:
        LOGGER.warning("No data received for %s", ticker)
        empty = pd.DataFrame(columns=_EXPECTED_COLUMNS)
        empty.index = pd.DatetimeIndex([], name="Date")
        return empty

    normalised = _normalise_columns(raw, ticker)
    normalised = _ensure_datetime_index(normalised)
    LOGGER.debug("Fetched %d rows for %s", len(normalised), ticker)
    return normalised


def append_to_csv(df: pd.DataFrame, path: str | Path) -> pd.DataFrame:
    """Append *df* to the CSV stored at *path* without duplicating rows."""

    if df.empty:
        LOGGER.info("No data to append for %s", path)
        return df

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df_to_write = _ensure_datetime_index(df)

    if file_path.exists():
        try:
            existing = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
            existing = _ensure_datetime_index(existing)
            combined = pd.concat([existing, df_to_write])
        except Exception:  # pragma: no cover - unexpected file issues
            LOGGER.exception("Failed reading existing data at %s", file_path)
            raise
    else:
        combined = df_to_write

    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    combined.to_csv(file_path, index_label="Date")
    LOGGER.info("Wrote %d rows to %s", len(combined), file_path)
    return combined


def run_fetch_all(tickers: Iterable[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    """Fetch and persist data for all provided *tickers*."""

    results: dict[str, pd.DataFrame] = {}
    data_dir = Path("/data")

    for ticker in tickers:
        try:
            fetched = fetch_data(ticker, start, end)
            written = append_to_csv(fetched, data_dir / f"{ticker}.csv")
            results[ticker] = written
        except Exception:
            LOGGER.exception("Error processing ticker %s", ticker)
            continue

    return results


__all__ = ["fetch_data", "append_to_csv", "run_fetch_all"]
