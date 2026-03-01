import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import logging

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URL = "postgresql://admin:password@localhost:5433/dellmology"
TABLE_NAME = "daily_prices"

# Constants from the reference model
MOVING_WINDOW_SIZE = 128
FEATURES = ['open', 'high', 'low', 'close', 'volume']
LABEL_LOOKAHEAD_DAYS = 5

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

def load_price_data(engine, symbol):
    """Loads all historical price data for a given symbol."""
    try:
        query = f"SELECT date, {', '.join(FEATURES)} FROM {TABLE_NAME} WHERE symbol = '{symbol}' ORDER BY date ASC;"
        df = pd.read_sql(query, engine, index_col='date')
        logging.info(f"Loaded {len(df)} records for symbol {symbol}.")
        return df
    except Exception as e:
        logging.error(f"Failed to load data for {symbol}: {e}")
        return pd.DataFrame()

def create_features_and_labels(df):
    """
    Creates the feature windows and corresponding labels from the historical data,
    replicating the logic from the reference loader.py.
    """
    if len(df) < MOVING_WINDOW_SIZE + LABEL_LOOKAHEAD_DAYS:
        logging.warning("Not enough data to create any features.")
        return np.array([]), np.array([])

    feature_set = []
    label_set = []

    data_np = df[FEATURES].to_numpy()

    for i in range(len(data_np) - (MOVING_WINDOW_SIZE + LABEL_LOOKAHEAD_DAYS)):
        # 1. Create the window of 128 days with 5 features
        window = data_np[i : i + MOVING_WINDOW_SIZE]

        # 2. Normalize the window using Min-Max scaling
        min_vals = window.min(axis=0)
        max_vals = window.max(axis=0)
        # Avoid division by zero if a column is constant
        range_vals = max_vals - min_vals
        range_vals[range_vals == 0] = 1 
        normalized_window = (window - min_vals) / range_vals
        feature_set.append(normalized_window)

        # 3. Create the label by looking 5 days ahead
        current_close = data_np[i + MOVING_WINDOW_SIZE - 1, 3] # Close price is at index 3
        future_close = data_np[i + MOVING_WINDOW_SIZE + LABEL_LOOKAHEAD_DAYS - 1, 3]
        
        if future_close > current_close:
            label_set.append([1.0, 0.0])  # UP
        else:
            label_set.append([0.0, 1.0])  # DOWN or SAME
            
    return np.array(feature_set), np.array(label_set)


def main():
    """Main function to run the feature generation process."""
    logging.info("Starting feature generation process...")
    engine = connect_to_db()

    # For now, we'll just process one stock as a prototype
    target_symbol = "BBCA" 
    
    df = load_price_data(engine, target_symbol)
    if df.empty:
        return
        
    features, labels = create_features_and_labels(df)
    
    if features.size > 0 and labels.size > 0:
        logging.info(f"Successfully generated {len(features)} samples.")
        logging.info(f"Feature set shape: {features.shape}") # (num_samples, 128, 5)
        logging.info(f"Label set shape: {labels.shape}")   # (num_samples, 2)
        
        # 4. Save the processed data to files
        # In a real MLOps pipeline, this would go to a feature store or cloud storage.
        # For now, we save locally.
        output_dir = "apps/ml-engine/processed_data"
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        np.save(os.path.join(output_dir, f"{target_symbol}_features.npy"), features)
        np.save(os.path.join(output_dir, f"{target_symbol}_labels.npy"), labels)
        
        logging.info(f"Saved feature and label sets to '{output_dir}'.")
    else:
        logging.warning("No features were generated.")


if __name__ == "__main__":
    main()
