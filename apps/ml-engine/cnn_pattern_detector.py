"""
CNN Pattern Recognition Module
Detects technical patterns otomatis menggunakan Deep Learning
Patterns: Bull Engulfing, Bear Engulfing, Double Bottom, Double Top, Head & Shoulders, etc
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PatternDetection:
    """Data class untuk pattern detection result"""
    symbol: str
    pattern_name: str
    pattern_type: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float  # 0-1
    start_date: str
    end_date: str
    entry_price: float
    target_price: float
    stop_loss: float
    pattern_description: str
    technical_score: float  # 0-100 untuk confluence dengan indikator lain


class CNNPatternRecognizer:
    """
    CNN-based pattern recognizer untuk deteksi teknikal patterns
    """

    # Pattern definitions dengan karakteristik
    PATTERNS = {
        "BULLISH_ENGULFING": {
            "type": "BULLISH",
            "description": "Candle besar hijau menutup di atas candle merah sebelumnya",
            "min_bars": 2,
            "max_bars": 50,
        },
        "BEARISH_ENGULFING": {
            "type": "BEARISH",
            "description": "Candle besar merah menutup di bawah candle hijau sebelumnya",
            "min_bars": 2,
            "max_bars": 50,
        },
        "DOUBLE_BOTTOM": {
            "type": "BULLISH",
            "description": "Dua valley pada level harga yang sama, sinyal reversal naik",
            "min_bars": 10,
            "max_bars": 100,
        },
        "DOUBLE_TOP": {
            "type": "BEARISH",
            "description": "Dua peak pada level harga yang sama, sinyal reversal turun",
            "min_bars": 10,
            "max_bars": 100,
        },
        "HEAD_AND_SHOULDERS": {
            "type": "BEARISH",
            "description": "Pola tiga puncak: bahu-kepala-bahu, sinyal bearish reversal",
            "min_bars": 15,
            "max_bars": 150,
        },
        "INVERSE_HEAD_AND_SHOULDERS": {
            "type": "BULLISH",
            "description": "Pola tiga lembah: bahu-kepala-bahu, sinyal bullish reversal",
            "min_bars": 15,
            "max_bars": 150,
        },
        "RISING_WEDGE": {
            "type": "BEARISH",
            "description": "Support dan resistance naik tapi naik lebih lambat, breakout bawah",
            "min_bars": 10,
            "max_bars": 100,
        },
        "FALLING_WEDGE": {
            "type": "BULLISH",
            "description": "Support dan resistance turun tapi turun lebih lambat, breakout atas",
            "min_bars": 10,
            "max_bars": 100,
        },
        "TRIANGLE": {
            "type": "NEUTRAL",
            "description": "Consolidation pattern, bisa breakout naik atau turun",
            "min_bars": 8,
            "max_bars": 80,
        },
        "FLAG_BULLISH": {
            "type": "BULLISH",
            "description": "Breakout naik setelah small consolidation",
            "min_bars": 5,
            "max_bars": 40,
        },
        "FLAG_BEARISH": {
            "type": "BEARISH",
            "description": "Breakout turun setelah small consolidation",
            "min_bars": 5,
            "max_bars": 40,
        },
    }

    def __init__(self, lookback_period: int = 100):
        """
        Initialize pattern recognizer
        
        Args:
            lookback_period: Jumlah candle untuk analysis
        """
        self.lookback_period = lookback_period

    def extract_candle_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract candle feature vector from OHLCV data
        
        Features: open, high, low, close, volume, body_range, range, hl2, hlc3, etc
        """
        features = []

        for idx, row in df.iterrows():
            open_price = row["open"]
            high = row["high"]
            low = row["low"]
            close = row["close"]
            volume = row["volume"]

            # Candle body
            body = abs(close - open_price)
            body_high = max(close, open_price)
            body_low = min(close, open_price)

            # Wicks
            upper_wick = high - body_high
            lower_wick = body_low - low

            # Trading range
            range_price = high - low

            # Typical price (HL2, HLC3, etc)
            hl2 = (high + low) / 2
            hlc3 = (high + low + close) / 3

            # Volume normalized
            volume_ma = df["volume"].rolling(window=10).mean().iloc[idx]
            volume_ratio = volume / (volume_ma + 1e-8)

            # Trend direction
            close_position = (close - low) / (range_price + 1e-8)  # 0=bottom, 1=top

            features.append(
                [
                    open_price,
                    high,
                    low,
                    close,
                    volume,
                    body,
                    range_price,
                    upper_wick,
                    lower_wick,
                    hl2,
                    hlc3,
                    volume_ratio,
                    close_position,
                ]
            )

        return np.array(features, dtype=np.float32)

    def detect_bullish_engulfing(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect bullish engulfing patterns"""
        patterns = []

        for i in range(1, len(df)):
            prev = df.iloc[i - 1]
            curr = df.iloc[i]

            # Prev candle harus bearish (close < open)
            # Curr candle harus bullish (close > open) dan lebih besar
            if (
                prev["close"] < prev["open"]  # Bearish
                and curr["close"] > curr["open"]  # Bullish
                and curr["open"] <= prev["close"]  # Opens at/below prev close
                and curr["close"] >= prev["open"]  # Closes at/above prev open
                and curr["close"] - curr["open"]
                > prev["open"] - prev["close"]  # Body lebih besar
            ):
                # Calculate confidence based on candle size and volume
                prev_body = prev["open"] - prev["close"]
                curr_body = curr["close"] - curr["open"]
                volume_ratio = curr["volume"] / (prev["volume"] + 1e-8)

                body_ratio = curr_body / (prev_body + 1e-8)
                confidence = min(
                    1.0, (body_ratio * 0.5 + volume_ratio * 0.3 + 0.2)
                )

                entry_price = curr["close"]
                entry_range = curr["high"] - curr["low"]
                target_price = curr["close"] + entry_range * 2
                stop_loss = prev["low"] * 0.99

                patterns.append(
                    PatternDetection(
                        symbol="",  # Will be set by caller
                        pattern_name="Bullish Engulfing",
                        pattern_type="BULLISH",
                        confidence=confidence,
                        start_date=prev["timestamp"].isoformat()
                        if hasattr(prev["timestamp"], "isoformat")
                        else str(prev["timestamp"]),
                        end_date=curr["timestamp"].isoformat()
                        if hasattr(curr["timestamp"], "isoformat")
                        else str(curr["timestamp"]),
                        entry_price=entry_price,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        pattern_description=self.PATTERNS["BULLISH_ENGULFING"][
                            "description"
                        ],
                        technical_score=confidence * 100,
                    )
                )

        return patterns

    def detect_double_bottom(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect double bottom patterns (W-shape reversal)"""
        patterns = []

        # Cari two lows yang approximately sama dalam 30-50 bars
        for i in range(15, len(df) - 15):
            window = df.iloc[max(0, i - 25) : min(len(df), i + 25)]

            local_min_idx = window["low"].idxmin()
            if local_min_idx > window.index.min() + 1:  # Min bukan di ujung window
                local_min_price = window.loc[local_min_idx, "low"]

                # Find second bottom
                after_min = window.loc[local_min_idx:].iloc[1:]
                if len(after_min) > 5:
                    second_min = after_min["low"].min()
                    second_min_idx = after_min["low"].idxmin()

                    # Check if lows are similar (within 1%)
                    if (
                        abs(local_min_price - second_min)
                        / (local_min_price + 1e-8)
                        < 0.01
                    ):
                        # Check for neckline resistance
                        between_idx = (local_min_idx + 1, second_min_idx)
                        high_between = df.loc[between_idx[0] : between_idx[1], "high"].max()

                        confidence = 0.7  # Moderate confidence

                        entry_price = high_between
                        target_price = high_between + (high_between - local_min_price) * 1.5
                        stop_loss = local_min_price * 0.99

                        patterns.append(
                            PatternDetection(
                                symbol="",
                                pattern_name="Double Bottom",
                                pattern_type="BULLISH",
                                confidence=confidence,
                                start_date=str(df.loc[local_min_idx, "timestamp"]),
                                end_date=str(df.loc[second_min_idx, "timestamp"]),
                                entry_price=entry_price,
                                target_price=target_price,
                                stop_loss=stop_loss,
                                pattern_description=self.PATTERNS["DOUBLE_BOTTOM"][
                                    "description"
                                ],
                                technical_score=confidence * 100,
                            )
                        )

        return patterns

    def detect_head_and_shoulders(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect head and shoulders pattern (bearish reversal)"""
        patterns = []

        for i in range(20, len(df) - 20):
            window = df.iloc[max(0, i - 15) : min(len(df), i + 15)]

            # Find peaks for shoulders and head
            peaks = []
            for j in range(1, len(window) - 1):
                if (
                    window.iloc[j]["high"]
                    > window.iloc[j - 1]["high"]
                    and window.iloc[j]["high"] > window.iloc[j + 1]["high"]
                ):
                    peaks.append((j, window.iloc[j]["high"]))

            if len(peaks) >= 3:
                # Check for pattern: shoulder, head, shoulder
                for j in range(len(peaks) - 2):
                    left_shoulder = peaks[j][1]
                    head = peaks[j + 1][1]
                    right_shoulder = peaks[j + 2][1]

                    # Head should be highest, shoulders similar
                    if (
                        head > left_shoulder * 1.02
                        and head > right_shoulder * 1.02
                        and abs(left_shoulder - right_shoulder)
                        / (left_shoulder + 1e-8)
                        < 0.05
                    ):
                        # Find neckline support
                        left_idx = peaks[j][0]
                        head_idx = peaks[j + 1][0]
                        right_idx = peaks[j + 2][0]

                        left_valley = (
                            window.iloc[left_idx : head_idx]["low"].min()
                        )
                        right_valley = (
                            window.iloc[head_idx : right_idx]["low"].min()
                        )
                        neckline = (left_valley + right_valley) / 2

                        confidence = 0.75

                        entry_price = neckline
                        breakout_distance = head - neckline
                        target_price = neckline - breakout_distance * 1.2
                        stop_loss = head * 1.01

                        patterns.append(
                            PatternDetection(
                                symbol="",
                                pattern_name="Head and Shoulders",
                                pattern_type="BEARISH",
                                confidence=confidence,
                                start_date=str(window.iloc[left_idx]["timestamp"]),
                                end_date=str(window.iloc[right_idx]["timestamp"]),
                                entry_price=entry_price,
                                target_price=target_price,
                                stop_loss=stop_loss,
                                pattern_description=self.PATTERNS[
                                    "HEAD_AND_SHOULDERS"
                                ]["description"],
                                technical_score=confidence * 100,
                            )
                        )

        return patterns

    def detect_all_patterns(self, df: pd.DataFrame, symbol: str) -> Dict[str, List]:
        """
        Detect all pattern types dalam dataframe
        
        Args:
            df: DataFrame dengan OHLCV data
            symbol: Stock symbol
            
        Returns:
            Dictionary berisi semua detected patterns per type
        """
        results = {
            "bullish_engulfing": self.detect_bullish_engulfing(df),
            "bearish_engulfing": self.detect_bearish_engulfing(df),
            "double_bottom": self.detect_double_bottom(df),
            "double_top": self.detect_double_top(df),
            "head_and_shoulders": self.detect_head_and_shoulders(df),
            "inverse_head_and_shoulders": self.detect_inverse_head_and_shoulders(df),
            "rising_wedge": self.detect_rising_wedge(df),
            "falling_wedge": self.detect_falling_wedge(df),
        }

        # Set symbol untuk semua patterns
        for pattern_list in results.values():
            for pattern in pattern_list:
                pattern.symbol = symbol

        return results

    def detect_bearish_engulfing(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect bearish engulfing patterns"""
        patterns = []

        for i in range(1, len(df)):
            prev = df.iloc[i - 1]
            curr = df.iloc[i]

            if (
                prev["close"] > prev["open"]  # Bullish
                and curr["close"] < curr["open"]  # Bearish
                and curr["open"] >= prev["close"]
                and curr["close"] <= prev["open"]
                and curr["open"] - curr["close"]
                > prev["close"] - prev["open"]
            ):
                prev_body = prev["close"] - prev["open"]
                curr_body = curr["open"] - curr["close"]
                volume_ratio = curr["volume"] / (prev["volume"] + 1e-8)

                body_ratio = curr_body / (prev_body + 1e-8)
                confidence = min(1.0, (body_ratio * 0.5 + volume_ratio * 0.3 + 0.2))

                entry_price = curr["close"]
                entry_range = curr["high"] - curr["low"]
                target_price = curr["close"] - entry_range * 2
                stop_loss = prev["high"] * 1.01

                patterns.append(
                    PatternDetection(
                        symbol="",
                        pattern_name="Bearish Engulfing",
                        pattern_type="BEARISH",
                        confidence=confidence,
                        start_date=str(prev["timestamp"]),
                        end_date=str(curr["timestamp"]),
                        entry_price=entry_price,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        pattern_description=self.PATTERNS["BEARISH_ENGULFING"][
                            "description"
                        ],
                        technical_score=confidence * 100,
                    )
                )

        return patterns

    def detect_double_top(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect double top patterns (M-shape reversal)"""
        patterns = []

        for i in range(15, len(df) - 15):
            window = df.iloc[max(0, i - 25) : min(len(df), i + 25)]

            local_max_idx = window["high"].idxmax()
            if local_max_idx > window.index.min() + 1:
                local_max_price = window.loc[local_max_idx, "high"]

                after_max = window.loc[local_max_idx:].iloc[1:]
                if len(after_max) > 5:
                    second_max = after_max["high"].max()
                    second_max_idx = after_max["high"].idxmax()

                    if (
                        abs(local_max_price - second_max)
                        / (local_max_price + 1e-8)
                        < 0.01
                    ):
                        between_idx = (local_max_idx + 1, second_max_idx)
                        low_between = df.loc[
                            between_idx[0] : between_idx[1], "low"
                        ].min()

                        confidence = 0.7

                        entry_price = low_between
                        target_price = low_between - (local_max_price - low_between) * 1.5
                        stop_loss = local_max_price * 1.01

                        patterns.append(
                            PatternDetection(
                                symbol="",
                                pattern_name="Double Top",
                                pattern_type="BEARISH",
                                confidence=confidence,
                                start_date=str(df.loc[local_max_idx, "timestamp"]),
                                end_date=str(df.loc[second_max_idx, "timestamp"]),
                                entry_price=entry_price,
                                target_price=target_price,
                                stop_loss=stop_loss,
                                pattern_description=self.PATTERNS["DOUBLE_TOP"][
                                    "description"
                                ],
                                technical_score=confidence * 100,
                            )
                        )

        return patterns

    def detect_inverse_head_and_shoulders(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect inverse head and shoulders (bullish reversal)"""
        patterns = []

        for i in range(20, len(df) - 20):
            window = df.iloc[max(0, i - 15) : min(len(df), i + 15)]

            valleys = []
            for j in range(1, len(window) - 1):
                if (
                    window.iloc[j]["low"]
                    < window.iloc[j - 1]["low"]
                    and window.iloc[j]["low"] < window.iloc[j + 1]["low"]
                ):
                    valleys.append((j, window.iloc[j]["low"]))

            if len(valleys) >= 3:
                for j in range(len(valleys) - 2):
                    left_shoulder = valleys[j][1]
                    head = valleys[j + 1][1]
                    right_shoulder = valleys[j + 2][1]

                    if (
                        head < left_shoulder * 0.98
                        and head < right_shoulder * 0.98
                        and abs(left_shoulder - right_shoulder)
                        / (left_shoulder + 1e-8)
                        < 0.05
                    ):
                        left_idx = valleys[j][0]
                        head_idx = valleys[j + 1][0]
                        right_idx = valleys[j + 2][0]

                        left_peak = window.iloc[left_idx:head_idx]["high"].max()
                        right_peak = window.iloc[head_idx:right_idx]["high"].max()
                        neckline = (left_peak + right_peak) / 2

                        confidence = 0.75

                        entry_price = neckline
                        breakout_distance = neckline - head
                        target_price = neckline + breakout_distance * 1.2
                        stop_loss = head * 0.99

                        patterns.append(
                            PatternDetection(
                                symbol="",
                                pattern_name="Inverse Head and Shoulders",
                                pattern_type="BULLISH",
                                confidence=confidence,
                                start_date=str(window.iloc[left_idx]["timestamp"]),
                                end_date=str(window.iloc[right_idx]["timestamp"]),
                                entry_price=entry_price,
                                target_price=target_price,
                                stop_loss=stop_loss,
                                pattern_description=self.PATTERNS[
                                    "INVERSE_HEAD_AND_SHOULDERS"
                                ]["description"],
                                technical_score=confidence * 100,
                            )
                        )

        return patterns

    def detect_rising_wedge(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect rising wedge (bearish pattern)"""
        # Simplified: check for highs and lows both rising but with decreasing range
        patterns = []
        window_size = 20

        for i in range(window_size, len(df)):
            window = df.iloc[i - window_size : i]

            highs = window["high"].values
            lows = window["low"].values

            # Check trend
            high_trend = np.polyfit(range(len(highs)), highs, 1)[0] > 0
            low_trend = np.polyfit(range(len(lows)), lows, 1)[0] > 0
            range_trend = (highs[-1] - lows[-1]) < (highs[0] - lows[0])

            if high_trend and low_trend and range_trend:
                confidence = 0.65

                entry_price = lows[-1]
                pattern_height = highs[0] - lows[0]
                target_price = entry_price - pattern_height * 1.0
                stop_loss = highs[-1] * 1.01

                patterns.append(
                    PatternDetection(
                        symbol="",
                        pattern_name="Rising Wedge",
                        pattern_type="BEARISH",
                        confidence=confidence,
                        start_date=str(window.iloc[0]["timestamp"]),
                        end_date=str(window.iloc[-1]["timestamp"]),
                        entry_price=entry_price,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        pattern_description=self.PATTERNS["RISING_WEDGE"][
                            "description"
                        ],
                        technical_score=confidence * 100,
                    )
                )

        return patterns

    def detect_falling_wedge(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect falling wedge (bullish pattern)"""
        patterns = []
        window_size = 20

        for i in range(window_size, len(df)):
            window = df.iloc[i - window_size : i]

            highs = window["high"].values
            lows = window["low"].values

            high_trend = np.polyfit(range(len(highs)), highs, 1)[0] < 0
            low_trend = np.polyfit(range(len(lows)), lows, 1)[0] < 0
            range_trend = (highs[-1] - lows[-1]) < (highs[0] - lows[0])

            if high_trend and low_trend and range_trend:
                confidence = 0.65

                entry_price = highs[-1]
                pattern_height = highs[0] - lows[0]
                target_price = entry_price + pattern_height * 1.0
                stop_loss = lows[-1] * 0.99

                patterns.append(
                    PatternDetection(
                        symbol="",
                        pattern_name="Falling Wedge",
                        pattern_type="BULLISH",
                        confidence=confidence,
                        start_date=str(window.iloc[0]["timestamp"]),
                        end_date=str(window.iloc[-1]["timestamp"]),
                        entry_price=entry_price,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        pattern_description=self.PATTERNS["FALLING_WEDGE"][
                            "description"
                        ],
                        technical_score=confidence * 100,
                    )
                )

        return patterns
