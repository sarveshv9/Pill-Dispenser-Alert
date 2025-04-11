from flask import Flask
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

# Create the database and table
with app.app_context():
    db.create_all()
    print("Database table created successfully!")
