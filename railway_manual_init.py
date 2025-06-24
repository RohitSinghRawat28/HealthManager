
"""
Manual database initialization for Railway
Run this if automatic initialization failed
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db
from models import Recipe, FoodCategory, User
from data_loader import DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_init_database():
    """Force initialize database with proper error handling"""
    try:
        with app.app_context():
            logger.info("Connecting to database...")
            
            # Test connection
            result = db.session.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            logger.info(f"PostgreSQL version: {version}")
            
            # Drop and recreate all tables
            logger.info("Dropping existing tables...")
            db.drop_all()
            
            logger.info("Creating new tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Created tables: {tables}")
            
            # Load data
            logger.info("Loading food categories...")
            loader = DataLoader()
            loader.load_food_categories()
            
            logger.info("Loading sample recipes...")
            loader.load_sample_recipes()
            
            # Verify data
            recipe_count = Recipe.query.count()
            category_count = FoodCategory.query.count()
            
            logger.info(f"✅ Database initialized successfully!")
            logger.info(f"   - Food categories: {category_count}")
            logger.info(f"   - Recipes: {recipe_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    logger.info("🚂 Railway Manual Database Initialization")
    logger.info("=" * 50)
    
    # Check if we're in Railway environment
    if not os.getenv('DATABASE_URL'):
        logger.error("DATABASE_URL not found. Are you running on Railway?")
        sys.exit(1)
    
    # Force initialize
    if force_init_database():
        logger.info("🎉 Manual initialization complete!")
    else:
        logger.error("💥 Manual initialization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
