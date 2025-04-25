from flask import Blueprint, jsonify, request

# Create a blueprint for main routes
main_bp = Blueprint('main', __name__, url_prefix='/main')

@main_bp.route('/', methods=['GET'])
def index():
    """
    Root endpoint for the main blueprint
    
    Returns:
        JSON response indicating the main service is available
    """
    return jsonify({
        'message': 'Main service is running',
        'status': 'active'
    })

# Example of a future route that could be added
# @main_bp.route('/feature1', methods=['GET'])
# def feature1():
#     return jsonify({'feature': 'Feature 1 data'})

# Example of another future route with parameters
# @main_bp.route('/items/<item_id>', methods=['GET'])
# def get_item(item_id):
#     return jsonify({'item_id': item_id, 'name': f'Item {item_id}'})