import os

import tensorflow as tf
import numpy as np

import training_data

x = tf.placeholder(tf.float32, [None, 16])
W = tf.Variable(tf.truncated_normal((16, 4), stddev=0.1))
b = tf.Variable(tf.zeros([4]))
y = tf.nn.softmax(tf.matmul(x, W) + b)
y_ = tf.placeholder(tf.float32, [None, 4])
cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))
train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)
sess = tf.InteractiveSession()
tf.global_variables_initializer().run()

# Load data
input_folder = 'single_file'

t = training_data.training_data()
t.read(input_folder)
x_training = t.get_x()
y_training = t.get_y()

number_of_items = t.size()
x_training = np.reshape(x_training, (number_of_items, 16)).astype(float)

#x_training_tensor = tf.convert_to_tensor(x_training, dtype='float32')
#y_training_tensor = tf.convert_to_tensor(y_training)
#print x_training_tensor

dataset = tf.data.Dataset.from_tensor_slices({"a": x_training, "b": y_training})

(thisW, thisb, thisy) = sess.run([W, b, y], feed_dict={x: x_training, y_: y_training})
print("Initial gradients: {}".format(thisW))
print("Initial biases: {}".format(thisb))
print("Initial output: {}".format(thisy))

for _ in range(1):
  sess.run(train_step, feed_dict={x: x_training, y_: y_training})

(thisW, thisb, thisy) = sess.run([W, b, y], feed_dict={x: x_training, y_: y_training})
print("Trained gradients: {}".format(thisW))
print("Trained biases: {}".format(thisb))
print("Trained output: {}".format(thisy))

correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
print(sess.run(accuracy, feed_dict={x: x_training, y_: y_training}))
