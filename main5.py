import pdfplumber
import time

# Load the PDF file
pdf_path = "./pdf/sample2.pdf"

# Initialize a list to store product details
product_details = []


# Hàm trích xuất thông tin bảng không viền dựa trên từ khóa
def extract_table_without_borders(pdf_path):
    extracted_data = []
    metadata = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Trích xuất toàn bộ văn bản trên trang
            """ table = page.extract_table(
                {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    # "snap_y_tolerance": 5,
                    # "intersection_x_tolerance": 15,
                }
            ) """

            table = page.extract_tables(
                table_settings={
                    "vertical_strategy": "explicit",
                    "horizontal_strategy": "lines",
                    "explicit_vertical_lines": [0, 35, 36, 55, 56, 75, 76, 85],
                }
            )

            tables = page.debug_tablefinder(
                {"vertical_strategy": "text", "horizontal_strategy": "lines"}
            )

            for t in tables.tables:
                print("box", t.bbox)
                for cell in t.cells:  # iterating through the required cells
                    print(cell)
                    c = page.crop(cell).extract_words()  # extract the words
                    print(c)

            text = page.extract_text(keep_blank_chars=True)
            # print(text)
            # print(table)
            # Phân tách từng dòng
            lines = text.split("\n")

            # Tìm các dòng chứa thông tin liên quan đến sản phẩm
            header_found = False
            index = 0
            order_id = ""
            order_qty = ""
            for line in lines:
                if not header_found and "Product Name" in line:
                    # Phát hiện dòng tiêu đề
                    header_found = True
                    continue

                if header_found:
                    if "Order ID:" in line:
                        order_id = line.split(":")[1].strip()
                        metadata["order_id"] = order_id
                        continue
                    if "Qty Total:" in line:
                        order_qty = line.split(":")[1].strip()
                        metadata["order_qty"] = order_qty
                        continue
                    # Dòng dữ liệu sản phẩm (phân tích dựa trên dấu phân cách hoặc định dạng)
                    columns = line.split(" ")  # Chia dữ liệu dựa trên khoảng trắng
                    print(columns)
                    # Xử lý và ánh xạ cột
                    if len(columns) >= 3:
                        sku = ""
                        qty = ""
                        print(columns[-1])
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
                            {"Product Name": product_name, "SKU": sku, "Qty": qty}
                        )
                    else:
                        extracted_data.append(
                            {
                                "Product Name": " ".join(columns),
                                "SKU": "NA",
                                "Qty": "NA",
                            }
                        )

    return extracted_data, metadata  # Gọi hàm để trích xuất bảng


raw_data = extract_table_without_borders(pdf_path)


def merge_products(data):
    merged_data = []
    temp_product_name = []

    current_idx = 0
    for item in data:
        # Kiểm tra nếu 'Qty' có thể chuyển đổi thành số nguyên
        if item["Qty"].isdigit():
            # Gộp các Product Name và thêm vào danh sách kết quả
            """ merged_data.append(
                {
                    "Product Name": item["Product Name"],
                    "SKU": item["SKU"],
                    "Qty": item["Qty"],
                }
            ) """
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

    return merged_data


print("ouput:", merge_products(raw_data))
""" for idx, raw_row in enumerate(raw_data):
    print(idx, raw_row)
    product_name = ""
    sku = ""
    qty = ""
    if raw_row["Qty"] != "NA":
        reset = True
        sku = raw_row["SKU"]
        qty = raw_row["Qty"]
    else:
        if product_name == "":
            product_name = raw_row["Product Name"]

    if reset and raw_row["Product Name"] != "":
        product_name = product_name + " " + raw_row["Product Name"]

    if idx + 1 < len(raw_data) and raw_data[idx + 1]["Qty"] == "1":
        reset = False
        data.append({"Product Name": product_name, "SKU": sku, "Qty": qty})
        product_name = ""
        sku = ""
        qty = ""


# Hiển thị kết quả
for row in data:
    print(row)
# Process the PDF using pdfplumber """
