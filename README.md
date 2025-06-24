# Health Manager Web Application

A comprehensive Flask-based health management system with AI-powered food recognition, recipe management, and nutrition tracking.

## Features

- **AI Food Recognition**: Upload photos to identify foods using Food-101 dataset
- **Recipe Management**: Browse 200+ recipes from global cuisines
- **Nutrition Tracking**: Log meals and track daily nutrition goals
- **Health Dashboard**: Visualize progress with interactive charts
- **User Profiles**: Personalized BMR/TDEE calculations
- **Search Engine**: Advanced recipe search with data structures

## Prerequisites

- Python 3.11 or higher
- PostgreSQL (for production) or SQLite (for development)
- pip (Python package manager)

## Quick Setup (Automated)

### Option 1: Automated Setup Script
```bash
# Clone and setup in one go
git clone <your-repository-url>
cd health-manager
python setup_local.py
```

The setup script will:
- Create virtual environment configuration
- Install all dependencies
- Generate secure environment variables
- Initialize database with sample data
- Create necessary directories

### Option 2: Manual Setup

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd health-manager
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements_local.txt
```

**Note**: TensorFlow dependencies are commented out by default. For AI food classification, uncomment those lines.

### 4. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Initialize Database and Load Data
```bash
python -c "
from app import app, db
from data_loader import DataLoader
with app.app_context():
    db.create_all()
    loader = DataLoader()
    loader.load_food_categories()
    loader.load_sample_recipes()
    print('Setup complete!')
"
```

### 6. Run the Application
```bash
python main.py
```

### 7. Access the Application
Open http://localhost:5000 in your browser

## Project Structure

```
health-manager/
├── app.py                 # Flask application factory
├── main.py               # Application entry point
├── models.py             # Database models
├── routes.py             # Application routes
├── config.py             # Configuration settings
├── data_loader.py        # Data loading utilities
├── ml_model.py           # AI/ML components
├── search_engine.py      # Recipe search engine
├── health_calculator.py  # Health calculations
├── email_service.py      # Email notifications
├── templates/            # HTML templates
├── static/               # CSS, JS, images
├── data/                 # Sample data files
└── requirements.txt      # Python dependencies
```

## Configuration Options

### Database Configuration

**SQLite (Development)**:
```bash
DATABASE_URL=sqlite:///health_manager.db
```

**PostgreSQL (Production)**:
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/health_manager
```

### Email Configuration

For Gmail with App Password:
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-character-app-password
```

### Security Settings

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Development Tips

1. **Debug Mode**: Set `DEBUG=True` for development
2. **Hot Reload**: Flask automatically reloads on file changes in debug mode
3. **Database Reset**: Delete the SQLite file to reset the database
4. **Logs**: Check terminal output for application logs

## Production Deployment

1. Set `FLASK_ENV=production` and `DEBUG=False`
2. Use PostgreSQL instead of SQLite
3. Set up proper reverse proxy (nginx)
4. Use environment variables for sensitive data
5. Set up SSL certificates
6. Configure proper logging

## Troubleshooting

**Common Issues:**

1. **Database Connection Error**: Check DATABASE_URL format
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Port Already in Use**: Change port in main.py or kill existing process
4. **Permission Errors**: Check file permissions for uploads directory

**Reset Database:**
```bash
# For SQLite
rm health_manager.db

# For PostgreSQL
psql -c "DROP DATABASE health_manager; CREATE DATABASE health_manager;"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.