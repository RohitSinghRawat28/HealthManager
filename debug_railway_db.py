
"""
Debug script to check Railway database status and manually initialize if needed
"""

import os
import logging
from app import app, db
from models import Recipe, FoodCategory, User
from data_loader import DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_tables():
    """Check if database tables exist"""
    try:
        with app.app_context():
            # Check if tables exist by trying to query them
            recipe_count = Recipe.query.count()
            category_count = FoodCategory.query.count()
            user_count = User.query.count()
            
            logger.info(f"Tables found:")
            logger.info(f"  - Recipes: {recipe_count}")
            logger.info(f"  - Food Categories: {category_count}")
            logger.info(f"  - Users: {user_count}")
            
            return True
    except Exception as e:
        logger.error(f"Tables check failed: {e}")
        return False

def recreate_tables():
    """Recreate all database tables"""
    try:
        with app.app_context():
            logger.info("Dropping all tables...")
            db.drop_all()
            
            logger.info("Creating all tables...")
            db.create_all()
            
            logger.info("Tables recreated successfully")
            return True
    except Exception as e:
        logger.error(f"Table recreation failed: {e}")
        return False

def load_data():
    """Load sample data"""
    try:
        with app.app_context():
            loader = DataLoader()
            
            # Load food categories
            logger.info("Loading food categories...")
            loader.load_food_categories()
            
            # Load sample recipes
            logger.info("Loading sample recipes...")
            loader.load_sample_recipes()
            
            # Verify data was loaded
            recipe_count = Recipe.query.count()
            category_count = FoodCategory.query.count()
            
            logger.info(f"Data loaded successfully:")
            logger.info(f"  - Recipes: {recipe_count}")
            logger.info(f"  - Food Categories: {category_count}")
            
            return True
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        return False

def main():
    """Main diagnostic and fix function"""
    logger.info("🔍 Railway Database Diagnostic")
    logger.info("=" * 50)
    
    # Check environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found")
        return
    
    logger.info(f"Database URL: {database_url[:30]}...")
    
    # Check if tables exist and have data
    if not check_tables():
        logger.info("Creating tables...")
        if not recreate_tables():
            logger.error("Failed to create tables")
            return
    
    # Check if we have recipes
    with app.app_context():
        recipe_count = Recipe.query.count()
        if recipe_count == 0:
            logger.info("No recipes found, loading sample data...")
            if not load_data():
                logger.error("Failed to load data")
                return
        else:
            logger.info(f"Database already has {recipe_count} recipes")
    
    logger.info("✅ Database diagnostic complete!")

if __name__ == "__main__":
    main()
