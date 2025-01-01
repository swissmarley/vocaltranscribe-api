import os
import sys
from app import app, db
from models import User, APIKey, RequestLog

with app.app_context():
    db.create_all()
    print("Database created successfully.")