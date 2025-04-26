from flask import Flask
from .extensions import initialize_firebase, initialize_postgresql
from .routes.blocks import block_bp
from .routes.auth import auth_bp
from .routes.main_auth import main_auth_bp
from .routes.main_student import main_student_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Initialize Firebase and Authentication
    initialize_firebase(app)
    
    # Initialize PostgreSQL database
    initialize_postgresql(app)
    
    # Register blueprints
    app.register_blueprint(block_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_auth_bp)
    app.register_blueprint(main_student_bp)
    
    # Configure CORS with specific origins if needed in production
    CORS(app, origins=["*"], supports_credentials=True)
    
    @app.route('/')
    def index():
        return {'message': 'Welcome to WaiEdu API!'}

    return app