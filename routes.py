from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
import json
from datetime import datetime, date, timedelta
import numpy as np
from PIL import Image
import io
import base64

from app import db
from models import User, Recipe, FoodLog, FoodCategory
from search_engine import RecipeSearchEngine
from ml_model import FoodClassifier
from health_calculator import HealthCalculator
from email_service import EmailService
from health_recommendations import health_recommender

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)

# Initialize services
search_engine = RecipeSearchEngine()
food_classifier = FoodClassifier()
health_calc = HealthCalculator()
email_service = EmailService()

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get today's food logs
    today = date.today()
    today_logs = FoodLog.query.filter_by(user_id=current_user.id, date_logged=today).all()
    
    # Calculate daily totals
    daily_calories = sum(log.calories * log.servings for log in today_logs)
    daily_protein = sum(log.protein * log.servings for log in today_logs)
    daily_carbs = sum(log.carbs * log.servings for log in today_logs)
    daily_fat = sum(log.fat * log.servings for log in today_logs)
    
    # Get calorie goal
    try:
        calorie_goal = current_user.daily_calorie_goal or (current_user.calculate_daily_calories() if hasattr(current_user, 'calculate_daily_calories') else None) or 2000
    except:
        calorie_goal = 2000
    
    # Get weekly data for chart
    week_data = []
    for i in range(7):
        day = today - timedelta(days=i)
        day_logs = FoodLog.query.filter_by(user_id=current_user.id, date_logged=day).all()
        day_calories = sum(log.calories * log.servings for log in day_logs)
        week_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'calories': day_calories
        })
    
    return render_template('dashboard.html', 
                         daily_calories=daily_calories,
                         daily_protein=daily_protein,
                         daily_carbs=daily_carbs,
                         daily_fat=daily_fat,
                         calorie_goal=calorie_goal,
                         week_data=json.dumps(week_data[::-1]),  # Reverse for chronological order
                         today_logs=today_logs,
                         current_date=today.strftime('%B %d, %Y'))

