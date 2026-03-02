# Order Flow Heatmap Engine - Implementation Guide

## Phase 2: Real-Time Order Flow Analysis (Complete)

This document describes the complete Phase 2 implementation of the IDX Analyst platform: real-time order flow heatmap visualization with anomaly detection.

---

## 1. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│             Real-Time Data Sources (Stockbit)           │
└────────────────────┬────────────────────────────────────┘
                     │ WebSocket Depth/Trade Data
                     ▼
┌─────────────────────────────────────────────────────────┐
│    Go Streamer Service (order_flow.go)                  │
│  • HAKA/HAKI Detection (aggressive buy/sell)           │
│  • Anomaly Detection (spoofing, phantom liquidity)      │
│  • Market Depth Processing                              │
│  • Broker Z-Score Tracking (whale detection)            │
└────────────────────┬────────────────────────────────────┘
                     │ Real-time Inserts
                     ▼
┌─────────────────────────────────────────────────────────┐
│    TimescaleDB (PostgreSQL + Time-series Extension)     │
│  ├─ order_flow_heatmap (raw data per price level)      │
│  ├─ order_flow_anomalies (detected issues)              │
│  ├─ market_depth (bid/ask snapshot)                     │
│  ├─ haka_haki_summary (buy/sell pressure)               │
│  ├─ order_events (order lifecycle tracking)             │
│  └─ broker_zscore (whale activity detection)            │
└────────────────────┬────────────────────────────────────┘
                     │ API Queries
                     ▼
┌─────────────────────────────────────────────────────────┐
│   Next.js API Route (route.ts)                          │
│  • /api/order-flow-heatmap GET/POST                    │
│  • Data aggregation & filtering                         │
│  • Caching (15s revalidate)                             │
└────────────────────┬────────────────────────────────────┘
                     │ JSON Response
                     ▼
┌─────────────────────────────────────────────────────────┐
│   React Component (OrderFlowHeatmap.tsx)                │
│  • Interactive grid visualization                       │
│  • Real-time updates (15s polling)                      │
│  • Market depth overlay                                 │
│  • Anomaly alerts                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema

### Core Tables

#### `order_flow_heatmap` (Hypertable)
Real-time order flow data per price level for visualization.

| Column | Type | Description |
|--------|------|-------------|
| `time` | TIMESTAMPTZ | Event timestamp (partition key) |
| `symbol` | VARCHAR(10) | Stock symbol |
| `price` | DECIMAL(10,2) | Price level |
| `bid_volume` | BIGINT | Cumulative bid volume |
| `ask_volume` | BIGINT | Cumulative ask volume |
| `net_volume` | BIGINT | bid_volume - ask_volume |
| `bid_ask_ratio` | DECIMAL(5,3) | Ratio for imbalance detection |
| `intensity` | DECIMAL(5,3) | Normalized activity (0-1) |
| `trade_count` | INT | Number of trades at level |

**Indexes:**
- `idx_order_flow_symbol_time` - For fast symbol + time queries
- `idx_order_flow_price` - For price-level lookups

#### `order_flow_anomalies` (Hypertable)
Detected anomalies (spoofing, phantom liquidity, wash trades).

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `time` | TIMESTAMPTZ | Detection timestamp |
| `symbol` | VARCHAR(10) | Stock symbol |
| `anomaly_type` | VARCHAR(50) | Type: SPOOFING, PHANTOM_LIQUIDITY, WASH_SALE, LAYERING |
| `price` | DECIMAL(10,2) | Associated price |
| `volume` | BIGINT | Related volume |
| `severity` | VARCHAR(10) | LOW, MEDIUM, HIGH |
| `description` | TEXT | Human-readable explanation |
| `is_confirmed` | BOOLEAN | Manual confirmation flag |

**Indexes:**
- `idx_anomaly_symbol_time` - Recent anomalies
- `idx_anomaly_severity` - Filter by severity

#### `market_depth` (Hypertable)
Five-second snapshots of full order book.

| Column | Type | Description |
|--------|------|-------------|
| `time` | TIMESTAMPTZ | Snapshot time |
| `symbol` | VARCHAR(10) | Stock symbol |
| `bid_levels` | JSONB | `{price: volume, ...}` mapping |
| `ask_levels` | JSONB | `{price: volume, ...}` mapping |
| `total_bid_volume` | BIGINT | Sum of all bid volumes |
| `total_ask_volume` | BIGINT | Sum of all ask volumes |
| `mid_price` | DECIMAL(10,2) | (bid + ask) / 2 |
| `bid_ask_spread` | DECIMAL(10,2) | ask_price - bid_price |
| `spread_bps` | INT | Spread in basis points |

