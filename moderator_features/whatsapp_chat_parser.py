# whatsapp_service.py

import io
import logging
from datetime import datetime
from bson import ObjectId
from .whatsapp_parser_android import parse_whatsapp_chat
from typing import Union, TextIO

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self, db):
        """Initialize WhatsApp service with database connection"""
        self.db = db

    def process_chat_file(self, file_content: str) -> dict:
        """Process the WhatsApp chat file content and return parsed data"""
        try:
            logger.debug("Starting to process chat file")
            
            # Create a file-like object from the content
            file_obj = io.StringIO(file_content)
            
            # Parse the chat
            logger.debug("Parsing chat file")
            chat_data = parse_whatsapp_chat(file_obj)
            
            if not chat_data:
                logger.warning("No chat data was parsed")
                return {
                    "status": "error",
                    "message": "No valid chat data found in the file"
                }
            
            logger.debug(f"Successfully parsed chat with {len(chat_data)} users")
            return {
                "status": "success",
                "data": chat_data,
                "message": f"Successfully parsed chat with {len(chat_data)} users"
            }
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp chat: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to process WhatsApp chat"
            }

    def add_members_to_group(self, group_name: str, members_data: list) -> dict:
        """Add members from WhatsApp chat to the group in MongoDB"""
        try:
            # Find the group
            group = self.db['groups'].find_one({"name": group_name})
            if not group:
                logger.error(f"Group {group_name} not found")
                return {
                    "status": "error",
                    "message": f"Group {group_name} not found"
                }

            member_ids = []
            for member in members_data:
                # Create or update member in members collection
                member_doc = {
                    "name": member["id"],  # Using WhatsApp ID as name
                    "last_seen": member["last_seen"],
                    "is_active": member["is_present_in_group"],
                    "updated_at": datetime.now()
                }
                
                # Upsert member
                result = self.db['members'].update_one(
                    {"name": member["id"]},
                    {
                        "$set": member_doc,
                        "$setOnInsert": {
                            "created_at": datetime.now()
                        }
                    },
                    upsert=True
                )
                
                # Get member ID
                if result.upserted_id:
                    member_ids.append(result.upserted_id)
                else:
                    member_doc = self.db['members'].find_one({"name": member["id"]})
                    if member_doc:
                        member_ids.append(member_doc["_id"])

            # Update group with member IDs if we found any
            if member_ids:
                self.db['groups'].update_one(
                    {"_id": group["_id"]},
                    {
                        "$addToSet": {
                            "members": {
                                "$each": member_ids
                            }
                        }
                    }
                )

            return {
                "status": "success",
                "data": {
                    "member_ids": [str(mid) for mid in member_ids],
                    "member_count": len(member_ids)
                },
                "message": f"Successfully added {len(member_ids)} members to group {group_name}"
            }

        except Exception as e:
            logger.error(f"Error adding members to group: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to add members to group {group_name}"
            }

    def save_chat_data(self, group_name: str, chat_data: list, uploaded_by: str) -> dict:
        """Save parsed WhatsApp chat data to MongoDB"""
        try:
            logger.debug(f"Starting to save chat data for group {group_name}")
            
            # First, add members to the group
            members_result = self.add_members_to_group(group_name, chat_data)
            if members_result["status"] == "error":
                return members_result

            # Create a document for whatsapp_chats collection
            chat_document = {
                "group_name": group_name,
                "uploaded_by": uploaded_by,
                "upload_date": datetime.now(),
                "chat_data": chat_data
            }
            
            # Insert into the whatsapp_chats collection
            result = self.db['whatsapp_chats'].insert_one(chat_document)
            chat_id = result.inserted_id
            
            # Create documents for whatsapp_data collection
            whatsapp_data = []
            for user_data in chat_data:
                for message in user_data.get("messages", []):
                    message_doc = {
                        "chat_id": chat_id,
                        "group_name": group_name,
                        "user_id": user_data["id"],
                        "date": message["date"],
                        "time_stamp": message["time_stamp"],
                        "message": message["message"],
                        "tagged": message.get("tagged"),
                        "created_at": datetime.now()
                    }
                    whatsapp_data.append(message_doc)

            # Insert messages into whatsapp_data collection
            if whatsapp_data:
                self.db['whatsapp_data'].insert_many(whatsapp_data)
            
            # Update the group's document with the chat reference
            self.db['groups'].update_one(
                {"name": group_name},
                {
                    "$set": {
                        "last_whatsapp_update": datetime.now(),
                        "whatsapp_chat_id": chat_id
                    }
                }
            )
            
            logger.debug(f"Successfully saved chat data for group {group_name}")
            return {
                "status": "success",
                "data": {
                    "chat_id": str(chat_id),
                    "group_name": group_name,
                    "message_count": len(whatsapp_data),
                    "member_count": members_result["data"]["member_count"]
                },
                "message": f"Successfully saved chat data for group {group_name}"
            }
            
        except Exception as e:
            logger.error(f"Error saving chat to MongoDB: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to save chat data for group {group_name}"
            }
