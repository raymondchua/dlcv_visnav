from __future__ import with_statement
from PIL import Image as pimg
import numpy as np
import tensorflow as tf
import  os
import preprocessing as pre
import logging
import time
from datetime import datetime
from tensorflow.contrib import rnn

tf.logging.set_verbosity(tf.logging.INFO)

BATCH_SIZE = 49
NUM_THREADS = 16
NUM_SAMPLES = 6811
NUM_BATCHES = int(NUM_SAMPLES/BATCH_SIZE)
MIN_QUEUE_SIZE = int(NUM_SAMPLES * 0.4)
NUM_ITER = 201

MOVING_AVERAGE_DECAY = 0.9999
NUM_EPOCHS_PER_DECAY = 300.0       	# Epochs after which learning rate decays.
LEARNING_RATE_DECAY_FACTOR = 0.1   	# Learning rate decay factor.
INITIAL_LEARNING_RATE = 0.001     	# Initial learning rate.

N_STEPS = 32
N_INPUT = 72
N_HIDDEN = 128




def train():
	graph = tf.Graph()
	with graph.as_default():

		global_step = tf.Variable(0, name='global_step', trainable=False)

		im, la = pre.get_val()
		images, labels = pre.read_opt_data(im, la, BATCH_SIZE, NUM_SAMPLES, False)

		#split images into original and optical flow
		images_ori, images_opt = tf.split(images, [3,3], 3)


		#---------------NVIDIA----------------------

		# First convolutional layer 
		W_conv1 = weight_variable('conv_weights_1', [5, 5, 3, 24], 0.01)
		b_conv1 = bias_variable('conv_biases_1', [24])
		h_conv1 = tf.nn.relu(conv2d(images_ori, W_conv1) + b_conv1)

		# Pooling layer - downsamples by 2X.
		max_pool_1 = max_pool_2x2(h_conv1)

		# Second convolutional layer 
		W_conv2 = weight_variable('conv_weights_2', [5, 5, 24, 36], 24.0)
		b_conv2 = bias_variable('conv_biases_2', [36])
		h_conv2 = tf.nn.relu(conv2d(max_pool_1, W_conv2) + b_conv2)

		# Second Pooling layer
		max_pool_2 = max_pool_2x2(h_conv2)

		# Third convolutional layer 
		W_conv3 = weight_variable('conv_weights_3', [5, 5, 36, 48], 36.0)
		b_conv3 = bias_variable('conv_biases_3', [48])
		h_conv3 = tf.nn.relu(conv2d(max_pool_2, W_conv3) + b_conv3)

		# Third Pooling layer
		max_pool_3 = max_pool_2x2(h_conv3)

		# Fourth convolutional layer 
		W_conv4 = weight_variable('conv_weights_4', [3, 3, 48, 64], 48.0)
		b_conv4 = bias_variable('conv_biases_4', [64])
		h_conv4 = tf.nn.relu(conv2d(max_pool_3, W_conv4) + b_conv4)

		# Fifth convolutional layer 
		W_conv5 = weight_variable('conv_weights_5', [3, 3, 64, 64], 64.0)
		b_conv5 = bias_variable('conv_biases_5', [64])
		h_conv5 = tf.nn.relu(conv2d(h_conv4, W_conv5) + b_conv5)

		#stack result into one dimensional vector by using -1 option
		#conv_flat = tf.reshape(h_conv5, [BATCH_SIZE, -1]) 

		# # Fully connected layer 1
		# W_fc1 = weight_variable('fc_weights_1', [1 * 18 * 64, 1164], 1164.0)
		# b_fc1 = bias_variable('fc_biases_1', [1164])
		# h_fc1 = tf.nn.relu(tf.matmul(conv_flat, W_fc1) + b_fc1)

		# # Fully connected layer 2
		# W_fc2 = weight_variable('fc_weights_2', [1164, 100], 100.0)
		# b_fc2 = bias_variable('fc_biases_2', [100])
		# h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

		# # Fully connected layer 3
		# W_fc3 = weight_variable('fc_weights_3', [100, 10], 10.0)
		# b_fc3 = bias_variable('fc_biases_3', [10])
		# h_fc3 = tf.nn.relu(tf.matmul(h_fc2, W_fc3) + b_fc3)

		# # Fully connected layer 4
		# W_fc4 = weight_variable('fc_weights_4', [10, 1], 1.0)
		# b_fc4 = bias_variable('fc_biases_4', [1])
		# h_fc4 = tf.matmul(h_fc3, W_fc4) + b_fc4

		# # radiants in the range of [-pi/2, pi/2] * 2 to get 360 range
		# y = tf.multiply(tf.atan(h_fc4), 2)


		#------------------OPTICAL FLOW---------------------------------

		# First convolutional layer 
		W_conv1_opt = weight_variable('conv_weights_1_opt', [5, 5, 3, 24], 0.01)
		b_conv1_opt = bias_variable('conv_biases_1_opt', [24])
		h_conv1_opt = tf.nn.relu(conv2d(images_opt, W_conv1_opt) + b_conv1_opt)

		# Pooling layer - downsamples by 2X.
		max_pool_1_opt = max_pool_2x2(h_conv1_opt)

		# Second convolutional layer 
		W_conv2_opt = weight_variable('conv_weights_2_opt', [5, 5, 24, 36], 24.0)
		b_conv2_opt = bias_variable('conv_biases_2_opt', [36])
		h_conv2_opt = tf.nn.relu(conv2d(max_pool_1_opt, W_conv2_opt) + b_conv2_opt)

		# Second Pooling layer
		max_pool_2_opt = max_pool_2x2(h_conv2_opt)

		# Third convolutional layer 
		W_conv3_opt = weight_variable('conv_weights_3_opt', [5, 5, 36, 48], 36.0)
		b_conv3_opt = bias_variable('conv_biases_3_opt', [48])
		h_conv3_opt = tf.nn.relu(conv2d(max_pool_2_opt, W_conv3_opt) + b_conv3_opt)

		# Third Pooling layer
		max_pool_3_opt = max_pool_2x2(h_conv3_opt)

		# Fourth convolutional layer 
		W_conv4_opt = weight_variable('conv_weights_4_opt', [3, 3, 48, 64], 48.0)
		b_conv4_opt = bias_variable('conv_biases_4_opt', [64])
		h_conv4_opt = tf.nn.relu(conv2d(max_pool_3_opt, W_conv4_opt) + b_conv4_opt)

		# Fifth convolutional layer 
		W_conv5_opt = weight_variable('conv_weights_5_opt', [3, 3, 64, 64], 64.0)
		b_conv5_opt = bias_variable('conv_biases_5_opt', [64])
		h_conv5_opt = tf.nn.relu(conv2d(h_conv4_opt, W_conv5_opt) + b_conv5_opt)

		#concat the convolution results and flatten them
		combined = tf.concat([h_conv5, h_conv5_opt], 3)

		pred = RNN(combined)

		loss = loss_func(pred, labels)

		# training operator for session call
		# train_op, lr = optimize(loss, global_step)

		# max_to_keep option to store all weights
		saver = tf.train.Saver(tf.global_variables(), max_to_keep=None)

		#tensorflow session 
		session = tf.Session()

		#tensorboard
		# merged = tf.summary.merge_all()
		# train_writer = tf.summary.FileWriter('train_lstm', session.graph)

		#initialization of all variables
		session.run(tf.global_variables_initializer())
		session.run(tf.local_variables_initializer())

		#threads
		coord = tf.train.Coordinator()
		threads = tf.train.start_queue_runners(coord=coord, sess=session)

		#save weights in directory
		#TODO file is empty
		# ckpt = tf.train.get_checkpoint_state('./weights/')
		# saver.restore(session, '/work/raymond/dlcv/dlcv_visnav/src/check_files/model99.ckpt-99')

		logging.basicConfig(filename='../log/training_lstm_eval.log',level=logging.INFO)


		for x in range(NUM_ITER):
			average_loss = 0.0
			
			ckpt = tf.train.get_checkpoint_state('/work/raymond/dlcv/dlcv_visnav/src/check_files_lstm/')

			checkpoint_dir = '/work/raymond/dlcv/dlcv_visnav/src/check_files_lstm/'
			checkpoint_filename = 'lstm_model'+str(x)+'.ckpt-'+str(x)
			saver.restore(session, checkpoint_dir+checkpoint_filename)
			print(checkpoint_filename + " loaded successfully...")

			for y in range(NUM_BATCHES):
				lossVal = session.run(loss)
				print('iteration: ', x)
				print('loss: ', lossVal)
				average_loss = average_loss+lossVal

			# 	#print("done")
				print('batch: ', y)
				#print(lossVal)
			# 	# print(image_out.shape)
				
			# 	#break
			
			average_loss = average_loss/NUM_BATCHES
			print("average_loss: ", average_loss)

			content = x, checkpoint_filename, average_loss
			logging.info(content)
			
			# str1 = str(x)
			# str2 = "check_files_lstm_v2/lstm_model"
			# str3 = ".ckpt"
			# str4 = str2 + str1 + str3

			# save_path = saver.save(session, str4, global_step=x)

			# content = datetime.now(), x, curr_learnRate, average_loss
			# logging.info(content)


		
		#train_writer.close()
		
		#tensorflow threads 
		coord.request_stop()
		coord.join(threads)

