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
            if ',' in date_str:
                date_str = date_str.split(',')[0]
            
            # Handle both 2 and 4 digit years
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    # Ensure year is in 4-digit format
                    if len(parts[2]) == 2:
                        parts[2] = '20' + parts[2]
                    
                    # Try both DD/MM/YYYY and MM/DD/YYYY formats
                    try:
                        # First try as DD/MM/YYYY
                        date_obj = datetime.strptime(f"{parts[0]}/{parts[1]}/{parts[2]}", '%d/%m/%Y')
                    except ValueError:
                        try:
                            # Then try as MM/DD/YYYY
                            date_obj = datetime.strptime(f"{parts[0]}/{parts[1]}/{parts[2]}", '%m/%d/%Y')
                        except ValueError:
                            return date_str
                    
                    return date_obj.strftime('%d/%m/%Y')
            
            return date_str
        except Exception as e:
            logger.error(f"Error standardizing date {date_str}: {e}")
            return date_str

    def convert_to_24hr(time_str):
        """Convert time to 24-hour format"""
        try:
            time_str = time_str.strip(' []')
            if ',' in time_str:
                time_str = time_str.split(', ')[1]
            
            # Remove any trailing spaces and standardize am/pm format
            time_str = time_str.lower().strip()
            time_str = time_str.replace('am', ' am').replace('pm', ' pm').strip()
            
            try:
                if 'am' in time_str or 'pm' in time_str:
                    time_obj = datetime.strptime(time_str, '%I:%M %p')
                else:
                    time_obj = datetime.strptime(time_str, '%H:%M')
                return time_obj.strftime('%H:%M')
            except ValueError:
                return time_str
            
        except Exception as e:
            logger.error(f"Error converting time {time_str}: {e}")
            return time_str

    def update_user_status(user_name, date_str, time_str, is_left=None):
        """Update user's status in the users dictionary"""
        user_name = user_name.strip('‎ ')
        
        if user_name == "You":
            return  # Skip "You" messages as we can't identify the user
            
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

    def handle_system_message(line, date_str, time_str):
        """Handle system messages"""
        # Common system message patterns
        patterns = [
            (r'(.+) created group "([^"]+)"', False),
            (r'(.+) added (.+)', False),
            (r'(.+) left', True),
            (r'(.+) removed (.+)', True),
            (r'You were added', None)  # Special case
        ]
        
        for pattern, is_left in patterns:
            match = re.search(pattern, line)
            if match:
                if pattern == r'You were added':
                    return True
                    
                if len(match.groups()) == 2 and "created group" not in pattern:
                    user_name = match.group(2).strip()
                else:
                    user_name = match.group(1).strip()
                
                update_user_status(user_name, date_str, time_str, is_left=is_left)
                return True
                
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                try:
                    line = line.strip()
                    if not line or 'Messages and calls are end-to-end encrypted' in line:
                        continue

                    # Match the Android message pattern
                    # Pattern: "DD/MM/YY, HH:MM am - Username: Message"
                    message_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}\s*(?:am|pm))\s*-\s*([^:]+):\s*(.+)'
                    match = re.match(message_pattern, line, re.IGNORECASE)
                    
                    if match:
                        date_str = standardize_date(match.group(1))
                        time_str = convert_to_24hr(match.group(2))
                        user_name = match.group(3).strip()
                        message = match.group(4).strip()

                        if user_name != "You":  # Skip messages from "You"
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

                    # Handle system messages
                    system_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}\s*(?:am|pm))\s*-\s*(.+)'
                    system_match = re.match(system_pattern, line, re.IGNORECASE)
                    
                    if system_match:
                        date_str = standardize_date(system_match.group(1))
                        time_str = convert_to_24hr(system_match.group(2))
                        content = system_match.group(3).strip()
                        
                        handle_system_message(content, date_str, time_str)

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
        input_file = "WhatsApp Chat with Whatupppp(Pixel_7a).txt"
        output_file = "chat_output(KIng_In_Black_Phone_7a).json"
        
        chat_data = parse_whatsapp_chat(input_file)
        save_to_json(chat_data, output_file)
        print(f"Successfully parsed chat and saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")
