from datetime import datetime, timedelta
from dellmology.backtest.backtest_runner import _compute_metrics_from_ohlc


def make_ohlc(n=30, start_price=100.0, step=1.0):
    """Create synthetic OHLC candles (oldest -> newest)"""
    ohlc = []
    t = datetime.utcnow() - timedelta(minutes=n * 5)
    price = start_price
    for i in range(n):
        open_p = price
        close_p = price + (step if i % 2 == 0 else -step)
        high_p = max(open_p, close_p) + 0.1
        low_p = min(open_p, close_p) - 0.1
        candle = {
            'timestamp': int(t.timestamp()),
            'open': round(open_p, 2),
            'high': round(high_p, 2),
            'low': round(low_p, 2),
            'close': round(close_p, 2),
            'volume': 1000
        }
        ohlc.append(candle)
        price = close_p
        t += timedelta(minutes=5)
    return ohlc


def test_compute_metrics_basic():
    data = make_ohlc(n=60, start_price=50.0, step=0.5)
    metrics = _compute_metrics_from_ohlc(data)
    # expect certain keys and reasonable types
    assert isinstance(metrics, dict)
    assert 'net_return_pct' in metrics
    assert 'trades' in metrics
    assert 'sharpe' in metrics
    assert 'max_drawdown_pct' in metrics
    # trades should be an int >= 0
    assert isinstance(metrics['trades'], int)
    assert metrics['trades'] >= 0


def test_run_backtest_deterministic():
    """Ensure the mock fallback in run_backtest is deterministic for same inputs."""
    from dellmology.backtest.backtest_runner import run_backtest

    a = run_backtest('DETERMINISTIC_MODEL', '2023-01-01', '2023-01-31')
    b = run_backtest('DETERMINISTIC_MODEL', '2023-01-01', '2023-01-31')
    assert a == b
