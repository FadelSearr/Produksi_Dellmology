import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import logging

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# In a real system, this would come from a DB or config file.
# Using the same list as the broker-importer. Appending .JK for yahoo finance format.
TARGET_SYMBOLS = ["BBCA.JK", "TLKM.JK", "GOTO.JK", "BBNI.JK"] 
DATABASE_URL = "postgresql://admin:password@localhost:5433/dellmology"
TABLE_NAME = "daily_prices"

# --- Main Execution ---

def connect_to_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        engine = create_engine(DATABASE_URL)
        logging.info("Successfully connected to the database.")
        return engine
    except Exception as e:
        logging.fatal(f"FATAL: Could not connect to database. Error: {e}")
        raise

def fetch_historical_data(symbol, period="5y"):
    """Fetches historical OHLCV data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        if history.empty:
            logging.warning(f"No data found for symbol {symbol}.")
            return None
        
        # Format the dataframe to match our table schema
        history.reset_index(inplace=True)
        history['symbol'] = symbol.replace('.JK', '') # Use clean symbol for DB
        history = history[['Date', 'symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
        history.columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        history['date'] = pd.to_datetime(history['date']).dt.date
        
        logging.info(f"Successfully fetched {len(history)} records for {symbol}.")
        return history
        
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {e}")
        return None

def store_data(engine, df):
    """Stores a dataframe into the specified database table."""
    try:
        # Use 'append' and rely on the primary key constraint to avoid duplicates.
        # This is simpler than checking for existing data but might be slower on very large datasets.
        # A more robust solution would be to load to a temp table and use SQL to merge.
        df.to_sql(
            TABLE_NAME,
            engine,
            if_exists='append',
            index=False,
            method=None # Let sqlalchemy decide the best method
        )
        logging.info(f"Successfully stored {len(df)} records in '{TABLE_NAME}'.")
    except Exception as e:
        # We log the error but don't stop the whole process if one batch fails.
        # This can happen if we try to insert duplicate primary keys.
        logging.error(f"Error storing data. This might be due to duplicate entries (date, symbol), which is safe to ignore. Details: {e}")


def main():
    """Main function to run the data import process."""
    logging.info("Starting historical data importer...")
    engine = connect_to_db()

    for symbol in TARGET_SYMBOLS:
        logging.info(f"--- Processing symbol: {symbol} ---")
        df = fetch_historical_data(symbol)
        if df is not None and not df.empty:
            store_data(engine, df)
    
    logging.info("Historical data import process finished.")

if __name__ == "__main__":
    main()
