from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from config import MONGO_URI, SECRET_KEY
from auth import generate_token
from middleware import token_required
from bson import ObjectId
from model.user_model import create_user, user_exists

# Initialize the Flask app
app = Flask(__name__)

# Load the MongoDB URI and secret key from the config file
app.config["MONGO_URI"] = MONGO_URI
app.config["SECRET_KEY"] = SECRET_KEY

# Initialize the MongoDB connection
mongo = PyMongo(app)
client = MongoClient('mongodb+srv://satyamjha9911:KOH4b6stO7WmHIJt@comclassdb.2moas.mongodb.net/?retryWrites=true&w=majority&appName=comclassdb')
db = client['sample_airbnb']
collection = db.list_collections()
print(f'client is {collection}')

# Route to test MongoDB connection
@app.route('/test_connection', methods=['GET'])
def test_connection():
    try:
        client.admin.command('ping')  # Test MongoDB connection
        return jsonify({"message": "MongoDB is connected"}), 200
    except Exception as e:
        return jsonify({"error": f"MongoDB connection failed: {str(e)}"}), 500

# User registration route
@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')
    confirm_pass = request.json.get('confirmPass')
    name = request.json.get('name')
    phone = request.json.get('phone')
    interests = request.json.get('interests')  # List of interests
    experties = request.json.get('experties')  # List of experties

    if not email or not password or not confirm_pass or not name or not phone or not interests or not experties:
        return jsonify({"error": "All fields are required"}), 400

    if password != confirm_pass:
        return jsonify({"error": "Passwords do not match"}), 400

    if user_exists(mongo, email=email):
        return jsonify({"error": "Email is already registered"}), 400
    if user_exists(mongo, phone=phone):
        return jsonify({"error": "Phone number is already registered"}), 400

    hashed_password = generate_password_hash(password)

    if not isinstance(interests, list):
        return jsonify({"error": "Interests must be a list"}), 400
    if not isinstance(experties, list):
        return jsonify({"error": "Experties must be a list"}), 400

    create_user(mongo, email, hashed_password, name, phone, interests, experties)
    
    return jsonify({"message": "User registered successfully"}), 201

# Login route
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid password"}), 400

    token = generate_token(user['_id'], user['email'])

    return jsonify({"message": "Login successful", "token": token}), 200

# Route to get user profile
@app.route('/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "interests": user["interests"],
        "experties": user["experties"]
    }
    return jsonify({"user_data": user_data}), 200

# Route to find experts
@app.route('/experts', methods=['GET'])
@token_required
def find_experts(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    interests = user["interests"]

    experts_cursor = mongo.db.users.find({
        "experties": {"$in": interests},
        "_id": {"$ne": ObjectId(user_id)}
    })

    expert_list = []
    for expert in experts_cursor:
        expert_data = {
            "_id": str(expert["_id"]),
            "name": expert["name"],
            "email": expert["email"],
            "phone": expert["phone"],
            "interests": expert["interests"],
            "experties": expert["experties"],
        }
        expert_list.append(expert_data)

    if expert_list:
        return jsonify({"experts": expert_list}), 200
    else:
        return jsonify({"message": "No experts found in your interests"}), 404

# --- Friend Requests ---

# Send friend request
@app.route('/friend_requests/send/<string:target_user_id>', methods=['POST'])
@token_required
def send_friend_request(user_id, target_user_id):
    if user_id == target_user_id:
        return jsonify({"error": "You cannot send a friend request to yourself"}), 400

    target_user = mongo.db.users.find_one({"_id": ObjectId(target_user_id)})
    if not target_user:
        return jsonify({"error": "Target user not found"}), 404

    existing_request = mongo.db.friend_requests.find_one({
        "from_user": ObjectId(user_id),
        "to_user": ObjectId(target_user_id)
    })

    if existing_request:
        return jsonify({"error": "Friend request already sent"}), 400

    mongo.db.friend_requests.insert_one({
        "from_user": ObjectId(user_id),
        "to_user": ObjectId(target_user_id),
        "status": "pending"
    })

    return jsonify({"message": "Friend request sent"}), 201

# Other routes for accepting, rejecting, showing requests, and friends...

if __name__ == '__main__':
    app.run(debug=True)
