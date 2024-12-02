import streamlit as st
from dotenv import load_dotenv
from auth import *
from database import *
from admin_features import *
from moderator_features import *
import os
from pymongo import MongoClient
import base64

st.set_page_config(layout="wide")

# Load environment variables
load_dotenv()
default_users_path = os.getenv("DEFAULT_USERS_PATH")
mongodb_uri = os.getenv("MONGODB_URI")
mongo_db_name = os.getenv("MONGO_DB_NAME")
mongo_collection = os.getenv("MONGO_COLLECTION")

# Function to encode image to base64
def get_base64_image(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    return encoded

# Add custom CSS with backdrop image and custom styles
def set_background(image_file):
    base64_image = get_base64_image(image_file)
    st.markdown(
        f"""
        <style>
        /* Background styling */
        .stApp {{
            background-image: url("data:image/jpeg;base64,{base64_image}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-color: rgba(0, 0, 0, 0.7); /* Add slight overlay */
            background-blend-mode: darken;
        }}

        /* Login box styling */
        .login-container {{
            background: rgba(255, 255, 255, 0.2); /* White semi-transparent */
            padding: 40px;
            border-radius: 15px;
            max-width: 400px;
            margin: 100px auto;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
            text-align: center;
            color: white;
        }}

        /* Title styling */
        .login-container h1 {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #FF69B4;
        }}

        .login-container p {{
            font-size: 1rem;
            margin-bottom: 20px;
        }}

        /* Input field styling */
        .stTextInput > div > input {{
            background: #333;
            border: 1px solid #555;
            border-radius: 8px;
            padding: 10px;
            font-size: 1rem;
            color: white;
            margin-bottom: 20px;
            width: 100%;
        }}

        /* Button styling */
        .stButton > button {{
            background-color: #FF69B4;
            color: white;
            font-size: 1rem;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            transition: background-color 0.3s ease;
        }}

        .stButton > button:hover {{
            background-color: #FF1493;
        }}

        /* Error styling */
        .stAlert {{
            background: rgba(255, 99, 71, 0.2);
            color: #FF6347;
            font-weight: bold;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Initialize database
def initialize_database():
    if 'client' not in st.session_state or st.session_state.client is None:
        st.session_state.client = MongoClient(mongodb_uri)  # Ensure the client is always initialized
        st.session_state.db = st.session_state.client[mongo_db_name]

def main():
    # Set background image and custom styles
    set_background("assets/bg3.jpg")
    
    st.markdown("<h1 class='title-style'>Kushal Maa Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle-style'>An Interactive Platform for Admins and Moderators</p>", unsafe_allow_html=True)
    
    # Initialize database connection
    initialize_database()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_name = None
        st.session_state.user_type = None

    if not st.session_state.logged_in:
        insert_initial_users_from_file(default_users_path)
        # Transparent container for the login section
        st.markdown("<div class='transparent-container'>", unsafe_allow_html=True)
        
        # User input section
        email = st.text_input("Please Enter Your Email Id", placeholder="Enter your email")
        password = st.text_input("Enter Password", type="password", placeholder="Enter your password")
        
        if st.button("Login", key="login_button"):
            if email and password:
                user = check_user(email)
                user_name = get_user_name(email)
                if user and password == "123":  # Validate password
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_name
                    st.session_state.user_type = user["user_type"]
                    st.session_state["reload"] = True
                elif not user:
                    st.error("User email id not registered. Please Contact Admin")
                else:
                    st.error("Incorrect password. Please try again.")
            else:
                st.warning("Please enter both email and password.")
        
        st.markdown("</div>", unsafe_allow_html=True)  # Close transparent container

    else:
        if st.session_state.user_type == "Admin":
            admin_main.admin_page(st.session_state.user_name)
        elif st.session_state.user_type == "Moderator":
            moderator_main.moderator_page(st.session_state.user_name)
        else:
            st.error("Invalid user type")
        
        if st.button("Logout", key="main_logout_button"):
            st.session_state.logged_in = False
            st.session_state.user_name = None
            st.session_state.user_type = None
            # Close the database connection
            if 'client' in st.session_state:
                st.session_state.client.close()
                del st.session_state.client
                del st.session_state.db
            st.session_state["reload"] = True


if __name__ == "__main__":
    main()
