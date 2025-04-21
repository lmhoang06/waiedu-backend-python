import os
import firebase_admin
from firebase_admin import credentials, firestore
import dotenv
import json
import base64

dotenv.load_dotenv()

def initialize_firebase(app):
    cred = credentials.Certificate(
        json.loads(
            base64.b64decode(
                os.getenv("FIREBASE_CRED")
            ).decode("utf-8")
        )
    )
    firebase_admin.initialize_app(cred)
    app.firestore_db = firestore.client()