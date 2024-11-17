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
    all_pdf_data = []

    processed_files = load_processed_files()
    if os.getenv("OVERWRITE_DATA") == "True":
        processed_files = []
    else:
        processed_files = load_processed_files()

    pdf_files = [
        f
        for f in os.listdir(pdf_dir)
        if f.lower().endswith(".pdf") and f not in processed_files
    ]

    if not pdf_files:
        print("No new PDF files found.")
        return []

    for pdf_filename in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    # pr::xallnt(page.extract_text())
                    text = page.extract_text()
                    lines = text.splitlines()

                    order_id, product_name, sku, seller_sku, qty, qty_total = (
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                    )

                    print("---------------------")

                    for idx, line in enumerate(lines):
                        print(idx, line)
                        # Look for specific fields based on patterns
                        if "Order ID:" in line:
                            order_id = line.split("Order ID:")[1].strip()

                            # Match "Product Name" and extract its value from the next line
                        if line.strip() == "Product Name":
                            if idx + 4 < len(lines):  # Check if the next line exists
                                product_name = lines[idx + 4].strip()

                        # Match "SKU" and extract its value from the next line
                        if line.strip() == "SKU":
                            if idx + 4 < len(lines):  # Check if the next line exists
                                sku = lines[idx + 4].strip()

                        # Match "Seller SKU" and extract its value from the next line
                        if line.strip() == "Seller SKU":
                            if idx + 4 < len(lines):  # Check if the next line exists
                                seller_sku = lines[idx + 4].strip()

                        # Match "Qty" and extract its value from the next line
                        if line.strip() == "Qty":
                            if idx + 4 < len(lines):  # Check if the next line exists
                                qty = lines[idx + 4].strip()

                        # Match "Qty Total" and extract its value from the next line
                        if line.strip() == "Qty Total:":
                            if idx + 2 < len(lines):  # Check if the next line exists
                                qty_total = lines[idx + 2].strip()

                    if order_id:
                        print(order_id, product_name, sku, seller_sku, qty, qty_total)
                        all_pdf_data.append(
                            {
                                "Order ID": order_id,
                                "Product Name": product_name,
                                "SKU": sku,
                                "Seller SKU": seller_sku,
                                "Qty": qty,
                                "Qty Total": qty_total,
                                "filename": pdf_filename,
                            }
                        )
                        order_id, product_name, sku, seller_sku, qty, qty_total = (
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                        )

        except Exception as e:
            print(f"Error processing {pdf_filename}: {e}")

    return all_pdf_data


def load_processed_files(file_path="processed_files.txt"):
    """
    Load list of processed files from a .txt file
    """
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as file:
        return file.read().splitlines()


def save_processed_files(processed_files, file_path="processed_files.txt"):
    """
    Save list of processed files to a .txt file
    """
    with open(file_path, "w") as file:
        file.write("\n".join(processed_files))


def get_google_sheets_service():
    """
    Authenticate and create Google Sheets service
    """
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def get_google_sheet_data(service, spreadsheet_id, range_name):
    """
    Retrieve data from a Google Sheet
    """
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    return result.get("values", [])


def insert_to_google_sheet(service, spreadsheet_id, range_name, values, append=False):
    """
    Insert data into a Google Sheet
    """
    body = {"values": values}
    if append:
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )
    else:
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
        pdf_dir = "./pdf/"
        order_data_list = extract_pdf_data(pdf_dir)

        SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
        RANGE_NAME = os.getenv("RANGE_NAME")
        if not SPREADSHEET_ID or not RANGE_NAME:
            raise ValueError("SPREADSHEET_ID and RANGE_NAME must be set")

        service = get_google_sheets_service()
        existing_data = get_google_sheet_data(service, SPREADSHEET_ID, RANGE_NAME)

        if os.getenv("OVERWRITE_DATA") == "True":
            print("Overwriting data.")
            print("Google Sheet is empty. Overwriting data.")

            header = [
                "Order ID",
                "Product Name",
                "SKU",
                "Seller SKU",
                "Qty",
                "Qty Total",
            ]
            values = [header] + [
                [
                    order["Order ID"],
                    order["Product Name"],
                    order["SKU"],
                    order["Seller SKU"],
                    order["Qty"],
                    order["Qty Total"],
                ]
                for order in order_data_list
            ]
            # print(values)
            insert_to_google_sheet(
                service, SPREADSHEET_ID, RANGE_NAME, values, append=False
            )
        else:
            if not existing_data:
                print("Google Sheet is empty. Overwriting data.")

                header = ["Order Number", "Quantity Total", "Total Amount", "Date"]
                values = [header] + [
                    [
                        order["order_number"],
                        order["quantity_total"],
                        order["total_amount"],
                        order["date"],
                    ]
                    for order in order_data_list
                ]
                insert_to_google_sheet(
                    service, SPREADSHEET_ID, RANGE_NAME, values, append=False
                )
            else:
                print("Appending data to Google Sheet.")
                values = [
                    [order["order_number"], order["total_amount"], order["date"]]
                    for order in order_data_list
                ]
                insert_to_google_sheet(
                    service, SPREADSHEET_ID, RANGE_NAME, values, append=True
                )

        # Update processed files
        processed_files = load_processed_files()
        processed_files.extend([order["filename"] for order in order_data_list])
        save_processed_files(processed_files)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
