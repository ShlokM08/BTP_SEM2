import pandas as pd
import re

def validate_csv_format(df):
    """Validate if CSV has required columns"""
    required_columns = ['User Name', 'Phone Number']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns in CSV: {', '.join(missing_columns)}. "
                        f"CSV must contain 'User Name' and 'Phone Number' columns.")
    
    # Check if columns have data
    if df.empty:
        raise ValueError("CSV file is empty")
    
    if df['User Name'].isna().all() or df['Phone Number'].isna().all():
        raise ValueError("One or more required columns are empty")
        
    print("CSV Validation successful!")
    print("DataFrame shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("First few rows:\n", df.head())

def replace_numbers_with_names(chat_file_path, csv_file_path, output_file_path):
    """
    Replace phone numbers in WhatsApp chat with corresponding names from CSV file.
    
    Parameters:
    chat_file_path (str): Path to WhatsApp chat text file
    csv_file_path (str): Path to CSV file containing name-number mappings
    output_file_path (str): Path where the processed chat file will be saved
    """
    try:
        print(f"\nDebug: Reading CSV file from {csv_file_path}")
        # First, verify the CSV file exists and has content
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()


            print("CSV content length:", len(csv_content))
            print("First 100 chars of CSV:", csv_content[:100])
            
        if not csv_content.strip():
            raise ValueError("CSV file is empty")
        
        # Try reading with pandas
        df = pd.read_csv(csv_file_path)
        print("Successfully read CSV with pandas")
        print("DataFrame info:")
        print(df.info())
        
        # Validate CSV format
        validate_csv_format(df)
        
        # Remove any spaces or special characters from phone numbers in CSV
        df['Phone Number'] = df['Phone Number'].astype(str)
        df['Phone Number'] = df['Phone Number'].str.replace(r'\s+|-|\+', '', regex=True)
        
        # Create mapping dictionaries
        number_to_name = {str(number): name for name, number in zip(df['User Name'], df['Phone Number'])}
        print("\nCreated number to name mapping:")
        print(number_to_name)
        
        print(f"\nDebug: Reading chat file from {chat_file_path}")
        # Read the chat file
        with open(chat_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

            print("Number of lines in chat:", len(lines))
            print("First line of chat:", lines[0] if lines else "No lines")
        
        processed_lines = []
        for line in lines:
            processed_line = line
            
            # Pattern 1: "+91 XXXXX XXXXX" format
            matches = re.finditer(r'\+91\s*(\d{5})\s*(\d{5})', processed_line)
            for match in matches:
                full_number = '91' + match.group(1) + match.group(2)
                if full_number in number_to_name:
                    original = match.group(0)
                    processed_line = processed_line.replace(original, number_to_name[full_number])
            
            # Pattern 2: "@91XXXXXXXXXX" format
            matches = re.finditer(r'@91(\d{10})', processed_line)
            for match in matches:
                full_number = '91' + match.group(1)
                if full_number in number_to_name:
                    original = match.group(0)
                    processed_line = processed_line.replace(original, '@' + number_to_name[full_number])
            
            processed_lines.append(processed_line)
        
        print(f"\nDebug: Writing output file to {output_file_path}")
        # Writing to file
        with open(output_file_path, 'w', encoding='utf-8') as file:
                file.writelines(processed_lines)

            
        print("Processing completed successfully!")
            
    except pd.errors.EmptyDataError:
        print("Pandas EmptyDataError occurred")
        raise ValueError("The CSV file is empty or contains no valid data")
    except Exception as e:
        print(f"Exception occurred: {type(e).__name__}: {str(e)}")
        raise Exception(f"Error processing files: {str(e)}")
