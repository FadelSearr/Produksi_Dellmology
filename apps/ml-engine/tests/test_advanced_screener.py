import pytest
from advanced_screener import AdvancedScreener, ScreenerConfig, StockScore

@pytest.fixture
def screener():
    return AdvancedScreener()


def test_scoring_range(screener):
    # create dummy input
    stock = {
        'patterns': [{'confidence': 0.9, 'type': 'BULLISH'}],
        'broker_flows': [{'z_score': 3}],
        'heatmap': {'net_volumes': [100, -100]},
        'volatility': 0.02,
        'anomalies': []
    }
    result = screener.screen_stock('TEST', stock)
    assert 0 <= result.score <= 100
    assert result.symbol == 'TEST'


def test_mode_change(screener):
    screener.set_mode('SWING')
    assert screener.config.mode == 'SWING'


def test_export_results(screener):
    scores = [StockScore(symbol='A', score=90, rank=1, technical_score=10, flow_score=10,
                         pressure_score=10, volatility_score=10, anomaly_score=10,
                         current_price=100, volatility_percent=0.02, haka_ratio=0.5,
                         broker_net_value=100000, risk_reward_ratio=2, recommendation='BUY',
                         reason='', pattern_matches=[], anomalies_detected=[]),]
    json_out = screener.export_results(scores, fmt='json')
    assert 'A' in json_out
    csv_out = screener.export_results(scores, fmt='csv')
    assert 'symbol,score' in csv_out
