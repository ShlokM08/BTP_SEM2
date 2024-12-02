import streamlit as st
from pymongo import MongoClient
from .whatsapp_chat_parser import *
from .zoom_audio_service import ZoomAudioService, handle_zoom_audio_upload
from .zoom_chat_service import ZoomChatService, handle_zoom_chat_upload
from .zoom_attendence_service import ZoomAttendanceService, handle_zoom_attendance_upload
from .number_to_names_parser import replace_numbers_with_names
from database import *
import tempfile
import os

from .moderator_dasboard_graphs import *

# Initialize database
try:
    MONGO_URI = os.getenv('MONGO_URI', 'your_default_mongo_uri_here')  # Replace with your Mongo URI or use dotenv
    client = MongoClient(MONGO_URI)
    db = client['kushal_maa_data']
    st.session_state.db = db
except Exception as e:
    st.error(f"Database initialization failed: {e}")

zoom_chat_service = ZoomChatService(st.session_state.db)


def get_moderator_groups(db, user_name):
    """Get list of groups assigned to moderator."""
    user = db['users'].find_one({"name": user_name, "user_type": "Moderator"})
    if user and "current_groups" in user:
        return user['current_groups']
    return []


def handle_whatsapp_upload(whatsapp_service, group_name, uploaded_file, user_name):
    """Handle WhatsApp chat file upload and processing"""
    try:
        # Read and process the file
        content = uploaded_file.getvalue().decode('utf-8', errors='replace')
        
        # Process the chat content
        process_result = whatsapp_service.process_chat_file(content)
        
        if process_result["status"] == "error":
            st.error(f"Error processing file: {process_result['message']}")
            return
            
        # Show preview of parsed data
        st.write("Preview of parsed data:")
        st.write(process_result["message"])
        
        # Save button
        if st.button(f"Save {group_name}'s WhatsApp chat to database"):
            save_result = whatsapp_service.save_chat_data(
                group_name,
                process_result["data"],
                user_name
            )
            
            if save_result["status"] == "success":
                st.success(f"""
                    WhatsApp chat for {group_name} uploaded and saved successfully!
                    Database ID: {save_result['data']['chat_id']}
                """)
            else:
                st.error(f"Error saving to database: {save_result['message']}")
                
    except Exception as e:
        st.error(f"Error handling WhatsApp chat: {e}")


