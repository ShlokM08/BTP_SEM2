from pymongo import MongoClient
import os
import json
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()
#publish
MONGO_URI = os.getenv('MONGODB_URI')

client = MongoClient(MONGO_URI)

# Now Selecting a Database to connect to
db = client['kushal_maa_data']

# Defining the groups collection
groups_collection = db["groups"]

# Defining the collections
whatsapp_collection = db['whatsapp_data']

# Defining the Zoom Audio Transcript Data
zoom_trancript_collection = db['zoom_audio_transcript']

# Defining the Zoom Chatbox Data Collection
zoom_chatbox_collection = db['zoom_chatbox']

# Defining the Zoom Attendence Data Collection
zoom_attendende_collection = db['zoom_attendence']

# Defining the User's Collection
# This database is hard coded and will be defined by the admin by hand
users_collection = db['users']

# Loading Initial users from the "default_users.json" file
def insert_initial_users_from_file(file_path):
    """Insert users from JSON file if database is empty"""
    if users_collection.count_documents({}) == 0:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                default_users = json.load(file)
                
                if isinstance(default_users, list):
                    for user in default_users:
                        if 'start_date' in user and '$date' in user['start_date']:
                            user['start_date'] = datetime.fromisoformat(
                                user['start_date']['$date'].replace('Z', '+00:00')
                            )
                    users_collection.insert_many(default_users)
                    print("Default users loaded successfully!")
                else:
                    print("Invalid JSON format: not a list")
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in file: {str(e)}")
        except Exception as e:
            print(f"Error loading users: {str(e)}")
