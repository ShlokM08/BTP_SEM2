import csv

def check_csv_headers(file_path):
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        headers = csv_reader.fieldnames
        print("CSV Headers:", headers)

# Path to the uploaded CSV file
file_path = file_path = '/home/bhartrihari/UCSF_Project/UCSFR01/Stage_2_All_Data_Combined/Data/Zoom_Data/attendence.csv'
# Call the function to check headers
check_csv_headers(file_path)
