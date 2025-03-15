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

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
credentials = service_account.Credentials.from_service_account_info(st.secrets["GOOGLE_CREDENTIALS"])
client = vision.ImageAnnotatorClient(credentials=credentials)

# Required columns
REQUIRED_COLUMNS = ["store_name", "date", "bill_no", "total_amount", "extracted_text"]

# Initialize session state
if "invoices" not in st.session_state:
    st.session_state.invoices = []
if "invoice_images" not in st.session_state:
    st.session_state.invoice_images = {}


def extract_text(image):
    """Extract text using Google Vision API."""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    image = vision.Image(content=img_byte_arr)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""


def extract_entities(text):
    """Extract structured invoice data including category prediction using Gemini API."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Extract the following details from this invoice text:
    - Store Name
    - Date (if the date is in a different format, convert it to DD/MM/YYYY format)
    - Bill Number
    - Total Amount
    - Category (choose from: Food, Travel, Office Supplies, Utilities, Others)

    Use the following **keywords for category classification**:
    - **Food**: restaurant, cafe, grocery, food, beverage, bakery, supermarket
    - **Travel**: flight, airline, hotel, taxi, fuel, petrol, Uber, Ola, bus, train
    - **Office Supplies**: stationery, printer, ink, paper, pen, laptop, computer, mouse, keyboard
    - **Utilities**: electricity, water, internet, mobile bill, phone bill, broadband, gas
    - **Others**: (use this if no relevant category is found)

    Provide ONLY a JSON response with these keys: "store_name", "date", "bill_no", "total_amount", "category".
    Do NOT include any additional text, explanation, or formatting outside of the JSON object.

    Invoice text:
    {text}
    """

    response = model.generate_content(prompt)

    # Extract JSON safely
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
            "category": "Others"
        }

def check_duplicate(extracted_text, threshold=90):
     """Compare extracted text with session state invoices for duplicate detection."""
     for stored_invoice in st.session_state.invoices:
         similarity_score = fuzz.ratio(extracted_text, stored_invoice["extracted_text"])
         if similarity_score >= threshold:
             return stored_invoice["id"], similarity_score
     
     return None, 0
 
def save_to_session_state(invoice_data, image):
     """Save invoice details and image to session state."""
     invoice_id = len(st.session_state.invoices) + 1  # Use the next available ID
     invoice_data["id"] = invoice_id
     st.session_state.invoices.append(invoice_data)
     
     # Store the image directly in session state
     st.session_state.invoice_images = st.session_state.get('invoice_images', {})
     st.session_state.invoice_images[invoice_id] = image
     return invoice_id
 
def process_pdf(uploaded_file):
     """Convert PDF pages to images and extract text."""
     images = convert_from_bytes(uploaded_file.read())
     extracted_text = extract_text(images[0])
     return extracted_text, images[0]
 
def calculate_total_amount():
     """Calculate the sum of total_amount from session_state invoices."""
     total = sum(float(invoice["total_amount"]) for invoice in st.session_state.invoices if invoice["total_amount"])
     return total
 
 
def clear_session_state_data():
     """Clear all invoices and images from session state."""
     st.session_state.invoices.clear()
     st.session_state.invoice_images.clear()


