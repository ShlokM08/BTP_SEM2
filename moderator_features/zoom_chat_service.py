# zoom_chat_service.py
from datetime import datetime
import streamlit as st
from bson import ObjectId

class ZoomChatService:
    def __init__(self, db):
        self.db = db
        self.collection = db["zoom_chatbox_messages"]

    def parse_chat_content(self, content):
        """Parse chat content from uploaded file"""
        user_messages = {}
        
        try:
            for line in content.split('\n'):
                # Skip empty lines
                if not line.strip():
                    continue
                    
                # Splitting the line based on time and message parts
                if '\t' in line:
                    time_stamp, rest = line.split('\t', 1)
                    try:
                        sender, message = rest.split(':', 1)
                    except ValueError:
                        continue  # Skip lines that don't have the proper format
                    
                    # Strip and clean up the sender's name
                    sender = sender.strip()
                    
                    # Check if the message tags someone
                    tagged = None
                    if '@' in message:
                        tagged = message.split('@')[1].split()[0]  # Extract tagged name
                    
                    # Create a message entry
                    message_entry = {
                        "time_stamp": time_stamp.strip(),
                        "message": message.strip(),
                        "tagged": tagged
                    }
                    
                    # Append the message to the correct user
                    if sender not in user_messages:
                        user_messages[sender] = {
                            "_id": str(ObjectId()),
                            "name": sender,
                            "messages": []
                        }
                    user_messages[sender]["messages"].append(message_entry)
            
            return {
                "status": "success",
                "data": list(user_messages.values()),
                "message": f"Successfully parsed {len(user_messages)} user chats"
            }
        except Exception as e:
            return {
                "status": "error",
                "data": None,
                "message": f"Error parsing chat content: {str(e)}"
            }

    def save_chat_data(self, group_name, chat_data, moderator_name):
        """Save parsed chat data to database"""
        try:
            # Create document for database
            chat_document = {
                "_id": str(ObjectId()),
                "group_name": group_name,
                "date_of_upload": datetime.now(),
                "uploaded_by": moderator_name,
                "chat_data": chat_data
            }
            
            # Insert into database
            result = self.collection.insert_one(chat_document)
            
            return {
                "status": "success",
                "data": {"chat_id": str(result.inserted_id)},
                "message": "Chat data saved successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "data": None,
                "message": f"Error saving chat data: {str(e)}"
            }

def handle_zoom_chat_upload(zoom_chat_service, group_name, uploaded_file, user_name):
    """Handle Zoom chat file upload and processing"""
    try:
        # Read and process the file
        content = uploaded_file.getvalue().decode('utf-8')
        
        # Process the chat content
        process_result = zoom_chat_service.parse_chat_content(content)
        
        if process_result["status"] == "error":
            st.error(f"Error processing file: {process_result['message']}")
            return
        
        # Show preview of parsed data
        st.write("Preview of parsed data:")
        st.write(f"Number of users in chat: {len(process_result['data'])}")
        if len(process_result['data']) > 0:
            st.write("Sample messages from first user:")
            first_user = process_result['data'][0]
            st.write(f"User: {first_user['name']}")
            for msg in first_user['messages'][:3]:  # Show first 3 messages
                st.write(f"- {msg['time_stamp']}: {msg['message']}")
        
        # Save button
        if st.button(f"Save {group_name}'s Zoom chat to database"):
            save_result = zoom_chat_service.save_chat_data(
                group_name,
                process_result["data"],
                user_name
            )
            
            if save_result["status"] == "success":
                st.success(f"""
                    Zoom chat for {group_name} uploaded and saved successfully!
                    Database ID: {save_result['data']['chat_id']}
                """)
            else:
                st.error(f"Error saving to database: {save_result['message']}")
                
    except Exception as e:
        st.error(f"Error handling Zoom chat: {str(e)}")
