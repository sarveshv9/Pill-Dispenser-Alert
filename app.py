import os
import requests
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

# Flask App setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarms.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
db = SQLAlchemy(app)

# Get Twilio credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER")

# Function to send WhatsApp notification via Twilio
def send_whatsapp_notification(message, pill_name=None):
    """Send WhatsApp notification with optional pill image using Twilio WhatsApp Sandbox"""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]):
        print("Twilio credentials not properly configured. WhatsApp not sent.")
        return False
        
    # Get WhatsApp sandbox numbers from environment variables
    TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
    TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")
        
    if not all([TWILIO_WHATSAPP_FROM, TWILIO_WHATSAPP_TO]):
        print("WhatsApp sandbox numbers not configured. Check your .env file.")
        return False
        
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                
        # If pill name is provided, try to send an image
        if pill_name:
            # Use a guaranteed working test image from Twilio's own domain
            # This should work in the WhatsApp sandbox
            test_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Amoxicillin.JPG/330px-Amoxicillin.JPG"
            
            print(f"Sending WhatsApp with test image URL: {test_image}")
            
            # Send message with test image
            whatsapp_message = client.messages.create(
                body=f"{message} (Pill: {pill_name})",
                from_=TWILIO_WHATSAPP_FROM,
                to=TWILIO_WHATSAPP_TO,
                media_url=[test_image]
            )
        else:
            # Send a text-only message
            whatsapp_message = client.messages.create(
                body=message,
                from_=TWILIO_WHATSAPP_FROM,
                to=TWILIO_WHATSAPP_TO
            )
                
        print(f"WhatsApp notification sent successfully: {whatsapp_message.sid}")
        return True
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")
        return False                  
# Alarm Model (updated with last_triggered column)
class Alarm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.String(10), nullable=True)
    end_date = db.Column(db.String(10), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    last_triggered = db.Column(db.DateTime, nullable=True)

# New database models for the Health Habit Genome Analyzer
class HealthMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=1)  # We'll use a default user for simplicity
    metric_type = db.Column(db.String(50), nullable=False)  # 'sleep', 'mood', 'energy', etc.
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.Text, nullable=True)

class HealthInsight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=1)
    insight_type = db.Column(db.String(50), nullable=False)  # 'correlation', 'pattern', 'recommendation'
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float, default=0.5)
    generated_at = db.Column(db.DateTime, default=datetime.now)
    is_helpful = db.Column(db.Boolean, nullable=True)  # User feedback

# Motivation Tip Function using Gemini API
def get_motivation_tip(task_type="stay healthy"):
    try:
        prompt = f"Give me a short, motivational one-liner for someone trying to {task_type}."
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            return "You're doing great! Keep up with your health routine."
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                return data['candidates'][0]['content']['parts'][0].get('text', 'No response text')
            else:
                return "🧠 No response text found from Gemini."
        else:
            return f"Every step you take toward better health is a victory. Keep going!"

    except Exception as e:
        print("🚨 Gemini API error:", e)
        return "You're doing great. Keep going!"

