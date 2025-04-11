from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'pill_reminder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the database model
class PillReminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    pill_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.String(10), nullable=False)
    end_date = db.Column(db.String(10), nullable=False)
    alarm_time = db.Column(db.String(5), nullable=False)
    pill_photo = db.Column(db.String(200), nullable=True)
    snooze = db.Column(db.Boolean, default=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Route to display the form
@app.route('/')
def form1():
    return render_template('form1.html')

# Route to handle form submission
@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    name = request.form['name']
    pill_name = request.form['pillName']
    start_date = request.form['startDate']
    end_date = request.form['endDate']
    alarm_time = request.form['alarmTime']
    snooze = 'snooze' in request.form  # Checkbox returns 'on' if checked

    # Handling image upload
    pill_photo = request.files['pillPhoto']
    photo_filename = None
    if pill_photo and pill_photo.filename:
        upload_folder = os.path.join('static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)  # Ensure folder exists
        photo_filename = os.path.join(upload_folder, pill_photo.filename)
        pill_photo.save(photo_filename)

    # Save to the database
    new_reminder = PillReminder(
        name=name, pill_name=pill_name, start_date=start_date,
        end_date=end_date, alarm_time=alarm_time, pill_photo=photo_filename, snooze=snooze
    )
    db.session.add(new_reminder)
    db.session.commit()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
