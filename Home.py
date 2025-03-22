import io
import json
import os
import re
from fpdf import FPDF
from PIL import Image
from pdf2image import convert_from_bytes
from fuzzywuzzy import fuzz
import streamlit as st
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
import tempfile
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import spending_trends



st.set_page_config(page_title="Home", page_icon="🏠")


# Configure APIs and credentials
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
credentials = service_account.Credentials.from_service_account_info(st.secrets["GOOGLE_CREDENTIALS"])
client = vision.ImageAnnotatorClient(credentials=credentials)

# Required columns (for clarity)
REQUIRED_COLUMNS = ["store_name", "date", "bill_no", "total_amount", "extracted_text"]

# Initialize session state for invoices and invoice images
if "invoices" not in st.session_state:
    st.session_state.invoices = []
if "invoice_images" not in st.session_state:
    st.session_state.invoice_images = {}

# -----------------------
# Helper Functions
# -----------------------

def extract_text(image):
    """Extract text using Google Vision API."""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    image_for_api = vision.Image(content=img_byte_arr)
    response = client.text_detection(image=image_for_api)
    texts = response.text_annotations
    return texts[0].description if texts else ""

def extract_entities(text):
    """Extract structured invoice data including GSTIN and category prediction using Gemini API."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Extract the following details from this invoice text:
    - Store Name
    - Date (if the date is in a different format, convert it to DD/MM/YYYY format)
    - Bill Number
    - Total Amount
    - Category (choose from: Food, Travel, Office Supplies, Utilities, Others)
    - GSTIN

    Use the following **keywords for category classification**:
    - **Food**: restaurant, cafe, grocery, food, beverage, bakery, supermarket
    - **Travel**: flight, airline, hotel, taxi, fuel, petrol, Uber, Ola, bus, train
    - **Office Supplies**: stationery, printer, ink, paper, pen, laptop, computer, mouse, keyboard
    - **Utilities**: electricity, water, internet, mobile bill, phone bill, broadband, gas
    - **Others**: (use this if no relevant category is found)

    Provide ONLY a JSON response with these keys: "store_name", "date", "bill_no", "total_amount", "category", "gstin".
    Do NOT include any additional text, explanation, or formatting outside of the JSON object.

    Invoice text:
    {text}
    """
    response = model.generate_content(prompt)
    try:
        json_text = response.text.strip()
        json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
        invoice_data = json.loads(json_text)
        return invoice_data
    except json.JSONDecodeError:
        return {
            "store_name": "N/A",
            "date": "N/A",
            "bill_no": "N/A",
            "total_amount": "0",
            "category": "Others",
            "gstin": "N/A"
        }


def check_duplicate(extracted_text, threshold=90):
    """Compare extracted text with session state invoices for duplicate detection."""
    for stored_invoice in st.session_state.invoices:
        stored_text = stored_invoice.get("extracted_text", "")
        similarity_score = fuzz.ratio(extracted_text, stored_text)
        if similarity_score >= threshold:
            return stored_invoice["id"], similarity_score
    return None, 0

def save_to_session_state(invoice_data, image):
    """Save invoice details and image to session state."""
    invoice_id = len(st.session_state.invoices) + 1  # Next available ID
    invoice_data["id"] = invoice_id
    st.session_state.invoices.append(invoice_data)
    st.session_state.invoice_images[invoice_id] = image
    return invoice_id

def process_pdf(uploaded_file):
    """Convert PDF pages to images and extract text."""
    images = convert_from_bytes(uploaded_file.read())
    extracted_text = extract_text(images[0])
    return extracted_text, images[0]

def calculate_total_amount():
    """Calculate the sum of total_amount from session state invoices."""
    total = sum(float(invoice.get("total_amount") or 0) for invoice in st.session_state.invoices)
    return total

def clear_session_state_data():
    """Clear all invoices and images from session state."""
    st.session_state.invoices.clear()
    st.session_state.invoice_images.clear()


def wrap_text(text, max_width, pdf):
    """
    Wrap text so that each line's width is less than max_width.
    Returns a string with newline characters inserted.
    """
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        # Check if adding the next word exceeds the max width.
        test_line = current_line + (" " if current_line else "") + word
        if pdf.get_string_width(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:  # Add the current line if it's not empty
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)

