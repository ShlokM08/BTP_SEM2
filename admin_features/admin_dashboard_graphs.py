import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from pymongo import MongoClient
import os

# Load environment variables
load_dotenv()

def main():
    # Streamlit setup
    st.title("Group Chat Analysis")

    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))

    # Access the default database and the `text_freq` collection
    db = client[os.getenv('MONGO_DB_NAME')]  # Use the user_analytics DB from the .env file
    collection = db[os.getenv('MONGO_COLLECTION')]  # Use the text_freq collection

    # Query data from MongoDB (assuming documents are stored in the same format)
    data_cursor = collection.find({})
    data = pd.DataFrame(list(data_cursor))

    # Check if data is present
    if not data.empty:
        # Data parsing and processing
        data['timestamp'] = pd.to_datetime(data['timestamp'], format='%d/%m/%Y, %H:%M')

        # Active users plot
        active_users = data['user'].nunique()
        st.subheader(f"Active Users: {active_users}")
        st.bar_chart(data['user'].value_counts())

        # Frequency of chats plot
        chat_freq = data['user'].value_counts()
        st.subheader("Chat Frequency by Users")
        st.bar_chart(chat_freq)

        # Text comparison plot
        st.subheader("Text Comparison Across Groups")
        # Add your logic for text comparison between groups (e.g., using word clouds or other methods)

        # User activity plot - X-axis: Frequency of Messages, Y-axis: Group Names (Line Graph)
        st.subheader("Frequency of Messages by Group")

        # Aggregate message count by group
        group_message_count = data.groupby('group').size().reset_index(name='message_count')

        # Plot line graph (X-axis: group names, Y-axis: message count)
        fig, ax = plt.subplots(facecolor='black')  # Set plot background to match dark theme
        ax.plot(group_message_count['group'], group_message_count['message_count'], marker='o', linestyle='-', color='skyblue')

        # Set Y-axis limits manually for better visibility (adjust as per your data)
        ax.set_ylim([min(group_message_count['message_count']) - 5, max(group_message_count['message_count']) + 5])

        # Enhance the appearance
        ax.set_xlabel('Group Name', fontsize=12, color='white')
        ax.set_ylabel('Message Count', fontsize=12, color='white')
        ax.set_title('Message Frequency by Group', fontsize=14, fontweight='bold', color='white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')

        # Set axis background to black to match the overall theme
        ax.set_facecolor('black')

        # Display plot
        st.pyplot(fig)

    else:
        st.write("No data found in the MongoDB collection.")

# Allow this file to be run standalone for testing or be imported with `main` callable
if __name__ == "__main__":
    main()
