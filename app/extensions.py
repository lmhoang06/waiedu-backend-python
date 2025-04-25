import os
import firebase_admin
from firebase_admin import credentials, firestore
import dotenv
import json
import base64
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

dotenv.load_dotenv()

# Create a SQLAlchemy instance
db = SQLAlchemy()

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

def initialize_postgresql(app):
    """
    Initialize the PostgreSQL database connection with the Flask application
    
    Args:
        app: Flask application instance
    """
    try:
        # Create database URI
        db_uri = os.environ.get('POSTGRES_DATABASE_URL')
        
        # Configure Flask application
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy with the Flask application
        db.init_app(app)
        
        # Use application context for operations that require it
        with app.app_context():
            # Create an engine and session for direct queries
            app.postgresql_engine = db.get_engine()
            Session = sessionmaker(bind=app.postgresql_engine)
            app.postgresql_session = Session()
        
        # Log successful connection
        logging.info(f"Successfully connected to PostgreSQL database.")
        
    except Exception as e:
        logging.error(f"Error initializing PostgreSQL database: {str(e)}")
        raise