def generate_invoice_pdf():
    """Generate a PDF with invoice summaries and charts."""
    progress_bar = st.progress(0)
    progress = 0

    # Step 1: Create PDF and add summary table
    progress_bar.progress(progress + 10)
    time.sleep(0.5)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, "Invoice Summary", ln=True, align="C")
    pdf.ln(10)
    
    # Calculate total sum with fallback for total_amount
    total_sum = sum(float(invoice.get("total_amount") or 0) for invoice in st.session_state.invoices)
    
    pdf.set_font("Arial", style='B', size=10)
    # Updated column widths: [Bill ID, Store Name, GSTIN, Date, Category, Total Amount]
    col_widths = [15, 50, 42, 25, 30, 30]
    headers = ["Bill ID", "Store Name", "GSTIN", "Date", "Category", "Total Amount"]
    progress += 10
    progress_bar.progress(progress + 10)
    time.sleep(0.5)
    
    # Draw table headers using normal cell since they are short
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    line_height = 5  # Height for each line of text
    # Loop through each invoice to print rows with wrapped text.
    for invoice in st.session_state.invoices:
        # Retrieve each field with fallback
        row_data = [
            str(invoice.get("id") or "N/A"),
            invoice.get("store_name") or "N/A",
            invoice.get("gstin") or "N/A",
            invoice.get("date") or "N/A",
            invoice.get("category") or "N/A",
            f"{float(invoice.get('total_amount') or 0):.2f}"
        ]
        
        # Wrap text in each cell and determine maximum number of lines for the row.
        wrapped_cells = []
        max_lines = 1
        for i, cell in enumerate(row_data):
            # Subtracting a small padding from col_width if needed.
            wrapped = wrap_text(cell, col_widths[i] - 2, pdf)
            lines = wrapped.split("\n")
            wrapped_cells.append(wrapped)
            if len(lines) > max_lines:
                max_lines = len(lines)
        row_height = line_height * max_lines
        
        # Save starting X and Y positions for the row.
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        # For each cell in the row, print the multi-line text and draw the border.
        for i, cell in enumerate(wrapped_cells):
            x_current = pdf.get_x()
            # Print the cell text with multi_cell.
            pdf.multi_cell(col_widths[i], line_height, cell, border=0)
            # Reset position to top-left of the current cell.
            pdf.set_xy(x_current, y_start)
            # Draw the cell border.
            pdf.rect(x_current, y_start, col_widths[i], row_height)
            # Move to the next cell on the right.
            pdf.set_xy(x_current + col_widths[i], y_start)
        # Move cursor to the next row.
        pdf.ln(row_height)
        progress += 5
        progress_bar.progress(progress)
    
    # Draw total amount row
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(sum(col_widths[:-1]), 8, "Total Amount", border=1, align="R")
    pdf.cell(col_widths[-1], 8, f"{total_sum:.2f}", border=1, align="C")
    pdf.ln(10)
    
    # Step 2: Add Spending Trends Charts
    pie_chart_path, line_chart_path, bar_chart_path = spending_trends(silent=True)# Call the function with silent=True for no display 

    invoice_df = pd.DataFrame(st.session_state.invoices)
    invoice_df['total_amount'] = pd.to_numeric(invoice_df['total_amount'], errors='coerce')
    spending_by_category = invoice_df.groupby('category').agg({'total_amount': 'sum'}).reset_index()
    
    pie_chart_path = tempfile.mkstemp(suffix=".png")[1]
    plt.figure(figsize=(8, 6))
    plt.pie(spending_by_category['total_amount'], labels=spending_by_category['category'], autopct='%1.1f%%', startangle=140)
    plt.title("Spending by Category")
    plt.savefig(pie_chart_path, format="png")
    plt.close()
    
    line_chart_path = tempfile.mkstemp(suffix=".png")[1]
    spending_by_date = invoice_df.groupby('date').agg({'total_amount': 'sum'}).reset_index()
    plt.figure(figsize=(10, 6))
    plt.plot(spending_by_date['date'], spending_by_date['total_amount'], marker='o')
    plt.title("Spending Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Total Amount (₹)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.savefig(line_chart_path, format="png")
    plt.close()
    
    bar_chart_path = tempfile.mkstemp(suffix=".png")[1]
    spending_by_store = invoice_df.groupby('store_name').agg({'total_amount': 'sum'}).reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='store_name', y='total_amount', data=spending_by_store, palette='viridis')
    plt.title("Spending by Store")
    plt.xlabel("Store Name")
    plt.ylabel("Total Amount (₹)")
    plt.xticks(rotation=45)
    plt.savefig(bar_chart_path, format="png")
    plt.close()
    
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, "Spending Trends", ln=True, align="C")
    pdf.ln(10)
    pdf.image(pie_chart_path, x=10, y=30, w=180)
    pdf.ln(100)
    pdf.image(line_chart_path, x=10, y=140, w=180)
    pdf.ln(100)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=14)
    pdf.image(bar_chart_path, x=10, y=30, w=180)
    progress += 10
    progress_bar.progress(progress)
    
    # Step 3: Add Invoice Images to the PDF
    for invoice_id, img in st.session_state.invoice_images.items():
        pdf.add_page()
        temp_path = os.path.join(tempfile.gettempdir(), f"invoice_{invoice_id}.png")
        img.save(temp_path, format="PNG")
        try:
            pdf.image(temp_path, x=10, y=10, w=180)
        finally:
            os.remove(temp_path)
        progress += 10
        progress_bar.progress(progress)
    
    # Step 4: Save PDF and provide download button
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    pdf.output(pdf_path)
    progress_bar.progress(100)
    st.success("✅ Invoice Summary PDF generated successfully!")
    
    with open(pdf_path, "rb") as pdf_file:
        st.download_button(
            label="📄 Download Invoice Summary PDF", 
            data=pdf_file, 
            file_name="invoices_summary.pdf", 
            mime="application/pdf",
            key="download_invoice_summary"
        )
    
    if os.path.exists(pdf_path):
        os.remove(pdf_path)




