from flask import Flask, request
from flask_restful import Resource, Api
import firebase_admin
from firebase_admin import auth, credentials

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
                email = email,
                password = password
            )
            return {'message' : 'User Created Successfully'}, 201
        except auth.EmailAlreadyExistsError:
            return {'message' : 'Email Already Exists'}, 409

class AuthTokenResource(Resource):
    # GET CUSTOM SESSION TOKEN per user
    def post(self):
        email = request.json.get('email')

        try:
            # Authenticate User
            user = auth.get_user_by_email(email)
            # Session Token
            session_claims = {
                'uid' : user.uid,
                'custom_claim' : 'AIzaSyBzQInEHejnK3ogHBLSGi9bC_SKiEfdr4g' # Web API Key
            }
            session_token = auth.create_custom_token(user.uid, session_claims)

            return {'token' : session_token.decode('utf-8')}, 200    
        except auth.InvalidIdTokenError:
            return {'message': 'Invalid credentials.'}, 401
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401

api.add_resource(RegisterResource, '/auth/register')
api.add_resource(AuthTokenResource, '/auth/token')

if __name__ == '__main__':
    app.run(debug=True)