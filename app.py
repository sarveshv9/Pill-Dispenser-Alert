import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarms.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
db = SQLAlchemy(app)

# Alarm Model
class Alarm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.String(10), nullable=True)
    end_date = db.Column(db.String(10), nullable=True)
    image = db.Column(db.String(200), nullable=True)  # Store image filename

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

@app.route('/categories')
def categories():
    return render_template('categories.html')

# Category: Pill Reminder
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

# Category: Yoga
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

# Category: Morning Alarm
@app.route('/morning_alarm')
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

# Category: Sleeping Alarm
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

# Category: Water Reminder
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

# Category: Workout Reminder
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

# General Add Alarm (Optional)
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

# Upcoming Alarms (with auto-complete logic)
@app.route('/upcoming')
def upcoming():
    now = datetime.now().strftime('%H:%M')
    alarms = Alarm.query.filter_by(completed=False).all()

    for alarm in alarms:
        if alarm.time < now:
            alarm.completed = True
            db.session.commit()

    return render_template('upcoming.html', alarms=alarms)

# Completed Alarms
@app.route('/completed')
def completed():
    completed_alarms = Alarm.query.filter_by(completed=True).all()
    return render_template('completed.html', alarms=completed_alarms)

# Get alarms for JS frontend
@app.route('/get_alarms')
def get_alarms():
    alarms = Alarm.query.filter_by(completed=False).all()
    alarms_data = []
    for alarm in alarms:
        alarm_data = {
            "medicine": alarm.medicine,
            "time": alarm.time,
            "image": url_for('static', filename='uploads/' + alarm.image) if alarm.image else None
        }
        alarms_data.append(alarm_data)
    return jsonify(alarms_data)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
