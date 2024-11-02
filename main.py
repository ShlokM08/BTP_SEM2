import streamlit as st
from dotenv import load_dotenv
from auth import *
from database import *
from admin_features import *
from moderator_features import *
import os
from pymongo import MongoClient
import base64

# Load the environment variables first
load_dotenv()
default_users_path = os.getenv("DEFAULT_USERS_PATH")

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
        /* Background Image */
        .stApp {{
           background-image: url("data:image/jpeg;base64,{base64_image}");
           background-size: cover;
           background-position: center;
           background-attachment: fixed;
           background-color: transparent;
        }}

        /* Font and Title Styling */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        * {{
            font-family: 'Roboto', sans-serif;
            color: white !important;
        }}
        
        h1.title-style {{
            font-size: 2.5em;
            text-align: center;
            font-weight: 700;
            color: white;
        }}

        p.subtitle-style {{
            font-size: 1.0em;
            text-align: center;
            font-weight: 400;
            color: white;
        }}

        /* Add space above the input field label */
        .stTextInput > label {{
            margin-top: 40px;  
            font-size: 1em;
            color: white;
        }}

        /* Button Styling */
        .stButton > button {{
            background-color: #FF69B4;  /* Pink */
            color: white;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
        }}
        .stButton > button:hover {{
            background-color: #FF1493;  /* Darker pink */
            color: white;
        }}

        /* Input Field Styling */
        .stTextInput > div > input {{
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid white;
            border-radius: 8px;
            color: white;
            font-size: 16px;
            padding: 10px;
        }}

        /* Error and Warning Message Styling */
        .stAlert {{
            color: #FF6347;  /* Tomato color for error/warning messages */
            font-weight: bold;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# Initialize database
def initialize_database():
    if 'client' not in st.session_state or st.session_state.client is None:
        st.session_state.client = MongoClient(MONGO_URI)  # Ensure the client is always initialized
        st.session_state.db = st.session_state.client['kushal_maa_data']

def main():
    # Set background image and custom styles
    set_background("assets/Untitled design.jpg")
    
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
        # Transparent container for the login section
        st.markdown("<div class='transparent-container'>", unsafe_allow_html=True)
        
        # User input section
        email = st.text_input("Please Enter Your Email Id", placeholder="Enter your email")
        
        if st.button("Login", key="login_button"):
            if email:
                user = check_user(email)
                user_name = get_user_name(email)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_name
                    st.session_state.user_type = user["user_type"]
                    st.experimental_rerun()
                else:
                    st.error("User email id not registered. Please Contact Admin")
            else:
                st.warning("Please enter an email address.")
        
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
            st.experimental_rerun()

if __name__ == "__main__":
    main()