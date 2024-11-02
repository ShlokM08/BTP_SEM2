import sys
sys.path.append(".")

import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from database import *

def remove_moderator(moderator_id):
    current_time = datetime.now()
    
    # Fetch the moderator
    moderator = users_collection.find_one({"_id": ObjectId(moderator_id)})
    
    if not moderator:
        st.error("Moderator not found.")
        return
    
    # Update moderator's end_date and move current_groups to past_groups
    users_collection.update_one(
        {"_id": ObjectId(moderator_id)},
        {
            "$set": {
                "end_date": current_time,
                "past_groups": moderator.get("current_groups", []),
                "current_groups": []
            }
        }
    )
    
    # Add removed_at timestamp to past_groups
    users_collection.update_one(
        {"_id": ObjectId(moderator_id)},
        {
            "$set": {
                "past_groups.$[].removed_at": current_time
            }
        }
    )
    
    # Remove moderator from all groups
    for group in moderator.get("current_groups", []):
        groups_collection.update_one(
            {"_id": group["group_id"]},
            {
                "$pull": {"current_moderators": {"name": moderator["name"]}},
                "$push": {
                    "past_moderators": {
                        "name": moderator["name"],
                        "added_at": group["added_at"],
                        "removed_at": current_time
                    }
                }
            }
        )
    
    st.success(f"Moderator {moderator['name']} has been removed and their group assignments have been updated.")

def manage_moderators():
    st.title("Moderator Management")
    
    # Fetch all active moderators (those with end_date as None)
    active_moderators = list(users_collection.find(
        {"user_type": "Moderator", "end_date": None},
        {"name": 1, "email": 1, "start_date": 1, "current_groups": 1}
    ))
    
    if not active_moderators:
        st.warning("No active moderators found.")
        return
    
    # Display moderator information and removal option
    for moderator in active_moderators:
        st.subheader(f"Moderator: {moderator['name']}")
        st.write(f"Email: {moderator['email']}")
        st.write(f"Start Date: {moderator['start_date']}")
        
        st.write("Current Groups:")
        for group in moderator.get("current_groups", []):
            st.write(f"- {group['group_name']} (Added: {group['added_at']})")
        
        if st.button(f"Remove {moderator['name']}", key=str(moderator['_id'])):
            remove_moderator(str(moderator['_id']))
            st.rerun()
