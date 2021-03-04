from keras import layers
from keras import models
from keras.datasets import mnist
from keras.utils import to_categorical
import conducto as co

###
# Main Pipeline
###
def main() -> co.Serial:
    root = co.Serial(image = get_image())
    
    # Get data from keras for testing and training
    root["Get Data"] = co.Exec(get_data)
    # Build the model
    # root["Build Model"] = co.Exec(define_model())
    # Train the model
    # root["Train Model"] = co.Exec(train_model())
    # Test the model
    # root["Test Model"] = co.Exec(test_model())

    return root

# Split the data into training and test sets
def get_data():
    (train_images, train_labels), (test_images, test_labels) = mnist.load_data()

    train_images = train_images.reshape((60000, 28, 28, 1))
    train_images = train_images.astype('float32') / 255

    test_images = test_images.reshape((10000, 28, 28, 1))
    test_images = test_images.astype('float32') / 255

    train_labels = to_categorical(train_labels)
    test_labels = to_categorical(test_labels)

    model = models.Sequential()

    model.add(layers.Conv2D(32, (5, 5), activation='relu', input_shape=(28, 28, 1)))
    model.add(layers.MaxPooling2D((2, 2)))

    model.add(layers.Conv2D(64, (5, 5), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))

    model.add(layers.Flatten())
    model.add(layers.Dense(10, activation='softmax'))

    model.summary()
    
    model.compile(loss='categorical_crossentropy', optimizer='sgd', metrics=['accuracy'])

    model.fit(train_images, train_labels, batch_size=100, epochs=5, verbose=1)
    
    test_loss, test_acc = model.evaluate(test_images, test_labels)

    print('Test accuracy:', test_acc)

# Define the CNN model
# def define_model():

# Use the training data to train the model
# def train_model():

# Test the model's accuracy with the test data
# def test_model():

###
# Helper functions
###
def get_image():
    return co.Image(
        "python:3.8-slim",
        copy_dir=".",
        reqs_py=["conducto", "tensorflow", "keras"],
    )

if __name__ == "__main__":
    co.main(default=main)