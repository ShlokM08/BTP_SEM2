import json
from bson import ObjectId
from datetime import datetime

# Simulated MongoDB Object ID for this example
def generate_object_id():
    return str(ObjectId())

# Function to parse the chat data
def parse_chat(file_path):
    user_messages = {}
    with open(file_path, 'r') as file:
        for line in file:
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
                    "date_of_upload": datetime.now().strftime('%Y-%m-%d'),
                    "time_stamp": time_stamp,
                    "message": message.strip(),
                    "tagged": tagged
                }
                
                # Append the message to the correct user
                if sender not in user_messages:
                    user_messages[sender] = {
                        "_id": generate_object_id(),
                        "name": sender,
                        "messages": []
                    }
                user_messages[sender]["messages"].append(message_entry)
    
    return list(user_messages.values())

# Example usage with chat data
file_path = '/home/bhartrihari/UCSF_Project/UCSFR01/Stage_2_All_Data_Combined/Data/Zoom_Data/chat_box_data_2.txt'
parsed_users = parse_chat(file_path)

# Output the JSON data
output_json = json.dumps(parsed_users, indent=4)
print(output_json)

# Save to file if needed
with open('chat_messages.json', 'w') as json_file:
    json_file.write(output_json)
