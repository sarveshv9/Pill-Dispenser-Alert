from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import jsonify
from flask import jsonify, url_for

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarms.db'
db = SQLAlchemy(app)

class Alarm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    completed = db.Column(db.Boolean, default=False)

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

@app.route('/pill')
def pill_form():
    return render_template('pill.html')

@app.route('/add_pill_alarm', methods=['POST'])
def add_pill_alarm():
    name = request.form.get('medicine')
    time = request.form.get('time')
    new_alarm = Alarm(medicine=f"Pill - {name}", time=time)
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

@app.route('/upcoming')
def upcoming():
    now = datetime.now().strftime('%H:%M')
    alarms = Alarm.query.filter_by(completed=False).all()

    for alarm in alarms:
        if alarm.time < now:
            alarm.completed = True
            db.session.commit()

    return render_template('upcoming.html', alarms=alarms)
@app.route('/completed')
def completed():
    completed_alarms = Alarm.query.filter_by(completed=True).all()
    return render_template('completed.html', alarms=completed_alarms)
 
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

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)