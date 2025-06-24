from flask import current_app, render_template_string
from flask_mail import Message
from app import mail
import logging
from datetime import date, timedelta
from health_calculator import HealthCalculator

class EmailService:
    
    @staticmethod
    def send_email(to, subject, html_body, text_body=None):
        """Send an email"""
        try:
            msg = Message(
                subject=subject,
                recipients=[to],
                html=html_body,
                body=text_body or html_body
            )
            mail.send(msg)
            logging.info(f"Email sent successfully to {to}")
            return True
        except Exception as e:
            logging.error(f"Failed to send email to {to}: {e}")
            return False
    
    @staticmethod
    def send_daily_summary(user):
        """Send daily nutrition summary email"""
        try:
            # Get today's nutrition data
            nutrition_summary = HealthCalculator.get_nutrition_summary(user.id, days=1)
            today_data = nutrition_summary['daily_data'].get(date.today().isoformat(), {
                'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'meals': 0
            })
            
            # Get calorie goal
            calorie_goal = user.daily_calorie_goal or user.calculate_daily_calories() or 2000
            
            # Calculate progress
            calorie_progress = (today_data['calories'] / calorie_goal * 100) if calorie_goal > 0 else 0
            
            # Get health recommendations
            recommendations = HealthCalculator.get_health_recommendations(user)
            
            subject = f"Daily Health Summary - {date.today().strftime('%B %d, %Y')}"
            
            html_template = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #007bff; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background-color: #f8f9fa; }
                    .stats { display: flex; justify-content: space-between; margin: 20px 0; }
                    .stat { text-align: center; flex: 1; }
                    .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
                    .progress-bar { background-color: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }
                    .progress-fill { background-color: #28a745; height: 100%; transition: width 0.3s; }
                    .recommendations { margin: 20px 0; }
                    .recommendation { background-color: white; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Daily Health Summary</h1>
                        <p>{{ date }}</p>
                    </div>
                    <div class="content">
                        <h2>Today's Nutrition</h2>
                        <div class="stats">
                            <div class="stat">
                                <div class="stat-value">{{ calories }}</div>
                                <div>Calories</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ protein }}g</div>
                                <div>Protein</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ carbs }}g</div>
                                <div>Carbs</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ fat }}g</div>
                                <div>Fat</div>
                            </div>
                        </div>
                        
                        <h3>Calorie Goal Progress</h3>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ progress }}%"></div>
                        </div>
                        <p>{{ calories }} / {{ goal }} calories ({{ progress }}%)</p>
                        
                        {% if recommendations %}
                        <div class="recommendations">
                            <h3>Health Recommendations</h3>
                            {% for rec in recommendations %}
                            <div class="recommendation">{{ rec }}</div>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        <p>Keep up the great work! Remember to stay hydrated and get enough sleep.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_body = render_template_string(html_template,
                date=date.today().strftime('%B %d, %Y'),
                calories=int(today_data['calories']),
                protein=round(today_data['protein'], 1),
                carbs=round(today_data['carbs'], 1),
                fat=round(today_data['fat'], 1),
                progress=min(100, round(calorie_progress, 1)),
                goal=calorie_goal,
                recommendations=recommendations
            )
            
            return EmailService.send_email(user.email, subject, html_body)
            
        except Exception as e:
            logging.error(f"Failed to send daily summary to user {user.id}: {e}")
            return False
    
    @staticmethod
    def send_weekly_summary(user):
        """Send weekly nutrition summary email"""
        try:
            # Get weekly nutrition data
            nutrition_summary = HealthCalculator.get_nutrition_summary(user.id, days=7)
            
            # Calculate weekly averages
            avg_calories = nutrition_summary['avg_calories']
            avg_protein = nutrition_summary['avg_protein']
            avg_carbs = nutrition_summary['avg_carbs']
            avg_fat = nutrition_summary['avg_fat']
            
            # Get calorie goal
            calorie_goal = user.daily_calorie_goal or user.calculate_daily_calories() or 2000
            
            # Calculate weekly progress
            weekly_progress = (avg_calories / calorie_goal * 100) if calorie_goal > 0 else 0
            
            # Get health recommendations
            recommendations = HealthCalculator.get_health_recommendations(user)
            
            subject = f"Weekly Health Summary - Week of {(date.today() - timedelta(days=6)).strftime('%B %d, %Y')}"
            
            html_template = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #28a745; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background-color: #f8f9fa; }
                    .stats { display: flex; justify-content: space-between; margin: 20px 0; }
                    .stat { text-align: center; flex: 1; }
                    .stat-value { font-size: 24px; font-weight: bold; color: #28a745; }
                    .recommendations { margin: 20px 0; }
                    .recommendation { background-color: white; padding: 10px; margin: 5px 0; border-left: 4px solid #28a745; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Weekly Health Summary</h1>
                        <p>{{ week_range }}</p>
                    </div>
                    <div class="content">
                        <h2>Weekly Averages</h2>
                        <div class="stats">
                            <div class="stat">
                                <div class="stat-value">{{ avg_calories }}</div>
                                <div>Avg Calories</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ avg_protein }}g</div>
                                <div>Avg Protein</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ avg_carbs }}g</div>
                                <div>Avg Carbs</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ avg_fat }}g</div>
                                <div>Avg Fat</div>
                            </div>
                        </div>
                        
                        <h3>Weekly Performance</h3>
                        <p>Your average daily intake was {{ avg_calories }} calories, which is {{ progress }}% of your {{ goal }} calorie goal.</p>
                        
                        {% if recommendations %}
                        <div class="recommendations">
                            <h3>Health Recommendations</h3>
                            {% for rec in recommendations %}
                            <div class="recommendation">{{ rec }}</div>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        <p>Great job tracking your nutrition this week! Keep up the healthy habits.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            week_start = date.today() - timedelta(days=6)
            week_end = date.today()
            week_range = f"{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}"
            
            html_body = render_template_string(html_template,
                week_range=week_range,
                avg_calories=round(avg_calories, 1),
                avg_protein=round(avg_protein, 1),
                avg_carbs=round(avg_carbs, 1),
                avg_fat=round(avg_fat, 1),
                progress=round(weekly_progress, 1),
                goal=calorie_goal,
                recommendations=recommendations
            )
            
            return EmailService.send_email(user.email, subject, html_body)
            
        except Exception as e:
            logging.error(f"Failed to send weekly summary to user {user.id}: {e}")
            return False
    
    @staticmethod
    def send_goal_achievement_notification(user, achievement_type, details):
        """Send notification when user achieves a goal"""
        try:
            subject = f"Congratulations! Goal Achievement: {achievement_type}"
            
            html_template = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #ffc107; color: #212529; padding: 20px; text-align: center; }
                    .content { padding: 20px; background-color: #f8f9fa; }
                    .achievement { background-color: white; padding: 20px; margin: 20px 0; border-radius: 10px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Congratulations!</h1>
                        <h2>{{ achievement_type }}</h2>
                    </div>
                    <div class="content">
                        <div class="achievement">
                            <h3>You've achieved your goal!</h3>
                            <p>{{ details }}</p>
                        </div>
                        <p>Keep up the excellent work and continue your healthy journey!</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_body = render_template_string(html_template,
                achievement_type=achievement_type,
                details=details
            )
            
            return EmailService.send_email(user.email, subject, html_body)
            
        except Exception as e:
            logging.error(f"Failed to send achievement notification to user {user.id}: {e}")
            return False
