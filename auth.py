from database import users_collection

def check_user(email):
    """Check if user exists and is active"""
    return users_collection.find_one({
        "email": email,
        "end_date": None  # Only active users
    })

def get_user_name(email):
    """Get user's name from email"""
    user = users_collection.find_one({"email": email})
    return user['name'] if user else None
