from flask import Flask, jsonify
import sqlite3
from datetime import datetime

app = Flask(_name_)

def fetch_alarms(status):
    conn = sqlite3.connect("pill_dispenser.db")
    cursor = conn.cursor()
    
    if status == "Upcoming":
        current_time = datetime.now().strftime("%H:%M")
        cursor.execute("SELECT * FROM alarms WHERE status='Upcoming' AND alarm_time > ? ORDER BY alarm_time ASC", (current_time,))
    else:
        cursor.execute("SELECT * FROM alarms WHERE status='Completed' ORDER BY alarm_time DESC")

    alarms = cursor.fetchall()
    conn.close()

    return [
        {"id": alarm[0], "medicine": alarm[1], "time": alarm[2], "image": alarm[3]}
        for alarm in alarms
    ]

@app.route("/get_upcoming_alarms")
def get_upcoming_alarms():
    return jsonify(fetch_alarms("Upcoming"))

@app.route("/get_completed_alarms")
def get_completed_alarms():
    return jsonify(fetch_alarms("Completed"))

if _name_ == "_main_":
    app.run(debug=True)
