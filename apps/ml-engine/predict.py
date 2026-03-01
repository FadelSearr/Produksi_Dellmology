import tensorflow as tf
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import os
import logging
import argparse

from model import StockCNN

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URL = "postgresql://admin:password@localhost:5433/dellmology"
CHECKPOINT_DIR = "apps/ml-engine/checkpoints"
TABLE_NAME = "daily_prices"
PREDICTION_TABLE = "cnn_predictions"
WINDOW_SIZE = 128
FEATURES = ['open', 'high', 'low', 'close', 'volume']

# --- Main Execution ---

def connect_to_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        logging.fatal(f"FATAL: Could not connect to database. Error: {e}")
        raise

def get_latest_data(engine, symbol):
    """Fetches the last N days of data for prediction."""
    logging.info(f"Fetching latest {WINDOW_SIZE} days of data for {symbol}...")
    try:
        query = f"""
            SELECT date, {', '.join(FEATURES)} FROM {TABLE_NAME} 
            WHERE symbol = '{symbol}' 
            ORDER BY date DESC 
            LIMIT {WINDOW_SIZE};
        """
        # Reading data and then reversing to maintain chronological order
        df = pd.read_sql(query, engine, index_col='date').sort_index(ascending=True)
        
        if len(df) < WINDOW_SIZE:
            logging.error(f"Not enough data for {symbol}. Found {len(df)} records, need {WINDOW_SIZE}.")
            return None, None
            
        return df, df.index[-1] # Return dataframe and the last date
    except Exception as e:
        logging.error(f"Failed to load data for {symbol}: {e}")
        return None, None

def process_data_for_prediction(df):
    """Normalizes a single window of data for prediction."""
    data_np = df[FEATURES].to_numpy()
    
    min_vals = data_np.min(axis=0)
    max_vals = data_np.max(axis=0)
    range_vals = max_vals - min_vals
    range_vals[range_vals == 0] = 1
    
    normalized_window = (data_np - min_vals) / range_vals
    
    # The model expects a batch, so we add a new axis
    return np.expand_dims(normalized_window, axis=0)

def store_prediction(engine, symbol, prediction_date, raw_prediction, model_version):
    """Stores the model's prediction in the database."""
    # The raw prediction is logits, we apply softmax to get probabilities
    probabilities = tf.nn.softmax(raw_prediction).eval()
    
    confidence_up = probabilities[0][0]
    confidence_down = probabilities[0][1]
    
    predicted_class = 'UP' if confidence_up > confidence_down else 'DOWN'
    
    logging.info(f"Prediction for {symbol} on {prediction_date}: {predicted_class} (UP: {confidence_up:.2%}, DOWN: {confidence_down:.2%})")

    df = pd.DataFrame([{
        'date': prediction_date,
        'symbol': symbol,
        'prediction': predicted_class,
        'confidence_up': confidence_up,
        'confidence_down': confidence_down,
        'model_version': model_version
    }])
    
    try:
        df.to_sql(PREDICTION_TABLE, engine, if_exists='append', index=False)
        logging.info("Successfully stored prediction in database.")
    except Exception as e:
        logging.error(f"Failed to store prediction: {e}")


def main(symbol):
    """Main function to run the inference process for a given symbol."""
    logging.info(f"--- Starting inference for symbol: {symbol} ---")
    
    # 1. Connect to DB and get data
    engine = connect_to_db()
    df, last_date = get_latest_data(engine, symbol)
    if df is None:
        return
        
    # 2. Process the data into a feature window
    feature_window = process_data_for_prediction(df)

    # 3. Define TensorFlow graph and load model
    image_ph = tf.placeholder(tf.float32, [None, WINDOW_SIZE, len(FEATURES)])
    label_ph = tf.placeholder(tf.float32, [None, 2]) # Not used for inference but needed for model constructor
    dropout_ph = tf.placeholder(tf.float32)

    model = StockCNN(image_ph, label_ph, dropout_prob=dropout_ph)
    saver = tf.train.Saver()

    with tf.Session() as sess:
        # Find the latest checkpoint
        latest_checkpoint = tf.train.latest_checkpoint(CHECKPOINT_DIR)
        if not latest_checkpoint:
            logging.fatal(f"FATAL: No trained model checkpoint found in {CHECKPOINT_DIR}. Please run 'train.py' first.")
            return
            
        logging.info(f"Restoring model from {latest_checkpoint}...")
        saver.restore(sess, latest_checkpoint)
        
        # 4. Make prediction
        prediction_logits = sess.run(model.prediction, {
            image_ph: feature_window,
            dropout_ph: 1.0 # No dropout for inference
        })
        
        # 5. Store the prediction
        model_version = os.path.basename(latest_checkpoint)
        store_prediction(engine, symbol, last_date, prediction_logits, model_version)
        
    logging.info(f"--- Inference for {symbol} finished ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", help="Stock symbol to run inference for (e.g., BBCA).")
    args = parser.parse_args()
    main(args.symbol)
