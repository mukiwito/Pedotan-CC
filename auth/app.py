from flask import Flask, request
from flask_restful import Resource, Api
import firebase_admin
from firebase_admin import auth, credentials, firestore

app = Flask(__name__)
api = Api(app)

cred = credentials.Certificate('auth/credentials/firebase_credentials.json')
firebase_admin.initialize_app(cred)

class RegisterResource(Resource):
    def post(self):
        email = request.json.get('email')
        password = request.json.get('password')

        try:
            # Register User in Firebase
            user = auth.create_user(
                email=email,
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
            
            session_token = auth.create_custom_token(user.uid)
            token_data = session_token.decode('utf-8')

            session_token_doc = {
                'token': token_data
            }
            db = firestore.client()
            db.collection('session token').document(user.uid).set(session_token_doc)

            return {'token': token_data}, 200
        except auth.InvalidIdTokenError:
            return {'message': 'Invalid credentials.'}, 401
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401

class LogoutResource(Resource):
    def post(self):
        email = request.json.get('email')

        user = auth.get_user_by_email(email)
        
        try:
            # Delete the given token
            db = firestore.client()
            db.collection('session token').document(user.uid).delete()
            return {'message': 'User logged out successfully'}, 200
        except auth.InvalidSessionCookieError:
            return {'message': 'Invalid session token.'}, 401
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401
        
class InputDataUserResource(Resource):
    def post(self):
        name = request.json.get('name')
        email = request.json.get('email')
        noHandphone = request.json.get('noHandphone')
        nik = request.json.get('nik')
        photo = request.json.get('photo')
        location = request.json.get('location')

        try:

            user = auth.get_user_by_email(email)
            
            user_data = {
                'name': name,
                'email': email,
                'noHandphone': noHandphone,
                'nik': nik,
                'photo': photo,
                'location': location
            }

            db = firestore.client()
            db.collection('email').document(user.uid).set(user_data)

            return {'message': 'User Data Has Been Saved'}, 201
        except auth.InvalidEmailError:
            return {'message': 'Use A Valid Email Address'}, 401
        

api.add_resource(RegisterResource, '/auth/register')
api.add_resource(AuthTokenResource, '/auth/token')
api.add_resource(LogoutResource, '/auth/logout')
api.add_resource(InputDataUserResource, '/auth/data')

if __name__ == '__main__':
    app.run(debug=True)
