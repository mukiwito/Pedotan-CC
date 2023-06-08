from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud import storage

app = Flask(__name__)
api = Api(app)

cred = credentials.Certificate('credentials/firebase_credentials.json')
firebase_admin.initialize_app(cred)

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

class AuthTokenResource(Resource):
    # GET CUSTOM SESSION TOKEN per user
    def post(self):
        email = request.json.get('email')

        try:
            # Authenticate User
            user = auth.get_user_by_email(email)
            
            # Create token
            session_token = auth.create_custom_token(user.uid)
            token = session_token.decode('utf-8')

            # Create data
            session_token_doc = {
                'uid': user.uid,
                'token': token
            }

            # Upload data to firestore
            db = firestore.client()
            db.collection('session token').document(user.uid).set(session_token_doc)

            return {'token': token}, 200
        except auth.InvalidIdTokenError:
            return {'message': 'Invalid credentials.'}, 401
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401

class LogoutResource(Resource):
    def post(self):
        email = request.json.get('email')
        
        try:
            user = auth.get_user_by_email(email)

            db = firestore.client()
            db.collection('session token').document(user.uid).delete()
            return {'message': 'User logged out successfully'}, 200
        except auth.InvalidSessionCookieError:
            return {'message': 'Invalid session token.'}, 401
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401

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

class GetUserData(Resource):
    def get(self):
        email = request.json.get('token')

        try: 

            user = auth.get_user_by_email(email)

            db = firestore.client()
            session_ref = db.collection('session token').document(user.id)
            session_data = session_ref.get()

            if not session_data.exists:
                return 'Invalid session token', 401

            user_data = db.collection('user data').document(user.uid).get()

            if user_data.exists:
                return user_data.to_dict(), 200
            else:
                return 'User data not found', 404
        except auth.UserNotFoundError:
            return 'User not found', 404            

class ProcessImage(Resource):
    def post(self):
        email = request.json.get('email')
        session_token = request.json.get('token')
        image_file = request.files['image']
        
        try:
            # get user data
            user = auth.get_user_by_email(email)

            db = firestore.client()
            user_session = db.collection('session token').document(user.uid).get()
            token_data = user_session.to_dict()['token']

            if not user_session.exists and session_token == token_data:
                return 'Invalid session token', 401

            ai_endpoint = ''
            response = request.post
        except:
            pass
            
        

api.add_resource(RegisterResource, '/auth/register')
api.add_resource(AuthTokenResource, '/auth/login')
api.add_resource(LogoutResource, '/auth/logout')
api.add_resource(InputDataUserResource, '/auth/inputdata')
api.add_resource(GetUserData, '/auth/getdata')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
