import tensorflow as tf
import numpy as np
import os
import logging

from model import StockCNN

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Data and Model paths
DATA_DIR = "apps/ml-engine/processed_data"
SYMBOL = "BBCA"
CHECKPOINT_DIR = "apps/ml-engine/checkpoints"
MODEL_NAME = "stock_model.ckpt"

# Training Parameters
BATCH_SIZE = 128
TRAINING_STEPS = 200000
TEST_SPLIT = 0.2 # 20% of data for testing
DROPOUT_PROB = 0.5

# --- Main Execution ---

def load_data():
    """Loads the processed feature and label files."""
    logging.info(f"Loading data for symbol {SYMBOL} from {DATA_DIR}...")
    try:
        features_path = os.path.join(DATA_DIR, f"{SYMBOL}_features.npy")
        labels_path = os.path.join(DATA_DIR, f"{SYMBOL}_labels.npy")
        
        features = np.load(features_path)
        labels = np.load(labels_path)
        
        logging.info(f"Features shape: {features.shape}")
        logging.info(f"Labels shape: {labels.shape}")
        
        return features, labels
    except FileNotFoundError:
        logging.fatal(f"FATAL: Data files not found. Please run 'feature_generator.py' first.")
        return None, None

def split_data(features, labels):
    """Splits data into training and testing sets."""
    split_idx = int(len(features) * (1 - TEST_SPLIT))
    
    x_train = features[:split_idx]
    y_train = labels[:split_idx]
    
    x_test = features[split_idx:]
    y_test = labels[split_idx:]
    
    logging.info(f"Training set size: {len(x_train)}")
    logging.info(f"Testing set size: {len(x_test)}")
    
    return x_train, y_train, x_test, y_test

def get_next_batch(features, labels, index, batch_size):
    """A simple utility to get the next batch of data."""
    start = index
    end = index + batch_size
    if end > len(features):
        return None, None, 0 # End of epoch
    return features[start:end], labels[start:end], end

def main():
    # 1. Load and prepare data
    features, labels = load_data()
    if features is None:
        return
    
    x_train, y_train, x_test, y_test = split_data(features, labels)
    
    # 2. Define TensorFlow graph
    # Input shapes from the model reference
    image_shape = [None, 128, 5] 
    label_shape = [None, 2]
    
    image_ph = tf.placeholder(tf.float32, image_shape, name="input_image")
    label_ph = tf.placeholder(tf.float32, label_shape, name="input_label")
    dropout_ph = tf.placeholder(tf.float32, name="dropout_prob")

    # 3. Instantiate the Model
    model = StockCNN(image_ph, label_ph, dropout_prob=dropout_ph)
    
    # 4. Create a saver to store the trained model
    saver = tf.train.Saver()
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    # 5. Start the training session
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True # Allow GPU memory to grow if needed
    
    with tf.Session(config=config) as sess:
        sess.run(tf.global_variables_initializer())
        logging.info("Starting model training...")
        
        batch_index = 0
        for i in range(TRAINING_STEPS):
            # Get the next batch of training data
            x_batch, y_batch, next_idx = get_next_batch(x_train, y_train, batch_index, BATCH_SIZE)
            
            # If we've reached the end of the epoch, reset
            if x_batch is None:
                batch_index = 0
                continue
            batch_index = next_idx

            # Run the optimization step
            sess.run(model.optimize, {
                image_ph: x_batch,
                label_ph: y_batch,
                dropout_ph: DROPOUT_PROB
            })
            
            # Periodically evaluate accuracy and save the model
            if i % 1000 == 0:
                # Evaluate on a batch of test data
                accuracy = sess.run(model.accuracy, {
                    image_ph: x_test, 
                    label_ph: y_test,
                    dropout_ph: 1.0 # No dropout during testing
                })
                logging.info(f"Step {i}, Test Accuracy: {accuracy:.4f}")
                
                # Save checkpoint
                save_path = saver.save(sess, os.path.join(CHECKPOINT_DIR, MODEL_NAME), global_step=i)
                logging.info(f"Model saved to {save_path}")

        # Final accuracy evaluation
        final_accuracy = sess.run(model.accuracy, {
            image_ph: x_test,
            label_ph: y_test,
            dropout_ph: 1.0
        })
        logging.info(f"Final accuracy on testing set: {final_accuracy:.4f}")

    logging.info("Training finished.")

if __name__ == '__main__':
    main()
