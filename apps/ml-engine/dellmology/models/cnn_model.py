"""
CNN Model Module
Deep Convolutional Neural Network for pattern recognition
"""

import logging
import tensorflow as tf

logger = logging.getLogger(__name__)


def build_cnn_model(input_shape=(20, 10)) -> tf.keras.Model:
    """
    Build CNN model for stock pattern detection
    
    Args:
        input_shape: Expected input shape (window, features)
    
    Returns:
        Compiled Keras model
    """
    model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(32, kernel_size=3, activation='relu', input_shape=input_shape),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Conv1D(64, kernel_size=3, activation='relu'),
        tf.keras.layers.GlobalMaxPooling1D(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model
