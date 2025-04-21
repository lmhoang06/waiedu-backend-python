import os
import firebase_admin
from firebase_admin import credentials, firestore
import dotenv

dotenv.load_dotenv()

def initialize_firebase(app):
    cred_path = os.path.join(os.path.dirname(__file__), os.getenv('FIREBASE_CRED_PATH'))
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    app.firestore_db = firestore.client()