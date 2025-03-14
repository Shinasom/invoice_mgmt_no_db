import os
import numpy as np
import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
from fuzzywuzzy import fuzz
import pytesseract
import google.generativeai as genai
import json
import re
from fpdf import FPDF
import tempfile
import time

# Configure Gemini API Key
genai.configure(api_key="AIzaSyDUqJdPpP8E51hfJ-UhxDKqiJVgJau2j0E")

# Initialize session state for storing invoices and images
if "invoices" not in st.session_state:
    st.session_state.invoices = []

# Required columns
REQUIRED_COLUMNS = ["store_name", "date", "bill_no", "total_amount", "extracted_text"]

def extract_text(image):
    """Extract text using Tesseract OCR."""
    return pytesseract.image_to_string(image, lang="eng")

def extract_entities(text):
    """Extract structured invoice data using Gemini 1.5 Flash API."""
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    Extract the following details from this invoice text:
    - Store Name
    - Date
    - Bill Number
    - Total Amount
    Provide the response **strictly in JSON format** with keys: "store_name", "date", "bill_no", "total_amount".
    
    Invoice text:
    {text}
    """

    response = model.generate_content(prompt)

    try:
        # Clean extra markdown or incorrect formatting
        clean_text = re.sub(r"```json\n(.*?)\n```", r"\1", response.text, flags=re.DOTALL).strip()
        
        # Parse JSON
        extracted_data = json.loads(clean_text)
    except json.JSONDecodeError:
        extracted_data = {"error": "Failed to parse response. Raw output: " + response.text}

    return extracted_data

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


def generate_invoice_pdf():
    """Generate a PDF with an invoice summary table on the first page and invoice images on subsequent pages."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=14)
    
    # Title
    pdf.cell(200, 10, "Invoice Summary", ln=True, align="C")
    pdf.ln(10)

    # Calculate total amount
    total_sum = sum(float(invoice["total_amount"]) for invoice in st.session_state.invoices)

    # Table Headers
    pdf.set_font("Arial", style='B', size=10)
    col_widths = [20, 60, 40, 30]
    headers = ["Bill ID", "Store Name", "Date", "Total Amount"]

    # Create progress bar and update as PDF is generated
    progress_bar = st.progress(0)
    progress = 0
    progress_increment = 100 / (len(st.session_state.invoices) + 1)  # Split progress among invoices and summary

    # Add table headers
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C")
    pdf.ln()

    # Table Data
    pdf.set_font("Arial", size=10)
    for i, invoice in enumerate(st.session_state.invoices):
        pdf.cell(col_widths[0], 8, str(invoice["id"]), border=1, align="C")
        pdf.cell(col_widths[1], 8, invoice["store_name"], border=1)
        pdf.cell(col_widths[2], 8, invoice["date"], border=1, align="C")
        pdf.cell(col_widths[3], 8, f"{float(invoice['total_amount']):.2f}", border=1, align="C")
        pdf.ln()

        # Update progress bar
        progress += progress_increment
        progress_bar.progress(min(int(progress), 100))  # Clamp progress to 100

    # Total sum row
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(sum(col_widths[:3]), 8, "Total Amount", border=1, align="R")
    pdf.cell(col_widths[3], 8, f"{total_sum:.2f}", border=1, align="C")
    pdf.ln(10)

    # Add invoice images on new pages
    for i, (invoice_id, img) in enumerate(st.session_state.invoice_images.items()):
        pdf.add_page()

        # Create a temporary file to save the image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            img.save(tmp_file.name)  # Save the image to the temporary file
            tmp_file_path = tmp_file.name

            # Add the image to the PDF
            pdf.image(tmp_file_path, x=10, y=10, w=180)

            # Explicitly close the temporary file handle
            tmp_file.close()

            # Add a small delay to ensure the file is released
            time.sleep(0.5)

            # Clean up the temporary file
            os.remove(tmp_file_path)

        # Update progress bar
        progress += progress_increment
        progress_bar.progress(min(int(progress), 100))  # Clamp progress to 100

    # Save and offer PDF for download
    pdf_output_path = "invoices_summary.pdf"
    pdf.output(pdf_output_path)
    st.success("✅ Invoice Summary PDF generated successfully!")

    with open(pdf_output_path, "rb") as pdf_file:
        st.download_button(label="📄 Download Invoice Summary PDF", data=pdf_file, file_name="invoices_summary.pdf", mime="application/pdf")


# Streamlit UI
st.title("Invoice OCR Scanner")

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

if st.button("Clear All Data (Invoices & Images)"):
    clear_session_state_data()
    st.success("All invoices and saved images have been deleted.")
    st.rerun()

if st.button("Generate Invoice Summary PDF"):
    generate_invoice_pdf()
