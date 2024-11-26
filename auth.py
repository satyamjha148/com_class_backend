# auth.py
import jwt
import datetime
from flask import current_app

# Function to generate JWT token
def generate_token(user_id, email):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    token = jwt.encode({'user_id': str(user_id), 'email': email, 'exp': expiration_time}, current_app.config["SECRET_KEY"], algorithm='HS256')
    return token
