import csv
import json
from bson import ObjectId  # For MongoDB ObjectId
from datetime import datetime

def process_attendance_csv(file_path):
    # List to hold the processed records
    attendance_records = []

    # Read the CSV file
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        
        # Process each row in the CSV
        for row in csv_reader:
            record = {
                "_id": str(ObjectId()),  # Generate a MongoDB ObjectId
                "name": row["Name (original name)"],  # Corrected column for name
                "date_of_file_upload": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_of_Meet(in_mins)": int(row["Total duration (minutes)"])  # Corrected column for duration
            }
            attendance_records.append(record)
    
    # Convert the records to JSON
    return json.dumps(attendance_records, indent=4)

# Path to the uploaded CSV file
file_path = '/home/bhartrihari/UCSF_Project/UCSFR01/Stage_2_All_Data_Combined/Data/Zoom_Data/attendence.csv'
# Call the function and print the output
attendance_json = process_attendance_csv(file_path)
print(attendance_json)
