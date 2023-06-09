from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from PIL import Image
import numpy as np
from keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
from io import BytesIO
import requests  # move requests to the end of the imports
from google.cloud import storage

app = Flask(__name__)
api = Api(app)

model = load_model('model/model2.h5')

disease_class = ["Apple__black_rot",
"Apple__healthy"
"Apple__rust",
"Apple__scab",
"Chili__healthy",
"Chili__leaf_curl",
"Chili__leaf_spot",
"Chili__whitefly",
"Chili__yellowish",
"Coffee__cercospora_leaf_spot",
"Coffee__healthy",
"Coffee__red_spider_mite",
"Coffee__rust",
"Corn__common_rust",
"Corn__gray_leaf_spot",
"Corn__healthy",
"Corn__northern_leaf_blight",
"Grape__black_measles",
"Grape__black_rot",
"Grape__healthy",
"Grape__leaf_blight_isariopsis_leaf_spot",
"Rice__brown_spot",
"Rice__healthy",
"Rice__hispa",
"Rice__leaf_blast",
"Rice__neck_blast",
"Tomato__bacterial_spot",
"Tomato__early_blight",
"Tomato__healthy",
"Tomato__late_blight",
"Tomato__leaf_mold",
"Tomato__mosaic_virus",
"Tomato__septoria_leaf_spot",
"Tomato__spider_mites",
"Tomato__target_spot",
"Tomato__yellow_leaf_curl_virus"]

def preprocess_image(url):
    res = requests.get(url).content
    img = Image.open(BytesIO(res)).convert('RGB')

    img_resized = img.resize((224, 224))

    image = img_to_array(img_resized)
    image /= 255
    image = np.expand_dims(image, axis = 0)
    image = np.vstack([image])

    return image

def get_predicted_label(pred_probabilities):
    # Turns an array of predictions probabilities into a label

    return disease_class[pred_probabilities.argmax()]
    
def upload(photo):
    client = storage.Client.from_service_account_json('auth/credentials/pedotanimage_credentials.json')
    bucket = client.get_bucket('pedotanimage')
    blob = bucket.blob(photo.filename)

    blob.upload_from_string(photo.read(), content_type=photo.content_type)
    blob.make_public()

    photo_link = blob.public_urlQ
    print('Uploaded image link:', photo_link)

    return photo_link

class PredictPlantDisease(Resource):
    def predict():
        photo = request.files.get('photo')
        url = upload(photo)

        if 'url' not in request.json:
            return jsonify({'error': 'No image URL in the request'}), 400
        url = request.json['url']
        if url == '':
            return jsonify({'error': 'No image URL provided'}), 400
        else:
            url = request.json('url')
            image = preprocess_image("ai_model/content/tomat.jpg")
            pred = model.predict(image)
            max_pred = max(pred[0])
            if max_pred > 0.5:
                pred_class = get_predicted_label(pred[0])
            else :
                pred_class = "sehat"
            return {'predict': pred_class}, 200
            
api.add_resource(PredictPlantDisease, '/ai/predictdisease')