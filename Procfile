release: python railway_setup.py
release: python debug_railway_db.py
release: python railway_manual_init.py
release: python -c "
from app import app, db
from models import Recipe
with app.app_context():
    count = Recipe.query.count()
    print(f'Recipes in database: {count}')
"
web: gunicorn main:app
