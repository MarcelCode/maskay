import pathlib
import gdown

import numpy as np

from maskay.tensorflow import Module
from maskay.utils import get_models_path


class KappaModelUNetL1C(Module):
    def __init__(self):
        super().__init__()
        self.model = model_setup()

    def forward(self, x):
        return self.model(x)

    def inProcessing(self, tensor: np.ndarray):
        # If all the pixels are zero skip the run and outProcessing.
        if np.sum(tensor) == 0:
            shp = tensor.shape
            tensor = np.zeros(
                (shp[0], 6, shp[1], shp[2])
            ) # 6 is the number of the output classes
            return [tensor]
        
        factor = np.array(
            [0.21, 0.326, 0.264, 0.298, 0.245, 0.258, 0.266] +
            [0.364, 0.259, 0.165, 0.055, 0.203, 0.208]
        )
        return tensor / 65_635 / factor[:, None, None]

    def outProcessing(self, tensor: np.ndarray):
        return (tensor * 10000).astype(np.int16)

def model_setup():
    
    CLASSES_KAPPAZETA = [
        "UNDEFINED",
        "CLEAR",
        "CLOUD_SHADOW",
        "SEMI_TRANSPARENT_CLOUD",
        "CLOUD",
        "MISSING",
    ]
    
    # Check if packages are installed
    is_external_package_installed = []

    try:
        import tensorflow as tf
    except ImportError:
        is_external_package_installed.append("tensorflow")

    class KappaModelUNet:
        def __init__(self, version: str = "L1C"):
            if version == "L1C":
                self.features = list(range(0, 13))            
            if version == "L2A":
                self.features = list(range(0, 14))            
            self.classes = CLASSES_KAPPAZETA        

        def construct(self, width=None, height=None):
            """
            Construct the model.
            """
            # For symmetrical neighbourhood, width and height must be odd numbers.
            input_shape = (width, height, len(self.features))

            with tf.name_scope("Model"):
                inputs = tf.keras.layers.Input(input_shape, name="input")

                conv1 = tf.keras.layers.Conv2D(
                    64, 3, activation="relu", padding="same", kernel_initializer="he_normal"
                )(inputs)
                conv1 = tf.keras.layers.Conv2D(
                    64, 3, activation="relu", padding="same", kernel_initializer="he_normal"
                )(conv1)
                pool1 = tf.keras.layers.MaxPool2D(pool_size=(2, 2))(conv1)

                conv2 = tf.keras.layers.Conv2D(
                    128,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(pool1)
                conv2 = tf.keras.layers.Conv2D(
                    128,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(conv2)
                pool2 = tf.keras.layers.MaxPool2D(pool_size=(2, 2))(conv2)

                conv3 = tf.keras.layers.Conv2D(
                    256,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(pool2)
                conv3 = tf.keras.layers.Conv2D(
                    256,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(conv3)
                pool3 = tf.keras.layers.MaxPool2D(pool_size=(2, 2))(conv3)

                conv4 = tf.keras.layers.Conv2D(
                    512,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(pool3)
                conv4 = tf.keras.layers.Conv2D(
                    512,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(conv4)
                drop4 = tf.keras.layers.Dropout(0.5)(conv4)
                pool4 = tf.keras.layers.MaxPool2D(pool_size=(2, 2))(drop4)

                conv5 = tf.keras.layers.Conv2D(
                    1024,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(pool4)
                conv5 = tf.keras.layers.Conv2D(
                    1024,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(conv5)
                drop5 = tf.keras.layers.Dropout(0.5)(conv5)

                up6 = tf.keras.layers.Conv2D(
                    512,
                    2,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(tf.keras.layers.UpSampling2D(size=(2, 2))(drop5))
                merge6 = tf.keras.layers.concatenate([drop4, up6], axis=3)
                conv6 = tf.keras.layers.Conv2D(
                    512,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(merge6)
                conv6 = tf.keras.layers.Conv2D(
                    512,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(conv6)

                up7 = tf.keras.layers.Conv2D(
                    256,
                    2,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(tf.keras.layers.UpSampling2D(size=(2, 2))(conv6))
                merge7 = tf.keras.layers.concatenate([conv3, up7], axis=3)
                conv7 = tf.keras.layers.Conv2D(
                    256,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(merge7)
                conv7 = tf.keras.layers.Conv2D(
                    256,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(conv7)

                up8 = tf.keras.layers.Conv2D(
                    128,
                    2,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(tf.keras.layers.UpSampling2D(size=(2, 2))(conv7))
                merge8 = tf.keras.layers.concatenate([conv2, up8], axis=3)
                conv8 = tf.keras.layers.Conv2D(
                    128,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(merge8)
                conv8 = tf.keras.layers.Conv2D(
                    128,
                    3,
                    activation="relu",
                    padding="same",
                    kernel_initializer="he_normal",
                )(conv8)

                up9 = tf.keras.layers.Conv2D(
                    64, 2, activation="relu", padding="same", kernel_initializer="he_normal"
                )(tf.keras.layers.UpSampling2D(size=(2, 2))(conv8))
                merge9 = tf.keras.layers.concatenate([conv1, up9], axis=3)

                conv9 = tf.keras.layers.Conv2D(
                    64, 3, activation="relu", padding="same", kernel_initializer="he_normal"
                )(merge9)
                conv9 = tf.keras.layers.Conv2D(
                    64, 3, activation="relu", padding="same", kernel_initializer="he_normal"
                )(conv9)
                conv9 = tf.keras.layers.Conv2D(
                    2, 3, activation="relu", padding="same", kernel_initializer="he_normal"
                )(conv9)
                conv10 = tf.keras.layers.Conv2D(
                    len(self.classes), (1, 1), activation="softmax"
                )(conv9)

                self.model = tf.keras.Model(inputs, conv10)

                return self.model
            
    filename = pathlib.Path(get_models_path()) / "kappamaskl1c.hdf5"
    
    # Download the model if it doesn't exist
    if not filename.is_file():
        # download file using gdown
        url = "https://drive.google.com/uc?id=1o9LeVsXCeD2jmS-G8s7ZISfciaP9v-DU"
        gdown.download(url, filename.as_posix())
    # Load the model
    model = KappaModelUNet("L1C").construct()
    model.load_weights(filename.as_posix())
    
    return model
