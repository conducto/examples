import os
import pathlib

import numpy as np
import tensorflow as tf

from tensorflow.keras.layers.experimental import preprocessing
from tensorflow.keras import layers
from tensorflow.keras import models
import conducto as co

# PyTorch example: https://pytorch.org/tutorials/beginner/audio_preprocessing_tutorial.html

# Convert the binary audio file to a tensor
def decode_audio(audio_binary):
  audio, _ = tf.audio.decode_wav(audio_binary)

  return tf.squeeze(audio, axis=-1)

# Get the label (yes, no, up, down, etc) for an audio file.
def get_label(file_path):
  parts = tf.strings.split(file_path, os.path.sep)

  # Note: You'll use indexing here instead of tuple unpacking to enable this to work in a TensorFlow graph.
  return parts[-2]

# Create a tuple that has the labeled audio files
def get_waveform_and_label(file_path):
  label = get_label(file_path)
  audio_binary = tf.io.read_file(file_path)
  waveform = decode_audio(audio_binary)

  return waveform, label

# Convert audio files to images with PyTorch
def get_spectrogram_pytorch(
    n_fft = 400,
    win_len = None,
    hop_len = None,
    power = 2.0,
    waveform = None
):
  import torchaudio.transforms as T

  spectrogram = T.Spectrogram(
      n_fft=n_fft,
      win_length=win_len,
      hop_length=hop_len,
      center=True,
      pad_mode="reflect",
      power=power,
  )

  return spectrogram(waveform)

# Convert audio files to images
def get_spectrogram(waveform):
  # Padding for files with less than 16000 samples
  zero_padding = tf.zeros([16000] - tf.shape(waveform), dtype=tf.float32)

  # Concatenate audio with padding so that all audio clips will be of the
  # same length
  waveform = tf.cast(waveform, tf.float32)
  equal_length = tf.concat([waveform, zero_padding], 0)
  spectrogram = tf.signal.stft(
      equal_length, frame_length=255, frame_step=128)

  spectrogram = tf.abs(spectrogram)

  return spectrogram

# Label the images created from the audio files and return a tuple
def get_spectrogram_and_label_id(audio, label, commands):
  spectrogram = get_spectrogram(audio)
  spectrogram = tf.expand_dims(spectrogram, -1)
  label_id = tf.argmax(label == commands)
  return spectrogram, label_id

# Preprocess any audio files
def preprocess_dataset(files, autotune, commands):
  # Creates the dataset
  files_ds = tf.data.Dataset.from_tensor_slices(files)

  # Matches audio files with correct labels
  output_ds = files_ds.map(get_waveform_and_label,
                            num_parallel_calls=autotune)

  # Matches audio file images to the correct labels
  output_ds = output_ds.map(lambda audio, label:
      get_spectrogram_and_label_id(audio, label, commands),  num_parallel_calls=autotune)

  return output_ds

###
# Main Pipeline
###
def main() -> co.Serial:
    path = "/conducto/data/pipeline"
    root = co.Serial(image=get_image())

    # Get data from keras for testing and training
    root["Get Data"] = co.Exec(get_data, f"{path}/raw")

    root["Split"] = co.Exec(
        split_data,
        input_path=f"{path}/raw/mini_speech_commands",
        train_path=f"{path}/train",
        test_path=f"{path}/test",
        validate_path=f"{path}/validate",
        commands_path=f"{path}/commands"
    )

    root["Model"] = co.Exec(fit_model, train_path=f"{path}/train", validate_path=f"{path}/validate", model_path=f"{path}/model", commands_path=f"{path}/commands")

    root["Test"] = co.Exec(test_model, model_path=f"{path}/model", test_path=f"{path}/test", commands_file=f"{path}/commands")

    # root["Models"] = co.Parallel()
    # for algo in ["CNN"]:
    #     model_node = co.Serial()
    #     model_node["Fit"] = co.Exec(
    #         fit_model, data=f"{path}/train", model=f"{path}/{algo}")
    #     model_node["Test"] = co.Exec(
    #         test_model, data=f"{path}/test", model=f"{path}/{algo}", result=f"{path}/result/{algo}")
    #     root["Models"][algo] = model_node

    # root["Summary"] = co.Exec(summarize_model, results=f"{path}/result")

    return root

def get_data(path):
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


def fit_model(train_path, validate_path, model_path, commands_path):
  import pickle

  with open(commands_path, "rb") as f:
    commands = pickle.load(f)

  with open(train_path, "rb") as f:
    train_files = pickle.load(f)

  with open(validate_path, "rb") as f:
    validation_files = pickle.load(f)
    
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

def fit_model_pytorch(train_path, validation_path, model_path, commands_file):
  import torch
  import torchaudio
  import torchaudio.functional as F
  import torchaudio.transforms as T
  import pickle

  with open(commands_file, "rb") as f:
    commands = pickle.load(f)

  with open(train_path, "rb") as f:
    train_files = pickle.load(f)

  with open(validation_path, "rb") as f:
    validation_files = pickle.load(f)


def test_model(model_path, test_path, commands_file):
  import pickle
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


def summarize_model():
    return "Summarize model"


###
# Pipeline Helper functions
###


def get_image():
    return co.Image(
        "python:3.8-slim",
        copy_dir=".",
        reqs_py=["conducto", "tensorflow", "keras", "torch", "torchaudio"],
    )


if __name__ == "__main__":
    co.main(default=main)
