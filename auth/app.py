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
            # Session Token
            session_claims = {
                'uid': user.uid,
                'custom_claim': 'your_web_api_key'  # Replace with your Web API Key
            }
            session_token = auth.create_custom_token(user.uid, session_claims)

            session_token_doc = {
                'uid': user.uid,
                'token': session_token.decode('utf-8')
            }
            db = firestore.client()
            db.collection('session token').document('session_token').set(session_token_doc)

            return {'token': session_token.decode('utf-8')}, 200
        except auth.InvalidIdTokenError:
            return {'message': 'Invalid credentials.'}, 401
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401

class LogoutResource(Resource):
    def post(self):
        token = request.json.get('token')
        email = request.json.get('email')

        user = auth.get_user_by_email(email)
        

        try:
            # Revoke the given token
            auth.revoke_refresh_tokens(user.uid)
            return {'message': 'User logged out successfully'}, 200
        except auth.InvalidSessionCookieError:
            return {'message': 'Invalid session token.'}, 401

api.add_resource(RegisterResource, '/auth/register')
api.add_resource(AuthTokenResource, '/auth/token')
api.add_resource(LogoutResource, '/auth/logout')

if __name__ == '__main__':
    app.run(debug=True)
