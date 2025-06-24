import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///health_manager.db')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@healthmanager.com')
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # ML Model configuration
    FOOD101_DATASET_PATH = os.environ.get('FOOD101_DATASET_PATH', 'data/food_c101_n10099_r32x32x1.h5')
    MODEL_PATH = 'food_classifier_model.h5'
    
    # Application settings
    RECIPES_PER_PAGE = 12
    SEARCH_RESULTS_LIMIT = 20
    
    # Health calculation settings
    DEFAULT_CALORIE_GOAL = 2000
    DEFAULT_ACTIVITY_LEVEL = 'moderate'
    
    # Email notification settings
    SEND_DAILY_SUMMARIES = True
    SEND_WEEKLY_SUMMARIES = True
    DAILY_SUMMARY_TIME = "20:00"  # 8 PM
    WEEKLY_SUMMARY_DAY = 6  # Sunday (0=Monday, 6=Sunday)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///health_manager_dev.db')

class ProductionConfig(Config):
    DEBUG = False
    # Use environment variables for production database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set for production environment")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
