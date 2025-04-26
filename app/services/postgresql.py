"""
PostgreSQL Service Module

This module provides database connection and query functions using SQLAlchemy.
It serves as a wrapper around SQLAlchemy to simplify database interactions.
"""
from flask import current_app
from sqlalchemy.orm import sessionmaker
import logging
import time
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, StatementError
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from ..extensions import db


def get_db():
    """
    Get the SQLAlchemy database instance
    
    Returns:
        SQLAlchemy database instance
    """
    return db


def get_engine():
    """
    Get the SQLAlchemy engine from the current Flask application
    
    Returns:
        SQLAlchemy engine
    """
    return current_app.postgresql_engine


def get_session():
    """
    Get the SQLAlchemy session from the current Flask application
    
    Returns:
        SQLAlchemy session
    """
    return current_app.postgresql_session


def check_db_connection(max_retries=3, retry_delay=1.0):
    """
    Check if the database connection is alive and reconnect if necessary
    
    Args:
        max_retries: Maximum number of reconnection attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        True if connection is successful, raises exception otherwise
    """
    session = get_session()
    engine = get_engine()
    
    for attempt in range(max_retries):
        try:
            # Execute a simple query to check the connection
            session.execute(text("SELECT 1"))
            return True
        except (OperationalError, StatementError) as e:
            logging.warning(f"Database connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
            
            if attempt < max_retries - 1:
                logging.info(f"Attempting to reconnect in {retry_delay} seconds...")
                time.sleep(retry_delay)
                
                # Dispose the engine to close all connections in the pool
                engine.dispose()
                
                # Get a new session
                current_app.postgresql_session.close()
                Session = sessionmaker(bind=current_app.postgresql_engine)
                current_app.postgresql_session = Session()
            else:
                logging.error("Failed to reconnect to database after maximum retries")
                raise
    
    return False


def ensure_db_connection(f):
    """
    Decorator to ensure database connection is alive before executing a function
    
    Args:
        f: The function to wrap
    
    Returns:
        Wrapped function that checks database connection before execution
    """
    def wrapper(*args, **kwargs):
        check_db_connection()
        return f(*args, **kwargs)
    
    # Preserve the function name and docstring
    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    
    return wrapper


def execute_query(query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query and return the results as a list of dictionaries
    
    Args:
        query: SQL query string
        params: Parameters to bind to the query
        
    Returns:
        List of dictionaries containing query results
    """
    try:
        # Ensure connection is alive
        check_db_connection()
        
        session = get_session()
        result = session.execute(text(query), params or {})
        
        # Convert result to list of dictionaries
        column_names = result.keys()
        rows = [dict(zip(column_names, row)) for row in result.fetchall()]
        
        session.commit()
        return rows
    except Exception as e:
        session.rollback()
        logging.error(f"Error executing query: {str(e)}")
        raise


def execute_write_query(query: str, params: Dict[str, Any] = None) -> int:
    """
    Execute a raw SQL write query (INSERT, UPDATE, DELETE)
    
    Args:
        query: SQL query string
        params: Parameters to bind to the query
        
    Returns:
        Number of rows affected
    """
    try:
        # Ensure connection is alive
        check_db_connection()
        
        session = get_session()
        result = session.execute(text(query), params or {})
        rows_affected = result.rowcount
        
        session.commit()
        return rows_affected
    except Exception as e:
        session.rollback()
        logging.error(f"Error executing write query: {str(e)}")
        raise


def create_tables():
    """
    Create all tables defined by SQLAlchemy models
    """
    try:
        # Ensure connection is alive
        check_db_connection()
        
        db.create_all()
        logging.info("Successfully created all database tables")
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
        raise