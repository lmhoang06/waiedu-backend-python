"""
PostgreSQL Service Module

This module provides database connection and query functions using SQLAlchemy.
It serves as a wrapper around SQLAlchemy to simplify database interactions.
"""
import os
from flask import current_app
import logging
from sqlalchemy import text
from typing import Any, Dict, List, Optional, Tuple, Union
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
        db.create_all()
        logging.info("Successfully created all database tables")
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
        raise