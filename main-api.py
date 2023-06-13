from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud import storage
import jwt
from PIL import Image
import numpy as np
from keras.models import load_model
from tensorflow.keras.utils import img_to_array
from io import BytesIO
import requests 

app = Flask(__name__)
api = Api(app)

cred = credentials.Certificate('auth/credentials/firebase_credentials.json')
firebase_admin.initialize_app(cred)

jwt_secret = 'PEDOTAN'

class RegisterResource(Resource):
    def post(self):
        email = request.json.get('email')
        name = request.json.get('name')
        password = request.json.get('password')

        try:
            # Register User in Firebase
            user = auth.create_user(
                email=email,
                display_name=name,
                password=password
            )
            db = firestore.client()
            db.collection('user data').document(user.uid).set({'email' : email, 'name': name})

            return {'message': 'User Created Successfully'}, 201
        except auth.EmailAlreadyExistsError:
            return {'message': 'Email Already Exists'}, 409

class RegisterGoogleResource(Resource):
    def post(self):
        email = request.json.get('email')
        name = request.json.get('name')
        try:
            user = auth.get_user_by_email(email)
            db = firestore.client()
            db.collection('user data').document(user.uid).set({'email' : email, 'name': name})
            return {'message': 'User Created Successfully'}, 201
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401        

def generate_session_token(user_uid):
    payload = {
        'uid': user_uid,
    }
    session_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    return session_token

class AuthTokenResource(Resource):
    def post(self):
        email = request.json.get('email')

        try:
            # Authenticate User
            user = auth.get_user_by_email(email)

            # Generate session token
            session_token = generate_session_token(user.uid)

            # Store the session token in Firestore or any other database
            db = firestore.client()
            session_token_doc = {
                'token': session_token
            }
            db.collection('session_tokens').document(user.uid).set(session_token_doc)

            return {'token': session_token}, 200
        except auth.InvalidIdTokenError:
            return {'message': 'Invalid credentials.'}, 401
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401

