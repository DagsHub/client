# Credit to TensorFlow Expert Quickstart for providing much of this code
# Note: This is a terrible model architecture with bad pracices, meant only
# to demonstrate and test the DAGsHubLogger callback
from dagshub.keras import DAGsHubLogger
from tensorflow.keras.layers import Dense, Flatten, Conv2D, Input
from tensorflow.keras import Sequential
from tensorflow.keras.datasets import mnist
from tensorflow.data import Dataset
import tensorflow as tf
print("TensorFlow version:", tf.__version__)


(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0
x_train = x_train[..., tf.newaxis].astype("float32")
x_test = x_test[..., tf.newaxis].astype("float32")
train_ds = Dataset.from_tensor_slices((x_train, y_train)).shuffle(10000).batch(32)
test_ds = Dataset.from_tensor_slices((x_test, y_test)).batch(32)


model = Sequential([
    Input((28, 28, 1)),
    Conv2D(10, 3, activation='relu'),
    Flatten(),
    Dense(20, activation='relu'),
    Dense(10)
])
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics='accuracy')
model.summary()

model.fit(train_ds, validation_data=test_ds, epochs=10, callbacks=[DAGsHubLogger()])
