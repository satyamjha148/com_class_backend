# middleware.py
from functools import wraps
from flask import request, jsonify
import jwt
from config import SECRET_KEY

# Middleware to verify JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')  # Get Bearer token
        if not token:
            return jsonify({"error": "Token is missing!"}), 401

        try:
            decoded = jwt.decode(token.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
            user_id = decoded['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401

        return f(user_id, *args, **kwargs)
    return decorated
