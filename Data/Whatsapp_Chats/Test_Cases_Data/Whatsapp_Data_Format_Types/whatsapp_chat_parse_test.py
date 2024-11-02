import re
from datetime import datetime
import json

def parse_whatsapp_chat(file_path):
    # Dictionary to store user messages
    chat_data = {}
    
    # Regular expressions for different date formats and message patterns
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{2,4})',  # DD/MM/YY or MM/DD/YY or YYYY
        r'\[(\d{1,2}/\d{1,2}/\d{2,4})'  # [DD/MM/YY or [MM/DD/YY or YYYY
    ]
    
    time_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)'
    tag_pattern = r'@(\d+)'

    def standardize_date(date_str):
        # Try different date formats and convert to DD/MM/YYYY
        date_formats = ['%d/%m/%y', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y']
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                # Convert to DD/MM/YYYY format
                return date_obj.strftime('%d/%m/%Y')
            except ValueError:
                continue
        return date_str

    def convert_to_24hr(time_str):
        # Convert various time formats to 24-hour format
        try:
            # Handle different time formats
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                # 12-hour format with AM/PM
                time_obj = datetime.strptime(time_str.strip(), '%I:%M %p')
            else:
                # 24-hour format
                time_obj = datetime.strptime(time_str.strip(), '%H:%M')
            return time_obj.strftime('%H:%M')
        except ValueError:
            try:
                # Try parsing with seconds
                if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                    time_obj = datetime.strptime(time_str.strip(), '%I:%M:%S %p')
                else:
                    time_obj = datetime.strptime(time_str.strip(), '%H:%M:%S')
                return time_obj.strftime('%H:%M')
            except ValueError:
                return time_str

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            # Skip encryption message
            if 'Messages and calls are end-to-end encrypted' in line:
                continue

            # Extract date
            date_str = None
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    date_str = match.group(1)
                    break

            if not date_str:
                continue

            # Extract time
            time_match = re.search(time_pattern, line)
            if not time_match:
                continue

            # Extract message content and sender
            message_pattern = r'[^\]]*?\] (.+?):(.*)|[^-]*?- (.+?):(.*)'
            message_match = re.search(message_pattern, line)
            
            if message_match:
                # Handle different message formats
                if message_match.group(1):  # Format with brackets
                    sender = message_match.group(1).strip()
                    message = message_match.group(2).strip()
                else:  # Format with hyphen
                    sender = message_match.group(3).strip()
                    message = message_match.group(4).strip()

                # Extract tags
                tags = re.findall(tag_pattern, message)
                tags = tags if tags else None

                # Initialize user entry if not exists
                if sender not in chat_data:
                    chat_data[sender] = {
                        "id": sender,
                        "messages": []
                    }

                # Add message to user's messages
                chat_data[sender]["messages"].append({
                    "date": standardize_date(date_str),
                    "time_stamp": convert_to_24hr(time_match.group(1)),
                    "message": message,
                    "tagged": tags
                })

    # Convert to list format
    return list(chat_data.values())

def save_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Example usage
if __name__ == "__main__":
    input_file = "/home/bhartrihari/UCSF_Project/UCSFR01/Stage_2_All_Data_Combined/Data/Whatsapp_Chats/iphone_whatsapp_data/left_member_case/WhatsApp Chat - Whatupppp/_chat.txt"  # Replace with your file path
    output_file = "chat_output(iphone_left_case).json"
    
    try:
        chat_data = parse_whatsapp_chat(input_file)
        save_to_json(chat_data, output_file)
        print(f"Successfully parsed chat and saved to {output_file}")
    except Exception as e:
        print(f"Error processing file: {str(e)}")
