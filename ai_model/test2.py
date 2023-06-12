from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from PIL import Image
import numpy as np
from keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
from io import BytesIO
import requests  # move requests to the end of the imports
from google.cloud import storage


model = load_model('ai_model/model/model3.h5')

disease_class = ['Nitrogen(N)', 'Phosphorus(P)', 'Potassium(K)']

def preprocess_image(url):
    img = Image.open(url).convert('RGB')

    # Resize the image
    img_resized = img.resize((224, 224))

    # Convert the image to numpy array and normalize the pixel values
    image = img_to_array(img_resized)
    image /= 255
    image = np.expand_dims(image, axis = 0)
    image = np.vstack([image])

    return image

def get_predicted_label(pred_probabilities):
    # Turns an array of predictions probabilities into a label

    return disease_class[pred_probabilities.argmax()]

def predict():
    # if 'url' not in request.json
    image = preprocess_image("ai_model/content/0b37761a-de32-47ee-a3a4-e138b97ef542___JR_FrgE.S 2908.jpeg")
    pred = model.predict(image)
    max_pred = max(pred[0])
    if max_pred > 0.8:
        pred_class = get_predicted_label(pred[0])
    else :
        pred_class = "sehat"

    print(max_pred)
    print(pred_class)
    return {'predict': pred_class}, 200

predict()