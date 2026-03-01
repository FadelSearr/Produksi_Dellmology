-- Order Flow Heatmap Schema
-- Stores real-time bid/offer queue depth for order flow analysis

CREATE TABLE IF NOT EXISTS order_book (
  id BIGSERIAL,
  timestamp TIMESTAMPTZ NOT NULL,
  symbol VARCHAR(10) NOT NULL,
  level_index INT NOT NULL, -- Position in order book (0=top, 1=2nd, etc)
  side VARCHAR(3) NOT NULL, -- 'BID' or 'ASK'
  price DECIMAL NOT NULL,
  volume BIGINT NOT NULL,
  cumulative_volume BIGINT NOT NULL -- Total volume from best price to this level
);

SELECT create_hypertable('order_book', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS order_book_symbol_timestamp_idx ON order_book (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS order_book_symbol_side_timestamp_idx ON order_book (symbol, side, timestamp DESC);

-- Order Flow Heatmap aggregated data (for faster queries)
CREATE TABLE IF NOT EXISTS order_flow_heatmap (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL,
  symbol VARCHAR(10) NOT NULL,
  price DECIMAL NOT NULL,
  bid_volume BIGINT NOT NULL DEFAULT 0,
  ask_volume BIGINT NOT NULL DEFAULT 0,
  net_volume BIGINT NOT NULL DEFAULT 0, -- bid_volume - ask_volume
  bid_ask_ratio DECIMAL NOT NULL DEFAULT 1.0, -- bid_volume / ask_volume
  intensity DECIMAL NOT NULL DEFAULT 0.5 -- 0-1 scale for heatmap color
);

CREATE INDEX IF NOT EXISTS order_flow_heatmap_symbol_timestamp_idx ON order_flow_heatmap (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS order_flow_heatmap_symbol_price_timestamp_idx ON order_flow_heatmap (symbol, price, timestamp DESC);

-- Order Flow Anomalies (Spoofing detection)
CREATE TABLE IF NOT EXISTS order_flow_anomalies (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL,
  symbol VARCHAR(10) NOT NULL,
  anomaly_type VARCHAR(50) NOT NULL, -- 'LAYERING', 'SPOOFING', 'PHANTOM_LIQUIDITY', 'SPLIT_ORDER'
  price DECIMAL NOT NULL,
  volume BIGINT NOT NULL,
  severity VARCHAR(20) NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH'
  description TEXT,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS order_flow_anomalies_symbol_timestamp_idx ON order_flow_anomalies (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS order_flow_anomalies_severity_idx ON order_flow_anomalies (severity);

-- Market Depth Snapshot (for visualization)
CREATE TABLE IF NOT EXISTS market_depth (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL,
  symbol VARCHAR(10) NOT NULL,
  bid_levels JSON NOT NULL,     -- Array of {price, volume}
  ask_levels JSON NOT NULL,     -- Array of {price, volume}
  total_bid_volume BIGINT NOT NULL,
  total_ask_volume BIGINT NOT NULL,
  mid_price DECIMAL NOT NULL,
  bid_ask_spread DECIMAL NOT NULL,
  spread_bps INT NOT NULL -- Spread in basis points (0.01%)
);

CREATE INDEX IF NOT EXISTS market_depth_symbol_timestamp_idx ON market_depth (symbol, timestamp DESC);
