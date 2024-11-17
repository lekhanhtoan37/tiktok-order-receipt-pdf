import os
import re
import PyPDF2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()


def extract_pdf_data(pdf_dir):
    """
    Extract data from TikTok receipt PDFs in a directory
    Args:
        pdf_dir (str): Path to the directory containing PDF files

    Returns:
        list: List of extracted order information dictionaries
    """
    # List to store extracted data from all PDFs
    all_pdf_data = []

    # Find all PDF files in the directory
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDF files found in the directory.")
        return []

    # Process each PDF file
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = reader.pages[0].extract_text()

                # Example extraction patterns (adjust based on actual PDF format)
                order_number = re.search(r"Order #(\d+)", text)
                total_amount = re.search(r"\$(\d+\.\d{2})", text)
                date = re.search(r"Date: (\d{2}/\d{2}/\d{4})", text)

                pdf_data = {
                    "filename": pdf_filename,
                    "order_number": order_number.group(1) if order_number else "N/A",
                    "total_amount": total_amount.group(1) if total_amount else "N/A",
                    "date": date.group(1) if date else "N/A",
                }

                all_pdf_data.append(pdf_data)

        except Exception as e:
            print(f"Error processing {pdf_filename}: {e}")

    return all_pdf_data


def get_google_sheets_service():
    """
    Authenticate and create Google Sheets service

    Returns:
        googleapiclient.discovery.Resource: Google Sheets service
    """
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = None

    # Use the following line if you have a Google API key
    # if os.getenv("GOOGLE_API_KEY"):
    # return build("sheets", "v4", developerKey=os.getenv("GOOGLE_API_KEY"))

    # The file token.json stores the user's access and refresh tokens
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def get_google_sheet_data():
    pass


def insert_to_google_sheet(service, spreadsheet_id, range_name, values):
    """
    Insert data into a Google Sheet

    Args:
        service: Google Sheets service
        spreadsheet_id (str): ID of the Google Sheet
        range_name (str): Sheet range to insert data
        values (list): Data to insert
    """
    values = [
        [
            "Name",
            "Email",
            "Phone Number",
            "Address",
            "City",
            "State",
            "Zip Code",
            "Country",
            "Notes",
        ],
    ]
    body = {"values": values}

    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )

    print(f"{result.get('updatedCells')} cells updated.")


def main():
    """
    Main function to process PDF and insert data to Google Sheet
    """

    print("Processing PDFs...")
    try:
        # Path to directory containing TikTok receipt PDFs
        # Change this to your PDF directory
        pdf_dir = "./pdf/"

        # Extract data from PDFs
        order_data_list = extract_pdf_data(pdf_dir)

        # Google Sheet details
        SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
        RANGE_NAME = os.getenv("RANGE_NAME")
        if not SPREADSHEET_ID or not RANGE_NAME:
            raise ValueError("SPREADSHEET_ID and RANGE_NAME must be set")

        # Prepare data for insertion
        for order_data in order_data_list:
            print(f"Processing {order_data['filename']}...")
            print(order_data)
            values = [
                [
                    order_data["order_number"],
                    order_data["total_amount"],
                    order_data["date"],
                ]
            ]

            # Get Google Sheets service and insert data
            service = get_google_sheets_service()
            insert_to_google_sheet(service, SPREADSHEET_ID, RANGE_NAME, values)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
