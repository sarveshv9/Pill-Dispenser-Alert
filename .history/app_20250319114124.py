from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarms.db'
db = SQLAlchemy(app)

class Alarm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(10), nullable=False)  # Store in HH:MM format
    completed = db.Column(db.Boolean, default=False)

@app.route('/')
def show_login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == "admin" and password == "password":
        return redirect(url_for('dashboard'))  # Redirect to dashboard on success
    else:
        return render_template('login.html', error="Invalid credentials")

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/form')
def form():
    return render_template('form1.html')


@app.route('/upcoming')
def upcoming():
    now = datetime.now().strftime('%H:%M')

    # Fetch alarms that are not completed
    alarms = Alarm.query.filter_by(completed=False).all()

    for alarm in alarms:
        # If the alarm time has passed, mark it as completed
        if alarm.time < now:
            alarm.completed = True
            db.session.commit()

    # Fetch updated alarms list
    alarms = Alarm.query.filter_by(completed=False).all()
    
    return render_template('upcoming.html', alarms=alarms)

@app.route('/completed')
def completed():
    completed_alarms = Alarm.query.filter_by(completed=True).all()
    return render_template('completed.html', alarms=completed_alarms)

@app.route('/add_alarm', methods=['POST'])
def add_alarm():
    medicine = request.form.get('medicine')
    time = request.form.get('time')
    

    if medicine and time :
        new_alarm = Alarm(medicine=medicine, time=time)
        db.session.add(new_alarm)
        db.session.commit()

    return redirect(url_for('upcoming'))

@app.route('/pill')
def pill_form():
    return render_template('pill.html')

@app.route('/yoga')
def yoga_form():
    return render_template('yoga.html')

@app.route('/morning')
def morning_alarm():
    return render_template('morning.html')

@app.route('/sleeping')
def sleeping_alarm():
    return render_template('sleeping.html')

@app.route('/water')
def water_reminder():
    return render_template('water.html')

@app.route('/workout')
def workout_reminder():
    return render_template('workout.html')

@app.route('/categories')
def categories():
    return render_template('categories.html')



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
