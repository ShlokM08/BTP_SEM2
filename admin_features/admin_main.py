# All Codes of Admin Will Reside here
import streamlit as st
from .group_management import *
from .moderator_management import *
from .add_new_users import *
from .display_overview_chats import *

def admin_page(user_name):
    st.title(f"Admin Dashboard - {user_name}")

    # Creating sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Overview", "Moderators", "Add Moderators", "Groups"])

    if page == "Overview":
        display_overview() 
    elif page == "Moderators":
        manage_moderators()
    elif page == "Add Moderators":
        add_new_moderators() # TODO
    elif page == "Groups":
        manage_groups() 
    # elif page =="Users":
    #     manage_users() 
