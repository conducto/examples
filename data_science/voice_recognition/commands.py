import typing

def get_data(path):
    if os.path.exists(path):
        print("Data already downloaded")
    else:
        # Get the files from external source and put them in an accessible directory
        print("Downloading")
        tf.keras.utils.get_file(
            "mini_speech_commands.zip",
            origin="http://storage.googleapis.com/download.tensorflow.org/data/mini_speech_commands.zip",
            extract=True
        )
        print("Moving it to", path)
        os.rename("data/mini_speech_commands", path)


def split_data(input, train, test, validate, split:typing.List[float]):
    # Create the list of files for training data
    train_files = filenames[:6400]
    # Create the list of files for validation data
    validation_files = filenames[6400: 6400 + 800]
    # Create the list of files for test data
    test_files = filenames[-800:]


def run_whole_thing(out_dir):
    os.makedirs(out_dir, exist_ok=True)

    # Set seed for experiment reproducibility
    seed = 55
    tf.random.set_seed(seed)
    np.random.seed(seed)

    data_dir = pathlib.Path("data/mini_speech_commands")

    if not data_dir.exists():
        # Get the files from external source and put them in an accessible directory
        tf.keras.utils.get_file(
            'mini_speech_commands.zip',
            origin="http://storage.googleapis.com/download.tensorflow.org/data/mini_speech_commands.zip",
            extract=True)

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
    def get_spectrogram_and_label_id(audio, label):
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
        output_ds = output_ds.map(
            get_spectrogram_and_label_id, num_parallel_calls=autotune)

        return output_ds

    # Get all of the commands for the audio files
    commands = np.array(tf.io.gfile.listdir(str(data_dir)))
    commands = commands[commands != 'README.md']

    # Get a list of all the files in the directory
    filenames = tf.io.gfile.glob(str(data_dir) + '/*/*')

    # Shuffle the file names so that random bunches can be used as the training, testing, and validation sets
    filenames = tf.random.shuffle(filenames)

    # Create the list of files for training data
    train_files = filenames[:6400]
    # Create the list of files for validation data
    validation_files = filenames[6400: 6400 + 800]
    # Create the list of files for test data
    test_files = filenames[-800:]

    autotune = tf.data.AUTOTUNE

    # Get the converted audio files for training the model
    files_ds = tf.data.Dataset.from_tensor_slices(train_files)
    waveform_ds = files_ds.map(
        get_waveform_and_label, num_parallel_calls=autotune)
    spectrogram_ds = waveform_ds.map(
        get_spectrogram_and_label_id, num_parallel_calls=autotune)

    # Preprocess the training, test, and validation datasets
    train_ds = preprocess_dataset(train_files, autotune, commands)
    validation_ds = preprocess_dataset(
        validation_files, autotune, commands)
    test_ds = preprocess_dataset(test_files, autotune, commands)

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