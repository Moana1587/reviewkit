"""
ReviewKit Backend - Main Flask Application
A well-structured Flask application for managing and analyzing customer reviews using AI
"""

from flask import Flask, current_app
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'

# Initialize database
from models import db
db.init_app(app)

# Import and register routes
from routes import register_routes
register_routes(app)

# Initialize database tables
@app.before_request
def initialize_database():
    with current_app.app_context():
        from db_utils import initialize_database
        initialize_database()

def main():
    """Main application entry point"""
    # Create all tables
    with app.app_context():
        db.create_all()
    
    # Parse command line arguments
    host = '127.0.0.1'  # Default to localhost
    port = 8000
    debug = True
    
    if '--host' in sys.argv:
        host_idx = sys.argv.index('--host')
        if host_idx + 1 < len(sys.argv):
            host = sys.argv[host_idx + 1]
            debug = False  # Disable debug in production
    
    if '--port' in sys.argv:
        port_idx = sys.argv.index('--port')
        if port_idx + 1 < len(sys.argv):
            port = int(sys.argv[port_idx + 1])
    
    # Print startup information
    print(f"\n{'='*60}")
    print(f"  ReviewKit Server Starting")
    print(f"{'='*60}")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Debug: {debug}")
    print(f"  Access at: http://{host if host != '0.0.0.0' else 'YOUR_SERVER_IP'}:{port}")
    print(f"{'='*60}\n")
    
    # Run the application
    app.run(debug=debug, host=host, port=port, use_reloader=False, threaded=True)

if __name__ == '__main__':
    main()