#### `haka_haki_summary` (Hypertable)
HAKA (aggressive buy) vs HAKI (aggressive sell) from order flow.

| Column | Type | Description |
|--------|------|-------------|
| `time` | TIMESTAMPTZ | Summary timestamp |
| `symbol` | VARCHAR(10) | Stock symbol |
| `haka_volume` | BIGINT | Volume traded at ask (aggressive buys) |
| `haki_volume` | BIGINT | Volume traded at bid (aggressive sells) |
| `haka_ratio` | DECIMAL(5,3) | HAKA / (HAKA + HAKI) |
| `dominance` | VARCHAR(10) | HAKA, HAKI, or BALANCED |
| `net_pressure` | INT | -100 (all HAKI) to +100 (all HAKA) |

#### `order_events` (Hypertable)
Order lifecycle for spoofing detection.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Event ID |
| `time` | TIMESTAMPTZ | Event time |
| `symbol` | VARCHAR(10) | Stock symbol |
| `price` | DECIMAL(10,2) | Order price |
| `volume` | BIGINT | Order volume |
| `side` | VARCHAR(10) | BID or ASK |
| `event_type` | VARCHAR(20) | PLACED, MODIFIED, CANCELLED, EXECUTED |
| `order_id` | VARCHAR(100) | Unique order identifier |
| `broker_code` | VARCHAR(10) | Broker code (BBKP, BTPN, etc.) |
| `duration_ms` | INT | Lifetime in milliseconds |

#### `broker_zscore` (Hypertable)
Z-score tracking for whale detection.

| Column | Type | Description |
|--------|------|-------------|
| `time` | TIMESTAMPTZ | Calculation time |
| `symbol` | VARCHAR(10) | Stock symbol |
| `broker_code` | VARCHAR(10) | Broker identifier |
| `net_volume` | BIGINT | Net volume for period |
| `z_score` | DECIMAL(8,3) | Statistical deviation |
| `is_anomaly` | BOOLEAN | True if Z-score > 3σ |

---

## 3. Go Streamer Implementation

### AnomalyDetector struct

```go
type AnomalyDetector struct {
    db                      *sql.DB
    recentOrders            map[string][]OrderFlowEvent
    recentAnomalies         map[string][]OrderFlowAnomaly
    marketDepthCache        map[string]*MarketDepthSnapshot
    mu                      sync.RWMutex
    spoosingThresholdMs     int      // 5000ms
    phantomRatioThreshold   float64  // 3.0
    washTradeThreshold      int64    // 100
}
```

### Key Methods

#### Spoofing Detection
```go
func (ad *AnomalyDetector) DetectSpoofing(event OrderFlowEvent) *OrderFlowAnomaly
```
**Logic:**
- Monitors order lifetime before cancellation
- Threshold: < 5 seconds = spoofing
- Severity: Based on volume (HIGH > 1M, MEDIUM > 100K, LOW < 100K)

#### Phantom Liquidity Detection
```go
func (ad *AnomalyDetector) DetectPhantomLiquidity(symbol string, bidVol, askVol int64) *OrderFlowAnomaly
```
**Logic:**
- Calculates bid/ask ratio
- Threshold: > 3:1 imbalance = phantom liquidity
- Indicates orders likely to be cancelled without execution

#### Wash Trade Detection
```go
func (ad *AnomalyDetector) DetectWashTrade(symbol string, buyVol, sellVol int64) *OrderFlowAnomaly
```
**Logic:**
- Detects balanced buy/sell volumes with minimal net flow
- Threshold: |buyVol - sellVol| < 100 with both > 100K
- Indicates circular trading (same party buying and selling)

#### Layering Detection
```go
func (ad *AnomalyDetector) DetectLayering(symbol string, price float64, orderCount int) *OrderFlowAnomaly
```
**Logic:**
- Counts orders at same price level
- Threshold: > 10 orders at same level
- Indicates potential market manipulation

### Market Data Processing

```go
func (ad *AnomalyDetector) ProcessDepthData(ctx context.Context, data DepthData) error
```
**Flow:**
1. Parse incoming depth snapshot
2. Cache in memory for fast access
3. Insert into `market_depth` table
4. Calculate derived metrics (spread, mid-price)

### HAKA/HAKI Calculation

```go
func (ad *AnomalyDetector) CalculateHAKAHAKI(ctx context.Context, symbol string) (*HAKAHAKISummary, error)
```
**Definition:**
- **HAKA** (Harga Agresif Kena Ask): Trades executing at or above current ask → Aggressive buying
- **HAKI** (Harga Agresif Kena Bid): Trades executing at or below current bid → Aggressive selling
- **Ratio**: HAKA / (HAKA + HAKI) → 0.5 = balanced, > 0.6 = HAKA dominant, < 0.4 = HAKI dominant

