import math
from datetime import date, datetime, timedelta
from models import User, FoodLog
from app import db

class HealthCalculator:
    
    @staticmethod
    def calculate_bmr(age, gender, height_cm, weight_kg):
        """
        Calculate Basal Metabolic Rate using Harris-Benedict equation
        
        Args:
            age: Age in years
            gender: 'male' or 'female'
            height_cm: Height in centimeters
            weight_kg: Weight in kilograms
        
        Returns:
            BMR in calories per day
        """
        if gender.lower() == 'male':
            bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
        
        return bmr
    
    @staticmethod
    def calculate_tdee(bmr, activity_level):
        """
        Calculate Total Daily Energy Expenditure
        
        Args:
            bmr: Basal Metabolic Rate
            activity_level: Activity level string
        
        Returns:
            TDEE in calories per day
        """
        activity_multipliers = {
            'sedentary': 1.2,      # Little or no exercise
            'light': 1.375,        # Light exercise/sports 1-3 days/week
            'moderate': 1.55,      # Moderate exercise/sports 3-5 days/week
            'active': 1.725,       # Hard exercise/sports 6-7 days a week
            'very_active': 1.9     # Very hard exercise, physical job
        }
        
        multiplier = activity_multipliers.get(activity_level, 1.2)
        return bmr * multiplier
    
    @staticmethod
    def calculate_calorie_goal(bmr, activity_level, goal):
        """
        Calculate daily calorie goal based on weight goal
        
        Args:
            bmr: Basal Metabolic Rate
            activity_level: Activity level string
            goal: 'lose', 'maintain', or 'gain'
        
        Returns:
            Daily calorie goal
        """
        tdee = HealthCalculator.calculate_tdee(bmr, activity_level)
        
        if goal == 'lose':
            return int(tdee - 500)  # 500 calorie deficit for ~1 lb/week loss
        elif goal == 'gain':
            return int(tdee + 500)  # 500 calorie surplus for ~1 lb/week gain
        else:  # maintain
            return int(tdee)
    
    @staticmethod
    def calculate_bmi(height_cm, weight_kg):
        """
        Calculate Body Mass Index
        
        Args:
            height_cm: Height in centimeters
            weight_kg: Weight in kilograms
        
        Returns:
            BMI value and category
        """
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        
        if bmi < 18.5:
            category = 'Underweight'
        elif bmi < 25:
            category = 'Normal weight'
        elif bmi < 30:
            category = 'Overweight'
        else:
            category = 'Obese'
        
        return round(bmi, 1), category
    
    @staticmethod
    def calculate_ideal_weight(height_cm, gender):
        """
        Calculate ideal weight using Devine formula
        
        Args:
            height_cm: Height in centimeters
            gender: 'male' or 'female'
        
        Returns:
            Ideal weight in kg
        """
        height_inches = height_cm / 2.54
        
        if gender.lower() == 'male':
            # Devine formula for men: 50 kg + 2.3 kg per inch over 5 feet
            ideal_weight = 50 + 2.3 * max(0, height_inches - 60)
        else:
            # Devine formula for women: 45.5 kg + 2.3 kg per inch over 5 feet
            ideal_weight = 45.5 + 2.3 * max(0, height_inches - 60)
        
        return round(ideal_weight, 1)
    
    @staticmethod
    def calculate_water_intake(weight_kg, activity_level='moderate'):
        """
        Calculate recommended daily water intake
        
        Args:
            weight_kg: Weight in kilograms
            activity_level: Activity level
        
        Returns:
            Water intake in liters
        """
        # Base calculation: 35ml per kg of body weight
        base_intake = weight_kg * 35 / 1000  # Convert to liters
        
        # Adjust for activity level
        if activity_level in ['active', 'very_active']:
            base_intake *= 1.2
        elif activity_level == 'light':
            base_intake *= 1.1
        
        return round(base_intake, 1)
    
    @staticmethod
    def get_nutrition_summary(user_id, days=7):
        """
        Get nutrition summary for a user over specified days
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            Dictionary with nutrition summary
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        logs = FoodLog.query.filter(
            FoodLog.user_id == user_id,
            FoodLog.date_logged >= start_date,
            FoodLog.date_logged <= end_date
        ).all()
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        daily_data = {}
        
        for log in logs:
            day_str = log.date_logged.isoformat()
            if day_str not in daily_data:
                daily_data[day_str] = {
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'meals': 0
                }
            
            calories = log.calories * log.servings
            protein = log.protein * log.servings
            carbs = log.carbs * log.servings
            fat = log.fat * log.servings
            
            daily_data[day_str]['calories'] += calories
            daily_data[day_str]['protein'] += protein
            daily_data[day_str]['carbs'] += carbs
            daily_data[day_str]['fat'] += fat
            daily_data[day_str]['meals'] += 1
            
            total_calories += calories
            total_protein += protein
            total_carbs += carbs
            total_fat += fat
        
        avg_calories = total_calories / days if days > 0 else 0
        avg_protein = total_protein / days if days > 0 else 0
        avg_carbs = total_carbs / days if days > 0 else 0
        avg_fat = total_fat / days if days > 0 else 0
        
        return {
            'days_analyzed': days,
            'total_calories': total_calories,
            'total_protein': total_protein,
            'total_carbs': total_carbs,
            'total_fat': total_fat,
            'avg_calories': round(avg_calories, 1),
            'avg_protein': round(avg_protein, 1),
            'avg_carbs': round(avg_carbs, 1),
            'avg_fat': round(avg_fat, 1),
            'daily_data': daily_data
        }
    
    @staticmethod
    def get_health_recommendations(user):
        """
        Get personalized health recommendations for a user
        
        Args:
            user: User object
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not user.age or not user.height or not user.weight:
            recommendations.append("Complete your profile to get personalized recommendations")
            return recommendations
        
        # BMI recommendations
        bmi, bmi_category = HealthCalculator.calculate_bmi(user.height, user.weight)
        
        if bmi_category == 'Underweight':
            recommendations.append("Consider consulting with a healthcare provider about healthy weight gain strategies")
        elif bmi_category == 'Overweight':
            recommendations.append("Consider a balanced approach to weight management with regular exercise")
        elif bmi_category == 'Obese':
            recommendations.append("Consider consulting with a healthcare provider for a comprehensive weight management plan")
        
        # Water intake recommendation
        if user.weight:
            water_intake = HealthCalculator.calculate_water_intake(user.weight, user.activity_level or 'moderate')
            recommendations.append(f"Aim to drink at least {water_intake}L of water daily")
        
        # Activity recommendations
        if user.activity_level == 'sedentary':
            recommendations.append("Try to incorporate at least 30 minutes of light exercise into your daily routine")
        elif user.activity_level in ['light', 'moderate']:
            recommendations.append("Great job staying active! Consider adding some strength training to your routine")
        
        # Calorie recommendations
        if user.daily_calorie_goal:
            # Get recent nutrition data
            nutrition_summary = HealthCalculator.get_nutrition_summary(user.id, days=7)
            avg_calories = nutrition_summary['avg_calories']
            
            if avg_calories < user.daily_calorie_goal * 0.8:
                recommendations.append("You may be eating too few calories. Consider increasing your intake gradually")
            elif avg_calories > user.daily_calorie_goal * 1.2:
                recommendations.append("You may be eating more calories than your goal. Consider portion control")
        
        # Nutrition balance recommendations
        nutrition_summary = HealthCalculator.get_nutrition_summary(user.id, days=7)
        if nutrition_summary['avg_calories'] > 0:
            protein_pct = (nutrition_summary['avg_protein'] * 4) / nutrition_summary['avg_calories'] * 100
            carb_pct = (nutrition_summary['avg_carbs'] * 4) / nutrition_summary['avg_calories'] * 100
            fat_pct = (nutrition_summary['avg_fat'] * 9) / nutrition_summary['avg_calories'] * 100
            
            if protein_pct < 15:
                recommendations.append("Consider increasing your protein intake for better muscle maintenance")
            if fat_pct > 35:
                recommendations.append("Consider reducing fat intake and increasing vegetables and whole grains")
        
        return recommendations[:5]  # Return top 5 recommendations