@main_bp.route('/recipes')
def recipes():
    search_query = request.args.get('search', '')
    category = request.args.get('category', '')
    health_filter = request.args.get('health_filter', '')
    page = request.args.get('page', 1, type=int)
    
    # If health filter is requested and user is logged in, get personalized recipes
    if health_filter == 'personalized' and current_user.is_authenticated:
        personalized_recipes = health_recommender.get_personalized_recipes(current_user, limit=100)
        recipe_ids = [r.id for r in personalized_recipes]
        query = Recipe.query.filter(Recipe.id.in_(recipe_ids))
    else:
        query = Recipe.query
        
        if search_query:
            recipes_found = search_engine.search_recipes(search_query)
            recipe_ids = [r.id for r in recipes_found]
            query = query.filter(Recipe.id.in_(recipe_ids))
        
        if category:
            query = query.filter_by(category=category)
    
    recipes_paginated = query.paginate(page=page, per_page=12, error_out=False)
    
    # Get all categories for filter
    categories = db.session.query(Recipe.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('recipes.html', 
                         recipes=recipes_paginated,
                         search_query=search_query,
                         categories=categories,
                         selected_category=category,
                         health_filter=health_filter)

@main_bp.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Parse ingredients and tags from JSON
    ingredients = json.loads(recipe.ingredients) if recipe.ingredients else []
    tags = json.loads(recipe.tags) if recipe.tags else []
    
    health_warnings = []
    health_benefits = []
    
    # Get health recommendations if user is logged in
    if current_user.is_authenticated:
        health_warnings = health_recommender.get_health_warnings(recipe, current_user)
        health_benefits = health_recommender.get_health_benefits(recipe, current_user)
    
    return render_template('recipe_detail.html', 
                         recipe=recipe,
                         ingredients=ingredients,
                         tags=tags,
                         health_warnings=health_warnings,
                         health_benefits=health_benefits)

@main_bp.route('/upload')
@login_required
def upload():
    return render_template('upload.html')

@main_bp.route('/profile')
@login_required
def profile():
    # Parse JSON fields for display
    user_allergies = []
    user_conditions = []
    user_restrictions = []
    
    try:
        if current_user.allergies:
            user_allergies = json.loads(current_user.allergies)
    except:
        user_allergies = []
        
    try:
        if current_user.medical_conditions:
            user_conditions = json.loads(current_user.medical_conditions)
    except:
        user_conditions = []
        
    try:
        if current_user.dietary_restrictions:
            user_restrictions = json.loads(current_user.dietary_restrictions)
    except:
        user_restrictions = []
    
    return render_template('profile.html', 
                         user_allergies=user_allergies,
                         user_conditions=user_conditions,
                         user_restrictions=user_restrictions)

@main_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        current_user.age = int(request.form.get('age', 0)) or None
        current_user.gender = request.form.get('gender') or None
        current_user.height = float(request.form.get('height', 0)) or None
        current_user.weight = float(request.form.get('weight', 0)) or None
        current_user.activity_level = request.form.get('activity_level') or None
        current_user.goal = request.form.get('goal') or None
        
        # Handle daily calorie goal
        calorie_goal = request.form.get('daily_calorie_goal')
        if calorie_goal:
            current_user.daily_calorie_goal = int(calorie_goal)
        elif all([current_user.age, current_user.gender, current_user.height, 
                current_user.weight, current_user.activity_level]):
            current_user.daily_calorie_goal = current_user.calculate_daily_calories()
        
        # Handle health conditions
        allergies_text = request.form.get('allergies', '').strip()
        if allergies_text:
            allergies_list = [allergy.strip() for allergy in allergies_text.split(',') if allergy.strip()]
            current_user.allergies = json.dumps(allergies_list)
        else:
            current_user.allergies = None
            
        conditions_text = request.form.get('medical_conditions', '').strip()
        if conditions_text:
            conditions_list = [condition.strip() for condition in conditions_text.split(',') if condition.strip()]
            current_user.medical_conditions = json.dumps(conditions_list)
        else:
            current_user.medical_conditions = None
            
        restrictions_text = request.form.get('dietary_restrictions', '').strip()
        if restrictions_text:
            restrictions_list = [restriction.strip() for restriction in restrictions_text.split(',') if restriction.strip()]
            current_user.dietary_restrictions = json.dumps(restrictions_list)
        else:
            current_user.dietary_restrictions = None
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except ValueError:
        flash('Please enter valid numeric values for age, height, and weight.', 'error')
    except Exception as e:
        flash('An error occurred while updating your profile.', 'error')
        current_app.logger.error(f"Profile update error: {e}")
    
    return redirect(url_for('main.profile'))

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.index'))

# API routes
@api_bp.route('/classify_food', methods=['POST'])
@login_required
def classify_food():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Process image
        try:
            # Reset file stream position
            file.stream.seek(0)
            image = Image.open(file.stream)
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            current_app.logger.error(f"Image processing error: {e}")
            return jsonify({'error': 'Could not process image file'}), 400
        
        # Classify image
        predictions = food_classifier.predict(image)
        
        if predictions:
            # Get the top prediction
            top_prediction = predictions[0]
            
            # Find recipes for this category
            recipes = Recipe.query.filter_by(food_category_id=top_prediction['category_id']).limit(5).all()
            
            # If no recipes found for exact category, search by name
            if not recipes:
                category_name = top_prediction['category'].replace('_', ' ')
                recipes = Recipe.query.filter(Recipe.name.ilike(f'%{category_name}%')).limit(5).all()
            
            # If still no recipes, get random popular recipes
            if not recipes:
                recipes = Recipe.query.order_by(Recipe.id.desc()).limit(5).all()
            
            recipe_data = []
            for recipe in recipes:
                recipe_data.append({
                    'id': recipe.id,
                    'name': recipe.name,
                    'calories_per_serving': recipe.calories_per_serving,
                    'prep_time': recipe.prep_time,
                    'cook_time': recipe.cook_time,
                    'description': recipe.description
                })
            
            return jsonify({
                'success': True,
                'predictions': predictions,
                'top_prediction': top_prediction,
                'recipes': recipe_data
            })
        else:
            return jsonify({'error': 'Could not classify image'}), 400
    
    except Exception as e:
        current_app.logger.error(f"Image classification error: {e}")
        return jsonify({'error': 'Image processing failed'}), 500

@api_bp.route('/log_food', methods=['POST'])
@login_required
def log_food():
    try:
        data = request.get_json()
        
        food_log = FoodLog(
            user_id=current_user.id,
            recipe_id=data.get('recipe_id'),
            food_name=data['food_name'],
            servings=float(data.get('servings', 1.0)),
            calories=int(data['calories']),
            protein=float(data.get('protein', 0)),
            carbs=float(data.get('carbs', 0)),
            fat=float(data.get('fat', 0)),
            meal_type=data.get('meal_type', 'snack'),
            date_logged=datetime.strptime(data.get('date', date.today().isoformat()), '%Y-%m-%d').date()
        )
        
        db.session.add(food_log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Food logged successfully'})
    
    except Exception as e:
        current_app.logger.error(f"Food logging error: {e}")
        return jsonify({'error': 'Failed to log food'}), 500

@api_bp.route('/search_recipes')
def search_recipes():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    recipes = search_engine.search_recipes(query, limit=10)
    
    results = []
    for recipe in recipes:
        results.append({
            'id': recipe.id,
            'name': recipe.name,
            'calories_per_serving': recipe.calories_per_serving,
            'prep_time': recipe.prep_time,
            'cook_time': recipe.cook_time,
            'category': recipe.category
        })
    
    return jsonify(results)

@api_bp.route('/nutrition_summary')
@login_required
def nutrition_summary():
    days = request.args.get('days', 7, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    logs = FoodLog.query.filter(
        FoodLog.user_id == current_user.id,
        FoodLog.date_logged >= start_date,
        FoodLog.date_logged <= end_date
    ).all()
    
    daily_data = {}
    for log in logs:
        day_str = log.date_logged.isoformat()
        if day_str not in daily_data:
            daily_data[day_str] = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0
            }
        
        daily_data[day_str]['calories'] += log.calories * log.servings
        daily_data[day_str]['protein'] += log.protein * log.servings
        daily_data[day_str]['carbs'] += log.carbs * log.servings
        daily_data[day_str]['fat'] += log.fat * log.servings
    
    return jsonify(daily_data)
