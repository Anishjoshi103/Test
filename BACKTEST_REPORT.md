# StockSage Pro Backtesting Report

Generated: 2026-03-09T15:34:47.985002Z
Universe: TCS.NS, RELIANCE.NS, HDFCBANK.NS, INFY.NS, AAPL, NVDA, TSLA
Horizon: 20 trading days

## Status
- No backtest metrics could be computed in this environment.
- Likely cause: outbound market-data requests blocked (proxy/tunnel policy).

## Fetch Errors
- TCS.NS: <urlopen error Tunnel connection failed: 403 Forbidden>
- RELIANCE.NS: <urlopen error Tunnel connection failed: 403 Forbidden>
- HDFCBANK.NS: <urlopen error Tunnel connection failed: 403 Forbidden>
- INFY.NS: <urlopen error Tunnel connection failed: 403 Forbidden>
- AAPL: <urlopen error Tunnel connection failed: 403 Forbidden>
- NVDA: <urlopen error Tunnel connection failed: 403 Forbidden>
- TSLA: <urlopen error Tunnel connection failed: 403 Forbidden>

## How to Run Locally
1. Ensure internet access to Yahoo Finance endpoints.
2. Run: `python3 backtest_report.py`
3. Review generated `BACKTEST_REPORT.md` metrics.
