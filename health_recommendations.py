"""
Health-based recommendation system for recipes and nutrition
"""
import json
import logging
from models import Recipe, User, db
from sqlalchemy import and_, or_, not_

class HealthRecommendationEngine:
    """Generate personalized recommendations based on health conditions"""
    
    def __init__(self):
        # Define allergen keywords to avoid
        self.allergen_keywords = {
            'peanuts': ['peanut', 'groundnut'],
            'tree nuts': ['almond', 'walnut', 'cashew', 'pecan', 'hazelnut', 'pistachio', 'brazil nut'],
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein'],
            'eggs': ['egg', 'albumin', 'mayonnaise'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'oyster', 'mussel', 'scallop'],
            'fish': ['salmon', 'tuna', 'cod', 'fish', 'anchovy'],
            'soy': ['soy', 'tofu', 'tempeh', 'miso', 'edamame'],
            'wheat': ['wheat', 'flour', 'bread', 'pasta', 'gluten'],
            'gluten': ['wheat', 'barley', 'rye', 'flour', 'bread', 'pasta', 'gluten'],
            'sesame': ['sesame', 'tahini']
        }
        
        # Condition-specific dietary recommendations
        self.condition_guidelines = {
            'diabetes': {
                'avoid_high': ['sugar', 'refined carbs'],
                'prefer_low': ['sugar', 'carbs'],
                'max_sugar_per_serving': 10,
                'max_carbs_per_serving': 45
            },
            'hypertension': {
                'avoid_high': ['sodium'],
                'max_sodium_per_serving': 600
            },
            'heart disease': {
                'avoid_high': ['saturated fat', 'sodium', 'cholesterol'],
                'prefer_low': ['fat', 'sodium'],
                'max_fat_per_serving': 15,
                'max_sodium_per_serving': 600
            },
            'high cholesterol': {
                'avoid_high': ['cholesterol', 'saturated fat'],
                'prefer_low': ['fat'],
                'max_fat_per_serving': 12
            },
            'kidney disease': {
                'avoid_high': ['sodium', 'protein', 'phosphorus'],
                'max_sodium_per_serving': 400,
                'max_protein_per_serving': 20
            },
            'obesity': {
                'prefer_low': ['calories', 'fat'],
                'max_calories_per_serving': 400,
                'max_fat_per_serving': 15
            }
        }
        
    def get_user_health_data(self, user):
        """Extract and parse user health information"""
        allergies = []
        conditions = []
        restrictions = []
        
        try:
            if user.allergies:
                allergies = json.loads(user.allergies)
        except:
            pass
            
        try:
            if user.medical_conditions:
                conditions = json.loads(user.medical_conditions)
        except:
            pass
            
        try:
            if user.dietary_restrictions:
                restrictions = json.loads(user.dietary_restrictions)
        except:
            pass
            
        return {
            'allergies': [a.lower().strip() for a in allergies],
            'conditions': [c.lower().strip() for c in conditions],
            'restrictions': [r.lower().strip() for r in restrictions]
        }
    
    def is_recipe_safe_for_allergies(self, recipe, allergies):
        """Check if recipe is safe for user with given allergies"""
        if not allergies:
            return True
            
        # Get recipe ingredients and tags
        recipe_text = f"{recipe.name} {recipe.description or ''} {recipe.ingredients or ''} {recipe.tags or ''}".lower()
        
        for allergy in allergies:
            # Get keywords for this allergy
            keywords = self.allergen_keywords.get(allergy, [allergy])
            
            # Check if any allergen keywords appear in recipe
            for keyword in keywords:
                if keyword in recipe_text:
                    return False
                    
        return True
    
    def is_recipe_suitable_for_conditions(self, recipe, conditions):
        """Check if recipe meets dietary requirements for medical conditions"""
        if not conditions:
            return True
            
        for condition in conditions:
            guidelines = self.condition_guidelines.get(condition)
            if not guidelines:
                continue
                
            # Check maximum limits
            if 'max_sugar_per_serving' in guidelines:
                if recipe.sugar and recipe.sugar > guidelines['max_sugar_per_serving']:
                    return False
                    
            if 'max_carbs_per_serving' in guidelines:
                if recipe.carbs and recipe.carbs > guidelines['max_carbs_per_serving']:
                    return False
                    
            if 'max_sodium_per_serving' in guidelines:
                if recipe.sodium and recipe.sodium > guidelines['max_sodium_per_serving']:
                    return False
                    
            if 'max_fat_per_serving' in guidelines:
                if recipe.fat and recipe.fat > guidelines['max_fat_per_serving']:
                    return False
                    
            if 'max_protein_per_serving' in guidelines:
                if recipe.protein and recipe.protein > guidelines['max_protein_per_serving']:
                    return False
                    
            if 'max_calories_per_serving' in guidelines:
                if recipe.calories_per_serving and recipe.calories_per_serving > guidelines['max_calories_per_serving']:
                    return False
                    
        return True
    
    def is_recipe_compatible_with_restrictions(self, recipe, restrictions):
        """Check if recipe meets dietary restrictions"""
        if not restrictions:
            return True
            
        recipe_text = f"{recipe.name} {recipe.description or ''} {recipe.ingredients or ''} {recipe.tags or ''}".lower()
        
        for restriction in restrictions:
            if restriction == 'vegetarian':
                meat_keywords = ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'seafood', 'meat']
                if any(keyword in recipe_text for keyword in meat_keywords):
                    return False
                    
            elif restriction == 'vegan':
                animal_keywords = ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'seafood', 'meat', 
                                 'dairy', 'milk', 'cheese', 'butter', 'cream', 'egg', 'honey']
                if any(keyword in recipe_text for keyword in animal_keywords):
                    return False
                    
            elif restriction == 'halal':
                haram_keywords = ['pork', 'ham', 'bacon', 'alcohol', 'wine', 'beer']
                if any(keyword in recipe_text for keyword in haram_keywords):
                    return False
                    
            elif restriction == 'kosher':
                non_kosher_keywords = ['pork', 'ham', 'bacon', 'shellfish', 'lobster', 'crab', 'shrimp']
                if any(keyword in recipe_text for keyword in non_kosher_keywords):
                    return False
                    
            elif restriction in ['keto', 'ketogenic']:
                if recipe.carbs and recipe.carbs > 10:
                    return False
                    
            elif restriction == 'low-sodium':
                if recipe.sodium and recipe.sodium > 500:
                    return False
                    
            elif restriction == 'low-carb':
                if recipe.carbs and recipe.carbs > 20:
                    return False
                    
        return True
    
    def get_personalized_recipes(self, user, limit=20):
        """Get recipes personalized for user's health conditions"""
        health_data = self.get_user_health_data(user)
        
        # Get all recipes
        all_recipes = Recipe.query.all()
        safe_recipes = []
        
        for recipe in all_recipes:
            # Check allergies
            if not self.is_recipe_safe_for_allergies(recipe, health_data['allergies']):
                continue
                
            # Check medical conditions
            if not self.is_recipe_suitable_for_conditions(recipe, health_data['conditions']):
                continue
                
            # Check dietary restrictions
            if not self.is_recipe_compatible_with_restrictions(recipe, health_data['restrictions']):
                continue
                
            safe_recipes.append(recipe)
        
        # Sort by nutritional suitability for user's goals
        if user.goal == 'lose':
            safe_recipes.sort(key=lambda r: (r.calories_per_serving or 999, r.fat or 999))
        elif user.goal == 'gain':
            safe_recipes.sort(key=lambda r: -(r.calories_per_serving or 0))
        else:  # maintain
            safe_recipes.sort(key=lambda r: abs((r.calories_per_serving or 400) - 400))
            
        return safe_recipes[:limit]
    
    def get_health_warnings(self, recipe, user):
        """Get warnings for a recipe based on user's health conditions"""
        health_data = self.get_user_health_data(user)
        warnings = []
        
        # Check allergies
        if not self.is_recipe_safe_for_allergies(recipe, health_data['allergies']):
            allergens_found = []
            recipe_text = f"{recipe.name} {recipe.description or ''} {recipe.ingredients or ''} {recipe.tags or ''}".lower()
            
            for allergy in health_data['allergies']:
                keywords = self.allergen_keywords.get(allergy, [allergy])
                if any(keyword in recipe_text for keyword in keywords):
                    allergens_found.append(allergy.title())
                    
            if allergens_found:
                warnings.append(f"⚠️ Contains allergens: {', '.join(allergens_found)}")
        
        # Check medical conditions
        for condition in health_data['conditions']:
            guidelines = self.condition_guidelines.get(condition)
            if not guidelines:
                continue
                
            if condition == 'diabetes' and recipe.sugar and recipe.sugar > 10:
                warnings.append(f"⚠️ High sugar content ({recipe.sugar}g) - not recommended for diabetes")
                
            if condition == 'hypertension' and recipe.sodium and recipe.sodium > 600:
                warnings.append(f"⚠️ High sodium content ({recipe.sodium}mg) - not recommended for hypertension")
                
            if condition == 'heart disease' and recipe.fat and recipe.fat > 15:
                warnings.append(f"⚠️ High fat content ({recipe.fat}g) - not recommended for heart disease")
                
        return warnings
    
    def get_health_benefits(self, recipe, user):
        """Get health benefits of a recipe for user's conditions"""
        health_data = self.get_user_health_data(user)
        benefits = []
        
        # Low sodium benefits
        if recipe.sodium and recipe.sodium < 300:
            if 'hypertension' in health_data['conditions'] or 'heart disease' in health_data['conditions']:
                benefits.append("✅ Low sodium - good for blood pressure")
        
        # High fiber benefits
        if recipe.fiber and recipe.fiber > 5:
            if 'diabetes' in health_data['conditions']:
                benefits.append("✅ High fiber - helps control blood sugar")
                
        # High protein benefits
        if recipe.protein and recipe.protein > 20:
            if user.goal == 'gain' or 'muscle building' in health_data['restrictions']:
                benefits.append("✅ High protein - supports muscle growth")
                
        # Low calorie benefits
        if recipe.calories_per_serving and recipe.calories_per_serving < 300:
            if user.goal == 'lose' or 'obesity' in health_data['conditions']:
                benefits.append("✅ Low calorie - supports weight management")
                
        return benefits

# Global instance
health_recommender = HealthRecommendationEngine()