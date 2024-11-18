import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from pymongo import MongoClient
import os

# Streamlit must configure page layout first
#st.set_page_config(layout="wide")

# Load environment variables
load_dotenv()

def main():
    st.title("Group Chat Analysis")

    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('MONGO_DB_NAME')]  # Access the database
    collection = db[os.getenv('MONGO_COLLECTION')]  # Access the collection

    # Query data from MongoDB
    data_cursor = collection.find({})
    data = pd.DataFrame(list(data_cursor))

    # Check if data exists
    if not data.empty:
        # Convert timestamp to datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'], format='%d/%m/%Y, %H:%M')

    # Layout setup: Create top metrics and main content
    header_container = st.container()
    with header_container:
        col1, col2 = st.columns([6, 1])  # Left column for title, right column for metrics
        with col2:  # Metrics on the right
            #st.markdown("### Group Chat Metrics")

            # Calculate metrics
            total_members = len(data['user'].unique())  # Number of unique users
            total_moderators = 10  # Replace with your logic to calculate moderators
            total_groups = len(data['group'].unique())  # Number of unique groups

        metric_col1, metric_col2, metric_col3 = st.columns(3)  # Nested columns for metrics
        with metric_col1:
            st.markdown(
                f"""
                <div style="background-color: #D59ED4; border-radius: 60px; padding: 12px; text-align: center; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);">
                    <h3>Total Members</h3>
                    <h1 style="color: white;">{total_members}</h1>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with metric_col2:
            st.markdown(
                f"""
                <div style="background-color: #D59ED4; border-radius: 60px; padding: 12px; text-align: center; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);">
                    <h3>Total Moderators</h3>
                    <h1 style="color: white;">{total_moderators}</h1>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with metric_col3:
            st.markdown(
                f"""
                <div style="background-color: #D59ED4; border-radius: 60px; padding: 12px; text-align: center; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);">
                    <h3>Total Groups</h3>
                    <h1 style="color: white;">{total_groups}</h1>
                </div>
                """,
                unsafe_allow_html=True,
            )


    # Content Section
    content_container = st.container()
    with content_container:
        st.subheader("Filters and Sorting")
        col1, col2 = st.columns(2)  # Create two columns for filters
        with col1:
            group_filter = st.selectbox("Select Group", ["All"] + data['group'].unique().tolist())
        with col2:
            sort_option = st.selectbox("Sort By", ["None", "Timestamp", "Group", "User"])

        # Apply group filter
        if group_filter != "All":
            data = data[data['group'] == group_filter]

        # Apply sorting
        if sort_option == "Timestamp":
            data = data.sort_values(by='timestamp')
        elif sort_option == "Group":
            data = data.sort_values(by='group')
        elif sort_option == "User":
            data = data.sort_values(by='user')

        # Visualization
        col1, col2 = st.columns(2)  # Create two columns for charts
        with col1:
            active_users = data['user'].nunique()
            st.subheader(f"Active Users: {active_users}")
            st.bar_chart(data['user'].value_counts())

        with col2:
            chat_freq = data['user'].value_counts()
            st.subheader("Chat Frequency by Users")
            st.bar_chart(chat_freq)

        # Text comparison and message frequency
        col1, col2 = st.columns(2)  # Create two columns again
        with col1:
            st.subheader("Text Comparison Across Groups")
            group_counts = data['group'].value_counts()
            fig, ax = plt.subplots()
            ax.pie(
                group_counts,
                labels=group_counts.index,
                autopct='%1.1f%%',
                startangle=90,
                colors=["skyblue", "lightgreen", "salmon"]
            )
            ax.set_title("Messages by Group")
            st.pyplot(fig)

        with col2:
            st.subheader("Frequency of Messages by Group")
            group_message_count = data.groupby('group').size().reset_index(name='message_count')

            fig, ax = plt.subplots()
            ax.plot(group_message_count['group'], group_message_count['message_count'], marker='o', linestyle='-', color='skyblue')
            ax.set_xlabel('Group Name')
            ax.set_ylabel('Message Count')
            ax.set_title('Message Frequency by Group')
            st.pyplot(fig)

if __name__ == "__main__":
    main()
