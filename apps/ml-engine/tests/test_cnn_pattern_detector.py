import pytest
import pandas as pd
from cnn_pattern_detector import CNNPatternRecognizer, PatternDetection

@pytest.fixture
def recognizer():
    return CNNPatternRecognizer(lookback_period=10)

@pytest.fixture
def simple_df():
    # create a small DataFrame with two candles
    data = {
        'open': [100, 110],
        'high': [110, 115],
        'low': [95, 108],
        'close': [105, 112],
        'volume': [1000, 1200],
        'timestamp': pd.date_range('2026-01-01', periods=2, freq='T')
    }
    return pd.DataFrame(data)


def test_extract_candle_features(recognizer, simple_df):
    features = recognizer.extract_candle_features(simple_df.iloc[0])
    assert len(features) == 13
    assert features[0] == 100


def test_detect_bullish_engulfing(recognizer, simple_df):
    # craft example for bullish engulfing
    prev = pd.Series({'open': 110, 'high': 112, 'low': 108, 'close': 109, 'volume': 1500, 'timestamp': pd.Timestamp('2026-01-01T00:00')})
    curr = pd.Series({'open': 108, 'high': 115, 'low': 107, 'close': 114, 'volume': 2000, 'timestamp': pd.Timestamp('2026-01-01T00:01')})
    det = recognizer.detect_bullish_engulfing(prev, curr, 'TEST')
    assert det.pattern_name == 'Bullish Engulfing'
    assert det.confidence > 0


def test_overall_pattern_detection(recognizer, simple_df):
    patterns = recognizer.detect_all_patterns(simple_df, 'TEST')
    assert isinstance(patterns, dict)
