import os
import pathlib

import conducto as co

# Convert the binary audio file to a tensor
def decode_audio(audio_binary):
  import tensorflow as tf

  audio, _ = tf.audio.decode_wav(audio_binary)

  return tf.squeeze(audio, axis=-1)

# Get the label (yes, no, up, down, etc) for an audio file.
def get_label(file_path):
  import tensorflow as tf

  parts = tf.strings.split(file_path, os.path.sep)

  # Note: You'll use indexing here instead of tuple unpacking to enable this to work in a TensorFlow graph.
  return parts[-2]

# Create a tuple that has the labeled audio files
def get_waveform_and_label(file_path):
  import tensorflow as tf

  label = get_label(file_path)
  audio_binary = tf.io.read_file(file_path)
  waveform = decode_audio(audio_binary)

  return waveform, label

# Convert audio files to images
def get_spectrogram(waveform):
  import tensorflow as tf

  # Padding for files with less than 16000 samples
  zero_padding = tf.zeros([16000] - tf.shape(waveform), dtype=tf.float32)

  # Concatenate audio with padding so that all audio clips will be of the same length
  waveform = tf.cast(waveform, tf.float32)
  equal_length = tf.concat([waveform, zero_padding], 0)
  spectrogram = tf.signal.stft(
      equal_length, frame_length=255, frame_step=128)

  spectrogram = tf.abs(spectrogram)

  return spectrogram

# Label the images created from the audio files and return a tuple
def get_spectrogram_and_label_id(audio, label, commands):
  import tensorflow as tf

  spectrogram = get_spectrogram(audio)
  spectrogram = tf.expand_dims(spectrogram, -1)
  label_id = tf.argmax(label == commands)
  return spectrogram, label_id

# Preprocess any audio files
def preprocess_dataset(files, autotune, commands):
  import tensorflow as tf

  # Creates the dataset
  files_ds = tf.data.Dataset.from_tensor_slices(files)

  # Matches audio files with correct labels
  output_ds = files_ds.map(get_waveform_and_label,
                            num_parallel_calls=autotune)

  # Matches audio file images to the correct labels
  output_ds = output_ds.map(lambda audio, label:
      get_spectrogram_and_label_id(audio, label, commands),  num_parallel_calls=autotune)

  return output_ds

# Convert audio files to images with PyTorch
def get_spectrogram_pytorch(waveform):
  import torch
  import torchaudio.transforms as T

  spectrogram = T.Spectrogram(
      n_fft=400,
      win_length=None,
      hop_length=None,
      center=True,
      pad_mode="reflect",
      power=2.0,
  )

  return spectrogram(waveform)

# Extract features for sklearn
def extract_feature(file_name, **kwargs):
  import soundfile
  import librosa
  import glob
  import numpy as np

  """
  Extract feature from audio file `file_name`
    Features supported:
      - MFCC (mfcc)
      - Chroma (chroma)
      - MEL Spectrogram Frequency (mel)
      - Contrast (contrast)
      - Tonnetz (tonnetz)
    e.g:
    `features = extract_feature(path, mel=True, mfcc=True)`
  """
  mfcc = kwargs.get("mfcc")
  chroma = kwargs.get("chroma")
  mel = kwargs.get("mel")
  contrast = kwargs.get("contrast")
  tonnetz = kwargs.get("tonnetz")

  with soundfile.SoundFile(file_name) as sound_file:
    X = sound_file.read(dtype="float32")
    sample_rate = sound_file.samplerate

    if chroma or contrast:
      stft = np.abs(librosa.stft(X))

    result = np.array([])

    if mfcc:
      mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=40).T, axis=0)
      result = np.hstack((result, mfccs))

    if chroma:
      chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T,axis=0)
      result = np.hstack((result, chroma))

    if mel:
      mel = np.mean(librosa.feature.melspectrogram(X, sr=sample_rate).T,axis=0)
      result = np.hstack((result, mel))

    if contrast:
      contrast = np.mean(librosa.feature.spectral_contrast(S=stft, sr=sample_rate).T,axis=0)
      result = np.hstack((result, contrast))

    if tonnetz:
      tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(X), sr=sample_rate).T,axis=0)
      result = np.hstack((result, tonnetz))

  return result

# Load data for sklearn
def load_data(filenames):
  X, y = [], []
  for file in filenames:
    # get the command label
    label = file.decode('UTF-8').split("/")[6]

    # Get the waveform
    waveform = extract_feature(file, mfcc=True, chroma=True, mel=True)

    # add to data
    X.append(waveform)
    y.append(label)

  return X, y