def loss_func(logits, labels):
	loss = tf.reduce_mean(tf.squared_difference(logits, labels))
	
	tf.add_to_collection('losses', loss)

	return tf.add_n(tf.get_collection('losses'), name='total_loss')

def _add_loss_summaries(total_loss):

	loss_averages = tf.train.ExponentialMovingAverage(0.9, name='avg')
	losses = tf.get_collection('losses')
	loss_averages_op = loss_averages.apply(losses + [total_loss])

	for l in losses + [total_loss]:
		# Name each loss as '(raw)' and name the moving average version of the loss
		# as the original loss name.
		tf.summary.scalar(l.op.name + ' (raw)', l)
		tf.summary.scalar(l.op.name, loss_averages.average(l))

	return loss_averages_op

def optimize(total_loss, global_step):
	# Variables that affect learning rate.
	num_batches_per_epoch = NUM_SAMPLES / BATCH_SIZE
	decay_steps = int(num_batches_per_epoch * NUM_EPOCHS_PER_DECAY)

	# Decay the learning rate exponentially based on the number of steps.
	lr = tf.train.exponential_decay(INITIAL_LEARNING_RATE,
									global_step,
									decay_steps,
									LEARNING_RATE_DECAY_FACTOR,
									staircase=True)
	tf.summary.scalar('learning_rate', lr)

	# Generate moving averages of all losses and associated summaries.
	loss_averages_op = _add_loss_summaries(total_loss)

	# Compute gradients.
	# control_dependencies is for the gpu to compute this first
	with tf.control_dependencies([loss_averages_op]):
		opt = tf.train.AdamOptimizer(lr)
		grads = opt.compute_gradients(total_loss)

	# Apply gradients to variables w = w + g
	apply_gradient_op = opt.apply_gradients(grads, global_step=global_step)

	# Add histograms for trainable variables.
	for var in tf.trainable_variables():
		tf.summary.histogram(var.op.name, var)

	# Add histograms for gradients.
	for grad, var in grads:
		if grad is not None:
			tf.summary.histogram(var.op.name + '/gradients', grad)

	# Track the moving averages of all trainable variables.
	# speeds up convergence for more info got to documentation
	variable_averages = tf.train.ExponentialMovingAverage(
			MOVING_AVERAGE_DECAY, global_step)
	variables_averages_op = variable_averages.apply(tf.trainable_variables())

	# placeholder to finish computation of dependencies
	with tf.control_dependencies([apply_gradient_op, variables_averages_op]):
		train_op = tf.no_op(name='train')

	return train_op, lr

