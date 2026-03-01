"""
README for ML-Engine Package
Dellmology Pro - Advanced Stock Market Analysis
"""

# ML Engine - Dellmology Pro

High-performance stock market analysis platform with Deep Learning and Bandarmology insights.

## Project Structure

```
ml-engine/
├── dellmology/              # Main package
│   ├── data_pipeline/       # Data fetching and processing
│   │   ├── data_importer.py
│   │   ├── market_analyzer.py
│   │   └── global_market_aggregator.py
│   │
│   ├── models/              # ML models
│   │   ├── cnn_model.py
│   │   ├── feature_generator.py
│   │   ├── cnn_pattern_detector.py
│   │   ├── train_manager.py
│   │   └── predict_manager.py
│   │
│   ├── analysis/            # Trading analysis
│   │   ├── screener.py      # Stock screener
│   │   ├── backtesting.py   # Historical backtesting
│   │   ├── flow_analyzer.py # Broker flow analysis
│   │   └── screener_api.py  # REST API endpoints
│   │
│   ├── intelligence/        # AI & XAI
│   │   ├── ai_narrative.py  # AI narrative generation
│   │   └── xai_explainer.py # Explainable AI
│   │
│   ├── telegram/            # Notification system
│   │   ├── telegram_service.py
│   │   └── telegram_notifier.py
│   │
│   └── utils/               # Utilities
│       ├── db_utils.py
│       ├── config.py
│       ├── model_retrain_scheduler.py
│       ├── alert_trigger.py
│       └── load_test.py
│
├── tests/                   # Test suite
│   ├── test_basic.py
│   └── test_integration.py
│
├── config.py                # Main configuration
├── main.py                  # FastAPI entry point
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Installation

1. **Setup Python Environment**
   ```bash
   cd apps/ml-engine
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp ../../.env.example .env
   # Edit .env with your settings
   ```

## Running the Application

### Start API Server
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Run Data Import
```bash
python -m dellmology.data_pipeline.data_importer
```

### Run Screener
```bash
python -c "from dellmology.analysis.screener import AdvancedScreener; s = AdvancedScreener(); s.scan(['BBCA', 'TLKM'])"
```

### Run Tests
```bash
pytest tests/
pytest tests/test_basic.py -v
```

## Configuration

Edit `config.py` or `.env` file to customize:

- **Database**: PostgreSQL connection
- **Redis**: Cache settings
- **Telegram**: Bot token and chat ID
- **Models**: ML model paths and parameters
- **Screener**: Daytrade vs Swing mode
- **Alerts**: Thresholds and conditions

## Key Features

### 1. Data Pipeline
- Real-time market data ingestion
- Historical data fetching from Yahoo Finance
- Order-flow and broker activity analysis

### 2. ML Models
- Deep CNN for pattern recognition
- Feature engineering (RSI, MACD, Bollinger Bands)
- Model training and evaluation

### 3. Trading Analysis
- Advanced stock screening (Daytrade/Swing modes)
- Broker flow analysis (Bandarmology)
- Historical backtesting

### 4. Intelligence
- AI narrative generation using Google Gemini
- Explainable AI (XAI) for model decisions
- Real-time alerts and notifications

### 5. Notifications
- Telegram bot integration
- Real-time trading alerts
- System status updates

## API Endpoints

```
GET  /health              - Health check
GET  /config              - Current configuration
GET  /api/screener/daytrade  - Daytrade opportunities
GET  /api/screener/swing     - Swing trading opportunities
```

## Database Schema

Requires PostgreSQL with TimescaleDB extension:

```sql
CREATE TABLE trades (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price NUMERIC,
    volume INTEGER,
    buyer_code TEXT,
    seller_code TEXT,
    net_value BIGINT
);

CREATE TABLE order_book_snapshots (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    bids JSONB,
    asks JSONB,
    last_price NUMERIC
);

CREATE TABLE data_validation_anomalies (
    detected_at TIMESTAMPTZ NOT NULL,
    symbol TEXT,
    anomaly_type TEXT,
    severity TEXT,
    description TEXT
);
```

## Troubleshooting

### Database Connection Error
```bash
# Check database URL in .env
# Ensure PostgreSQL is running
# Test connection: psql -U admin -d dellmology
```

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Telegram Not Working
```bash
# Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
# Test token: curl https://api.telegram.org/bot<TOKEN>/getMe
```

## Performance Notes

- Use Redis for caching frequently accessed data
- Run backtesting during market hours to avoid DB locks
- Monitor API latency with `/health` endpoint
- Scale with multiple workers: `API_WORKERS=8`

## Contributing

1. Test changes locally: `pytest tests/`
2. Update configuration if adding new settings
3. Add docstrings to new functions
4. Follow the module structure

## License

Dellmology Pro © 2024-2026
