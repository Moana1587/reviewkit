#!/usr/bin/env python3
"""
Alternative Flask runner for Windows compatibility
"""
from app import app, sqlite_db

if __name__ == '__main__':
    with app.app_context():
        sqlite_db.create_all()
    
    # Try different configurations for Windows compatibility
    try:
        # First try: Standard configuration
        app.run(debug=True, host='127.0.0.1', port=8000, use_reloader=False)
    except OSError as e:
        print(f"Port 8000 failed: {e}")
        try:
            # Second try: Different port
            app.run(debug=True, host='127.0.0.1', port=3000, use_reloader=False)
        except OSError as e2:
            print(f"Port 3000 failed: {e2}")
            try:
                # Third try: Let Flask choose port
                app.run(debug=True, host='127.0.0.1', port=0, use_reloader=False)
            except Exception as e3:
                print(f"All attempts failed: {e3}")
                print("Try running: python -m flask run --host=127.0.0.1 --port=8000")

