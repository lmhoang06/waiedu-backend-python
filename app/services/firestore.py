"""
Firestore Service Module

This module provides CRUD (Create, Read, Update, Delete) operations for Firestore.
It serves as a wrapper around the Firestore client to simplify database interactions.
"""
from flask import current_app
import logging
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Dict, List, Any, Optional, Union, Tuple


def get_db():
    """Get the Firestore database client from the current Flask application."""
    return current_app.firestore_db


# CREATE Operations

def add_document(collection_name: str, data: Dict[str, Any], document_id: str = None, id_as_int: bool = False) -> Dict[str, Any]:
    """
    Add a new document to a collection.
    
    Args:
        collection_name: Name of the collection
        data: Document data to add
        document_id: Optional document ID (auto-generated if not provided)
    
    Returns:
        Dictionary with document data and ID
    """
    try:
        db = get_db()
        collection_ref = db.collection(collection_name)
        
        if document_id:
            doc_ref = collection_ref.document(document_id)
            doc_ref.set(data)
            if id_as_int:
                document_id = int(document_id)
            data['id'] = document_id
            return data
        else:
            doc_ref = collection_ref.add(data)
            data['id'] = doc_ref[1].id
            return data
    except Exception as e:
        logging.error(f"Error adding document: {str(e)}")
        return None


