from app import db, Alarm

alarms = Alarm.query.all()
for alarm in alarms:
    print(alarm.id, alarm.medicine, alarm.time, alarm.completed)