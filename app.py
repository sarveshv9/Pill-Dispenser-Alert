import os
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask App setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarms.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
db = SQLAlchemy(app)

# Alarm Model (updated with last_triggered column)
class Alarm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.String(10), nullable=True)
    end_date = db.Column(db.String(10), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    last_triggered = db.Column(db.DateTime, nullable=True)  # New column

# Motivation Tip Function using Gemini API
def get_motivation_tip(task_type="stay healthy"):
    try:
        prompt = f"Give me a short, motivational one-liner for someone trying to {task_type}."
        api_key = os.getenv("GEMINI_API_KEY")
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
            return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        print("🚨 Gemini API error:", e)
        return "You're doing great. Keep going!"

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

@app.route('/get_alarms')
def get_alarms():
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    
    alarms = Alarm.query.filter_by(completed=False).all()
    alarms_to_ring = []

    for alarm in alarms:
        if alarm.time == current_time:
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
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)