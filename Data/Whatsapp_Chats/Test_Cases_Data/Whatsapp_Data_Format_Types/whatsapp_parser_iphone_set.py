import re
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def parse_whatsapp_chat(file_path):
    # Dictionary to store user data
    users = {}
    
    def standardize_date(date_str):
        """Convert various date formats to DD/MM/YYYY"""
        try:
            date_str = date_str.strip(' []')
            date_formats = ['%d/%m/%y', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y']
            
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    continue
            return date_str
        except Exception as e:
            logger.error(f"Error standardizing date {date_str}: {e}")
            return date_str

    def convert_to_24hr(time_str):
        """Convert time to 24-hour format"""
        try:
            time_str = time_str.strip(' []')
            
            # Handle "AM" and "PM" variations
            if ', ' in time_str:  # Handle cases like "10:54:08 AM"
                time_str = time_str.split(', ')[1]
            
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                try:
                    time_obj = datetime.strptime(time_str, '%I:%M:%S %p')
                except ValueError:
                    time_obj = datetime.strptime(time_str, '%I:%M %p')
            else:
                try:
                    time_obj = datetime.strptime(time_str, '%H:%M:%S')
                except ValueError:
                    time_obj = datetime.strptime(time_str, '%H:%M')
            
            return time_obj.strftime('%H:%M')
        except Exception as e:
            logger.error(f"Error converting time {time_str}: {e}")
            return time_str

    def update_user_status(user_name, date_str, time_str, is_left=None):
        """Update user's status in the users dictionary"""
        user_name = user_name.strip('‎ ')  # Remove invisible character
        if user_name not in users:
            users[user_name] = {
                "id": user_name,
                "messages": [],
                "last_seen": f"{date_str} {time_str}",
                "is_present_in_group": True if is_left is None else not is_left
            }
        else:
            users[user_name]["last_seen"] = f"{date_str} {time_str}"
            if is_left is not None:
                users[user_name]["is_present_in_group"] = not is_left

    def handle_system_message(date_str, time_str, user_name, message):
        """Handle system messages including left/removed actions"""
        message = message.strip('‎ ')  # Remove invisible character
        if " left" in message:
            affected_user = message.split(" left")[0].strip('‎ ')
            update_user_status(affected_user, date_str, time_str, is_left=True)
            return True
        elif " removed" in message:
            removed_user = message.split(" removed ")[1].strip()
            update_user_status(removed_user, date_str, time_str, is_left=True)
            return True
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                try:
                    line = line.strip()
                    if not line or 'Messages and calls are end-to-end encrypted' in line:
                        continue

                    # Updated pattern to handle bracketed timestamps
                    full_pattern = r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?)\]\s*([^:]+):\s*(.+)'
                    
                    match = re.match(full_pattern, line)
                    if match:
                        date_str = standardize_date(match.group(1))
                        time_str = convert_to_24hr(f"{match.group(1)}, {match.group(2)}")
                        user_name = match.group(3).strip('‎ ')
                        message = match.group(4).strip()

                        # Check if this is a system message about leaving/removing
                        if handle_system_message(date_str, time_str, user_name, message):
                            continue

                        # Extract tags
                        tags = re.findall(r'@(\d+)', message)
                        tags = tags if tags else None

                        # Update user status and add message
                        update_user_status(user_name, date_str, time_str)
                        
                        # Add message to user's messages
                        users[user_name]["messages"].append({
                            "date": date_str,
                            "time_stamp": time_str,
                            "message": message,
                            "tagged": tags
                        })
                        continue

                    # Check for system messages with bracketed timestamps
                    system_patterns = [
                        (r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?)\]\s*([^:]+) created group', False),
                        (r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?)\]\s*([^:]+) left', True),
                        (r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?)\]\s*([^:]+) added ([^:]+)', False),
                        (r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?)\]\s*([^:]+) removed ([^:]+)', True)
                    ]

                    for pattern, is_left in system_patterns:
                        system_match = re.match(pattern, line)
                        if system_match:
                            date_str = standardize_date(system_match.group(1))
                            time_str = convert_to_24hr(f"{system_match.group(1)}, {system_match.group(2)}")
                            
                            if len(system_match.groups()) == 4:  # added/removed
                                user_name = system_match.group(4).strip('‎ ')
                            else:  # left or created
                                user_name = system_match.group(3).strip('‎ ')
                            
                            update_user_status(user_name, date_str, time_str, is_left=is_left)
                            break

                except Exception as e:
                    logger.error(f"Error processing line: {line}\nError: {e}")
                    continue

        return list(users.values())

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

def save_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Example usage
if __name__ == "__main__":
    try:
        input_file = "/home/bhartrihari/UCSF_Project/UCSFR01/Stage_2_All_Data_Combined/Data/Whatsapp_Chats/iphone_whatsapp_data/left_member_case/WhatsApp Chat - Whatupppp/_chat.txt"
        output_file = "chat_output(IPHONE_FINALE).json"
        
        chat_data = parse_whatsapp_chat(input_file)
        save_to_json(chat_data, output_file)
        print(f"Successfully parsed chat and saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")