###
# Main Pipeline
###
def main() -> co.Serial:
  path = "/conducto/data/pipeline"
  root = co.Serial(image=get_image())

  # Get data from keras for testing and training
  root["Get Data"] = co.Exec(get_data, "/conducto/data/user/raw")

  root["Split"] = co.Exec(
      split_data,
      input_path="/conducto/data/user/raw/mini_speech_commands",
      train_path=f"{path}/train",
      test_path=f"{path}/test",
      validate_path=f"{path}/validate",
      commands_path=f"{path}/commands"
  )

  root["Models"] = co.Parallel()

  for tool in ["tensorflow", "pytorch", "sklearn"]:
    model_node = co.Serial()

    root["Models"][tool] = model_node

    model_node[f"Build and train {tool} model"] = co.Exec(
      fit_model, tool=tool, train_path=f"{path}/train", validate_path=f"{path}/validate", model_path=f"{path}/model/{tool}", commands_path=f"{path}/commands")

    model_node[f"Test {tool} model"] = co.Exec(
      test_model, tool=tool, test_path=f"{path}/test", model_path=f"{path}/model/{tool}", commands_path=f"{path}/commands")

  root["Summary"] = co.Exec(summarize_model)

  return root

def get_data(path):
  import tensorflow as tf
  
  if os.path.exists(path):
    print("Data already downloaded")
  else:
    # Get the files from external source and put them in an accessible directory
    print("Downloading")
    downloaded_path = tf.keras.utils.get_file(
        "mini_speech_commands.zip",
        origin="http://storage.googleapis.com/download.tensorflow.org/data/mini_speech_commands.zip",
        extract=True,
        cache_subdir=path
    )
    print("data in:", downloaded_path)

def split_data(input_path, train_path, test_path, validate_path, commands_path):
  import tensorflow as tf
  import numpy as np

  # Get a list of all the files in the directory
  filenames = tf.io.gfile.glob(input_path + '/*/*')

  # Get all of the commands for the audio files
  commands = np.array(tf.io.gfile.listdir(input_path))
  commands = commands[commands != 'README.md']
  
  # Shuffle the file names so that random bunches can be used as the training, testing, and validation sets
  filenames = tf.random.shuffle(filenames)

  # Create the list of files for training data
  train_files = filenames[:6400]
  # Create the list of files for validation data
  validation_files = filenames[6400: 6400 + 800]
  # Create the list of files for test data
  test_files = filenames[-800:]

  import pickle

  with open(train_path, "wb") as f:
    pickle.dump(train_files, f)

  print("split training data")

  with open(test_path, "wb") as f:
    pickle.dump(test_files, f)

  print("split test data")

  with open(validate_path, "wb") as f:
    pickle.dump(validation_files, f)

  print("split validation data")

  with open(commands_path, "wb") as f:
    pickle.dump(commands, f)

  print("split commands data")

def fit_model(tool, train_path, validate_path, model_path, commands_path):
  print(f"current tool: {tool}")
  if tool == "tensorflow":
    fit_model_tensorflow(train_path, validate_path, model_path, commands_path)
  elif tool == "pytorch":
    fit_model_pytorch(train_path, validate_path, model_path, commands_path)
  elif tool == "sklearn":
    fit_model_sklearn(train_path, validate_path, model_path, commands_path)
  else:
    print(f"current tool: {tool}")

def fit_model_tensorflow(train_path, validate_path, model_path, commands_path):
  import pickle
  import numpy as np
  import tensorflow as tf

  from tensorflow.keras.layers.experimental import preprocessing
  from tensorflow.keras import layers
  from tensorflow.keras import models

  with open(commands_path, "rb") as f:
    commands = pickle.load(f)

  with open(train_path, "rb") as f:
    train_files = pickle.load(f)

  with open(validate_path, "rb") as f:
    validation_files = pickle.load(f)

  print(train_files[0])
    
  # Set seed for experiment reproducibility
  seed = 55
  tf.random.set_seed(seed)
  np.random.seed(seed)

  autotune = tf.data.AUTOTUNE

  # Get the converted audio files for training the model
  files_ds = tf.data.Dataset.from_tensor_slices(train_files)
  waveform_ds = files_ds.map(
      get_waveform_and_label, num_parallel_calls=autotune)

  spectrogram_ds = waveform_ds.map(lambda waveform, label:
      get_spectrogram_and_label_id(waveform, label, commands), num_parallel_calls=autotune)

  # Preprocess the training, test, and validation datasets
  train_ds = preprocess_dataset(train_files, autotune, commands)
  validation_ds = preprocess_dataset(validation_files, autotune, commands)

  # Batch datasets for training and validation
  batch_size = 64
  train_ds = train_ds.batch(batch_size)
  validation_ds = validation_ds.batch(batch_size)

  # Reduce latency while training
  train_ds = train_ds.cache().prefetch(autotune)
  validation_ds = validation_ds.cache().prefetch(autotune)

  # Build model
  for spectrogram, _ in spectrogram_ds.take(1):
    input_shape = spectrogram.shape

  num_labels = len(commands)

  norm_layer = preprocessing.Normalization()
  norm_layer.adapt(spectrogram_ds.map(lambda x, _: x))

  model = models.Sequential([
    layers.Input(shape=input_shape),
    preprocessing.Resizing(32, 32),
    norm_layer,
    layers.Conv2D(32, 3, activation='relu'),
    layers.Conv2D(64, 3, activation='relu'),
    layers.MaxPooling2D(),
    layers.Dropout(0.25),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(num_labels),
  ])

  model.summary()

  # Configure built model with losses and metrics
  model.compile(
    optimizer=tf.keras.optimizers.Adam(),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(
        from_logits=True),
    metrics=['accuracy'],
  )

  # Finally train the model and return info about each epoch
  EPOCHS = 10
  model.fit(
    train_ds,
    validation_data=validation_ds,
    epochs=EPOCHS,
    callbacks=tf.keras.callbacks.EarlyStopping(verbose=1, patience=2),
  )

  print("saving model")
  
  os.makedirs(os.path.dirname(model_path), exist_ok=True)
  
  model_json = model.to_json()

  with open(model_path, "wb") as f:
    pickle.dump(model_json, f)

