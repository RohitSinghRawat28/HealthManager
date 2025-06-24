from app import db
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Health profile
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))  # 'male', 'female', 'other'
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    activity_level = db.Column(db.String(20))  # sedentary, light, moderate, active, very_active
    goal = db.Column(db.String(20))  # lose, maintain, gain
    daily_calorie_goal = db.Column(db.Integer)
    
    # Health conditions and preferences
    allergies = db.Column(db.Text)  # JSON string of allergies
    medical_conditions = db.Column(db.Text)  # JSON string of medical conditions
    dietary_restrictions = db.Column(db.Text)  # JSON string of dietary restrictions
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate using Harris-Benedict equation"""
        if not all([self.age, self.gender, self.height, self.weight]):
            return None
        
        if self.gender.lower() == 'male':
            bmr = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
        else:
            bmr = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
        
        return bmr
    
    def calculate_daily_calories(self):
        """Calculate daily calorie needs based on activity level"""
        bmr = self.calculate_bmr()
        if not bmr:
            return None
        
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        
        multiplier = activity_multipliers.get(self.activity_level, 1.2)
        daily_calories = bmr * multiplier
        
        # Adjust based on goal
        if self.goal == 'lose':
            daily_calories -= 500  # 500 calorie deficit for 1 lb/week loss
        elif self.goal == 'gain':
            daily_calories += 500  # 500 calorie surplus for 1 lb/week gain
        
        return int(daily_calories)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, nullable=False)  # JSON string
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer)  # in minutes
    cook_time = db.Column(db.Integer)  # in minutes
    servings = db.Column(db.Integer)
    calories_per_serving = db.Column(db.Integer)
    protein = db.Column(db.Float)  # grams per serving
    carbs = db.Column(db.Float)    # grams per serving
    fat = db.Column(db.Float)      # grams per serving
    fiber = db.Column(db.Float)    # grams per serving
    sugar = db.Column(db.Float)    # grams per serving
    sodium = db.Column(db.Float)   # mg per serving
    category = db.Column(db.String(100))
    tags = db.Column(db.Text)      # JSON string of tags
    food_category_id = db.Column(db.Integer)  # Food-101 category ID
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    food_name = db.Column(db.String(200), nullable=False)
    servings = db.Column(db.Float, default=1.0)
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, default=0)
    carbs = db.Column(db.Float, default=0)
    fat = db.Column(db.Float, default=0)
    meal_type = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    date_logged = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    recipe = db.relationship('Recipe', backref='food_logs')

class FoodCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, unique=True, nullable=False)  # Food-101 category ID
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
