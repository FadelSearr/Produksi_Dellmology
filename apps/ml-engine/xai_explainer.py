import os
import logging
import numpy as np
from sqlalchemy import text
from feature_generator import MOVING_WINDOW_SIZE, FEATURES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_latest_window(engine, symbol):
    """Load the most recent MOVING_WINDOW_SIZE rows for `symbol` and
    return a normalized input array shaped (1, MOVING_WINDOW_SIZE, len(FEATURES))."""
    with engine.connect() as conn:
        query = text(f"SELECT {', '.join(FEATURES)} FROM daily_prices WHERE symbol = :sym ORDER BY date DESC LIMIT {MOVING_WINDOW_SIZE}")
        df = conn.execute(query, {"sym": symbol}).fetchall()

    if not df or len(df) < MOVING_WINDOW_SIZE:
        raise ValueError("Not enough data to explain; need full moving window")

    arr = np.array([tuple(r) for r in df])
    # rows are newest->oldest, reverse to chronological
    arr = arr[::-1]

    # Min-max normalize per column
    min_vals = arr.min(axis=0)
    max_vals = arr.max(axis=0)
    range_vals = max_vals - min_vals
    range_vals[range_vals == 0] = 1
    normalized = (arr - min_vals) / range_vals
    return normalized.reshape(1, MOVING_WINDOW_SIZE, len(FEATURES)), min_vals, max_vals


def explain_symbol(symbol: str, engine, top_k: int = 10):
    """Return a simple ablation importance map for the latest input window.

    This performs a single-session restore of the TF1 CNN (same as prediction)
    and measures the change in predicted UP-probability when each single
    input feature (day,feature) is set to its column baseline.
    """
    try:
        import tensorflow as tf
        from model import StockCNN
    except Exception as e:
        logger.error(f"TensorFlow or model import failed: {e}")
        raise

    # load input
    input_array, min_vals, max_vals = load_latest_window(engine, symbol)
    num_days = MOVING_WINDOW_SIZE
    num_feats = len(FEATURES)

    checkpoint_dir = os.path.join(os.getcwd(), "checkpoints")

    tf.compat.v1.reset_default_graph()
    with tf.compat.v1.Session() as sess:
        image_ph = tf.compat.v1.placeholder(tf.float32, [None, MOVING_WINDOW_SIZE, num_feats], name="input_image")
        label_ph = tf.compat.v1.placeholder(tf.float32, [None, 2], name="input_label")
        dropout_ph = tf.compat.v1.placeholder(tf.float32, name="dropout_prob")

        model = StockCNN(image_ph, label_ph, dropout_prob=dropout_ph)
        saver = tf.compat.v1.train.Saver()

        latest = tf.train.latest_checkpoint(checkpoint_dir)
        if latest is None:
            raise FileNotFoundError("No checkpoint found for XAI explanation")
        saver.restore(sess, latest)

        def predict_probs(batch_input):
            # returns UP probability (index 0) for each sample
            logits = sess.run(model.prediction, {image_ph: batch_input, dropout_ph: 1.0})
            probs = tf.nn.softmax(logits).eval(session=sess)
            return probs[:, 0]

        base_prob = float(predict_probs(input_array)[0])

        # baseline per-column: use the column mean of the window
        baseline = input_array.mean(axis=1, keepdims=True)  # shape (1,1,num_feats)

        import copy
        import math

        importance_map = np.zeros((num_days, num_feats), dtype=float)

        # For each feature (day,feat) perform ablation to baseline and measure change
        for d in range(num_days):
            for f in range(num_feats):
                perturbed = input_array.copy()
                perturbed[0, d, f] = baseline[0, 0, f]
                try:
                    p = float(predict_probs(perturbed)[0])
                except Exception as e:
                    logger.error(f"Prediction failed during XAI for {symbol}: {e}")
                    p = base_prob
                importance_map[d, f] = abs(base_prob - p)

        # flatten and sort
        flat_idx = np.argsort(importance_map.flatten())[::-1]
        results = []
        for idx in flat_idx[:top_k]:
            day = idx // num_feats
            feat = idx % num_feats
            results.append({
                'day_index': int(day),
                'feature': FEATURES[feat],
                'importance': float(importance_map[day, feat])
            })

        # also return aggregated importance per feature name
        agg = {}
        for i, name in enumerate(FEATURES):
            agg[name] = float(importance_map[:, i].sum())

        return {
            'symbol': symbol,
            'base_prob_up': base_prob,
            'top_features': results,
            'aggregate_feature_importance': agg
        }


if __name__ == "__main__":
    # quick local test harness
    from predict import connect_to_db
    eng = connect_to_db()
    print(explain_symbol('BBCA', eng, top_k=8))
