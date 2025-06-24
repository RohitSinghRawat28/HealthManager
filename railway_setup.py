#!/usr/bin/env python3
"""
Railway.com deployment setup script
This script initializes the database and loads sample data for Railway deployment
"""

import os
import sys
import logging
from app import app, db
from data_loader import DataLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("✓ Database tables created successfully")
            return True
    except Exception as e:
        logger.error(f"✗ Failed to create database tables: {e}")
        return False

def load_sample_data():
    """Load sample data into database"""
    try:
        with app.app_context():
            loader = DataLoader()
            
            # Load food categories
            loader.load_food_categories()
            logger.info("✓ Food categories loaded")
            
            # Load sample recipes
            loader.load_sample_recipes()
            logger.info("✓ Sample recipes loaded")
            
            return True
    except Exception as e:
        logger.error(f"✗ Failed to load sample data: {e}")
        return False

def check_database_connection():
    """Check if database connection is working"""
    try:
        with app.app_context():
            # Try to execute a simple query
            db.session.execute(db.text('SELECT 1'))
            logger.info("✓ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def main():
    """Main setup function for Railway deployment"""
    logger.info("🚂 Railway.com Database Setup")
    logger.info("=" * 40)
    
    # Check environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not found")
        sys.exit(1)
    
    logger.info(f"Database URL: {database_url[:20]}...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Cannot connect to database")
        sys.exit(1)
    
    # Initialize database
    if not init_database():
        logger.error("Database initialization failed")
        sys.exit(1)
    
    # Load sample data
    if not load_sample_data():
        logger.warning("Sample data loading failed, but continuing...")
    
    logger.info("🎉 Railway database setup complete!")

if __name__ == "__main__":
    main()
