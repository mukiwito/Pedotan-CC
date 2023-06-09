import sys
sys.path.append('./')

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from PIL import Image
import numpy as np
from keras.models import load_model
from tensorflow.keras.utils import img_to_array
from io import BytesIO
import requests 
from google.cloud import storage
from auth.app import authorize_request

app = Flask(__name__)
api = Api(app)

model1 = load_model("ai_model/model/model1.h5")
model2 = load_model("C:/Users/Dzaki Putranto/Downloads/model2.h5")

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
    img = img.resize((224, 224))

    image = img_to_array(img)
    image /= 255
    image = np.expand_dims(image, axis = 0)
    image = np.vstack([image])

    return image

def get_predicted_label_disease(pred_probabilities):
    # Turns an array of predictions probabilities into a label

    return disease_class[pred_probabilities.argmax()]
    
def upload(photo):
    client = storage.Client.from_service_account_json('./auth/credentials/pedotanimage_credentials.json')
    bucket = client.get_bucket('pedotanimage')
    blob = bucket.blob(photo.filename)

    blob.upload_from_string(photo.read(), content_type=photo.content_type)
    blob.make_public()

    photo_link = blob.public_url
    print('Uploaded image link:', photo_link)

    return photo_link

class PredictPlantDisease(Resource):
    #@authorize_request
    def post(self):
        email = request.json.get('email')

        if 'image' not in request.files:
            return jsonify({'error': 'No image found in the request'}), 401
        
        image = request.files['image']
        url = upload(image)

        image = preprocess_image(url)
        pred = model2.predict(image)
        max_pred = max(pred[0])
        if max_pred > 0.5:
            pred_class = get_predicted_label_disease(pred[0])
        else :
            pred_class = "sehat"
        return {'predict': pred_class}, 200

komoditas_class = ['apple', 
                   'coffee', 
                   'grapes', 
                   'corn', 
                   'rice']

def get_predicted_label_commodity(pred_probabilities):
    """
    Turns an array of predictions probabilities into a label
    """
    return komoditas_class[pred_probabilities.argmax()]


class PredictCropCommodity(Resource):
    def post(self):
        json_data = request.json
        
        model_data = [
            [json_data['n'], 
             json_data['p'], 
             json_data['k'], 
             json_data['temperature'], 
             json_data['humidity'], 
             json_data['ph'], 
             json_data['rainfall']]
        ]
        
        pred = model1.predict(model_data)
        pred_class = get_predicted_label_commodity(pred[0])
        return {'predict': pred_class}, 200
            
api.add_resource(PredictPlantDisease, '/ai/predictdisease')
api.add_resource(PredictCropCommodity, '/ai/predictcrop')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
