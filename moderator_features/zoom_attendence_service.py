# zoom_attendance_service.py
import streamlit as st
from datetime import datetime
import pandas as pd
from bson import ObjectId

class ZoomAttendanceService:
    def __init__(self, db):
        self.db = db
        self.collection = db["zoom_attendance"]

    def process_attendance_file(self, file):
        """Process the uploaded attendance file and return structured data"""
        try:
            # Read the CSV file using pandas
            df = pd.read_csv(file)
            
            # Process each row in the dataframe
            attendance_records = []
            for _, row in df.iterrows():
                record = {
                    "_id": str(ObjectId()),
                    "name": row["Name (original name)"],  # Fixed column name
                    "date_of_file_upload": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_of_meet_mins": int(row["Total duration (minutes)"])  # Fixed column name
                }
                attendance_records.append(record)
            
            return {
                "status": "success",
                "data": attendance_records,
                "message": f"Successfully processed {len(attendance_records)} attendance records"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing attendance file: {str(e)}"
            }

    def save_attendance_data(self, group_name, attendance_data, uploaded_by):
        """Save the processed attendance data to MongoDB"""
        try:
            # Add metadata to each record
            for record in attendance_data:
                record.update({
                    "group_name": group_name,
                    "uploaded_by": uploaded_by,
                    "upload_timestamp": datetime.now()
                })
            
            # Insert the records into MongoDB
            result = self.collection.insert_many(attendance_data)
            
            return {
                "status": "success",
                "data": {
                    "attendance_ids": [str(id) for id in result.inserted_ids],
                    "records_count": len(result.inserted_ids)
                },
                "message": f"Successfully saved {len(result.inserted_ids)} attendance records"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error saving attendance data: {str(e)}"
            }

def handle_zoom_attendance_upload(attendance_service, group_name, uploaded_file, user_name):
    """Handle Zoom attendance file upload and processing"""
    try:
        # Process the attendance file
        process_result = attendance_service.process_attendance_file(uploaded_file)
        
        if process_result["status"] == "error":
            st.error(f"Error processing file: {process_result['message']}")
            return
            
        # Show preview of parsed data
        st.write("Preview of processed attendance records:")
        st.write(pd.DataFrame(process_result["data"]))
        
        # Save button
        if st.button(f"Save {group_name}'s Zoom attendance to database"):
            save_result = attendance_service.save_attendance_data(
                group_name,
                process_result["data"],
                user_name
            )
            
            if save_result["status"] == "success":
                st.success(f"""
                    Zoom attendance for {group_name} uploaded and saved successfully!
                    Records saved: {save_result['data']['records_count']}
                """)
            else:
                st.error(f"Error saving to database: {save_result['message']}")
                
    except Exception as e:
        st.error(f"Error handling Zoom attendance: {str(e)}")
