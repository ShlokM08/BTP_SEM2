import streamlit as st
from pymongo import MongoClient
from .whatsapp_chat_parser import *
from .zoom_audio_service import ZoomAudioService, handle_zoom_audio_upload
from .zoom_chat_service import ZoomChatService, handle_zoom_chat_upload
from .zoom_attendence_service import ZoomAttendanceService, handle_zoom_attendance_upload
from database import *
import base64

# Function to encode image to base64
def get_base64_image(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    return encoded

# Set background and styles
def set_background(image_file):
    base64_image = get_base64_image(image_file)
    st.markdown(
        f"""
        <style>
        .stApp {{
           background-image: url("data:image/jpeg;base64,{base64_image}");
           background-size: cover;
           background-position: center;
           background-attachment: fixed;
           background-color: transparent;
        }}

        /* Sidebar styling */
        .sidebar {{
            width: 180px;
            position: fixed;
            top: 40px;
            left: 0;
            height: 100%;
            background-color: #333;
            padding-top: 20px;
            z-index: 1;
            overflow-x: hidden;
        }}
        .sidebar a {{
            padding: 10px 10px;
            text-decoration: none;
            font-size: 1em;
            color: white;
            display: block;
            transition: 0.3s;
        }}
        .sidebar a:hover {{
            background-color: #575757;
        }}

        /* Top bar styling */
        .topbar {{
            position: fixed;
            right: 0;
            top: 46px;
            width: calc(100% - 220px);
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 2;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.5);
            height: 50px;
        }}
        .topbar .search-box {{
            background-color: white;
            color: black;
            border-radius: 5px;
            padding: 5px 10px;
            width: 200px;
            font-size: 0.9em;
        }}
        .profile-icon {{
            border-radius: 50%;
            background-color: #575757;
            color: white;
            padding: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 0.9em;
            position: relative;
        }}

        /* Dropdown for profile icon */
        .dropdown {{
            display: none;
            position: absolute;
            top: 35px;
            right: 0;
            background-color: #333;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
        }}
        .profile-icon:hover .dropdown {{
            display: block;
        }}
        .dropdown button {{
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            font-size: 0.9em;
            cursor: pointer;
        }}
        .dropdown button:hover {{
            background-color: #ff7878;
        }}

        /* Main content styling */
        .main-content {{
            margin-left: 220px;
            padding-top: 100px; /* Adjusted to move 'Welcome' higher */
            padding-right: 20px;
            color: white;
            font-size: 1.3em; /* Smaller font size for 'Welcome' */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Initialize database
client = MongoClient(MONGO_URI)
db = client['kushal_maa_data']
st.session_state.db = db

zoom_chat_service = ZoomChatService(st.session_state.db)

def get_moderator_groups(db, user_name):
    user = db['users'].find_one({"name": user_name, "user_type": "Moderator"})
    if user and "current_groups" in user:
        return user['current_groups']
    return []

def handle_whatsapp_upload(whatsapp_service, group_name, uploaded_file, user_name):
    try:
        content = uploaded_file.getvalue().decode('utf-8')
        process_result = whatsapp_service.process_chat_file(content)
        
        if process_result["status"] == "error":
            st.error(f"Error processing file: {process_result['message']}")
            return
        st.write("Preview of parsed data:")
        st.write(process_result["message"])

        if st.button(f"Save {group_name}'s WhatsApp chat to database"):
            save_result = whatsapp_service.save_chat_data(
                group_name,
                process_result["data"],
                user_name
            )
            
            if save_result["status"] == "success":
                st.success(f"WhatsApp chat for {group_name} uploaded and saved successfully!")
            else:
                st.error(f"Error saving to database: {save_result['message']}")
                
    except Exception as e:
        st.error(f"Error handling WhatsApp chat: {str(e)}")

def moderator_page(user_name):
    initials = ''.join([part[0] for part in user_name.split()]).upper()
    
    # Set background and styling
    set_background("assets/Untitled design.jpg")

    # Sidebar menu
    st.markdown(
        f"""
        <div class="sidebar">
            <a href="#">Dashboard</a>
            <a href="#">Groups</a>
            <a href="#">Statistics</a>
        </div>
        """, unsafe_allow_html=True
    )

    # Top bar with search and profile
    st.markdown(
        f"""
        <div class="topbar">
            <div>Kushal Maa</div>
            <input type="text" class="search-box" placeholder="Search for anything">
            <div class="profile-icon">{initials}
                <div class="dropdown">
                    <button onclick="logout()">Logout</button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # Display main content in the central area
    st.markdown("<div class='main-content'>", unsafe_allow_html=True)
    st.title(f"Welcome, {user_name}!")

    # Remove additional logout button from the main content
    st.markdown("</div>", unsafe_allow_html=True)