### Background Aggregation Worker

```go
func (ad *AnomalyDetector) StartAggregationWorker(ctx context.Context, symbols []string)
```
**Purpose:**
- Runs every 1 minute
- Aggregates per-price-level heatmap data
- Inserts into 1-minute continuous aggregate table
- Enables fast historical queries

---

## 4. Next.js API Route

### Endpoints

#### GET `/api/order-flow-heatmap`
**Query Parameters:**
- `symbol` (required): Stock symbol (e.g., "BBCA")
- `minutes` (optional, default=60): Time window in minutes
- `anomalies` (optional, default=false): Include anomaly data

**Response:**
```json
{
  "symbol": "BBCA",
  "timestamp": "2024-01-15T10:30:45Z",
  "heatmap": [
    {
      "price": 8000.00,
      "timestamp": "2024-01-15T10:30:00Z",
      "bid": 1500000,
      "ask": 800000,
      "ratio": 1.875,
      "intensity": 0.75
    }
  ],
  "marketDepth": {
    "symbol": "BBCA",
    "time": "2024-01-15T10:30:45Z",
    "mid_price": 8000.50,
    "spread_bps": 6,
    "total_bid_volume": 5000000,
    "total_ask_volume": 4800000
  },
  "anomalies": [
    {
      "time": "2024-01-15T10:28:30Z",
      "symbol": "BBCA",
      "anomaly_type": "SPOOFING",
      "price": 8001.00,
      "volume": 500000,
      "severity": "HIGH",
      "description": "Order cancelled after 2000ms"
    }
  ],
  "stats": {
    "totalDataPoints": 450,
    "minPrice": 7995.50,
    "maxPrice": 8005.75,
    "avgIntensity": 0.62,
    "anomalyCount": 3
  }
}
```

### Caching Strategy
- **Server-side**: 15 second revalidation
- **Browser**: 60 second stale-while-revalidate
- Keys: `heatmap:{symbol}:{limit}`
- Trades: 500 latest data points per symbol

---

## 5. React Component

### OrderFlowHeatmap Component

**Props:**
```typescript
interface OrderFlowHeatmapProps {
  symbol: string;          // Required: stock symbol
  minutes?: number;        // Optional: time window (default 60)
  showAnomalies?: boolean; // Optional: show anomalies (default true)
  height?: number;         // Optional: component height (default 500)
}
```

### Features

#### 1. Interactive Grid Heatmap
- **Coloring**: Green (bid pressure) ↔ Red (ask pressure)
- **Intensity**: 0-1 scale represented by opacity
- **Hover**: Shows price, volumes, bid/ask ratio
- **Layout**: Responsive grid with price-level bins

#### 2. Market Depth Stats
- Mid-price display
- Spread in basis points
- Total bid/ask volumes
- Bid/ask ratio indicator

#### 3. Anomaly Alert Panel
- Timeline of detected anomalies
- Color-coded by severity (RED=HIGH, YELLOW=MEDIUM, BLUE=LOW)
- Scrollable with max 10 recent alerts

#### 4. Real-time Updates
- Auto-refresh every 15 seconds
- Loading spinner during fetch
- Error handling with user feedback

---

## 6. Anomaly Detection Algorithms

### Spoofing (Order Painting)

**Detection:**
1. Monitor order events: PLACED → CANCELLED
2. Calculate duration in milliseconds
3. If duration < 5 seconds AND volume > threshold → FLAG

**Severity:**
- HIGH: > 1,000,000 volume
- MEDIUM: 100,000 - 1,000,000
- LOW: < 100,000

**Example:**
```
PLACED: 10:30:00.500 | Volume: 500K | Price: 8000.00
CANCELLED: 10:30:02.200 | Duration: 1700ms
→ SPOOFING DETECTED (severity: MEDIUM)
```

### Phantom Liquidity (Position Squatting)

**Detection:**
1. Calculate bid/ask volume ratio
2. If ratio > 3.0 → FLAG
3. Indicates large orders unlikely to execute

**Calculation:**
```
Bid Volume: 5,000,000
Ask Volume: 1,000,000
Ratio: 5.0 → PHANTOM LIQUIDITY DETECTED
```

### Wash Sales (Circular Trading)

**Detection:**
1. Calculate net flow over period
2. If |buyVol - sellVol| < 100 with both > 100K → FLAG
3. High buy + high sell but no net movement

**Example:**
```
Buy Volume: 500,000
Sell Volume: 510,000
Net: +10,000 (minimal)
→ WASH SALE DETECTED
```

### Layering (Spoofing Multiple Levels)

