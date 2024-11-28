import pdfplumber

# Đường dẫn tới file PDF

pdf_path = "./pdf/sample.pdf"


def extract_table_data(pdf_path):
    products = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[17:18]:
            # Sử dụng extract_table để lấy bảng
            table = page.extract_table(
                {
                    "vertical_strategy": "text",  # Phân chia cột dựa trên văn bản
                    "horizontal_strategy": "lines",  # Phân chia hàng dựa trên văn bản
                    "min_words_horizontal": 1,  # Tối thiểu 2 từ để nhận diện thành một cột
                }
            )
            print(table)
            """ if table:
                # Duyệt qua các dòng của bảng
                for row in table:
                    if (
                        "Combo" in row[0]
                    ):  # Kiểm tra nếu dòng có chứa "Combo" (Product Name)
                        product_name = row[
                            0
                        ].strip()  # Lấy tên sản phẩm từ cột đầu tiên
                        sku = (
                            row[1].strip() if len(row) > 1 else ""
                        )  # Lấy SKU từ cột thứ hai (nếu có)
                        qty = (
                            row[3].strip() if len(row) > 3 else "0"
                        )  # Lấy số lượng từ cột thứ tư (nếu có)

                        products.append(
                            {
                                "Product Name": product_name,
                                "SKU": sku,
                                "Seller SKU": "",  # Không có Seller SKU trong bảng này
                                "Qty": int(qty),
                            }
                        ) """

    return products


# Gọi hàm để trích xuất thông tin sản phẩm
product_data = extract_table_data(pdf_path)

# Hiển thị kết quả
for product in product_data:
    print(product)
