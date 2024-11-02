# Final and Most Polished code
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict, Any, Tuple
import re
import os
import argparse

'''
This is code for testing the ZOom chat schema saving in the mongodb in localhost:2720 port.
Its not production ready code as I am trying to just covering all the cases of zoom audio trancript I can thnk in my mind
'''

class ZoomChatProcessor:
    def __init__(self, mongodb_uri: str, db_name: str):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.collection = self.db.zoom_chats

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
        """Process VTT data and return structured data for MongoDB"""
        lines = vtt_data.strip().split('\n')
        conversation_chunks: List[Tuple[str, str, str, str]] = []
        
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
        user_messages: Dict[str, List[Dict[str, Any]]] = {}
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
        current_date = datetime.now().isoformat()
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
                    'date_of_upload': current_date,
                    'messages': formatted_messages
                }]
            })

        return processed_data

    def save_to_mongodb(self, processed_data: List[Dict[str, Any]]) -> List[str]:
        """Save processed data to MongoDB and return inserted IDs"""
        result = self.collection.insert_many(processed_data)
        return result.inserted_ids

    def process_and_save_file(self, file_path: str) -> Dict[str, Any]:
        """Process a text file and save to MongoDB"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': f"File not found: {file_path}"}
            
            if not file_path.endswith('.txt'):
                return {'success': False, 'error': f"Invalid file format. Please provide a .txt file"}
            
            with open(file_path, 'r', encoding='utf-8') as file:
                vtt_data = file.read()
            
            processed_data = self.process_vtt_data(vtt_data)
            inserted_ids = self.save_to_mongodb(processed_data)
            
            return {
                'success': True,
                'processed_users': len(processed_data),
                'inserted_ids': [str(id) for id in inserted_ids]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

def get_user_chat(processor: ZoomChatProcessor, user_name: str):
    """Retrieve chat data for a specific user"""
    return processor.collection.find_one({'user_name': user_name})

def main():
    parser = argparse.ArgumentParser(description='Process Zoom chat text file and save to MongoDB')
    parser.add_argument('file_path', type=str, help='Path to the text file containing Zoom chat data')
    parser.add_argument('--mongodb-uri', type=str, default="mongodb://localhost:2720/",
                        help='MongoDB URI (default: mongodb://localhost:2720/)')
    parser.add_argument('--db-name', type=str, default="zoom_chats_db",
                        help='MongoDB database name (default: zoom_chats_db)')
    
    args = parser.parse_args()
    
    processor = ZoomChatProcessor(
        mongodb_uri=args.mongodb_uri,
        db_name=args.db_name
    )
    
    try:
        result = processor.process_and_save_file(args.file_path)
        
        if result['success']:
            print(f"Successfully processed and saved chat data:")
            print(f"- Processed users: {result['processed_users']}")
            print(f"- Inserted document IDs: {', '.join(result['inserted_ids'])}")
            
            # Example query
            user_name = "Pushpendra Singh"
            user_chat = get_user_chat(processor, user_name)
            if user_chat:
                print(f"\nExample data for user {user_name}:")
                print(f"Total duration: {user_chat['total_duration']}ms")
                for chat_session in user_chat['chat']:
                    print(f"Upload date: {chat_session['date_of_upload']}")
                    for message_group in chat_session['messages']:
                        print(f"Timestamp: {message_group['time_stamp']}")
                        print(f"Message: {message_group['messages']}")
        else:
            print(f"Error: {result['error']}")
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        processor.client.close()