def fit_model_pytorch(train_path, validate_path, model_path, commands_path):
  import pickle
  import torch
  import torch.nn as nn
  import torch.nn.functional as Fnn
  import torch.optim as optim
  import torchaudio
  import torchaudio.functional as F

  with open(commands_path, "rb") as f:
    commands = pickle.load(f)

  with open(train_path, "rb") as f:
    train_files = pickle.load(f)

  with open(validate_path, "rb") as f:
    validation_files = pickle.load(f)

  print("starting to convert training and validation data to pytorch format")

  # Return an array of tuples with the waveform and sample rate
  train_data_converted = train_files.numpy().tolist()

  train_data = []
  labels = []
  for file in train_data_converted:
    train_data.append(torchaudio.load(file))
    labels.append(file.decode("utf-8").split("/")[6])

  # Returns an array of spectrograms
  spectrograms = []
  for waveform, sample_rate in train_data:
    spectrograms.append(get_spectrogram_pytorch(waveform))

  print("Made spectrograms...")

  labeled_spectrograms = []
  # Returns an array of spectrograms with labels
  for i, waveform in enumerate(spectrograms):
    labeled_spectrograms.append([waveform, labels[i]])

  print("Labelled spectrograms...")

  # Class that defines the CNN model in PyTorch
  class PyTorchNet(nn.Module):
    def __init__(self, n_input=1, n_output=35, stride=16, n_channel=32):
      super().__init__()
      self.conv1 = nn.Conv1d(n_input, n_channel, kernel_size=80, stride=stride)
      self.bn1 = nn.BatchNorm1d(n_channel)
      self.pool1 = nn.MaxPool1d(4)
      self.conv2 = nn.Conv1d(n_channel, n_channel, kernel_size=3)
      self.bn2 = nn.BatchNorm1d(n_channel)
      self.pool2 = nn.MaxPool1d(4)
      self.conv3 = nn.Conv1d(n_channel, 2 * n_channel, kernel_size=3)
      self.bn3 = nn.BatchNorm1d(2 * n_channel)
      self.pool3 = nn.MaxPool1d(4)
      self.conv4 = nn.Conv1d(2 * n_channel, 2 * n_channel, kernel_size=3)
      self.bn4 = nn.BatchNorm1d(2 * n_channel)
      self.pool4 = nn.MaxPool1d(4)
      self.fc1 = nn.Linear(2 * n_channel, n_output)

    def forward(self, x):
      x = self.conv1(x)
      x = Fnn.relu(self.bn1(x))
      x = self.pool1(x)
      x = self.conv2(x)
      x = Fnn.relu(self.bn2(x))
      x = self.pool2(x)
      x = self.conv3(x)
      x = Fnn.relu(self.bn3(x))
      x = self.pool3(x)
      x = self.conv4(x)
      x = Fnn.relu(self.bn4(x))
      x = self.pool4(x)
      x = Fnn.avg_pool1d(x, x.shape[-1])
      x = x.permute(0, 2, 1)
      x = self.fc1(x)

      return Fnn.log_softmax(x, dim=2)

  # Creates the CNN
  model = PyTorchNet()

  # Defines the loss function and optimizer for the model
  criterion = nn.CrossEntropyLoss()
  optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

  # Train the model with the training data
  model.train()
  for epoch in range(2):  # loop over the dataset multiple times
    running_loss = 0.0
    for i, data in enumerate(labeled_spectrograms, 0):
      # get the input; data is a list of [waveform, label]
      waveform, label = data

      # zero the parameter gradients
      optimizer.zero_grad()

      # forward + backward + optimize
      output = model(waveform)
      loss = criterion(output, label)
      loss.backward()
      optimizer.step()

      # print statistics
      running_loss += loss.item()
      if i % 2000 == 1999:    # print every 2000 mini-batches
        print('[%d, %5d] loss: %.3f' %
              (epoch + 1, i + 1, running_loss / 2000))
        running_loss = 0.0
  
  # Save model
  torch.save(model.state_dict(), model_path)

