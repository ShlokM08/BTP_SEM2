import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def moderator_graph_main():
    st.title("Group Chat Analysis")

    # Connect to MongoDB
    try:
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client[os.getenv("MONGO_DB_NAME")]
        collection = db[os.getenv("MONGO_COLLECTION")]
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {str(e)}")
        return

    # Fetch data
    try:
        data_cursor = collection.find({})
        data = pd.DataFrame(list(data_cursor))

        if data.empty:
            st.error("No data found in the database.")
            return

        # Ensure required fields are present
        required_fields = ["user", "group", "timestamp", "message"]
        for field in required_fields:
            if field not in data.columns:
                st.error(f"Missing required field: {field}")
                return

        # Convert timestamp to datetime
        data["timestamp"] = pd.to_datetime(data["timestamp"], format="%d/%m/%Y, %H:%M", errors="coerce")

        # Layout setup: Create metrics
        st.markdown("### Chat Metrics Overview")
        col1, col2, col3 = st.columns(3)

        with col1:
            total_members = data["user"].nunique()
            st.metric("Total Members", total_members)

        with col2:
            total_groups = data["group"].nunique()
            st.metric("Total Groups", total_groups)

        with col3:
            total_messages = len(data)
            st.metric("Total Messages", total_messages)

        # Filters Section
        st.markdown("### Filters and Sorting")
        col1, col2 = st.columns(2)

        with col1:
            group_filter = st.selectbox("Select Group", ["All"] + sorted(data["group"].dropna().unique().tolist()))
        with col2:
            sort_option = st.selectbox("Sort By", ["None", "Timestamp", "Group", "User"])

        # Apply group filter
        if group_filter != "All":
            data = data[data["group"] == group_filter]

        # Apply sorting
        if sort_option == "Timestamp":
            data = data.sort_values(by="timestamp")
        elif sort_option == "Group":
            data = data.sort_values(by="group")
        elif sort_option == "User":
            data = data.sort_values(by="user")

        # Visualization
        st.markdown("### Visualizations")
        col1, col2 = st.columns(2)

        with col1:
            active_users = data["user"].nunique()
            st.subheader(f"Active Users: {active_users}")
            user_message_count = data["user"].value_counts()
            st.bar_chart(user_message_count)

        with col2:
            st.subheader("Chat Frequency by Groups")
            group_message_count = data["group"].value_counts()
            st.bar_chart(group_message_count)

        # Text Comparison Across Groups
        st.markdown("### Text Comparison Across Groups")
        col1, col2 = st.columns(2)

        with col1:
            group_counts = data["group"].value_counts()
            fig, ax = plt.subplots()
            ax.pie(
                group_counts,
                labels=group_counts.index,
                autopct="%1.1f%%",
                startangle=90,
                colors=["skyblue", "lightgreen", "salmon"]
            )
            ax.set_title("Messages by Group")
            st.pyplot(fig)

        with col2:
            st.subheader("Frequency of Messages by Group")
            group_message_count = data.groupby("group").size().reset_index(name="message_count")

            fig, ax = plt.subplots()
            ax.plot(
                group_message_count["group"],
                group_message_count["message_count"],
                marker="o",
                linestyle="-",
                color="skyblue"
            )
            ax.set_xlabel("Group Name")
            ax.set_ylabel("Message Count")
            ax.set_title("Message Frequency by Group")
            st.pyplot(fig)

        # Display processed data
        st.markdown("### Processed Data")
        st.dataframe(data)

    except Exception as e:
        st.error(f"Error fetching or processing data: {str(e)}")

if __name__ == "__main__":
    main()
