from flask import Blueprint, jsonify, request
from app.services import firestore

# Create a blueprint for block routes
block_bp = Blueprint('block', __name__, url_prefix='/blocks')

# Define allowed fields that will be returned in the response
# This can be modified later as needed
ALLOWED_FIELDS = ['tenKhoi', 'loaiKhoi', 'blobUrl', 'canNang', 'id', 'donViCanNang', 'kichThuoc']

@block_bp.route('/', methods=['GET'])
def get_all_blocks():
    """
    Retrieve all blocks from Firestore collection 'objects3d'
    
    Returns:
        JSON array with all blocks, each containing only allowed fields.
        Returns an empty array if no blocks are found.
    """
    # Get all documents from the collection
    blocks_data = firestore.get_all_documents('objects3d')
    
    # If no documents were found, return an empty array
    if not blocks_data:
        return jsonify([])
    
    # Filter each block to include only allowed fields
    filtered_blocks = []
    for block in blocks_data:
        filtered_block = {field: block.get(field) for field in ALLOWED_FIELDS if field in block}
        try:
            if 'id' in filtered_block:
                filtered_block['id'] = int(filtered_block['id'])
        except (ValueError, TypeError):
            pass
        filtered_blocks.append(filtered_block)
    
    return jsonify(filtered_blocks)

@block_bp.route('/<block_id>', methods=['GET'])
def get_block(block_id):
    """
    Retrieve an block by its ID from Firestore collection 'objects3d'
    
    Args:
        block_id: The ID of the block document to retrieve
        
    Returns:
        JSON response with the allowed fields of the block
    """
    # Get the document directly by its ID
    block_data = firestore.get_document('objects3d', block_id, id_as_int=True)
    
    # Check if the document exists
    if not block_data:
        return jsonify({'error': 'block not found'}), 404
    
    # Filter the document to include only allowed fields
    filtered_data = {field: block_data.get(field) for field in ALLOWED_FIELDS if field in block_data}
    
    return jsonify(filtered_data)

@block_bp.route('/', methods=['POST'])
def add_block():
    """
    Add a new block to Firestore collection 'objects3d'
    
    The document ID will be the 'id' field from the JSON data.
    All other fields from the JSON will be saved as-is, preserving their types.
    
    Returns:
        JSON response with the created block data
    """
    # Get the JSON data from the request
    block_data = request.get_json()
    
    if not block_data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Check if the 'id' field is present in the JSON data
    if 'id' not in block_data:
        return jsonify({'error': 'ID field is required'}), 400
    
    # Ensure the 'id' field is an integer or can be converted to an integer
    try:
        block_data['id'] = int(block_data['id'])
    except (ValueError, TypeError):
        return jsonify({'error': 'ID field must be an integer or convertible to an integer'}), 400
    
    # Extract the block ID from the data and ensure it's a string
    # (Firestore document IDs must be strings)
    block_id = str(block_data['id'])
    
    # Create a copy of the data to avoid modifying the original
    firestore_data = block_data.copy()
    
    # Add the document to Firestore using the specified ID as string
    # Other numeric fields will be preserved as their original type
    result = firestore.add_document('objects3d', firestore_data, block_id, id_as_int=True)
    
    if not result:
        return jsonify({'error': 'Failed to add block'}), 500
    
    return jsonify(result), 201

@block_bp.route('/', methods=['PUT'])
def update_block():
    """
    Update an existing block in Firestore collection 'objects3d'
    
    The document to update is identified by the 'id' field in the JSON data.
    All other fields from the JSON will be updated, preserving their types.
    
    Returns:
        JSON response with the updated block data
    """
    # Get the JSON data from the request
    block_data = request.get_json()
    
    if not block_data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Check if the 'id' field is present in the JSON data
    if 'id' not in block_data:
        return jsonify({'error': 'ID field is required'}), 400
    
    # Ensure the 'id' field is an integer or can be converted to an integer
    try:
        block_id_int = int(block_data['id'])
        block_data['id'] = block_id_int
    except (ValueError, TypeError):
        return jsonify({'error': 'ID field must be an integer or convertible to an integer'}), 400
    
    # Convert the ID to string for Firestore document ID
    block_id = str(block_id_int)
    
    # Check if the document exists
    if not firestore.document_exists('objects3d', block_id):
        return jsonify({'error': 'Block not found'}), 404
    
    # Create a copy of the data to avoid modifying the original
    update_data = block_data.copy()
    
    # Update the document in Firestore
    result = firestore.update_document('objects3d', block_id, update_data)
    
    if not result:
        return jsonify({'error': 'Failed to update block'}), 500
    
    return jsonify(result)

@block_bp.route('/', methods=['DELETE'])
def delete_block():
    """
    Delete existing block(s) from Firestore collection 'objects3d'
    
    The document(s) to delete is identified by either:
    - 'id' field in the JSON data for a single document
    - 'ids' field (array) in the JSON data for multiple documents
    
    Returns:
        JSON response with success message
    """
    # Get the JSON data from the request
    block_data = request.get_json()
    
    if not block_data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Check if both 'id' and 'ids' fields are present (conflicting request)
    if 'id' in block_data and 'ids' in block_data:
        return jsonify({'error': 'Request is ambiguous. Please provide either "id" or "ids", not both'}), 400
    
    # Case 1: Single document deletion
    if 'id' in block_data:
        # Ensure the 'id' field is an integer or can be converted to an integer
        try:
            block_id_int = int(block_data['id'])
        except (ValueError, TypeError):
            return jsonify({'error': 'ID field must be an integer or convertible to an integer'}), 400
        
        # Convert the ID to string for Firestore document ID
        block_id = str(block_id_int)
        
        # Check if the document exists
        if not firestore.document_exists('objects3d', block_id):
            return jsonify({'error': 'Block not found'}), 404
        
        # Delete the document from Firestore
        success = firestore.delete_document('objects3d', block_id)
        
        if not success:
            return jsonify({'error': f'Failed to delete block with ID {block_id_int}'}), 500
        
        return jsonify({'message': f'Block with ID {block_id_int} successfully deleted'}), 200
    
    # Case 2: Multiple document deletion
    elif 'ids' in block_data:
        ids = block_data['ids']
        
        # Validate that ids is an array
        if not isinstance(ids, list):
            return jsonify({'error': 'The "ids" field must be an array'}), 400
        
        if len(ids) == 0:
            return jsonify({'error': 'The "ids" array is empty'}), 400
        
        # Track successful and failed deletions
        success_count = 0
        failed_ids = []
        not_found_ids = []
        
        # Process each ID
        for item_id in ids:
            try:
                # Convert to integer if possible
                block_id_int = int(item_id)
                block_id = str(block_id_int)
                
                # Check if document exists
                if not firestore.document_exists('objects3d', block_id):
                    not_found_ids.append(block_id_int)
                    continue
                
                # Delete the document
                success = firestore.delete_document('objects3d', block_id)
                
                if success:
                    success_count += 1
                else:
                    failed_ids.append(block_id_int)
                    
            except (ValueError, TypeError):
                failed_ids.append(item_id)
        
        # Prepare response
        response = {
            'message': f'Deleted {success_count} blocks successfully'
        }
        
        if failed_ids:
            response['failed_ids'] = failed_ids
        
        if not_found_ids:
            response['not_found_ids'] = not_found_ids
        
        # If all operations failed, return 500
        if success_count == 0 and (failed_ids or not_found_ids):
            return jsonify(response), 500
            
        return jsonify(response), 200
    
    else:
        return jsonify({'error': 'Either "id" or "ids" field is required'}), 400