from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from config import SECRET_KEY
from auth import generate_token
from middleware import token_required
from bson import ObjectId  # Import ObjectId to handle MongoDB _id
from model.user_model import create_user, user_exists

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://satyamjha9911:KOH4b6stO7WmHIJt@comclassdb.2moas.mongodb.net/?retryWrites=true&w=majority&appName=comclassdb"
app.config["SECRET_KEY"] = SECRET_KEY
mongo = PyMongo(app)



@app.route('/test_connection', methods=['GET'])
def test_connection():
    try:
        mongo.db.command('ping')  # A simple command to check connection
        return jsonify({"message": "MongoDB is connected"}), 200
    except Exception as e:
        return jsonify({"error": f"MongoDB connection failed: {str(e)}"}), 500


# Endpoint to register a user
@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')
    confirm_pass = request.json.get('confirmPass')
    name = request.json.get('name')
    phone = request.json.get('phone')
    interests = request.json.get('interests')  # Assuming interests is passed as a list
    experties = request.json.get('experties')  # Assuming experties is passed as a list

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

# Endpoint to login
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

# Endpoint to get user profile
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

# Endpoint to find users who are experts in the same interest
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

# Accept friend request
@app.route('/friend_requests/accept/<string:request_id>', methods=['POST'])
@token_required
def accept_friend_request(user_id, request_id):
    friend_request = mongo.db.friend_requests.find_one({"_id": ObjectId(request_id)})

    if not friend_request or friend_request["to_user"] != ObjectId(user_id):
        return jsonify({"error": "Friend request not found"}), 404

    mongo.db.friend_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "accepted"}}
    )

    return jsonify({"message": "Friend request accepted"}), 200

# Reject friend request
@app.route('/friend_requests/reject/<string:request_id>', methods=['POST'])
@token_required
def reject_friend_request(user_id, request_id):
    friend_request = mongo.db.friend_requests.find_one({"_id": ObjectId(request_id)})

    if not friend_request or friend_request["to_user"] != ObjectId(user_id):
        return jsonify({"error": "Friend request not found"}), 404

    mongo.db.friend_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "rejected"}}
    )

    return jsonify({"message": "Friend request rejected"}), 200



# Show friend requests (both sent and received)
@app.route('/friend_requests', methods=['GET'])
@token_required
def show_friend_requests(user_id):
    # Find all friend requests where the user is either the sender or the receiver
    sent_requests = mongo.db.friend_requests.find({"from_user": ObjectId(user_id)})
    received_requests = mongo.db.friend_requests.find({"to_user": ObjectId(user_id)})

    # Format the data for sent requests
    sent_list = []
    for request in sent_requests:
        target_user = mongo.db.users.find_one({"_id": request["to_user"]})
        sent_list.append({
            "request_id": str(request["_id"]),
            "to_user": {
                "user_id": str(target_user["_id"]),
                "name": target_user["name"],
                "email": target_user["email"]
            },
            "status": request["status"]
        })

    # Format the data for received requests
    received_list = []
    for request in received_requests:
        from_user = mongo.db.users.find_one({"_id": request["from_user"]})
        received_list.append({
            "request_id": str(request["_id"]),
            "from_user": {
                "user_id": str(from_user["_id"]),
                "name": from_user["name"],
                "email": from_user["email"]
            },
            "status": request["status"]
        })

    return jsonify({
        "sent_requests": sent_list,
        "received_requests": received_list
    }), 200


# Show friends
@app.route('/friends', methods=['GET'])
@token_required
def show_friends(user_id):
    # Find all accepted friend requests where the user is either the sender or receiver
    accepted_requests = mongo.db.friend_requests.find({
        "$or": [
            {"from_user": ObjectId(user_id), "status": "accepted"},
            {"to_user": ObjectId(user_id), "status": "accepted"}
        ]
    })

    # List to store complete friends' data
    friends_list = []
    for request in accepted_requests:
        # Determine the friend's user_id
        friend_id = (
            request["to_user"] if request["from_user"] == ObjectId(user_id) else request["from_user"]
        )

        # Fetch friend's complete details
        friend = mongo.db.users.find_one({"_id": friend_id})
        if friend:
            # Convert MongoDB ObjectId to string and add friend to the list
            friend["_id"] = str(friend["_id"])  # Convert ObjectId to string
            friends_list.append(friend)

    return jsonify({"friends": friends_list}), 200


if __name__ == '__main__':
    app.run(debug=True)
