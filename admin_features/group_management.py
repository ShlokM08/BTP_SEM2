import sys
sys.path.append(".")

from pymongo import MongoClient
import streamlit as st
from datetime import datetime
from bson import ObjectId
from database import *

def manage_groups():
    st.header("Manage Groups")

    # Create a new group
    st.subheader("Create a New Group")
    new_group_name = st.text_input("Enter new group name")
    if st.button("Create Group"):
        if new_group_name:
            create_group(new_group_name)
            st.success(f"Group '{new_group_name}' created successfully!")
        else:
            st.warning("Please enter a group name.")

    # Manage existing groups
    st.subheader("Manage Existing Groups")
    groups = list(groups_collection.find({}, {"name": 1}))
    group_names = [group["name"] for group in groups]
    selected_group = st.selectbox("Select a group to manage", group_names)

    if selected_group:
        manage_group_moderators(selected_group)

def manage_group_moderators(group_name):
    group = groups_collection.find_one({"name": group_name})
    st.write(f"Managing moderators for group: {group_name}")

    # Display current moderators
    st.subheader("Current Moderators")
    current_moderators = group.get('current_moderators', [])
    for moderator in current_moderators:
        st.write(f"- {moderator['name']} (Added: {moderator['added_at']})")

    # Add new moderator
    st.subheader("Add New Moderator")
    available_moderators = list(users_collection.find(
        {
            "user_type": "Moderator",
            "end_date": None,  # Only include moderators with null end_date
            "name": {"$nin": [mod['name'] for mod in current_moderators]}
        },
        {"name": 1}
    ))
    available_moderator_names = [mod["name"] for mod in available_moderators]
    
    if available_moderator_names:
        new_moderator = st.selectbox("Select a moderator to add", available_moderator_names)
        if st.button("Add Moderator"):
            add_moderator_to_group(group['_id'], group['name'], new_moderator)
            st.success(f"Moderator '{new_moderator}' added to the group!")
            st.rerun()
    else:
        st.info("No available moderators to add.")

    # Remove moderator
    st.subheader("Remove Moderator")
    if current_moderators:
        moderator_to_remove = st.selectbox("Select a moderator to remove", [mod['name'] for mod in current_moderators])
        if st.button("Remove Moderator"):
            remove_moderator_from_group(group['_id'], group['name'], moderator_to_remove)
            st.success(f"Moderator '{moderator_to_remove}' removed from the group!")
            st.rerun()
    else:
        st.info("No moderators to remove.")

def create_group(name):
    return groups_collection.insert_one({
        "name": name,
        "current_moderators": [],
        "past_moderators": []
    }).inserted_id

def add_moderator_to_group(group_id, group_name, moderator_name):
    current_time = datetime.now()
    
    # Check if moderator is already in the group
    group = groups_collection.find_one({"_id": group_id})
    if any(mod['name'] == moderator_name for mod in group.get('current_moderators', [])):
        st.error(f"Moderator '{moderator_name}' is already in the group.")
        return

    # Update group document
    groups_collection.update_one(
        {"_id": group_id},
        {
            "$push": {
                "current_moderators": {
                    "name": moderator_name,
                    "added_at": current_time
                }
            }
        }
    )

    # Update moderator document
    users_collection.update_one(
        {"name": moderator_name, "user_type": "Moderator"},
        {
            "$push": {
                "current_groups": {
                    "group_id": group_id,
                    "group_name": group_name,
                    "added_at": current_time
                }
            }
        }
    )

def remove_moderator_from_group(group_id, group_name, moderator_name):
    current_time = datetime.now()
    
    # Update group document
    group = groups_collection.find_one({"_id": group_id})
    current_moderators = group.get('current_moderators', [])
    
    for moderator in current_moderators:
        if moderator['name'] == moderator_name:
            groups_collection.update_one(
                {"_id": group_id},
                {
                    "$pull": {"current_moderators": {"name": moderator_name}},
                    "$push": {
                        "past_moderators": {
                            "name": moderator_name,
                            "added_at": moderator['added_at'],
                            "removed_at": current_time
                        }
                    }
                }
            )
            break

    # Update moderator document
    users_collection.update_one(
        {"name": moderator_name, "user_type": "Moderator"},
        {
            "$pull": {"current_groups": {"group_id": group_id}},
            "$push": {
                "past_groups": {
                    "group_id": group_id,
                    "group_name": group_name,
                    "added_at": moderator['added_at'],
                    "removed_at": current_time
                }
            }
        }
    )

def initialize_users(users_data):
    for user in users_data:
        if user["user_type"] == "Moderator":
            users_collection.insert_one({
                "name": user["name"],
                "email": user["email"],
                "user_type": user["user_type"],
                "start_date": user["start_date"],
                "end_date": user["end_date"],
                "current_groups": [],
                "past_groups": []
            })
        else:  # Admin or any other user type
            users_collection.insert_one(user)