# Health Genome Helper Functions
def generate_health_overview_charts():
    """Generate visualizations of health metrics over time"""
    charts = {}
    
    # Get all metrics from the past 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    metrics = HealthMetric.query.filter(HealthMetric.timestamp >= thirty_days_ago).all()
    
    if not metrics:
        # Create a placeholder chart if no data
        plt.figure(figsize=(10, 4))
        plt.plot([0, 1], [0, 0], 'r-', alpha=0)  # Create an empty plot
        plt.title('No Data Available Yet')
        plt.xticks([])
        plt.yticks([])
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        charts['placeholder'] = base64.b64encode(image_png).decode('utf-8')
        return charts
    
    # Create a dataframe from metrics
    df = pd.DataFrame([{
        'metric_type': m.metric_type,
        'value': m.value,
        'date': m.timestamp.date(),
        'full_timestamp': m.timestamp
    } for m in metrics])
    
    # Generate charts for each metric type
    for metric_type in df['metric_type'].unique():
        metric_data = df[df['metric_type'] == metric_type]
        
        # Create a time series plot even with just 1-2 data points
        plt.figure(figsize=(10, 4))
        
        # Set a consistent style for all charts
        sns.set_style("whitegrid")
        
        # Plot the data points
        sns.lineplot(data=metric_data, x='full_timestamp', y='value', marker='o', color='#1976D2')
        
        # Add a trend line if enough data points
        if len(metric_data) >= 3:
            # Simple trend line using polynomial fit
            x = np.array([(ts - metric_data['full_timestamp'].min()).total_seconds() 
                        for ts in metric_data['full_timestamp']])
            y = metric_data['value'].values
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            plt.plot(metric_data['full_timestamp'], p(x), "r--", alpha=0.7)
        
        plt.title(f'{metric_type.capitalize()} Over Time', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel(f'{metric_type.capitalize()} Value', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert plot to base64 string for embedding in HTML
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        chart = base64.b64encode(image_png).decode('utf-8')
        charts[metric_type] = chart
    
    return charts

def analyze_health_correlations():
    """Analyze correlations between different health metrics and medication adherence"""
    correlations = []
    
    # Get all metrics (no date filtering to ensure we have data)
    metrics = HealthMetric.query.all()
    
    # Get all alarms with completion data
    alarms = Alarm.query.filter(Alarm.last_triggered != None).all()
    
    if len(metrics) < 5 or not alarms:
        # Create placeholder correlations if not enough data
        default_correlations = [
            {
                'metric': 'sleep',
                'correlation': 0.65,
                'description': "Sleep quality tends to be associated with better medication adherence",
                'strength': 0.65,
                'confidence': 'Moderate'
            },
            {
                'metric': 'mood',
                'correlation': 0.55,
                'description': "Positive mood often correlates with consistent medication taking",
                'strength': 0.55,
                'confidence': 'Moderate'
            },
            {
                'metric': 'energy',
                'correlation': 0.48,
                'description': "Higher energy levels show some relation to better medication adherence",
                'strength': 0.48,
                'confidence': 'Weak'
            }
        ]
        return default_correlations
    
    # Create dataframes
    metrics_df = pd.DataFrame([{
        'metric_type': m.metric_type,
        'value': m.value,
        'date': m.timestamp.date()
    } for m in metrics])
    
    alarms_df = pd.DataFrame([{
        'medicine': a.medicine,
        'completed': a.completed,
        'date': a.last_triggered.date() if a.last_triggered else None
    } for a in alarms if a.last_triggered])
    
    # Group metrics by date and type
    metrics_pivot = metrics_df.pivot_table(
        index='date', 
        columns='metric_type', 
        values='value', 
        aggfunc='mean'
    ).reset_index()
    
    # Calculate medication adherence by date
    adherence_by_date = alarms_df.groupby('date')['completed'].mean().reset_index()
    adherence_by_date.columns = ['date', 'adherence_rate']
    
    # Merge datasets on date
    combined_df = pd.merge(metrics_pivot, adherence_by_date, on='date', how='inner')
    
    # Calculate correlations if enough data
    if len(combined_df) >= 3:
        correlation_matrix = combined_df.corr()
        
        # Extract correlations with adherence
        if 'adherence_rate' in correlation_matrix.columns:
            adherence_correlations = correlation_matrix['adherence_rate'].drop('adherence_rate')
            
            for metric, corr_value in adherence_correlations.items():
                if not pd.isna(corr_value):
                    strength = abs(corr_value)
                    direction = "positive" if corr_value > 0 else "negative"
                    
                    if strength >= 0.6:
                        confidence = "Strong"
                    elif strength >= 0.3:
                        confidence = "Moderate"
                    else:
                        confidence = "Weak"
                    
                    correlations.append({
                        'metric': metric,
                        'correlation': round(corr_value, 2),
                        'description': f"{confidence} {direction} correlation between {metric} and medication adherence",
                        'strength': strength,
                        'confidence': confidence
                    })
    
    # If no meaningful correlations found, add placeholder
    if not correlations:
        correlations.append({
            'metric': 'sleep',
            'correlation': 0.65,
            'description': "Sleep quality tends to be associated with better medication adherence",
            'strength': 0.65,
            'confidence': 'Moderate'
        })
    
    # Sort by correlation strength
    correlations.sort(key=lambda x: x['strength'], reverse=True)
    
    return correlations

def analyze_patterns_and_generate_insights():
    """Analyze patterns in health data and generate insights"""
    # Get historical data
    metrics = HealthMetric.query.all()
    alarms = Alarm.query.all()
    
    if not metrics or len(metrics) < 5:
        # Add a default insight if not enough data
        existing = HealthInsight.query.filter_by(title="Getting Started").first()
        
        if not existing:
            new_insight = HealthInsight(
                insight_type="recommendation",
                title="Getting Started",
                description="Track your health metrics consistently for at least a week to start seeing personalized patterns and recommendations.",
                confidence_score=0.9
            )
            db.session.add(new_insight)
            db.session.commit()
        return
    
    # Create dataframe for analysis
    metrics_df = pd.DataFrame([{
        'id': m.id,
        'metric_type': m.metric_type,
        'value': m.value,
        'timestamp': m.timestamp,
        'hour': m.timestamp.hour,
        'day_of_week': m.timestamp.weekday()
    } for m in metrics])
    
    # Group metrics by type
    metric_types = metrics_df['metric_type'].unique()
    
    for metric_type in metric_types:
        type_df = metrics_df[metrics_df['metric_type'] == metric_type]
        
        if len(type_df) < 3:
            continue
            
        # Find optimal times (when values are best)
        hourly_average = type_df.groupby('hour')['value'].mean()
        best_hour = hourly_average.idxmax() if metric_type in ['energy', 'mood'] else hourly_average.idxmin()
        
        # Find weekly patterns
        weekly_average = type_df.groupby('day_of_week')['value'].mean()
        best_day = weekly_average.idxmax() if metric_type in ['energy', 'mood'] else weekly_average.idxmin()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Generate insight
        insight_title = f"Optimal timing for {metric_type}"
        insight_desc = f"Your {metric_type} levels tend to be best at {best_hour}:00 and on {days[best_day]}s."
        
        # Check if similar insight already exists
        existing = HealthInsight.query.filter_by(title=insight_title).first()
        if existing:
            existing.description = insight_desc
            existing.generated_at = datetime.now()
        else:
            new_insight = HealthInsight(
                insight_type="pattern",
                title=insight_title,
                description=insight_desc,
                confidence_score=0.7 if len(type_df) > 10 else 0.5
            )
            db.session.add(new_insight)
    
    # Look for medication adherence patterns
    if alarms:
        completed_alarms = [a for a in alarms if a.completed and a.last_triggered]
        
        if completed_alarms:
            # Analyze times of day with highest adherence
            hour_counts = Counter([a.last_triggered.hour for a in completed_alarms])
            total_by_hour = {}
            
            for a in alarms:
                if a.last_triggered:
                    hour = a.last_triggered.hour
                    total_by_hour[hour] = total_by_hour.get(hour, 0) + 1
            
            if total_by_hour:  # Make sure we have data
                adherence_by_hour = {hour: hour_counts.get(hour, 0) / total_by_hour.get(hour, 1) 
                                  for hour in total_by_hour.keys()}
                
                if adherence_by_hour:  # Double-check we have valid data
                    best_adherence_hour = max(adherence_by_hour.items(), key=lambda x: x[1])[0]
                    worst_adherence_hour = min(adherence_by_hour.items(), key=lambda x: x[1])[0]
                    
                    # Generate insights about adherence patterns
                    insight_title = "Medication adherence patterns"
                    insight_desc = f"You tend to be most consistent with medications at {best_adherence_hour}:00 " \
                                 f"and struggle most at {worst_adherence_hour}:00."
                    
                    existing = HealthInsight.query.filter_by(title=insight_title).first()
                    if existing:
                        existing.description = insight_desc
                        existing.generated_at = datetime.now()
                    else:
                        new_insight = HealthInsight(
                            insight_type="pattern",
                            title=insight_title,
                            description=insight_desc,
                            confidence_score=0.6
                        )
                        db.session.add(new_insight)
    
    db.session.commit()
    
    # Generate recommendations based on patterns
    generate_recommendations()

def generate_recommendations():
    """Generate personalized health recommendations based on insights and patterns"""
    recommendations = []
    
    # Get recent metrics and insights
    recent_metrics = HealthMetric.query.order_by(HealthMetric.timestamp.desc()).limit(100).all()
    insights = HealthInsight.query.all()
    
    if not recent_metrics or len(recent_metrics) < 5:
        # Create default recommendations if not enough data
        default_recommendations = [
            {
                'title': "Consistent Tracking",
                'description': "Start by tracking your health metrics at the same time each day for more accurate insights.",
                'priority': 'high'
            },
            {
                'title': "Medication Reminder Setup",
                'description': "Place your medication in a visible spot or set up physical reminders alongside app notifications.",
                'priority': 'medium'
            },
            {
                'title': "Morning Routine",
                'description': "Consider taking morning medications with breakfast to establish a consistent routine.",
                'priority': 'medium'
            }
        ]
        return default_recommendations
    
    # Create metric dataframe
    metrics_df = pd.DataFrame([{
        'metric_type': m.metric_type,
        'value': m.value,
        'timestamp': m.timestamp
    } for m in recent_metrics])
    
    # Check for trends in each metric type
    for metric_type in metrics_df['metric_type'].unique():
        type_df = metrics_df[metrics_df['metric_type'] == metric_type].sort_values('timestamp')
        
        if len(type_df) < 5:
            continue
        
        # Calculate moving average
        values = type_df['value'].values
        if len(values) >= 5:
            recent_avg = np.mean(values[-5:])
            older_avg = np.mean(values[:-5])
            
            if abs(recent_avg - older_avg) / (older_avg if older_avg != 0 else 1) > 0.15:  # 15% change
                direction = "improving" if (recent_avg > older_avg and metric_type in ['energy', 'mood']) or \
                                         (recent_avg < older_avg and metric_type not in ['energy', 'mood']) else "declining"
                
                if direction == "declining":
                    # Generate recommendation
                    if metric_type == 'sleep':
                        recommendations.append({
                            'title': "Sleep Optimization",
                            'description': "Your sleep quality has been declining. Consider setting a consistent sleep schedule and avoiding screens 1 hour before bedtime.",
                            'priority': 'high'
                        })
                    elif metric_type == 'energy':
                        recommendations.append({
                            'title': "Energy Boosting",
                            'description': "Your energy levels have been lower recently. Try adding a 10-minute morning stretching routine and ensure consistent medication timing.",
                            'priority': 'medium'
                        })
                    elif metric_type == 'mood':
                        recommendations.append({
                            'title': "Mood Enhancement",
                            'description': "Your mood patterns show a recent decline. Consider incorporating 15 minutes of mindfulness practice and ensure you're taking medications consistently.",
                            'priority': 'high'
                        })
                    elif metric_type == 'stress':
                        recommendations.append({
                            'title': "Stress Management",
                            'description': "Your stress levels have been increasing. Consider adding short breathing exercises throughout the day and maintain medication routines.",
                            'priority': 'high'
                        })
                    elif metric_type == 'focus':
                        recommendations.append({
                            'title': "Focus Improvement",
                            'description': "Your focus scores have been decreasing. Try working in 25-minute focused sessions with short breaks and ensure medication adherence.",
                            'priority': 'medium'
                        })
    
    # Look for medication adherence recommendations
    alarms = Alarm.query.filter(Alarm.completed == False, Alarm.last_triggered != None).all()
    missed_meds = [a for a in alarms if a.last_triggered and (datetime.now() - a.last_triggered).days < 7]
    
    if missed_meds:
        missed_types = Counter([m.medicine.split(' - ')[0] if ' - ' in m.medicine else 'Other' for m in missed_meds])
        if missed_types:
            most_missed = missed_types.most_common(1)[0][0]
            
            recommendations.append({
                'title': f"Improve {most_missed} Adherence",
                'description': f"You've missed several {most_missed.lower()} reminders recently. " \
                              f"Try setting up a specific area in your home dedicated to {most_missed.lower()} activities.",
                'priority': 'high'
            })
    
    # Check for correlations between metrics and adherence to generate recommendations
    correlations = analyze_health_correlations()
    
    for corr in correlations:
        if corr['strength'] > 0.5:
            metric = corr['metric']
            if corr['correlation'] > 0:
                recommendations.append({
                    'title': f"Leverage {metric.capitalize()} Connection",
                    'description': f"Higher {metric} levels are strongly associated with better medication adherence. " \
                                  f"Consider scheduling important medications during your peak {metric} times.",
                    'priority': 'medium'
                })
    
    # If no recommendations were generated, add default ones
    if not recommendations:
        recommendations.append({
            'title': "Establish Routine",
            'description': "Set a consistent daily routine for your medications to increase adherence.",
            'priority': 'medium'
        })
    
    # Sort recommendations by priority
    priority_rank = {'high': 0, 'medium': 1, 'low': 2}
    recommendations.sort(key=lambda x: priority_rank.get(x.get('priority', 'low'), 3))
    
    # Save new recommendations as insights
    for rec in recommendations[:3]:  # Save top 3 recommendations
        existing = HealthInsight.query.filter_by(title=rec['title']).first()
        if existing:
            existing.description = rec['description']
            existing.generated_at = datetime.now()
        else:
            new_insight = HealthInsight(
                insight_type="recommendation",
                title=rec['title'],
                description=rec['description'],
                confidence_score=0.7 if rec['priority'] == 'high' else 0.5
            )
            db.session.add(new_insight)
    
    db.session.commit()
    
    return recommendations

# Add this route to quickly generate sample data for testing
@app.route('/generate_sample_data')
def generate_sample_data():
    """Generate sample health data for demonstration purposes"""
    # Create sample metrics for the past 30 days
    for days_ago in range(30, 0, -1):
        date = datetime.now() - timedelta(days=days_ago)
        
        # Add sleep data (slightly random values between 3-9)
        sleep_value = round(5 + 2 * np.random.randn(), 1)
        sleep_value = max(3, min(9, sleep_value))  # Keep between a 3-9
        db.session.add(HealthMetric(
            metric_type="sleep",
            value=sleep_value,
            timestamp=date.replace(hour=8, minute=0),
            notes="Sample sleep data"
        ))
        
        # Add mood data (gradually improving trend)
        base_mood = 5 + days_ago/15  # Trending upward as days_ago decreases
        mood_value = round(max(1, min(10, base_mood + np.random.randn())), 1)
        db.session.add(HealthMetric(
            metric_type="mood",
            value=mood_value,
            timestamp=date.replace(hour=12, minute=0),
            notes="Sample mood data"
        ))
        
        # Add energy data (correlated with mood but with some variance)
        energy_value = round(max(1, min(10, mood_value * 0.8 + 1 + np.random.randn())), 1)
        db.session.add(HealthMetric(
            metric_type="energy",
            value=energy_value,
            timestamp=date.replace(hour=16, minute=0),
            notes="Sample energy data"
        ))
        
        # Add stress data (inversely correlated with sleep)
        stress_value = round(max(1, min(10, 10 - sleep_value + np.random.randn())), 1)
        db.session.add(HealthMetric(
            metric_type="stress",
            value=stress_value,
            timestamp=date.replace(hour=18, minute=0),
            notes="Sample stress data"
        ))
        
        # Add focus data (correlated with sleep)
        focus_value = round(max(1, min(10, sleep_value * 0.7 + 2 + np.random.randn())), 1)
        db.session.add(HealthMetric(
            metric_type="focus",
            value=focus_value,
            timestamp=date.replace(hour=14, minute=0),
            notes="Sample focus data"
        ))
    
    db.session.commit()
    
    # Create some alarms and mark some as completed
    medicines = ["Vitamin D", "Blood Pressure Medication", "Antihistamine", "Pain Reliever"]
    
    # Add completed alarms from the past
    for days_ago in range(20, 0, -1):
        date = datetime.now() - timedelta(days=days_ago)
        for med in medicines:
            # 70% chance of completion
            completed = np.random.random() > 0.3
            alarm = Alarm(
                medicine=f"Pill - {med}",
                time=f"{np.random.randint(7, 20):02d}:00",
                completed=completed,
                last_triggered=date.replace(hour=np.random.randint(7, 20))
            )
            db.session.add(alarm)
    
    # Add some current alarms
    for med in medicines:
        alarm = Alarm(
            medicine=f"Pill - {med}",
            time=f"{np.random.randint(7, 20):02d}:00",
            completed=False
        )
        db.session.add(alarm)
    
    db.session.commit()
    
    # Force analysis to run with the new data
    analyze_patterns_and_generate_insights()
    
    return redirect(url_for('health_genome'))

# Routes
@app.route('/')
def show_login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == "admin" and password == "password":
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error="Invalid credentials")

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/motivation_tip')
def motivation_tip():
    tip = get_motivation_tip("take medicine")
    return jsonify({"tip": tip})

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/pill')
def pill_form():
    return render_template('pill.html')

@app.route('/add_pill_alarm', methods=['POST'])
def add_pill_alarm():
    name = request.form.get('medicine')
    time = request.form.get('time')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    image_file = request.files.get('image')

    image_filename = None
    if image_file and image_file.filename:
        image_filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    new_alarm = Alarm(
        medicine=f"Pill - {name}",
        time=time,
        start_date=start_date,
        end_date=end_date,
        image=image_filename
    )
    db.session.add(new_alarm)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/yoga')
def yoga_form():
    return render_template('yoga.html')

@app.route('/add_yoga_alarm', methods=['POST'])
def add_yoga_alarm():
    name = request.form.get('name')
    time = request.form.get('time')
    new_alarm = Alarm(medicine=f"Yoga - {name}", time=time)
    db.session.add(new_alarm)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/morning')
def morning_alarm():
    return render_template('morning.html')

@app.route('/add_morning_alarm', methods=['POST'])
def add_morning_alarm():
    name = request.form.get('name')
    time = request.form.get('time')
    new_alarm = Alarm(medicine=f"Morning - {name}", time=time)
    db.session.add(new_alarm)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/sleeping')
def sleeping_alarm():
    return render_template('sleeping.html')

@app.route('/add_sleeping_alarm', methods=['POST'])
def add_sleeping_alarm():
    name = request.form.get('name')
    time = request.form.get('sleep_time')
    new_alarm = Alarm(medicine=f"Sleep - {name}", time=time)
    db.session.add(new_alarm)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/water')
def water_reminder():
    return render_template('water.html')

@app.route('/add_water_alarm', methods=['POST'])
def add_water_alarm():
    name = request.form.get('name')
    time = request.form.get('time')
    new_alarm = Alarm(medicine=f"Water - {name}", time=time)
    db.session.add(new_alarm)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/workout')
def workout_reminder():
    return render_template('workout.html')

@app.route('/add_workout_alarm', methods=['POST'])
def add_workout_alarm():
    name = request.form.get('name')
    time = request.form.get('time')
    new_alarm = Alarm(medicine=f"Workout - {name}", time=time)
    db.session.add(new_alarm)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_alarm', methods=['POST'])
def add_alarm():
    medicine = request.form.get('medicine')
    time = request.form.get('time')
    image_file = request.files.get('image')

    image_filename = None
    if image_file and image_file.filename:
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image_file.save(image_path)

    if medicine and time:
        new_alarm = Alarm(medicine=medicine, time=time, image=image_filename)
        db.session.add(new_alarm)
        db.session.commit()

    return redirect(url_for('upcoming'))

@app.route('/upcoming')
def upcoming():
    alarms = Alarm.query.filter_by(completed=False).all()
    return render_template('upcoming.html', alarms=alarms)

@app.route('/completed')
def completed():
    completed_alarms = Alarm.query.filter_by(completed=True).all()
    return render_template('completed.html', alarms=completed_alarms)

@app.route('/map')
def find_doctors():
    return render_template('map.html')

# Health Genome routes
@app.route('/genome')
def health_genome():
    # Get all health metrics and insights for display
    metrics = HealthMetric.query.order_by(HealthMetric.timestamp.desc()).limit(100).all()
    insights = HealthInsight.query.order_by(HealthInsight.generated_at.desc()).all()
    
    # Generate health overview visualizations
    overview_charts = generate_health_overview_charts()
    
    # Generate recent patterns and correlations
    correlations = analyze_health_correlations()
    
    # Get recommendations based on patterns
    recommendations = generate_recommendations()
    
    return render_template(
        'genome.html', 
        metrics=metrics,
        insights=insights, 
        overview_charts=overview_charts,
        correlations=correlations,
        recommendations=recommendations
    )

@app.route('/add_health_metric', methods=['POST'])
def add_health_metric():
    metric_type = request.form.get('metric_type')
    value = float(request.form.get('value'))
    notes = request.form.get('notes', '')
    
    new_metric = HealthMetric(
        metric_type=metric_type,
        value=value,
        notes=notes,
        timestamp=datetime.now()
    )
    
    db.session.add(new_metric)
    db.session.commit()
    
    # After adding new data, trigger analysis to generate new insights
    analyze_patterns_and_generate_insights()
    
    return redirect(url_for('health_genome'))

@app.route('/insight_feedback', methods=['POST'])
def insight_feedback():
    data = request.get_json()
    insight_id = data.get('insight_id')
    is_helpful = data.get('is_helpful')
    
    insight = HealthInsight.query.get(insight_id)
    if insight:
        insight.is_helpful = is_helpful
        db.session.commit()
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Insight not found"}), 404

@app.route('/get_alarms')
def get_alarms():
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    
    # Get alarms that should trigger now
    alarms = Alarm.query.filter_by(completed=False).all()
    alarms_to_ring = []

    for alarm in alarms:
        # Check if alarm time matches current time
        if alarm.time == current_time:
            # Update last_triggered timestamp
            alarm.last_triggered = now
            db.session.commit()
            
            # Format message for notification
            alarm_type = alarm.medicine.split(' - ')[0] if ' - ' in alarm.medicine else "Reminder"
            alarm_name = alarm.medicine.split(' - ')[1] if ' - ' in alarm.medicine else alarm.medicine
            message = f"REMINDER: It's time for your {alarm_type} - {alarm_name} at {alarm.time}"
            
            # Use the image name if available
            image_path = alarm.image if alarm.image else None
            
            # Send WhatsApp notification with image reference
            send_whatsapp_notification(message, image_path)
            
            alarms_to_ring.append({
                "id": alarm.id,
                "medicine": alarm.medicine,
                "time": alarm.time,
                "image": url_for('static', filename=f'uploads/{alarm.image}') if alarm.image else None
            })
    
    return jsonify(alarms_to_ring)

@app.route('/mark_alarm_done', methods=['POST'])
def mark_alarm_done():
    try:
        data = request.get_json()
        alarm_id = data.get('id')
        
        if alarm_id:
            alarm = Alarm.query.get(alarm_id)
            if alarm:
                alarm.completed = True
                alarm.last_triggered = datetime.now()  # Set the timestamp
                db.session.commit()
                return jsonify({"status": "success", "message": "Alarm marked as completed"})
            else:
                return jsonify({"status": "error", "message": "Alarm not found"}), 404
        else:
            time = data.get('time')
            medicine = data.get('medicine')
            
            if not time or not medicine:
                return jsonify({"status": "error", "message": "Missing time or medicine name"}), 400
                
            alarm = Alarm.query.filter(
                Alarm.time == time, 
                Alarm.medicine.in_([medicine, f"Pill - {medicine}", f"Water - {medicine}"]), 
                Alarm.completed == False
            ).first()
            
            if alarm:
                alarm.completed = True
                alarm.last_triggered = datetime.now()  # Set the timestamp
                db.session.commit()
                return jsonify({"status": "success", "message": "Alarm marked as completed"})
            else:
                return jsonify({"status": "error", "message": "Alarm not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_completed', methods=['POST'])
def delete_completed():
    data = request.get_json()
    if data.get('delete_all'):
        Alarm.query.filter_by(completed=True).delete()
    else:
        alarm_id = data.get('alarm_id')
        Alarm.query.filter_by(id=alarm_id, completed=True).delete()
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/clear_completed', methods=['POST'])
def clear_completed():
    # Delete all completed alarms older than 30 days
    threshold = datetime.now() - timedelta(days=30)
    Alarm.query.filter(Alarm.completed == True, Alarm.last_triggered < threshold).delete()
    db.session.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Check if Twilio is configured properly
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, USER_PHONE_NUMBER]):
        print("⚠️ WARNING: Twilio is not fully configured. SMS notifications will not work.")
        print("Please check your .env file and make sure all Twilio environment variables are set.")
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)