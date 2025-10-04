Project Vision

We’re building a local-first trading research tool focused on ASX equities. It’s not a trading bot—it’s a backtesting and signal generation platform. A retail trader should be able to run it daily on their machine, see trading opportunities, and evaluate strategies over time in a professional dashboard.

Core Objectives

Fetch and normalize stock data

Automated download of OHLCV data for a list of ASX tickers.

Store in CSV locally (/data/), resilient to API quirks (multi-index, missing data).

Must be re-runnable daily, appending new rows.

Implement robust trading strategies

Strategies as pluggable modules (SMA cross, pullback, Donchian breakout, gap-up high volume, etc.).

Each strategy returns signals (buy/sell) as structured DataFrames.

Easy to add new strategies without breaking the pipeline.

Backtest consistently

Backtester simulates capital allocation, entry/exit, take-profit/stop-loss.

Outputs both trade-by-trade CSVs and summary stats (P/L, win rate, drawdowns).

Standardize metrics across all strategies.

Generate actionable alerts

From the most recent daily data, highlight “active buy signals”.

Save alerts in SQLite DB (signals.db) for persistence.

Must tolerate empty or no-signal days gracefully.

Daily automation runner

Single script (run_daily.py) that orchestrates:

Fetch data

Run strategies

Backtest

Generate alerts

Logs summary of successes/failures (no silent crashes).

Can be scheduled via cron/Task Scheduler.

Dashboard UI

Flask-based web app for browsing results.

Home page: key metrics (PnL, win rate, trades count) in summary cards.

Signals page: table of current actionable trades.

Trades page: per-ticker trade history with charts (Plotly candlesticks, equity curve).

Bootstrap 5 for styling, responsive, simple and professional.

Must handle empty/missing data with user-friendly messages.

Configuration

config.json defines tickers, start date, capital, take-profit/stop-loss %.

Human-readable and strict JSON (no trailing commas).

Should be validated at load time with helpful errors.

Testing & Quality

pytest suite covering:

Data fetcher (mocked downloads).

Strategy outputs (expected buy/sell flags).

Backtester on a dummy dataset.

Alerts pipeline handling empty/no signals.

Dashboard routes returning 200 OK.

Run python -m compileall . as part of CI to catch syntax/import issues.

Technical Stack

Language: Python 3.12 (target for macOS 10.15.7 environment).

Libraries:

pandas, numpy for data handling.

yfinance for price downloads.

matplotlib / plotly for charts.

Flask + Bootstrap 5 for dashboard.

SQLAlchemy or sqlite3 for signal DB.

pytest for tests.

User Workflow

User sets tickers and parameters in config.json.

User runs python run_daily.py (or cron job runs it at market close).

Data is fetched, signals generated, trades simulated, alerts written.

User starts dashboard with python dashboard.py.

User navigates to:

/ for summary cards and charts.

/signals for active trade alerts.

/trades/<ticker> for historical trades visualization.

Key Differentiators

Offline-first: all data and signals are local files. No external DB or cloud dependency.

Resilient: handles missing tickers, empty CSVs, no alerts without crashing.

Pluggable strategies: new ideas can be added in days, not weeks.

Accessible UI: trader sees their edge visually, not buried in logs.
