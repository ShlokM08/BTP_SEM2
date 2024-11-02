import streamlit as st
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from database import *

def add_new_moderators():
    st.header("Add New Admin/Moderator")
    
    # Create form for adding new moderator
    with st.form("add_moderator_form"):
        # Dropdown for user type selection
        user_type = st.selectbox(
            "Select Role",
            ["Admin", "Moderator"],
            help="Select whether to add an Admin or Moderator"
        )
        
        # Input fields for name and email
        name = st.text_input(
            "Name",
            help="Enter the full name of the new admin/moderator"
        )
        
        email = st.text_input(
            "Email",
            help="Enter the email address"
        )
        
        # Submit button
        submitted = st.form_submit_button("Add User")
        
        if submitted:
            if not name or not email:
                st.error("Please fill in all fields")
                return
            
            # Basic email validation
            if "@" not in email or "." not in email:
                st.error("Please enter a valid email address")
                return
                
            try:
                # Create new user document
                new_user = {
                    "name": name,
                    "email": email,
                    "user_type": user_type,
                    "start_date": datetime.utcnow(),
                    "end_date": None,
                    "current_groups": []
                }
                
                # Get database connection (assuming it's set up in your app)
                client = MongoClient(MONGO_URI)
                db = client["kushal_maa_data"]
                
                # Check if email already exists
                existing_user = db.users.find_one({"email": email})
                if existing_user:
                    st.error(f"A user with email {email} already exists")
                    return
                
                # Insert the new user
                result = db.users.insert_one(new_user)
                
                if result.inserted_id:
                    st.success(f"Successfully added new {user_type.lower()}: {name}")
                    
                    # Show new user details
                    st.info(f"""
                    **New {user_type} Details:**
                    - Name: {name}
                    - Email: {email}
                    - Role: {user_type}
                    - Start Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
                    """)
                else:
                    st.error("Failed to add new user")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                
            finally:
                if 'client' in locals():
                    client.close()
