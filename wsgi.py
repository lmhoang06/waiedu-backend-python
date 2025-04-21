from app import create_app

# Create the Flask application using our factory function
application = create_app()

# This allows the file to be run directly using `python wsgi.py`
if __name__ == "__main__":
    application.run(host="0.0.0.0", debug=True)