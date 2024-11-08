import streamlit as st
from pymongo import MongoClient
import matplotlib.pyplot as plt
from .whatsapp_chat_parser import *
from .zoom_audio_service import ZoomAudioService, handle_zoom_audio_upload
from .zoom_chat_service import ZoomChatService, handle_zoom_chat_upload
from .zoom_attendence_service import ZoomAttendanceService, handle_zoom_attendance_upload
from database import *

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

def get_group_message_count(db, group_name):
    # Aggregates messages by user in the specified group
    pipeline = [
        {"$match": {"group_name": group_name}},
        {"$unwind": "$chat_data"},  # Unwind to go through each message in chat_data
        {"$group": {"_id": "$chat_data.user", "message_count": {"$sum": 1}}}
    ]
    result = db['whatsapp_chats'].aggregate(pipeline)
    return list(result)

def plot_message_counts(message_counts):
    # Prepare data for plotting
    users = [entry["_id"] for entry in message_counts]
    message_counts = [entry["message_count"] for entry in message_counts]

    # Plot data using matplotlib
    fig, ax = plt.subplots()
    ax.bar(users, message_counts, color="skyblue")
    ax.set_xlabel("Users")
    ax.set_ylabel("Message Count")
    ax.set_title("Messages per User in Group")

    # Display plot in Streamlit
    st.pyplot(fig)

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
    st.sidebar.title("Dashboard")
    st.sidebar.write("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Groups", "Statistics"])

    st.title(f"Welcome, {user_name}!")

    if page == "Dashboard":
        st.write("This is the main dashboard page.")
    elif page == "Groups":
        st.subheader("Your Groups")
        groups = get_moderator_groups(st.session_state.db, user_name)
        
        if groups:
            selected_group = st.selectbox("Select a Group to View Messages", groups)
            
            if st.button("Show Message Statistics"):
                message_counts = get_group_message_count(st.session_state.db, selected_group)
                if message_counts:
                    plot_message_counts(message_counts)
                else:
                    st.info("No messages found for this group.")
        else:
            st.info("No groups found for this user.")
    elif page == "Statistics":
        st.write("Statistics page under construction.")

# Example usage
moderator_page("John Doe")
