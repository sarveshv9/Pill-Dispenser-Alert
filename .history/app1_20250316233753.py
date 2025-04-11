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
    image = db.Column(db.String(200), nullable=True)
    completed = db.Column(db.Boolean, default=False)



@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/upcoming')
def upcoming():
    now = datetime.now().strftime('%H:%M')
    alarms = Alarm.query.filter_by(completed=False).all()
    return render_template('upcoming.html', alarms=alarms)

@app.route('/completed')
def completed():
    completed_alarms = Alarm.query.filter_by(completed=True).all()
    return render_template('completed.html', alarms=completed_alarms)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
