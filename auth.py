import jwt
import datetime
from config import SECRET_KEY

def generate_token(user_id, email):
    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Expiry time
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