def display_invoice_details(invoice_id, invoice_data):
    # Apply fallbacks for every element
    store_name   = invoice_data.get("store_name") or "N/A"
    bill_no      = invoice_data.get("bill_no") or "N/A"
    date_value   = invoice_data.get("date") or "N/A"
    category     = invoice_data.get("category") or "N/A"
    total_amount = invoice_data.get("total_amount") or 0

    details = {
        "Field": ["Invoice ID", "Store Name", "Bill No", "Date", "Category", "Total Amount"],
        "Value": [
            invoice_id,
            store_name,
            bill_no,
            date_value,
            category,
            f"₹{float(total_amount):.2f}"
        ]
    }
    st.table(details)

def proceed_callback():
    invoice_data = extract_entities(st.session_state.duplicate_extracted_text)
    invoice_data["extracted_text"] = st.session_state.duplicate_extracted_text
    saved_id = save_to_session_state(invoice_data, st.session_state.duplicate_image)
    st.session_state["saved_invoice_id"] = saved_id
    st.session_state["saved_invoice_data"] = invoice_data
    st.session_state["show_table"] = True
    # Store the success message in session state
    st.session_state["success_message"] = f"✅ Invoice Saved successfully! Invoice ID: {saved_id}"
    # Clear the temporary duplicate data
    del st.session_state.duplicate_extracted_text
    del st.session_state.duplicate_image


def file_upload_handler(uploaded_file):
    """Handle file upload and invoice processing."""
    if uploaded_file.type == "application/pdf":
        extracted_text, image = process_pdf(uploaded_file)
    else:
        image = Image.open(uploaded_file)
        extracted_text = extract_text(image)
    
    # Check for duplicate invoices
    duplicate_id, similarity_score = check_duplicate(extracted_text)
    if duplicate_id:
        st.warning(f"⚠️ This invoice is similar to Invoice ID {duplicate_id} with a similarity score of {similarity_score}.")
        
        # Show both images side by side for comparison
        col1, col2 = st.columns(2)
        with col1:
            st.image(st.session_state.invoice_images[duplicate_id], caption=f"Existing Invoice - ID: {duplicate_id}",  use_container_width=True)
        with col2:
             st.image(image, caption="New Uploaded Invoice",  use_container_width=True)
            
        
        # Store duplicate data temporarily in session state
        st.session_state.duplicate_extracted_text = extracted_text
        st.session_state.duplicate_image = image
        
        # Use on_click callback to trigger proceed_callback when button is pressed
        st.button("Proceed to Save Anyway", key="proceed_duplicate_button", on_click=proceed_callback)
        return
    
    # Normal processing if no duplicate is found
    invoice_data = extract_entities(extracted_text)
    invoice_data["extracted_text"] = extracted_text
    invoice_id = save_to_session_state(invoice_data, image)
    st.session_state["saved_invoice_id"] = invoice_id
    st.session_state["saved_invoice_data"] = invoice_data
    st.session_state["show_table"] = True
    st.session_state["success_message"] = f"✅ Invoice Saved successfully! Invoice ID: {invoice_id}"


# -------------------------
# Main Streamlit UI Section
# -------------------------
st.title("Invoice Management System")

# Create a container for the uploader widget
if "file_upload_count" not in st.session_state:
    st.session_state.file_upload_count = 0
uploader_container = st.empty()

uploaded_file = uploader_container.file_uploader(
    "Upload Invoice Image or PDF", 
    type=["png", "jpg", "jpeg", "pdf"],
    key=f"uploaded_file_{st.session_state.file_upload_count}"
)

if uploaded_file:
    file_upload_handler(uploaded_file)
    st.session_state.file_upload_count += 1
    uploader_container.empty()
    uploader_container.file_uploader(
        "Upload Invoice Image or PDF", 
        type=["png", "jpg", "jpeg", "pdf"],
        key=f"uploaded_file_{st.session_state.file_upload_count}"
    )

# Create a placeholder for the success message (positioned below the uploader)
success_placeholder = st.empty()
if st.session_state.get("success_message"):
    with success_placeholder:
        st.success(st.session_state["success_message"])
    del st.session_state["success_message"]

# Create a placeholder BELOW the uploader container for the invoice details table
table_placeholder = st.empty()
if st.session_state.get("show_table", False):
    with table_placeholder:
        display_invoice_details(
            st.session_state["saved_invoice_id"],
            st.session_state["saved_invoice_data"]
        )
    st.session_state["show_table"] = False

    
# Additional UI buttons for other actions
if st.button("Sum of All Invoices"):
    total_sum = calculate_total_amount()
    st.success(f"💰 Total sum of all invoices: ₹{total_sum:.2f}")


if st.button("Clear All Data (Invoices & Images)"):
    clear_session_state_data()
    st.success("All invoices and saved images have been deleted.")

if st.button("Generate Invoice Summary PDF"):
    generate_invoice_pdf()