def handle_name_mapping(whatsapp_file, mapping_file):
    """Handle WhatsApp chat file processing with name mapping."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temporary file paths
            temp_chat_file = os.path.join(temp_dir, "chat.txt")
            temp_csv_file = os.path.join(temp_dir, "mapping.csv")
            temp_output_file = os.path.join(temp_dir, "output.txt")

            # Write uploaded files to temporary locations
            chat_content = whatsapp_file.getvalue().decode('utf-8', errors='replace')
            csv_content = mapping_file.getvalue().decode('utf-8', errors='replace')
            
            with open(temp_chat_file, 'w', encoding='utf-8') as f:
                f.write(chat_content)
            with open(temp_csv_file, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            # Process files
            replace_numbers_with_names(temp_chat_file, temp_csv_file, temp_output_file)

            # Read and display processed content
            with open(temp_output_file, 'r', encoding='utf-8') as f:
                processed_content = f.read()

            if not processed_content.strip():
                st.error("Processing resulted in empty output. Please check your input files.")
                return

            # Create download button
            st.success("File processed successfully!")
            st.download_button(
                label="Download Processed Chat File",
                data=processed_content,
                file_name=f"processed_chat.txt",
                mime="text/plain"
            )
    except Exception as e:
        st.error(f"Error processing files: {e}")


def handle_groups_page(user_name):
    """Handle Groups Page."""
    st.title("Groups")
    groups = get_moderator_groups(st.session_state.db, user_name)

    if not groups:
        st.warning("You are not assigned to any group currently.")
        return

    st.subheader("You are currently assigned to the following groups:")
    for group in groups:
        group_name = group.get('group_name', 'Unknown Group')  # Use default value if 'group_name' key is missing
        st.write(f"- {group_name}")


def handle_dashboard():
    moderator_graph_main()


def moderator_page(user_name):
    """Main Moderator Interface."""
    st.sidebar.title("Moderator Navigation")
    page = st.sidebar.radio("Navigate to", ["Dashboard", "Upload Transcripts", "Groups"])

    if page == "Dashboard":
        handle_dashboard()

    elif page == "Upload Transcripts":
        st.title(f"Welcome, {user_name}!")
        
        # Ensure database is initialized
        if 'db' not in st.session_state:
            st.error("Database not initialized. Please contact Admin.")
            return

        # Initialize services
        whatsapp_service = WhatsAppService(st.session_state.db)
        zoom_audio_service = ZoomAudioService(st.session_state.db)
        zoom_attendance_service = ZoomAttendanceService(st.session_state.db)

        groups = get_moderator_groups(st.session_state.db, user_name)
        if not groups:
            st.warning("You are not assigned to any group currently.")
            return

        st.subheader("You are currently assigned to the following groups:")
        
        for group in groups:
            group_name = group.get('group_name', 'Unknown Group')
            st.write(f"Group: {group_name}")
            
            # Create tabs for different upload types
            tabs = st.tabs(["WhatsApp Chat", "Zoom Audio", "Zoom Chat", "Zoom Attendance"])
            
            # WhatsApp Chat Tab
            with tabs[0]:
                st.subheader("1. Process WhatsApp Chat with Name Mapping")
                
                col1, col2 = st.columns(2)
                with col1:
                    whatsapp_chat = st.file_uploader(
                        f"Upload original WhatsApp chat for {group_name}",
                        type=["txt"],
                        key=f"whatsapp_original_{group_name}"
                    )
                with col2:
                    mapping_file = st.file_uploader(
                        "Upload name mapping CSV file",
                        type=["csv"],
                        key=f"mapping_{group_name}"
                    )
                
                if whatsapp_chat and mapping_file:
                    if st.button("Process Files", key=f"process_{group_name}"):
                        handle_name_mapping(whatsapp_chat, mapping_file)
                
                st.markdown("---")
                st.subheader("2. Upload Processed Chat to Database")
                st.info("After downloading the processed chat file above, verify its contents and upload here.")
                processed_chat = st.file_uploader(
                    f"Upload processed WhatsApp chat for {group_name}",
                    type=["txt"],
                    key=f"whatsapp_processed_{group_name}"
                )
                if processed_chat:
                    handle_whatsapp_upload(whatsapp_service, group_name, processed_chat, user_name)
            
            # Zoom Audio Tab
            with tabs[1]:
                zoom_audio = st.file_uploader(
                    f"Upload Zoom audio transcript for {group_name}",
                    type=["txt"],
                    key=f"transcript_{group_name}"
                )
                if zoom_audio:
                    handle_zoom_audio_upload(zoom_audio_service, group_name, zoom_audio, user_name)
            
            # Zoom Chat Tab
            with tabs[2]:
                zoom_chat = st.file_uploader(
                    f"Upload Zoom chat file for {group_name}",
                    type=["txt"],
                    key=f"chat_{group_name}"
                )
                if zoom_chat:
                    handle_zoom_chat_upload(zoom_chat_service, group_name, zoom_chat, user_name)
            
            # Zoom Attendance Tab
            with tabs[3]:
                zoom_attendance = st.file_uploader(
                    f"Upload Zoom attendance file for {group_name}",
                    type=["csv", "xls", "xlsx"],
                    key=f"attendance_{group_name}"
                )
                if zoom_attendance:
                    handle_zoom_attendance_upload(zoom_attendance_service, group_name, zoom_attendance, user_name)

    elif page == "Groups":
        handle_groups_page(user_name)


# Example usage
# moderator_page("John Doe")