def add_batch_documents(collection_name: str, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add multiple documents in a batch operation.
    
    Args:
        collection_name: Name of the collection
        data_list: List of document data to add
    
    Returns:
        List of documents with their IDs
    """
    try:
        db = get_db()
        batch = db.batch()
        collection_ref = db.collection(collection_name)
        result = []
        
        for data in data_list:
            doc_id = data.get('id')
            if doc_id:
                doc_ref = collection_ref.document(doc_id)
                batch.set(doc_ref, data)
                result.append(data)
            else:
                doc_ref = collection_ref.document()
                batch.set(doc_ref, data)
                data_copy = data.copy()
                data_copy['id'] = doc_ref.id
                result.append(data_copy)
                
        batch.commit()
        return result
    except Exception as e:
        logging.error(f"Error adding batch documents: {str(e)}")
        return []


# READ Operations

def get_document(collection_name: str, document_id: str, id_as_int: bool = False) -> Dict[str, Any]:
    """
    Retrieve a document by its ID.
    
    Args:
        collection_name: Name of the collection
        document_id: ID of the document to retrieve
    
    Returns:
        Document data as dictionary or None if not found
    """
    try:
        db = get_db()
        doc_ref = db.collection(collection_name).document(document_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()

            try:
                if id_as_int:
                    document_id = int(document_id)
            except (ValueError, TypeError):
                logging.error(f"Error converting document ID to int: {str(e)}")
            
            data['id'] = document_id
            return data
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting document: {str(e)}")
        return None


def get_all_documents(collection_name: str, limit: int = None, order_by: str = None, 
                      direction: str = 'ASCENDING') -> List[Dict[str, Any]]:
    """
    Retrieve all documents from a collection with optional pagination and sorting.
    
    Args:
        collection_name: Name of the collection
        limit: Maximum number of documents to return
        order_by: Field to sort by
        direction: Sort direction ('ASCENDING' or 'DESCENDING')
    
    Returns:
        List of documents
    """
    try:
        db = get_db()
        collection_ref = db.collection(collection_name)
        
        # Apply ordering if specified
        if order_by:
            if direction.upper() == 'DESCENDING':
                collection_ref = collection_ref.order_by(order_by, direction=db.Query.DESCENDING)
            else:
                collection_ref = collection_ref.order_by(order_by)
        
        # Apply limit if specified
        if limit:
            collection_ref = collection_ref.limit(limit)
            
        docs = collection_ref.stream()
        result = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            result.append(data)
            
        return result
    except Exception as e:
        logging.error(f"Error getting all documents: {str(e)}")
        return []


def query_documents(collection_name: str, filters: List[Tuple[str, str, Any]], 
                   limit: int = None, order_by: str = None, 
                   direction: str = 'ASCENDING') -> List[Dict[str, Any]]:
    """
    Query documents with filters.
    
    Args:
        collection_name: Name of the collection
        filters: List of tuples (field, operator, value)
                 Operators: ==, >, <, >=, <=, !=, array_contains, in
        limit: Maximum number of documents to return
        order_by: Field to sort by
        direction: Sort direction ('ASCENDING' or 'DESCENDING')
    
    Returns:
        List of matching documents
    """
    try:
        db = get_db()
        collection_ref = db.collection(collection_name)
        
        # Apply filters
        for field, op, value in filters:
            if op == '==':
                collection_ref = collection_ref.where(field, '==', value)
            elif op == '>':
                collection_ref = collection_ref.where(field, '>', value)
            elif op == '<':
                collection_ref = collection_ref.where(field, '<', value)
            elif op == '>=':
                collection_ref = collection_ref.where(field, '>=', value)
            elif op == '<=':
                collection_ref = collection_ref.where(field, '<=', value)
            elif op == '!=':
                collection_ref = collection_ref.where(field, '!=', value)
            elif op == 'array_contains':
                collection_ref = collection_ref.where(field, 'array_contains', value)
            elif op == 'in':
                collection_ref = collection_ref.where(field, 'in', value)
            elif op == 'array_contains_any':
                collection_ref = collection_ref.where(field, 'array_contains_any', value)
        
        # Apply ordering if specified
        if order_by:
            if direction.upper() == 'DESCENDING':
                collection_ref = collection_ref.order_by(order_by, direction=db.Query.DESCENDING)
            else:
                collection_ref = collection_ref.order_by(order_by)
        
        # Apply limit if specified
        if limit:
            collection_ref = collection_ref.limit(limit)
            
        docs = collection_ref.stream()
        result = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            result.append(data)
            
        return result
    except Exception as e:
        logging.error(f"Error querying documents: {str(e)}")
        return []


# UPDATE Operations

def update_document(collection_name: str, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a document with new data.
    
    Args:
        collection_name: Name of the collection
        document_id: ID of the document to update
        data: New data to update (only specified fields will be updated)
    
    Returns:
        Updated document data
    """
    try:
        db = get_db()
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.update(data)
        
        # Get the updated document
        updated_doc = doc_ref.get()
        if updated_doc.exists:
            result = updated_doc.to_dict()
            result['id'] = document_id
            return result
        return None
    except Exception as e:
        logging.error(f"Error updating document: {str(e)}")
        return None


def replace_document(collection_name: str, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace an entire document with new data.
    
    Args:
        collection_name: Name of the collection
        document_id: ID of the document to replace
        data: New data that will completely replace the old document
    
    Returns:
        Replaced document data
    """
    try:
        db = get_db()
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.set(data)  # This replaces the entire document
        
        data['id'] = document_id
        return data
    except Exception as e:
        logging.error(f"Error replacing document: {str(e)}")
        return None


# DELETE Operations

def delete_document(collection_name: str, document_id: str) -> bool:
    """
    Delete a document from a collection.
    
    Args:
        collection_name: Name of the collection
        document_id: ID of the document to delete
    
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        db = get_db()
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.delete()
        return True
    except Exception as e:
        logging.error(f"Error deleting document: {str(e)}")
        return False


def delete_collection(collection_name: str, batch_size: int = 500) -> bool:
    """
    Delete an entire collection.
    
    Args:
        collection_name: Name of the collection to delete
        batch_size: Number of documents to delete in each batch
    
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        db = get_db()
        collection_ref = db.collection(collection_name)
        docs = collection_ref.limit(batch_size).stream()
        deleted = 0
        
        for doc in docs:
            doc.reference.delete()
            deleted += 1
            
        if deleted >= batch_size:
            return delete_collection(collection_name, batch_size)
            
        return True
    except Exception as e:
        logging.error(f"Error deleting collection: {str(e)}")
        return False


# Utility Operations

def document_exists(collection_name: str, document_id: str) -> bool:
    """
    Check if a document exists.
    
    Args:
        collection_name: Name of the collection
        document_id: ID of the document to check
    
    Returns:
        True if the document exists, False otherwise
    """
    try:
        db = get_db()
        doc_ref = db.collection(collection_name).document(document_id)
        doc = doc_ref.get()
        return doc.exists
    except Exception as e:
        logging.error(f"Error checking document existence: {str(e)}")
        return False


def collection_exists(collection_name: str) -> bool:
    """
    Check if a collection exists.
    
    Args:
        collection_name: Name of the collection to check
    
    Returns:
        True if the collection exists, False otherwise
    """
    try:
        db = get_db()
        docs = db.collection(collection_name).limit(1).stream()
        return len(list(docs)) > 0
    except Exception as e:
        logging.error(f"Error checking collection existence: {str(e)}")
        return False


def increment_field(collection_name: str, document_id: str, field: str, value: int = 1) -> Dict[str, Any]:
    """
    Increment a numeric field in a document.
    
    Args:
        collection_name: Name of the collection
        document_id: ID of the document
        field: Field to increment
        value: Value to increment by
    
    Returns:
        Updated document data
    """
    try:
        db = get_db()
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.update({field: db.Increment(value)})
        
        # Get the updated document
        updated_doc = doc_ref.get()
        if updated_doc.exists:
            result = updated_doc.to_dict()
            result['id'] = document_id
            return result
        return None
    except Exception as e:
        logging.error(f"Error incrementing field: {str(e)}")
        return None


def array_operations(collection_name: str, document_id: str, 
                    array_field: str, values: List[Any], 
                    operation: str = 'append') -> Dict[str, Any]:
    """
    Perform operations on array fields (append or remove).
    
    Args:
        collection_name: Name of the collection
        document_id: ID of the document
        array_field: Name of the array field
        values: Values to append or remove
        operation: 'append' or 'remove'
    
    Returns:
        Updated document data
    """
    try:
        db = get_db()
        doc_ref = db.collection(collection_name).document(document_id)
        
        if operation.lower() == 'append':
            doc_ref.update({array_field: db.ArrayUnion(values)})
        elif operation.lower() == 'remove':
            doc_ref.update({array_field: db.ArrayRemove(values)})
        
        # Get the updated document
        updated_doc = doc_ref.get()
        if updated_doc.exists:
            result = updated_doc.to_dict()
            result['id'] = document_id
            return result
        return None
    except Exception as e:
        logging.error(f"Error performing array operation: {str(e)}")
        return None