**Detection:**
1. Count orders at specific price level
2. If count > 10 → FLAG
3. Indicates multiple orders from single actor intent on manipulation

---

## 7. Testing

### Unit Tests (`test_order_flow.py`)

```bash
# Run all tests
pytest apps/ml-engine/tests/test_order_flow.py -v

# Test specific class
pytest apps/ml-engine/tests/test_order_flow.py::TestAnomalyDetection -v
```

### Test Coverage

1. **AnomalyDetection Tests**
   - Spoofing detection (short-lived orders)
   - Phantom liquidity (extreme imbalances)
   - Wash trades (balanced flows)
   - Layering (multiple orders)

2. **Severity Calculation**
   - Volume-based thresholds
   - HIGH/MEDIUM/LOW classification

3. **Heatmap Aggregation**
   - Intensity normalization (0-1)
   - Net volume calculation
   - Multiple price aggregation

4. **HAKA/HAKI**
   - Dominance detection
   - Net pressure calculation
   - Balanced detection

5. **Market Depth**
   - Spread calculation in basis points
   - Mid-price accuracy

---

## 8. Integration with Go Streamer

### Initialization

In `main.go`:
```go
func init() {
    anomalyDetector = NewAnomalyDetector(db)
}

func main() {
    // Start aggregation worker
    go anomalyDetector.StartAggregationWorker(
        context.Background(),
        []string{"BBCA", "ASII", "TLKM"}, // Active symbols
    )
    
    // Process incoming depth data
    // (called from WebSocket handler)
}
```

### WebSocket Handler Integration

```go
func handleDepthMessage(ctx context.Context, data DepthData) {
    if anomalyDetector != nil {
        if err := anomalyDetector.ProcessDepthData(ctx, data); err != nil {
            log.Printf("Error processing depth data: %v", err)
        }
    }
}
```

---

## 9. Database Migrations

### Apply Migrations

```bash
# Using psql
psql -U postgres -d idx_analyst -f db/init/04-order-flow.sql

# Or using Supabase CLI
supabase db push
```

### Verify Setup

```sql
-- Check hypertables
SELECT * FROM timescaledb_information.hypertables
WHERE table_name IN ('order_flow_heatmap', 'order_flow_anomalies', 
                     'market_depth', 'haka_haki_summary');

-- Check indexes
\di order_flow_*

-- Check continuous aggregates
SELECT view_name FROM timescaledb_information.continuous_aggregates;
```

---

## 10. Performance Considerations

### Data Volume
- **Per minute**: ~1,000 trades per active symbol
- **Heatmap tables**: ~100 price levels per symbol
- **Retention**: 90 days (configurable)

### Query Optimization
1. **Time-series indexes**: Fast time-range queries
2. **Symbol+time composite**: Efficient symbol lookups
3. **Continuous aggregates**: Pre-computed 1-minute bins
4. **Hypertable compression**: Automatic for data > 1 week old

### Caching Strategy
- **API**: 15 second revalidation
- **Browser**: 60 second stale-while-revalidate
- **In-memory**: Market depth snapshot per symbol
- **Redis** (optional): For cross-instance caching

### Scaling
- Hypertable sharding by symbol
- Continuous aggregate partitioning
- Connection pooling (PgBouncer)
- Read replicas for aggregation queries

---

## 11. Deployment Checklist

- [ ] Database schema created (04-order-flow.sql)
- [ ] Hypertables configured with correct partitioning
- [ ] Indexes created for performance
- [ ] Go streamer updated with AnomalyDetector
- [ ] Next.js API route deployed
- [ ] React component imported in dashboard pages
- [ ] WebSocket handler calling ProcessDepthData
- [ ] Aggregation worker started on service init
- [ ] Monitoring alerts configured (anomaly spikes)
- [ ] Tests passing (pytest test_order_flow.py)

---

## 12. Future Enhancements

### Phase 3 (Post-Market)
- Broker flow summary (daily aggregation)
- Whale tracking via broker Z-scores
- Flow-based trend prediction

### Phase 4 (Global Context)
- Cross-symbol correlation heatmaps
- Sector-wide flow analysis
- Market regime detection

### Phase 5 (UI Integration)
- Advanced visualization library (Three.js 3D heatmap)
- Real-time anomaly notifications
- Flow-based trading strategy backtesting

---

## 13. References

- **TimescaleDB Docs**: https://docs.timescale.com/
- **Spoofing Detection**: SEC Market Manipulation Guidelines
- **Order Flow Analysis**: "The Day Trader's Advantage" by James Dalton
- **Go Database/SQL**: https://pkg.go.dev/database/sql
- **Next.js API Routes**: https://nextjs.org/docs/app/building-your-application/routing/route-handlers