def fit_model_sklearn(train_path, validate_path, model_path, commands_path):
  import pickle
  from sklearn.neural_network import MLPClassifier

  with open(commands_path, "rb") as f:
    commands = pickle.load(f)

  with open(train_path, "rb") as f:
    train_files = pickle.load(f)

  print(train_files)

  formatted_train_files = train_files.numpy()

  X_train, y_train = load_data(formatted_train_files)
    
  print("got training data")

  # Best model, determined by a grid search
  model_params = {
    'alpha': 0.01,
    'batch_size': 256,
    'epsilon': 1e-08, 
    'hidden_layer_sizes': (300,), 
    'learning_rate': 'adaptive', 
    'max_iter': 500, 
  }

  print("training model")

  # Initialize Multi Layer Perceptron classifier with best initial parameters
  model = MLPClassifier(**model_params)

  # Train the model
  model.fit(X_train, y_train)

  print("saving model")

  with open(model_path, "wb") as f:
    pickle.dump(model, f)

def test_model(tool, test_path, model_path, commands_path):
  print(f"current tool: {tool}")
  if tool == "tensorflow":
    test_model_tensorflow(model_path, test_path, commands_path)
  elif tool == "pytorch":
    test_model_pytorch(model_path, test_path)
  elif tool == "sklearn":
    test_model_sklearn(model_path, test_path)
  else:
    print(f"current tool: {tool}")

def test_model_tensorflow(model_path, test_path, commands_file):
  import pickle
  import numpy as np
  import tensorflow as tf

  from keras.models import model_from_json

  with open(model_path, "rb") as f:
    model_json = pickle.load(f)

  model = model_from_json(model_json)

  with open(test_path, "rb") as f:
    test_files = pickle.load(f)

  with open(commands_file, "rb") as f:
    commands = pickle.load(f)

  autotune = tf.data.AUTOTUNE
    
  test_ds = preprocess_dataset(test_files, autotune, commands)

  # Test the model
  test_audio = []
  test_labels = []

  for audio, label in test_ds:
      test_audio.append(audio.numpy())
      test_labels.append(label.numpy())

  test_audio = np.array(test_audio)
  test_labels = np.array(test_labels)

  # See how accurate the model is when making predictions on the test dataset
  y_pred = np.argmax(model.predict(test_audio), axis=1)
  y_true = test_labels

  test_acc = sum(y_pred == y_true) / len(y_true)

  print(f'Test set accuracy: {test_acc:.0%}')

def test_model_pytorch(model_path, test_path):
  import torch
  import torchaudio

  # Load saved model
  model = PyTorchNet()
  model.load_state_dict(torch.load(model_path))

  import pickle

  with open(test_path, "rb") as f:
    test_files = pickle.load(f)

  # Return an array of tuples with the waveform and sample rate
  test_data = test_files.map(torchaudio.load)

  # Returns an array of spectrograms
  test_spectrograms = test_data.map(lambda waveform, sample_rate: get_spectrogram_pytorch(waveform))

  # Test the model
  correct = 0
  total = 0
  with torch.no_grad():
    for data in test_files:
      images, labels = test_spectrograms
      outputs = model(images)
      _, predicted = torch.max(outputs.data, 1)
      total += labels.size(0)
      correct += (predicted == labels).sum().item()

  print('Accuracy of the network on the 10000 test images: %d %%' % (100 * correct / total))

def test_model_sklearn(model_path, test_path):
  import pickle
  from sklearn.metrics import accuracy_score

  # Load saved model
  with open(model_path, "rb") as f:
    model = pickle.load(f)

  with open(test_path, "rb") as f:
    test_files = pickle.load(f)

  # Return the waveforms and labels for the test data
  X_test, y_test = load_data(test_files.numpy())

  # Test the model
  y_pred = model.predict(X_test)

  # Calculate the accuracy
  accuracy = accuracy_score(y_true=y_test, y_pred=y_pred)

  print("Accuracy: {:.2f}%".format(accuracy*100))

def summarize_model():
    return "Summarized model"

###
# Pipeline Helper functions
###
def get_image():
  return co.Image(
    "ubuntu:groovy",
    copy_dir=".",
    reqs_py=["conducto", "keras", "librosa", "sklearn", "soundfile", "tensorflow", "torch", "torchaudio"],
    reqs_packages=["libsndfile1"]
  )

if __name__ == "__main__":
  co.main(default=main)
