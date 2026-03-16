# server/models.py (Example; you can also keep this in app.py)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy() # Initialize SQLAlchemy without the app

# Define the data model
class SystemData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(255), nullable=False)
    hostname = db.Column(db.String(255), nullable=False)
    model_number = db.Column(db.String(255))
    ip_address = db.Column(db.String(20))
    cpu_usage = db.Column(db.Float)
    ram_usage = db.Column(db.Float)
    software_benchmark = db.Column(db.Float)
    hardware_benchmark = db.Column(db.Float)
    overall_benchmark = db.Column(db.Float)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<SystemData(serial_number='{self.serial_number}', hostname='{self.hostname}')>"