def RNN(x):
	batch_x = tf.reshape(x, [BATCH_SIZE, N_STEPS, N_INPUT])

	# Unstack to get a list of 'n_steps' tensors of shape (batch_size, n_input)
	x_unstack = tf.unstack(batch_x, N_STEPS, 1)

	# Define a lstm cell with tensorflow
	lstm_cell = rnn.BasicLSTMCell(N_HIDDEN, forget_bias=1.0)

	# Get lstm cell output
	outputs, states = rnn.static_rnn(lstm_cell, x_unstack, dtype=tf.float32)

	W_fc1_opt = weight_variable('lstm_weights_1', [N_HIDDEN, 1], float(N_HIDDEN))
	b_fc1_opt = bias_variable('lstm_bias_1', [1])

	outputs = tf.matmul(outputs[-1], W_fc1_opt) + b_fc1_opt

	# radiants in the range of [-pi/2, pi/2] * 2 to get 360 range
	y_opt = tf.multiply(tf.atan(outputs), 2)


	return y_opt


def conv2d(x, W):
	"""conv2d returns a 2d convolution layer with full stride."""
	return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID')


def max_pool_2x2(x):
	"""max_pool_2x2 downsamples a feature map by 2X."""
	return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')


def weight_variable(name, shape, stddev):
	"""weight_variable generates a weight variable of a given shape."""
	#1/sqrt(x)
	initial = tf.truncated_normal_initializer(stddev=tf.rsqrt(stddev))
	return _variable_with_weight_decay(name, shape, initial, wd=0.0004)


def bias_variable(name, shape):
	"""bias_variable generates a bias variable of a given shape."""
	initial = tf.constant_initializer(0.1)
	return _variable_with_weight_decay(name, shape, initial, wd=0.0004)

def _variable_on_cpu(name, shape, initializer):
	with tf.device('/cpu:0'):
		var = tf.get_variable(name, shape,tf.float32,initializer)
	return var

def _variable_with_weight_decay(name, shape, initializer, wd=None):
	"""
	Helper function to create an initialized variable with weight decay
	A weight decay act as a regularization, only is only added if specified.
	In our case, it is the l2-norm of the weights multiply by the weight decay value.
	"""

	var = _variable_on_cpu(name, shape, initializer)

	if wd is not None:
		weight_decay = tf.multiply(tf.nn.l2_loss(var), wd, name='weight_loss')
		tf.add_to_collection('losses', weight_decay)
	return var


def main():
	train()

if __name__ == "__main__":
	main()