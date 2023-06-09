from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud import storage
import jwt

app = Flask(__name__)
api = Api(app)

cred = credentials.Certificate('credentials/firebase_credentials.json')
firebase_admin.initialize_app(cred)

jwt_secret = 'PEDOTAN'

class RegisterResource(Resource):
    def post(self):
        email = request.json.get('email')
        username = request.json.get('username')
        password = request.json.get('password')

        try:
            # Register User in Firebase
            user = auth.create_user(
                email=email,
                display_name=username,
                password=password
            )
            return {'message': 'User Created Successfully'}, 201
        except auth.EmailAlreadyExistsError:
            return {'message': 'Email Already Exists'}, 409

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
    client = storage.Client.from_service_account_json('credentials/pedotanimage_credentials.json')
    bucket = client.get_bucket('pedotanimage')
    blob = bucket.blob(photo.filename)

    blob.upload_from_string(photo.read(), content_type=photo.content_type)
    blob.make_public()

    photo_link = blob.public_url
    print('Uploaded image link:', photo_link)

    return photo_link

class InputDataUserResource(Resource):
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
                'email': email,
                'noHandphone': noHandphone,
                'nik': nik,
                'photo': photo_link,
                'location': location
            }

            # Upload data to firebase
            db = firestore.client()
            db.collection('user data').document(user.uid).set(user_data)

            return {'message': 'User Data Has Been Saved'}, 201
        except auth.InvalidEmailError:
            return {'message': 'Use A Valid Email Address'}, 401
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401

class GetUserData(Resource):
    @authorize_request
    def get(self):
        email = request.json.get('email')

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

api.add_resource(RegisterResource, '/auth/register')
api.add_resource(AuthTokenResource, '/auth/login')
api.add_resource(InputDataUserResource, '/auth/inputdata')
api.add_resource(GetUserData, '/auth/getdata')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
