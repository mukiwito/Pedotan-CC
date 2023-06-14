from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from google.cloud import storage
import firebase_admin
from firebase_admin import auth, credentials, firestore
from app import authorize_request

app = Flask(__name__)
api = Api(app)

class FarmDataResource(Resource):
    def post(self):
        # Get request data
        email = request.json.get('email')
        farm_name = request.json.get('farm name')
        commodity = request.json.get('commodity')
        location = request.json.get('location')   
        area = request.json.get('area')
        status = "baik"

        db = firestore.client()
        try:
            # Get the user by email and create user document if not exist
            user = auth.get_user_by_email(email)
            user_doc_ref = db.collection('user farm').document(user.uid)
            user_doc_ref.set({'email': email})

            # Create farm document within the user's subcollection
            farms_collection_ref = user_doc_ref.collection('farms')
            farm_doc_ref = farms_collection_ref.document()
            farm_doc_ref.set({
                'farm name': farm_name,
                'commodity': commodity,
                'location': location,
                'area': area,
                'status': status
            })

            return {'message': 'Farm Data Has Been Saved', 'farm_id': farm_doc_ref.id}, 201
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401
    
    def get(self):
        # Get query parameters
        email = request.args.get('email')
        farm_id = request.args.get('farm_id')

        # Get the reference to the farm document
        try:
            user = auth.get_user_by_email(email)
            db = firestore.client()
            farm_ref = db.collection("user farm").document(user.uid).collection("farms").document(farm_id)

            # Retrieve the farm document
            farm_doc = farm_ref.get()

            if farm_doc.exists:
                farm_data = farm_doc.to_dict()
                return farm_data, 200
            else:
                return {'message': 'Farm document does not exist.'}, 404
        except auth.EmailNotFoundError:
            return {'message': 'Email not found.'}, 401


api.add_resource(FarmDataResource, '/auth/data-kebun')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