def spending_trends():
    # Convert session invoices to a DataFrame for easier manipulation
    invoices_df = pd.DataFrame(st.session_state.invoices)

    # Clean the date column (no format conversion, just removing ordinal suffixes)
    invoices_df['date'] = invoices_df['date'].astype(str).str.replace(r'\d+(st|nd|rd|th)', '', regex=True)

    # Ensure 'total_amount' is numeric and handle errors
    invoices_df['total_amount'] = pd.to_numeric(invoices_df['total_amount'], errors='coerce')

    # Remove rows where 'total_amount' is NaN after conversion
    invoices_df = invoices_df.dropna(subset=['total_amount'])

    # Spending by Category (Pie chart)
    spending_by_category = invoices_df.groupby('category').agg({'total_amount': 'sum'}).reset_index()

    # Group small categories into "Other" to improve readability
    threshold = spending_by_category['total_amount'].quantile(0.05)
    spending_by_category['category'] = spending_by_category['category'].apply(
        lambda x: x if spending_by_category.loc[spending_by_category['category'] == x, 'total_amount'].values[0] >= threshold
        else 'Other'
    )
    spending_by_category = spending_by_category.groupby('category').agg({'total_amount': 'sum'}).reset_index()

    plt.figure(figsize=(8, 6))
    plt.pie(spending_by_category['total_amount'], labels=spending_by_category['category'], autopct='%1.1f%%', startangle=140)
    plt.title("Spending by Category")
    st.pyplot(plt)

    # Spending Trends Over Time (Line chart)
    spending_by_date = invoices_df.groupby(invoices_df['date']).agg({'total_amount': 'sum'}).reset_index()

    plt.figure(figsize=(10, 6))
    plt.plot(spending_by_date['date'], spending_by_date['total_amount'], marker='o')
    plt.title("Spending Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Total Amount (₹)")
    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(plt)

    # Spending by Store (Bar chart)
    spending_by_store = invoices_df.groupby('store_name').agg({'total_amount': 'sum'}).reset_index()

    plt.figure(figsize=(10, 6))
    sns.barplot(x='store_name', y='total_amount', data=spending_by_store, palette='viridis')
    plt.title("Spending by Store")
    plt.xlabel("Store Name")
    plt.ylabel("Total Amount (₹)")
    plt.xticks(rotation=45)
    st.pyplot(plt)

    # Show a summary of total spending
    total_spending = invoices_df['total_amount'].sum()
    st.subheader(f"Total Spending: ₹{total_spending:,.2f}")


def generate_invoice_pdf():
    """Generate a PDF with an invoice summary table on the first page and invoice images on subsequent pages."""
    progress_bar = st.progress(0)  # Initialize progress bar
    progress = 0

    # Step 1: Upload Progress (30%)
    progress_bar.progress(progress + 10)
    time.sleep(0.5)  # Simulate processing time

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=14)

    pdf.cell(200, 10, "Invoice Summary", ln=True, align="C")
    pdf.ln(10)

    total_sum = sum(float(invoice["total_amount"]) for invoice in st.session_state.invoices)

    # Table Headers
    pdf.set_font("Arial", style='B', size=10)
    col_widths = [20, 50, 30, 30, 30]  # Adjusted for category before total
    headers = ["Bill ID", "Store Name", "Date", "Category", "Total Amount"]

    progress += 10
    progress_bar.progress(progress + 10)  # 20% progress
    time.sleep(0.5)

    # Step 2: Process Invoices (40%)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for i, invoice in enumerate(st.session_state.invoices):
        pdf.cell(col_widths[0], 8, str(invoice["id"]), border=1, align="C")
        pdf.cell(col_widths[1], 8, invoice["store_name"], border=1)
        pdf.cell(col_widths[2], 8, invoice["date"], border=1, align="C")
        pdf.cell(col_widths[3], 8, invoice["category"], border=1, align="C")  # Category before total
        pdf.cell(col_widths[4], 8, f"{float(invoice['total_amount']):.2f}", border=1, align="C")
        pdf.ln()

        progress += 5  # Increment progress
        progress_bar.progress(progress)  

    # Total sum row
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(sum(col_widths[:4]), 8, "Total Amount", border=1, align="R")
    pdf.cell(col_widths[4], 8, f"{total_sum:.2f}", border=1, align="C")
    pdf.ln(10)

    # Step 3: Generate Spending Trends Charts (30%)
    # Now, generate and add the charts to the second page of the PDF.
    spending_trends()

    # Convert 'total_amount' to numeric before performing aggregation
    invoice_df = pd.DataFrame(st.session_state.invoices)
    invoice_df['total_amount'] = pd.to_numeric(invoice_df['total_amount'], errors='coerce')

    spending_by_category = invoice_df.groupby('category').agg({'total_amount': 'sum'}).reset_index()

    # Save the Spending by Category Pie chart
    pie_chart_path = tempfile.mktemp(suffix=".png")
    plt.figure(figsize=(8, 6))
    plt.pie(spending_by_category['total_amount'], labels=spending_by_category['category'], autopct='%1.1f%%', startangle=140)
    plt.title("Spending by Category")
    plt.savefig(pie_chart_path, format="png")
    plt.close()

    # Save the Spending Trends Over Time Line chart
    line_chart_path = tempfile.mktemp(suffix=".png")
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

    # Save the Spending by Store Bar chart
    bar_chart_path = tempfile.mktemp(suffix=".png")
    spending_by_store = invoice_df.groupby('store_name').agg({'total_amount': 'sum'}).reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='store_name', y='total_amount', data=spending_by_store, palette='viridis')
    plt.title("Spending by Store")
    plt.xlabel("Store Name")
    plt.ylabel("Total Amount (₹)")
    plt.xticks(rotation=45)
    plt.savefig(bar_chart_path, format="png")
    plt.close()

    # Add charts to the second page of the PDF
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, "Spending Trends", ln=True, align="C")
    pdf.ln(10)

    # Insert pie chart
    pdf.image(pie_chart_path, x=10, y=30, w=180)
    pdf.ln(100)  # Adjust position for next chart

    # Insert line chart
    pdf.image(line_chart_path, x=10, y=140, w=180)
    pdf.ln(100)

    pdf.add_page()
    pdf.set_font("Arial", style='B', size=14)
    pdf.image(bar_chart_path, x=10, y=30, w=180)

    progress += 10
    progress_bar.progress(progress)

    # Step 4: Generate Invoice Images (30%)
    for invoice_id, img in st.session_state.invoice_images.items():
        pdf.add_page()
        temp_path = os.path.join(tempfile.gettempdir(), f"invoice_{invoice_id}.png")
        img.save(temp_path, format="PNG")  # Save image temporarily

        try:
            pdf.image(temp_path, x=10, y=10, w=180)
        finally:
            os.remove(temp_path)  # Cleanup

        progress += 10
        progress_bar.progress(progress)

    # Step 5: Save and Offer PDF Download (Final 30%)
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")  # Generate temp file path
    os.close(fd)  # Close file descriptor
    pdf.output(pdf_path)  # Save PDF

    progress_bar.progress(100)  # Completed ✅
    st.success("✅ Invoice Summary PDF generated successfully!")

    # Use a unique key for the download button
    with open(pdf_path, "rb") as pdf_file:
        st.download_button(
            label="📄 Download Invoice Summary PDF", 
            data=pdf_file, 
            file_name="invoices_summary.pdf", 
            mime="application/pdf",
            key="download_invoice_summary"  # Unique key for the button
        )

    # Cleanup: Remove file after user interaction
    if os.path.exists(pdf_path):
        os.remove(pdf_path)


 
 # Streamlit UI
