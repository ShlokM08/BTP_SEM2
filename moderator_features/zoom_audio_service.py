from datetime import datetime
import streamlit as st
from typing import Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from datetime import datetime

from datetime import datetime
from typing import Dict, Any, List
from pymongo.database import Database
from datetime import datetime

class ZoomChatProcessorLight:
    """Lightweight version of ZoomChatProcessor without MongoDB dependencies"""
    def __init__(self):
        self.current_date = datetime.now().isoformat()

    def parse_timestamp(self, time_str: str) -> datetime:
        """Convert timestamp string to datetime object"""
        return datetime.strptime(time_str, '%H:%M:%S.%f')

    def format_timestamp_range(self, start_time: str, end_time: str) -> str:
        """Format timestamp range as string"""
        return f"{start_time} --> {end_time}"

    def calculate_duration_ms(self, start: str, end: str) -> int:
        """Calculate duration in milliseconds between two timestamp strings"""
        start_time = self.parse_timestamp(start)
        end_time = self.parse_timestamp(end)
        return int((end_time - start_time).total_seconds() * 1000)

    def process_vtt_data(self, vtt_data: str) -> List[Dict[str, Any]]:
        """Process VTT data and return structured data"""
        import re
        lines = vtt_data.strip().split('\n')
        conversation_chunks = []
        
        current_timestamp = ''
        current_speaker = ''
        current_message = ''
        timestamp_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$')
        
        for line in lines:
            line = line.strip()
            
            # Skip numbered lines
            if line.isdigit():
                continue
            
            # Check for timestamp
            if timestamp_pattern.match(line):
                current_timestamp = line
                continue
            
            # Check for speaker and message
            if ':' in line:
                speaker, message = line.split(':', 1)
                speaker = speaker.strip()
                message = message.strip()
                
                if current_timestamp:
                    start_time, end_time = current_timestamp.split(' --> ')
                    conversation_chunks.append((speaker, start_time, end_time, message))

        # Process conversation chunks into user messages
        user_messages = {}
        current_user = ''
        current_chunk = None

        for speaker, start_time, end_time, message in conversation_chunks:
            if speaker != current_user:
                # New speaker, save previous chunk if exists
                if current_chunk is not None:
                    if current_user not in user_messages:
                        user_messages[current_user] = []
                    user_messages[current_user].append(current_chunk)
                # Start new chunk
                current_user = speaker
                current_chunk = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'messages': [message]
                }
            else:
                # Same speaker, extend current chunk
                current_chunk['end_time'] = end_time
                current_chunk['messages'].append(message)

        # Add the last chunk
        if current_chunk is not None and current_user:
            if current_user not in user_messages:
                user_messages[current_user] = []
            user_messages[current_user].append(current_chunk)

        # Format final output
        processed_data = []

        for user_name, message_chunks in user_messages.items():
            total_duration = sum(
                self.calculate_duration_ms(chunk['start_time'], chunk['end_time'])
                for chunk in message_chunks
            )
            
            formatted_messages = [
                {
                    'time_stamp': self.format_timestamp_range(chunk['start_time'], chunk['end_time']),
                    'messages': ' '.join(chunk['messages'])
                }
                for chunk in message_chunks
            ]
            
            processed_data.append({
                'user_name': user_name,
                'total_duration': total_duration,
                'chat': [{
                    'date_of_upload': self.current_date,
                    'messages': formatted_messages
                }]
            })

        return processed_data

class ZoomAudioService:
    def __init__(self, db: Database):
        self.db = db
        self.collection = db["Zoom_audio_chat"]

    def process_chat_file(self, file_content: str) -> Dict[str, Any]:
        """Process the uploaded Zoom audio transcript file"""
        try:
            # Create lightweight processor instance
            processor = ZoomChatProcessorLight()
            
            # Process the VTT data
            processed_data = processor.process_vtt_data(file_content)
            
            return {
                "status": "success",
                "message": "File processed successfully",
                "data": processed_data
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing file: {str(e)}",
                "data": None
            }

    def save_chat_data(self, group_name: str, chat_data: list, moderator_name: str) -> Dict[str, Any]:
        """Save the processed chat data to MongoDB"""
        try:
            # Add metadata to each chat document
            for chat in chat_data:
                chat.update({
                    "group_name": group_name,
                    "uploaded_by": moderator_name,
                    "upload_timestamp": datetime.now().isoformat(),
                    "chat_type": "zoom_audio"
                })
            
            # Insert the documents
            result = self.collection.insert_many(chat_data)
            
            return {
                "status": "success",
                "message": "Chat data saved successfully",
                "data": {
                    "chat_ids": [str(id) for id in result.inserted_ids],
                    "documents_saved": len(result.inserted_ids)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error saving to database: {str(e)}",
                "data": None
            }

def handle_zoom_audio_upload(zoom_audio_service, group_name: str, uploaded_file, user_name: str):
    """Handle Zoom audio transcript file upload and processing"""
    try:
        # Read and process the file
        content = uploaded_file.getvalue().decode('utf-8')
        
        # Process the chat content
        process_result = zoom_audio_service.process_chat_file(content)
        
        if process_result["status"] == "error":
            st.error(f"Error processing file: {process_result['message']}")
            return
        
        # Show preview of parsed data
        st.write("Preview of processed data:")
        st.write(f"Number of participants: {len(process_result['data'])}")
        
        # Display sample of processed data
        if process_result['data']:
            st.write("Sample participant data:")
            st.json(process_result['data'][0])
        
        # Save button
        if st.button(f"Save {group_name}'s Zoom audio transcript to database"):
            save_result = zoom_audio_service.save_chat_data(
                group_name,
                process_result["data"],
                user_name
            )
            
            if save_result["status"] == "success":
                st.success(f"""
                    Zoom audio transcript for {group_name} uploaded and saved successfully!
                    Documents saved: {save_result['data']['documents_saved']}
                    Database IDs: {', '.join(save_result['data']['chat_ids'])}
                """)
            else:
                st.error(f"Error saving to database: {save_result['message']}")
                
    except Exception as e:
        st.error(f"Error handling Zoom audio transcript: {str(e)}")
