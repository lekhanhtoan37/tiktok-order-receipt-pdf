from PyPDF2 import PdfReader


def extract_data_with_rectangles(file_path):
    # Initialize reader
    reader = PdfReader(file_path)
    data = []

    for page in reader.pages[0::-2]:
        print(page)
        print(page.get_object())
        annot = page.get("/Annots")
        print("annot", annot)
        if "/Annots" in page:
            for annot in page["/Annots"]:
                obj = annot.get_object()
                print(obj)
                # annotation = {"subtype": obj["/Subtype"], "location": obj["/Rect"]}
                # print(annotation)
        else:
            print("No annotations found.")

    return data

    for page_num, page in enumerate(reader.pages):
        # Extract text and positional information
        raw_text = page.extract_text()

        # Extract annotations, if present
        annotations = []
        if "/Annots" in page:
            for annot_ref in page["/Annots"]:
                annotation = annot_ref.get_object()  # Dereference the IndirectObject
                annotations.append(annotation)
        rect_positions = []

        if annotations:
            # Resolve indirect objects
            for annot_ref in annotations:
                annot = annot_ref.get_object()
                if annot:
                    rect = annot.get("/Rect")
                    if rect:
                        # Extract and normalize the coordinates
                        rect_positions.append(tuple(map(float, rect)))

        # Extract text lines
        lines = raw_text.splitlines()

        # Process sections using rectangles (example logic)
        current_section = []
        last_y = None

        for line in lines:
            # Simulate Y-coordinate logic (you can replace this with real rectangle-based coordinates)
            line_y = len(
                line
            )  # Placeholder for Y-coordinate based on line length (mock logic)
            if (
                last_y is not None and abs(line_y - last_y) > 50
            ):  # Example gap threshold
                if current_section:
                    process_section(current_section, data)
                    current_section = []  # Reset section
            current_section.append(line)
            last_y = line_y

        # Process any remaining section
        if current_section:
            process_section(current_section, data)

    print(data)
    return data


def process_section(lines, data):
    """
    Parse a section of text and append structured data.
    """
    order_id, product_name, sku, seller_sku, qty, qty_total = (
        None,
        None,
        None,
        None,
        None,
        None,
    )
    for i, line in enumerate(lines):
        if "Order ID:" in line:
            order_id = line.split("Order ID:")[1].strip()
        elif line.strip() == "Product Name":
            product_name = (
                " ".join(lines[i + 1 :]).split("SKU")[0].strip()
            )  # Example split
        elif line.strip() == "SKU":
            sku = lines[i + 1].strip()
        elif line.strip() == "Seller SKU":
            seller_sku = lines[i + 1].strip()
        elif line.strip() == "Qty":
            qty = lines[i + 1].strip()
        elif line.strip() == "Qty Total:":
            qty_total = lines[i + 1].strip()

    if order_id and product_name and sku and seller_sku and qty and qty_total:
        data.append(
            {
                "Order ID": order_id,
                "Product Name": product_name,
                "SKU": sku,
                "Seller SKU": seller_sku,
                "Qty": qty,
                "Qty Total": qty_total,
            }
        )


# Example usage
file_path = "./pdf/sample.pdf"
data = extract_data_with_rectangles(file_path)

# Print the structured data
for record in data:
    print(record)
