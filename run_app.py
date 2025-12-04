#!/usr/bin/env python3
"""
Simple startup script for the Disaster Management System
This handles common startup issues and provides better error messages
"""

import sys
import os
import traceback

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask',
        'flask_sqlalchemy', 
        'pydantic',
        'requests',
        'werkzeug'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install flask flask-sqlalchemy pydantic requests")
        return False
    
    print("✅ All required packages found")
    return True

def setup_environment():
    """Setup basic environment"""
    # Create necessary directories
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    print("✅ Directories created")

def main():
    print("🚀 Starting Disaster Management System...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    try:
        # Import and run the app
        print("📦 Loading application...")
        from app import app
        
        print("🗄️  Initializing database...")
        # Database should be initialized in app.py
        
        print("🌐 Starting web server...")
        print("=" * 50)
        print("✅ Server running at: http://localhost:5000")
        print("📋 Default credentials:")
        print("   Admin: admin / admin123")
        print("   Government: govuser / govpass123")
        print("=" * 50)
        
        # Run the app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Prevent double startup
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Check if all files are in the correct location")
        traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Startup Error: {e}")
        traceback.print_exc()
        
    input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()