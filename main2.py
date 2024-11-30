import os
import re
import PyPDF2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv
from numpy import extract
import pdfplumber
import csv
import sys

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

        data = extract_table_without_borders(pdf_path)
        if data:
            print(f"Extracted data from {pdf_filename}")
            merged_data = merge_products(data)
            if merged_data:
                for d in merged_data:
                    print(f"Merged data from {pdf_filename}, order_id: {d['order_id']}")
                    d["filename"] = pdf_filename
                    d["page"] = d["Page"]
                    all_pdf_data.append(d)
            else:
                print(f"No data to insert to sheet from {pdf_filename}")

    # print("all_pdf_data", all_pdf_data)
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


# Hàm trích xuất thông tin bảng không viền dựa trên từ khóa
def extract_table_without_borders(pdf_path):
    extracted_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            text = page.extract_text(keep_blank_chars=True)
            # Phân tách từng dòng
            lines = text.split("\n")

            # Tìm các dòng chứa thông tin liên quan đến sản phẩm
            header_found = False
            index = 0
            order_id = ""
            order_qty = ""
            first_line = ""
            for line in lines:
                if not header_found and "Product Name" in line:
                    # Phát hiện dòng tiêu đề
                    header_found = True
                    continue

                if header_found:
                    if "Order ID:" in line:
                        order_id = line.split(":")[1].strip()
                        for d in extracted_data:
                            if d["Page"] == idx + 1:
                                d["order_id"] = order_id
                        continue
                    if "Qty Total:" in line:
                        order_qty = line.split(":")[1].strip()
                        for d in extracted_data:
                            if d["Page"] == idx + 1:
                                d["order_qty"] = order_qty

                        continue
                    # Dòng dữ liệu sản phẩm (phân tích dựa trên dấu phân cách hoặc định dạng)
                    columns = line.split(" ")  # Chia dữ liệu dựa trên khoảng trắng
                    columns_len = len(columns)
                    if columns_len >= 3 and columns_len > len(first_line.split(" ")):
                        first_line = line
                    # Xử lý và ánh xạ cột
                    if columns_len >= len(first_line.split(" ")):
                        sku = ""
                        qty = ""
                        if columns[-1].isdigit():
                            sku = columns[-2]  # SKU (cột áp chót)
                            qty = columns[-1]  # Qty (cột cuối)
                            index += 1
                        else:
                            sku = "NA"
                            qty = "NA"

                        product_name = " ".join(
                            columns[:-2]
                        )  # Tên sản phẩm (trước 2 cột cuối)

                        if not columns[-1].isdigit():
                            product_name = " ".join(
                                columns
                            )  # Tên sản phẩm (trước 2 cột cuối)

                        # Lưu thông tin vào danh sách
                        extracted_data.append(
                            {
                                "Product Name": product_name,
                                "SKU": sku,
                                "Qty": qty,
                                "Page": idx + 1,
                            }
                        )

                    else:
                        extracted_data.append(
                            {
                                "Product Name": " ".join(columns),
                                "SKU": "NA",
                                "Qty": "NA",
                                "Page": idx + 1,
                            }
                        )

    return extracted_data  # Gọi hàm để trích xuất bảng


def merge_products(data: list):
    merged_data = []
    temp_product_name = []

    current_idx = 0
    if isinstance(data, str):
        return merged_data

    for item in data:
        # Kiểm tra nếu 'Qty' có thể chuyển đổi thành số nguyên
        if isinstance(item, str):
            continue

        try:
            if item["Qty"].isdigit():
                # Gộp các Product Name và thêm vào danh sách kết quả

                current_idx += 1
                temp_product_name = []  # Reset danh sách tạm thời

                # Thêm sản phẩm với Qty là số nguyên vào danh sách
                merged_data.append(item)
            else:
                # Nếu không phải số nguyên, gộp Product Name
                temp_product_name.append(item["Product Name"])

            # Xử lý trường hợp còn dữ liệu chưa gộp
            if len(temp_product_name) > 0:
                merged_data[current_idx - 1]["Product Name"] = (
                    merged_data[current_idx - 1]["Product Name"]
                    + " "
                    + " ".join(temp_product_name)
                )
        except Exception as e:
            print("merge_products error", e)
            continue

    return merged_data


def save_to_csv(data, filename="output.csv"):
    """Save the extracted data to a CSV file."""
    header = ["Order ID", "Product Name", "SKU", "Qty", "Qty Total", "Page", "Filename"]
    with open(
        filename, mode="w", newline="", encoding="utf-8"
    ) as file:  # Đảm bảo mã hóa utf-8
        writer = csv.writer(file)
        writer.writerow(header)  # Ghi header
        for row in data:
            writer.writerow(
                [
                    row.get("order_id", ""),
                    row.get("Product Name", ""),
                    row.get("SKU", ""),
                    row.get("Qty", ""),
                    row.get("order_qty", ""),
                    row.get("page", ""),
                    row.get("filename", ""),
                ]
            )  # Ghi các dữ liệu


def main():
    """
    Main function to process PDF and insert data to CSV file
    """
    print("Processing PDFs...")
    try:
        pdf_dir = "./pdf"

        order_data_list = extract_pdf_data(pdf_dir)

        if order_data_list:
            # Lưu dữ liệu vào file CSV
            save_to_csv(order_data_list, "order_data.csv")

        # Cập nhật danh sách các file đã xử lý
        processed_files = load_processed_files()
        processed_files.extend([order["filename"] for order in order_data_list])
        save_processed_files(processed_files)

        print("Process completed successfully.")
        sys.exit(0)  # Thoát với mã thành công (exit code 0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)  # Thoát với mã lỗi (exit code 1)


if __name__ == "__main__":
    main()