st.title("Invoice Management System")
 
uploaded_file = st.file_uploader("Upload Invoice Image or PDF", type=["png", "jpg", "jpeg", "pdf"])
 
if uploaded_file:


     
     file_type = uploaded_file.name.split(".")[-1].lower()
 
     if file_type in ["png", "jpg", "jpeg"]:
         image = Image.open(uploaded_file)
         extracted_text = extract_text(image)
     elif file_type == "pdf":
         extracted_text, image = process_pdf(uploaded_file)
     
     invoice_data = extract_entities(extracted_text)
     invoice_data["extracted_text"] = extracted_text
     
     st.subheader("Extracted Invoice Details")
     st.json(invoice_data)
     
     duplicate_id, similarity_score = check_duplicate(extracted_text)
     
     if duplicate_id:
         st.warning(f"⚠ Duplicate Invoice Detected! (ID: {duplicate_id}, Similarity Score: {similarity_score}%)")
         existing_image = st.session_state.invoice_images[duplicate_id]
         col1, col2 = st.columns(2)
         with col1:
             st.image(image, caption="New Uploaded Invoice", use_column_width=True)
         with col2:
             st.image(existing_image, caption="Existing Invoice", use_column_width=True)
         
         if st.button("Proceed to Save Anyway"):
             saved_id = save_to_session_state(invoice_data, image)
             st.success(f"Invoice saved with ID: {saved_id}.")
     else:
         saved_id = save_to_session_state(invoice_data, image)
         st.success(f"✅ Invoice saved with ID: {saved_id}.")
 
if st.button("Sum of All Invoices"):
     total_sum = calculate_total_amount()
     st.success(f"💰 Total sum of all invoices: ₹{total_sum:.2f}")


if st.button("Analyze Spending Trends"):
    spending_trends()
 
if st.button("Clear All Data (Invoices & Images)"):
     clear_session_state_data()
     st.success("All invoices and saved images have been deleted.")
     st.rerun()
 
if st.button("Generate Invoice Summary PDF"):
     generate_invoice_pdf()