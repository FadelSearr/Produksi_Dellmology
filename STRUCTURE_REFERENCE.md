# Repository Structure Reference

Complete visual reference of the new repository structure.

## 📦 Root Level

```
IDX_Analyst/
├── .env.example                    # Configuration template
├── RESTRUCTURING_GUIDE.md          # Detailed migration guide  
├── RESTRUCTURING_SUMMARY.md        # Quick summary
├── STRUCTURE_REFERENCE.md          # This file
├── start.sh                        # Startup script
├── docker-compose.yml              # Docker configuration
│
├── apps/                           # Application services
├── db/                             # Database init & migrations
├── references/                     # External references
└── README.md                       # Main readme
```

---

## 🐍 ML-Engine (Python) - Complete Structure

```
apps/ml-engine/
│
├── dellmology/                     # Main package (Python module)
│   ├── __init__.py                 (Module initialization)
│   │
│   ├── data_pipeline/              # Data ingestion
│   │   ├── __init__.py
│   │   ├── data_importer.py        (Fetch from Yahoo Finance)
│   │   ├── market_analyzer.py      (Analyze market data)
│   │   └── global_market_aggregator.py (Aggregate multi-source)
│   │
│   ├── models/                     # Machine Learning
│   │   ├── __init__.py
│   │   ├── cnn_model.py            (Deep Learning CNN)
│   │   ├── feature_generator.py    (Technical indicators)
│   │   ├── cnn_pattern_detector.py (Pattern recognition)
│   │   ├── train_manager.py        (Model training)
│   │   └── predict_manager.py      (Inference)
│   │
│   ├── analysis/                   # Trading Analysis
│   │   ├── __init__.py
│   │   ├── screener.py             (Stock screening engine)
│   │   ├── backtesting.py          (Historical simulation)
│   │   ├── flow_analyzer.py        (Broker flow analysis)
│   │   └── screener_api.py         (REST API endpoints)
│   │
│   ├── intelligence/               # AI & Explainability
│   │   ├── __init__.py
│   │   ├── ai_narrative.py         (Gemini AI narratives)
│   │   └── xai_explainer.py        (Explainable AI)
│   │
│   ├── telegram/                   # Notifications
│   │   ├── __init__.py
│   │   ├── telegram_service.py     (Bot service)
│   │   └── telegram_notifier.py    (Alert helpers)
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── db_utils.py             (Database operations)
│       ├── config.py               (Utils config import)
│       ├── model_retrain_scheduler.py (APScheduler wrapper)
│       ├── alert_trigger.py        (Alert monitoring)
│       └── load_test.py            (Performance testing)
│
├── tests/                          # Test Suite
│   ├── test_basic.py               (Unit tests)
│   └── test_integration.py         (Integration tests)
│
├── config.py                       # ⭐ MAIN CONFIGURATION
│   └── Contains: Database, Redis, Telegram, API, Models, etc.
│
├── main.py                         # ⭐ FASTAPI ENTRY POINT
│   └── API server on port 8000
│
├── requirements.txt                # Python dependencies
├── requirements-prod.txt           # Production dependencies
├── requirements-backup.txt         # Backup dependencies
│
├── README.md                       # Module documentation
└── Dockerfile.telegram             # Docker build (Telegram bot)
```

### Key Python Files at Root
- `config.py` - Centralized configuration (30+ settings)
- `main.py` - FastAPI server entry point
- `requirements.txt` - All dependencies listed

---

## ⚙️ Go Streamer - Complete Structure

```
apps/streamer/
│
├── cmd/                            # Command-line applications
│   └── streamer/
│       └── main.go                 # Entry point
│
├── internal/                       # Private packages (not importable)
│   │
│   ├── models/                     # Data Structures
│   │   └── types.go                (Trade, Quote, WebSocket types)
│   │
│   ├── data/                       # Data Storage & Streaming
│   │   ├── storage.go              (Database operations)
│   │   └── streaming.go            (WebSocket handling)
│   │
│   ├── analysis/                   # Market Analysis Engines
│   │   ├── broker.go               (Z-Score, HAKA/HAKI, Whale)
│   │   └── market.go               (Regime detection)
│   │
│   └── order/                      # Order Flow Analysis
│       └── flow.go                 (Heatmap, big walls)
│
├── config/                         # Configuration
│   └── config.go                   (Env variable handling)
│
├── go.mod                          # Go module definition
├── go.sum                          # Go dependency checksums
├── README.md                       # Documentation
└── .gitignore
```