def authorize_request(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token or not token.startswith('Bearer '):
            return jsonify({'message': 'Missing or invalid token'}), 401

        session_token = token.split(' ')[1]

        # Verify and decode the session token
        try:
            decoded_token = jwt.decode(session_token, jwt_secret, algorithms=['HS256'])
            user_uid = decoded_token.get('uid')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return jsonify({'message': 'Invalid token'}), 401

        # Check if the session token exists in Firestore or any other database
        db = firestore.client()
        session_token_doc = db.collection('session_tokens').document(user_uid).get()
        if not session_token_doc.exists or session_token_doc.to_dict().get('token') != session_token:
            return jsonify({'message': 'Invalid token'}), 401

        # Add the user UID to the request context for further use if needed
        request.user_uid = user_uid

        return func(*args, **kwargs)

    return wrapper

def upload(photo):
    client = storage.Client.from_service_account_json('auth/credentials/pedotanimage_credentials.json')
    bucket = client.get_bucket('pedotanimage')
    blob = bucket.blob(photo.filename)

    blob.upload_from_string(photo.read(), content_type=photo.content_type)
    blob.make_public()

    photo_link = blob.public_url
    print('Uploaded image link:', photo_link)

    return photo_link


class LogoutResource(Resource):
    @authorize_request
    def post(self):
        email = request.json.get('email')

        try:
            # Get user data
            user = auth.get_user_by_email(email)    

            # Delete the given token
            db = firestore.client()
            db.collection('session_tokens').document(user.uid).delete()

            return {'message': 'Logout successful'}, 200
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401


class DataUserResource(Resource):
    @authorize_request
    def post(self):
        # Get request data
        name = request.form.get('name')
        email = request.form.get('email')
        noHandphone = request.form.get('noHandphone')
        nik = request.form.get('nik')
        photo = request.files.get('photo')
        location = request.form.get('location')

        photo_link = upload(photo)
        print(photo_link)

        try:
            user = auth.get_user_by_email(email)
            
            user_data = {
                'name': name,
                'noHandphone': noHandphone,
                'nik': nik,
                'photo': photo_link,
                'location': location
            }

            # Upload data to firebase
            db = firestore.client()
            db.collection('user data').document(user.uid).update(user_data)

            return {'message': 'User Data Has Been Saved'}, 201
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401
    
    @authorize_request
    def get(self):
        email = request.args.get('email')

        try: 
            user = auth.get_user_by_email(email)

            db = firestore.client()
            user_data = db.collection('user data').document(user.uid).get()

            if user_data.exists:
                return user_data.to_dict(), 200
            else:
                return 'User data not found', 404
        except auth.UserNotFoundError:
            return 'User not found', 404
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401   


class DataKebunResource(Resource):
    @authorize_request
    def post(self):
        # Get request data
        email = request.json.get('email')
        commodity = request.json.get('commodity')
        location = request.json.get('location')   
        area = request.json.get('area')
        status = "baik"

        try:
            user = auth.get_user_by_email(email)
            
            data_kebun = {
                'email': email,
                'commodity': commodity,
                'location': location,
                'area': area,
                'status': status
            }

            # Upload data to firebase
            db = firestore.client()
            db.collection('data kebun').document(user.uid).set(data_kebun)
        
            return {'message': 'Data Kebun Has Been Saved'}, 201
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401
    

    @authorize_request
    def get(self):
        email = request.args.get('email')

        try: 

            user = auth.get_user_by_email(email)

            db = firestore.client()
            user_data = db.collection('data kebun').document(user.uid).get()

            if user_data.exists:
                return user_data.to_dict(), 200
            else:
                return 'User data not found', 404
        except auth.UserNotFoundError:
            return 'User not found', 404
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401 
        
model1 = load_model("ai_model/model/model1.h5")
model2 = load_model("ai_model/model/model2.h5")
model3 = load_model("ai_model/model/model3.h5")

disease_class = ["Apple black rot",
"Apple healthy"
"Apple rust",
"Apple scab",
"Chili healthy",
"Chili leaf_curl",
"Chili leaf_spot",
"Chili whitefly",
"Chili yellowish",
"Coffee cercospora_leaf_spot",
"Coffee healthy",
"Coffee red spider mite",
"Coffee rust",
"Corn common rust",
"Corn gray leaf spot",
"Corn healthy",
"Corn northern leaf blight",
"Grape black measles",
"Grape black rot",
"Grape healthy",
"Grape leaf blight isariopsis leaf spot",
"Rice brown spot",
"Rice healthy",
"Rice hispa",
"Rice leaf blast",
"Rice neck blast",
"Tomato bacterial spot",
"Tomato early blight",
"Tomato healthy",
"Tomato late blight",
"Tomato leaf mold",
"Tomato mosaic virus",
"Tomato septoria leaf spot",
"Tomato spider mites",
"Tomato target spot",
"Tomato yellow leaf curl virus"]

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

class PredictPlantDisease(Resource):
    @authorize_request
    def post(self):
        email = request.form.get('email')

        if 'image' not in request.files:
            return jsonify({'error': 'No image found in the request'}), 401
        
        try:
            user = auth.get_user_by_email(email)

            image = request.files['image']
            url = upload(image)

            image = preprocess_image(url)
            pred = model2.predict(image)
            max_pred = max(pred[0])
            db = firestore.client()
            if max_pred > 0.8:
                pred_class = get_predicted_label_disease(pred[0])
                db.collection('data kebun').document(user.uid).update({'model2' : pred_class})
                
                data_kebun = db.collection('data kebun').document(user.uid).get()
                komoditas = data_kebun.get('commodity')
                
                if 'model1' not in data_kebun.to_dict():
                    db.collection('data kebun').document(user.uid).update({'status': "kurang baik"})
                else:
                    data_model1 = data_kebun.get('model1')
                    if komoditas != data_model1:
                        db.collection('data kebun').document(user.uid).update({'status': "buruk"})
                    else:
                        db.collection('data kebun').document(user.uid).update({'status': "kurang baik"})
            else :
                pred_class = "sehat"
            
            return {'predict': pred_class}, 200
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401
        

komoditas_class = ['apel', 
                   'kopi', 
                   'anggur', 
                   'jagung', 
                   'padi']

def get_predicted_label_commodity(pred_probabilities):
    """
    Turns an array of predictions probabilities into a label
    """
    return komoditas_class[pred_probabilities.argmax()]

npk_class = ['N', 'P', 'K']

def get_predicted_label_npk(pred_probabilities):
    """
    Turns an array of predictions probabilities into a label
    """
    return npk_class[pred_probabilities.argmax()]

class PredictCropCommodity(Resource):
    @authorize_request
    def post(self):
        email = request.form.get('email')
        data = request.form
        
        if 'image' in request.files:
            image = request.files['image']
            url = upload(image)
            
            # NPK data initialization
            n = 80.0
            p = 80.0
            k = 80.0

            image = preprocess_image(url)
            pred = model3.predict(image)
            max_pred = max(pred[0])

            if max_pred > 0.8:
                pred_class = get_predicted_label_npk(pred[0])
            else :
                pred_class = "sehat"

            if pred_class == "N":
                n = 20.0
            elif pred_class == "P":
                p = 20.0
            elif pred_class == "K":
                k = 20.0
            
            model_data = [
            [n, 
             p, 
             k, 
             float(data.get('temperature')), 
             float(data.get('humidity')), 
             float(data.get('ph')), 
             float(data.get('rainfall'))]
            ]
        else:
            model_data = [
                [float(data.get('n')), 
                float(data.get('p')), 
                float(data.get('k')), 
                float(data.get('temperature')), 
                float(data.get('humidity')), 
                float(data.get('ph')), 
                float(data.get('rainfall'))]
            ]

        try:
            user = auth.get_user_by_email(email)
            pred = model1.predict(model_data)
            pred_class = get_predicted_label_commodity(pred[0])
            db = firestore.client()
            db.collection('data kebun').document(user.uid).update({'model1' : pred_class})
            
            data_kebun = db.collection('data kebun').document(user.uid).get()
            komoditas = data_kebun.get('commodity')
            # if komoditas != pred_class:
            #     if 'model2' not in data_kebun.to_dict():
            #         db.collection('data kebun').document(user.uid).update({'status': "kurang baik"})
            #     else:
            #         db.collection('data kebun').document(user.uid).update({'status': "buruk"})
            if 'model2' not in data_kebun.to_dict():
                if komoditas != pred_class:
                    db.collection('data kebun').document(user.uid).update({'status': "kurang baik"})
                else:
                    db.collection('data kebun').document(user.uid).update({'status': "baik"})
            else:
                if komoditas != pred_class:
                    db.collection('data kebun').document(user.uid).update({'status': "buruk"})
                else:
                    db.collection('data kebun').document(user.uid).update({'status': "kurang baik"})
            
            return {'predict': pred_class}, 200
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401


api.add_resource(RegisterResource, '/auth/register')
api.add_resource(RegisterGoogleResource, '/auth/google')
api.add_resource(AuthTokenResource, '/auth/login')
api.add_resource(DataUserResource, '/auth/datauser')
api.add_resource(DataKebunResource, '/auth/datakebun')
api.add_resource(LogoutResource, '/auth/logout')
api.add_resource(PredictPlantDisease, '/ai/predictdisease')
api.add_resource(PredictCropCommodity, '/ai/predictcrop')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
