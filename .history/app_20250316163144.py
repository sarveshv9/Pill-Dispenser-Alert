from flask import Flask, render_template, request, jsonify
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
    
@app.route('/')  # Add this route for the home page
def home():
    return "Welcome to the Pill Dispenser!"

@app.route('/upcoming')
def upcoming():
    return render_template('upcoming.html')

@app.route('/add_alarm', methods=['POST'])
def add_alarm():
    data = request.json
    new_alarm = Alarm(
        medicine=data['medicine'],
        time=data['time'],
        image=data['image']
    )
    db.session.add(new_alarm)
    db.session.commit()
    return jsonify({'message': 'Alarm added successfully'}), 201

@app.route('/get_upcoming_alarms', methods=['GET'])
def get_upcoming_alarms():
    now = datetime.now().strftime('%H:%M')
    alarms = Alarm.query.filter_by(completed=False).all()
    upcoming_alarms = [
        {'id': alarm.id, 'medicine': alarm.medicine, 'time': alarm.time, 'image': alarm.image}
        for alarm in alarms if alarm.time >= now
    ]
    return jsonify(upcoming_alarms)

@app.route('/mark_alarm_completed', methods=['POST'])
def mark_alarm_completed():
    data = request.json
    alarm = Alarm.query.get(data['id'])
    if alarm:
        alarm.completed = True
        db.session.commit()
        return jsonify({'message': 'Alarm marked as completed'})
    return jsonify({'error': 'Alarm not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