### Go Streamer Utilities
- Real-time WebSocket streaming
- Redis caching for performance
- PostgreSQL storage with TimescaleDB
- Risk mitigation (RoC, cooldowns)

---

## ⚙️ Go Broker-Importer - Complete Structure

```
apps/broker-importer/
│
├── cmd/                            # Entry point
│   └── importer/
│       └── main.go                 # Start point
│
├── internal/                       # Private packages
│   ├── models.go                   (Broker data structures)
│   └── storage.go                  (DB operations)
│
├── go.mod                          # Module definition
├── go.sum                          # Checksums
├── README.md                       # Documentation
└── .gitignore
```

### Broker-Importer Purpose
- Import End-of-Day (EOD) broker summaries
- Calculate net buy/sell per broker
- Store in PostgreSQL
- Supports mock data for testing

---

## 📊 Database Structure

```
db/
│
├── init/                           # Initialization scripts
│   ├── 01-schema.sql               (Main tables)
│   ├── 02-model-metrics.sql        (ML metrics)
│   └── 03-alert-thresholds.sql     (Alert configuration)
│
└── migrations/                     # Future migrations
```

### Tables Referenced
- `trades` - Real-time trade data
- `order_book_snapshots` - Order book state
- `broker_summaries` - EOD flows
- `data_validation_anomalies` - Error tracking

---

## 🔧 Configuration System

### Files Involved
```
.env.example          ← Template (30+ settings)
↓
config.py             ← Python reads this
├── DATABASE_URL
├── REDIS_HOST/PORT
├── TELEGRAM_BOT_TOKEN
├── TARGET_SYMBOLS
├── MODEL_PATH
├── API_HOST/PORT
├── SCREENER_MODE (daytrade/swing)
├── BACKTEST dates
└── ALERT thresholds

config/config.go      ← Go reads from env vars
├── tokenAPIURL
├── websocketURL
├── databaseURL
├── redisHost/Port
└── risk parameters
```

### How Configuration Works
1. **Python**: `from config import Config` 
   - Reads `.env` file
   - Fallbacks to hardcoded defaults
   - Accessible as `Config.DATABASE_URL` etc.

2. **Go**: `config.LoadConfig()`
   - Reads environment variables
   - Fallbacks to hardcoded defaults
   - Returns Config struct

---

## 🧪 Test Structure

```
tests/
├── test_basic.py       # Unit tests
│   ├── test_config_loading()
│   ├── test_data_importer()
│   └── test_screener()
│
└── test_integration.py # Integration tests
    └── TestDatabaseIntegration
        └── test_db_health()
```

Run tests:
```bash
pytest tests/
pytest tests/test_basic.py -v
pytest tests/test_integration.py -v
```

---

## 📋 Module Dependencies

### Data Pipeline → Everything Else
```
data_importer.py
    ↓
feature_generator.py (uses OHLCV data)
    ↓
cnn_model.py (trains on features)
    ↓
predict.py (makes predictions)
    ↓
screener_api.py (exposes via REST)
```

### Analysis Flow
```
screener.py (AdvancedScreener)
    ←→ flow_analyzer.py (broker analysis)
    ←→ backtesting.py (historical test)
    ↓
ai_narrative.py (Gemini generates explanation)
```

### Notifications
```
alert_trigger.py (detects conditions)
    ↓
telegram_service.py (sends message)
    ←→ telegram_notifier.py (helpers)
```

---

## 🚀 Startup Sequence

### Python (ML-Engine)
```
1. main.py starts
2. Imports: config, dellmology packages
3. Initializes: db_utils.init_db()
4. Starts: uvicorn FastAPI server
5. Loads: screener, neural models, telegram
6. Ready: API listening on :8000
```

### Go (Streamer)
```
1. cmd/streamer/main.go starts
2. Loads: config.LoadConfig()
3. Initializes: data.InitDB()
4. Connects: Redis client
5. Starts: WebSocket listener
6. Ready: Streaming real-time data
```

### Go (Broker-Importer)
```
1. cmd/importer/main.go starts
2. Loads: config
3. Initializes: database storage
4. Fetches: EOD broker data
5. Stores: In PostgreSQL
6. Done: Waits for next schedule
```

---

## 🔄 File Migration Map

### Python Files Moved/Organized

