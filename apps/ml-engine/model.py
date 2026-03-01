import tensorflow as tf
import functools

# Note: This is an adaptation of the model structure from the reference project
# 'Deep-Convolution-Stock-Technical-Analysis-master'. The 'ops.py' file
# from that project would be required, containing implementations for
# conv1d, fully_connected, batchnorm, lrelu, and relu.

# Since ops.py is not provided, we will use tf.layers and other standard
# TensorFlow functions as modern equivalents where possible.

def conv1d(input_, output_dim, kernel_size=9, stride=1, stddev=0.02, name="conv1d"):
    with tf.variable_scope(name):
        return tf.layers.conv1d(
            inputs=input_,
            filters=output_dim,
            kernel_size=kernel_size,
            strides=stride,
            padding='same',
            kernel_initializer=tf.truncated_normal_initializer(stddev=stddev),
            bias_initializer=tf.constant_initializer(0.0)
        )

def fully_connected(input_, output_size, scope=None, stddev=0.02, bias_start=0.0, with_w=False):
     with tf.variable_scope(scope or "fully_connected"):
         return tf.layers.dense(
             inputs=input_,
             units=output_size,
             activation=None,
             kernel_initializer=tf.random_normal_initializer(stddev=stddev),
             bias_initializer=tf.constant_initializer(bias_start)
         )

def lrelu(x, leak=0.2, name="lrelu"):
  return tf.maximum(x, leak*x)

def relu(x, name="relu"):
    return tf.nn.relu(x)

def batchnorm(input_, is_2d=False):
    return tf.layers.batch_normalization(input_, training=True, momentum=0.9, epsilon=1e-5)


@functools.wraps(tf.variable_scope)
def define_scope(function, scope=None, *args, **kwargs):
    """
    A decorator for functions that define TensorFlow operations. The wrapped
    function will only be executed once. Subsequent calls to it will directly
    return the result so that operations are added to the graph only once.
    """
    attribute = '_cache_' + function.__name__
    name = scope or function.__name__
    @property
    @functools.wraps(function)
    def decorator(self):
        if not hasattr(self, attribute):
            with tf.variable_scope(name, *args, **kwargs):
                setattr(self, attribute, function(self))
        return getattr(self, attribute)
    return decorator

class StockCNN:
  def __init__(self,
    image,
    label,
    dropout_prob=0.5,
    filter_num=128):

    self.image = image
    self.label = label
    self.dropout_prob = dropout_prob
    self.filter_num = filter_num

    self.prediction
    self.optimize
    self.accuracy

  @define_scope
  def prediction(self):
    # The architecture is based on the reference model.
    layers = []

    # Layer 1: conv_1
    with tf.variable_scope("conv_1"):
        output = relu(conv1d(self.image, self.filter_num, name='conv_1'))
        layers.append(output)

    # Subsequent convolutional layers
    layer_specs = [
        (self.filter_num * 2, 0.5),  # conv_2
        (self.filter_num * 4, 0.5),  # conv_3
        (self.filter_num * 8, 0.5),  # conv_4
        (self.filter_num * 8, 0.5),  # conv_5
        (self.filter_num * 8, 0.5)   # conv_6
    ]

    for i, (out_channels, dropout) in enumerate(layer_specs):
        with tf.variable_scope(f"conv_{i+2}"):
            rectified = lrelu(layers[-1], 0.2)
            convolved = conv1d(rectified, out_channels)
            output = batchnorm(convolved)
            if dropout > 0.0:
                output = tf.nn.dropout(output, keep_prob=1 - dropout)
            layers.append(output)

    # Flatten the last conv layer
    flat_output = tf.layers.flatten(layers[-1])

    # Fully connected layers
    h_fc1 = relu(fully_connected(flat_output, 256, scope='fc1'))
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob=self.dropout_prob)
    
    # Output layer (2 classes: UP or DOWN)
    result = fully_connected(h_fc1_drop, 2, scope='fc2')
    
    return result

  @define_scope
  def optimize(self):
    # Using softmax cross-entropy for classification loss
    cross_entropy = tf.reduce_mean(
        tf.nn.softmax_cross_entropy_with_logits_v2(labels=self.label, logits=self.prediction)
    )
    # Using Adam optimizer
    return tf.train.AdamOptimizer(learning_rate=0.0001).minimize(cross_entropy)

  @define_scope
  def accuracy(self):
    correct_prediction = tf.equal(tf.argmax(self.label, 1), tf.argmax(self.prediction, 1))
    return tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
