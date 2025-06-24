#!/usr/bin/env python3
"""
Local setup script for Health Manager application
Run this script to set up the application for local development
"""

import os
import secrets
import subprocess
import sys

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_hex(32)

def create_env_file():
    """Create .env file with secure defaults"""
    env_content = f"""# Database Configuration
DATABASE_URL=sqlite:///health_manager.db

# Security Configuration
SESSION_SECRET={generate_secret_key()}
FLASK_ENV=development
DEBUG=True

# Email Configuration (Optional - configure for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif

# Application Settings
RECIPES_PER_PAGE=12
SEARCH_RESULTS_LIMIT=20
DEFAULT_CALORIE_GOAL=2000
DEFAULT_ACTIVITY_LEVEL=moderate

# Email Notification Settings
SEND_DAILY_SUMMARIES=False
SEND_WEEKLY_SUMMARIES=False
DAILY_SUMMARY_TIME=20:00
WEEKLY_SUMMARY_DAY=6
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✓ Created .env file with secure configuration")

def create_uploads_dir():
    """Create uploads directory"""
    os.makedirs('uploads', exist_ok=True)
    print("✓ Created uploads directory")

def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_local.txt'])
        print("✓ Installed Python dependencies")
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        return False
    return True

def initialize_database():
    """Initialize the database"""
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
            print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return False
    return True

def load_sample_data():
    """Load sample data"""
    try:
        from app import app
        from data_loader import DataLoader
        with app.app_context():
            loader = DataLoader()
            loader.load_food_categories()
            loader.load_sample_recipes()
            print("✓ Sample data loaded")
    except Exception as e:
        print(f"✗ Failed to load sample data: {e}")
        return False
    return True

def main():
    """Main setup function"""
    print("🏥 Health Manager Local Setup")
    print("=" * 40)
    
    # Check if .env already exists
    if os.path.exists('.env'):
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env creation")
        else:
            create_env_file()
    else:
        create_env_file()
    
    # Create directories
    create_uploads_dir()
    
    # Install dependencies
    if not install_dependencies():
        print("Setup failed during dependency installation")
        return
    
    # Initialize database
    if not initialize_database():
        print("Setup failed during database initialization")
        return
    
    # Load sample data
    if not load_sample_data():
        print("Warning: Failed to load sample data, but setup can continue")
    
    print("\n🎉 Setup complete!")
    print("\nTo start the application:")
    print("  python main.py")
    print("\nThen open: http://localhost:5000")

if __name__ == "__main__":
    main()