| Original Name | New Location | Package | Purpose |
|---|---|---|---|
| `data_importer.py` | `dellmology/data_pipeline/data_importer.py` | data_pipeline | Yahoo Finance import |
| `feature_generator.py` | `dellmology/models/feature_generator.py` | models | Technical indicators |
| `model.py` | `dellmology/models/cnn_model.py` | models | Deep Learning model |
| `train.py` | `dellmology/models/train_manager.py` | models | Model training |
| `predict.py` | `dellmology/models/predict_manager.py` | models | Inference |
| `cnn_pattern_detector.py` | `dellmology/models/cnn_pattern_detector.py` | models | Pattern detection |
| `advanced_screener.py` | `dellmology/analysis/screener.py` | analysis | Stock screening |
| `backtesting.py` | `dellmology/analysis/backtesting.py` | analysis | Backtest engine |
| `screener_api.py` | `dellmology/analysis/screener_api.py` | analysis | REST API |
| `ai_narrative.py` | `dellmology/intelligence/ai_narrative.py` | intelligence | AI narrative |
| `xai_explainer.py` | `dellmology/intelligence/xai_explainer.py` | intelligence | Explainable AI |
| `telegram_service.py` | `dellmology/telegram/telegram_service.py` | telegram | Telegram bot |
| `telegram_notifier.py` | `dellmology/telegram/telegram_notifier.py` | telegram | Notification utils |
| `db_utils.py` | `dellmology/utils/db_utils.py` | utils | Database helpers |
| `model_retrain_scheduler.py` | `dellmology/utils/model_retrain_scheduler.py` | utils | Scheduler |
| `alert_trigger.py` | `dellmology/utils/alert_trigger.py` | utils | Alert system |

---

## 📚 Documentation Files

```
README.md (Root)
    ↓
RESTRUCTURING_SUMMARY.md     ← Quick overview
RESTRUCTURING_GUIDE.md       ← Detailed guide  
STRUCTURE_REFERENCE.md       ← This file
    ↓
apps/ml-engine/README.md     ← Python module docs
apps/streamer/README.md      ← Go streamer docs
apps/broker-importer/README.md ← Go importer docs
```

---

## 💾 Capacity & Performance

### Python Package Size
- **Main Package**: dellmology/ (~50KB organized code)
- **Dependencies**: See requirements.txt

### Go Binary Size (typical)
- **Streamer**: ~20MB (compiled)
- **Broker-Importer**: ~5MB (compiled)

### Database
- **TimescaleDB**: Optimized for time-series
- **Retention**: 7 days for tick data
- **Archives**: Permanent summaries

---

## ✅ Verification Checklist

Use this to verify the new structure is correct:

- [ ] All `/dellmology` subdirectories have `__init__.py`
- [ ] All Go packages have proper file organization
- [ ] `config.py` exists at ml-engine root
- [ ] `main.py` exists at ml-engine root
- [ ] `.env.example` exists at project root
- [ ] README.md files exist in each module
- [ ] `go.mod` files reference correct paths
- [ ] Test files under `tests/` directory
- [ ] No duplicate files in old locations
- [ ] All imports updated to new paths

---

## 🎯 Quick Commands

```bash
# Python
cd apps/ml-engine
python main.py                          # Run API
python -m dellmology.data_pipeline...  # Run module
pytest tests/                           # Run tests

# Go Streamer
cd apps/streamer
go mod tidy
go build -o streamer cmd/streamer/main.go
./streamer

# Go Broker-Importer
cd apps/broker-importer
go mod tidy
go build -o broker-importer cmd/importer/main.go
./broker-importer
```

---

## 🎓 Directory Naming Conventions

| Type | Example | Meaning |
|---|---|---|
| Package | `dellmology/` | Main module |
| Sub-package | `data_pipeline/` | Related functionality |
| Entry point | `cmd/streamer/` | Application start |
| Private | `internal/` | Not importable |
| Tests | `tests/` | Test files |
| Config | `config/` | Configuration |
| Docs | `README.md` | Documentation |

---

## 📖 Further Reading

For more details, refer to:
- `RESTRUCTURING_GUIDE.md` - Migration instructions
- `.env.example` - Configuration options
- `apps/ml-engine/README.md` - Python specifics
- `apps/streamer/README.md` - Go streamer details
- `apps/broker-importer/README.md` - Importer specifics

Struktur repositori kini professional dan terorganisir dengan baik! 🎉
