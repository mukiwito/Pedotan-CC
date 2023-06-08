import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import load_img, img_to_array

new_model = tf.keras.models.load_model(filepath="content/my_model_final_v2.h5")

uploaded = "content/ikan.jpg"

# predicting image
path = uploaded
img = load_img(path, target_size=(150, 150))

x = img_to_array(img)
x /= 255
x = np.expand_dims(x, axis=0)
images = np.vstack([x])

classes = new_model.predict(images, batch_size=5)

print(classes)
