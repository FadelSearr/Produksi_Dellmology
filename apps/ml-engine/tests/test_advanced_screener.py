import pytest
from dellmology.analysis.screener import AdvancedScreener, ScreenerMode


def test_mode_defaults_and_change():
    s = AdvancedScreener()
    assert s.mode == ScreenerMode.SWING
    s.mode = ScreenerMode.DAYTRADE
    assert s.mode == ScreenerMode.DAYTRADE

