release: python railway_setup.py
railway run python debug_railway_db.py
railway run python railway_manual_init.py
railway run python -c "
from app import app, db
from models import Recipe
with app.app_context():
    count = Recipe.query.count()
    print(f'Recipes in database: {count}')
"
web: gunicorn main:app
