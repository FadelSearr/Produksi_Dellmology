"""
Global Market Aggregator
Aggregates market data from multiple sources and time periods
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def aggregate_market_data(symbols: List[str]) -> Dict:
    """Aggregate market data for multiple symbols"""
    return {'symbols': symbols, 'timestamp': 'now'}
