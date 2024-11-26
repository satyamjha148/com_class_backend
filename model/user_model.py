# models.py
from flask_pymongo import PyMongo

# Function to check if a user exists by email or phone
def user_exists(mongo, email=None, phone=None):
    if email:
        return mongo.db.users.find_one({"email": email})
    if phone:
        return mongo.db.users.find_one({"phone": phone})
    return None

# Function to create a new user
def create_user(mongo, email, password, name, phone, interests, experties):
    mongo.db.users.insert_one({
        "email": email,
        "password": password,
        "name": name,
        "phone": phone,
        "interests": interests,
        "experties": experties
    })
