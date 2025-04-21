from flask import Flask
from .extensions import initialize_firebase
from .routes.blocks import block_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    initialize_firebase(app)
    
    # Register blueprints
    app.register_blueprint(block_bp)
    CORS(app, origins=["*"])
    
    @app.route('/')
    def index():
        return {'message': 'Welcome to WaiEdu API!'}

    return app