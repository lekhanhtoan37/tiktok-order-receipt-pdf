import PyPDF2
import pandas as pd
import cv2
import pytesseract
import numpy as np


def extract_product_data(pdf_file):
    with open(pdf_file, "rb") as pdf_reader:
        reader = PyPDF2.PdfReader(pdf_reader)
        page = reader.pages[0]  # Giả sử thông tin sản phẩm nằm ở trang đầu tiên

        # Chuyển đổi trang PDF thành hình ảnh
        page_image = page.to_image()
        img = cv2.cvtColor(np.array(page_image), cv2.COLOR_RGB2BGR)

        # Xử lý ảnh để tăng độ tương phản, giảm nhiễu
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Tìm các đường thẳng
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10
        )

        # Tìm dòng bắt đầu chứa thông tin sản phẩm
        text = page.extract_text()
        lines_text = text.split("\n")
        start_index = 0
        for i, line in enumerate(lines_text):
            if "Product Name" in line:
                start_index = i
                break

        # Tạo một list để lưu trữ thông tin các sản phẩm
        products = []
        current_product = {}
        for i in range(start_index, len(lines_text)):
            line = lines_text[i].strip()
            if not line:
                if current_product:
                    products.append(current_product)
                    current_product = {}
                continue

            # Chia dòng thành các cột
            columns = line.split(",")

            # Kiểm tra xem dòng này có phải là dòng đầu tiên của sản phẩm không
            if i == start_index or words[0].isupper():
                # Nếu là dòng đầu tiên hoặc từ đầu tiên viết hoa, thì đây là phần tên sản phẩm
                current_product["Product Name"] = (
                    current_product.get("Product Name", "") + " " + line
                )
            else:
                # Nếu không phải dòng đầu tiên và từ đầu tiên không viết hoa, thì đây là các thông tin khác của sản phẩm
                # Ví dụ:
                current_product["SKU"] = columns[0]
                current_product["Price"] = columns[1]

            # Kiểm tra xem có đường gạch ngang không và cập nhật current_product
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # Kiểm tra độ nghiêng của đường thẳng (để xác định xem có phải là đường ngang không)
                if abs(y2 - y1) < 10 and y1 > start_index * (
                    img.shape[0] / len(lines_text)
                ):
                    if current_product:
                        products.append(current_product)
                        current_product = {}
                    break

        # Tạo DataFrame từ danh sách sản phẩm
        df = pd.DataFrame(products)
        return df


# Ví dụ sử dụng hàm
pdf_file = "./pdf/sample.pdf"
df = extract_product_data(pdf_file)
df.to_csv("products.csv", index=False)
