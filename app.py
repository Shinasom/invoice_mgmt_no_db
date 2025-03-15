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

# Configure Gemini API Key
if "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
else:
    st.error("Gemini API key not found. Please add it to Streamlit secrets.")
    st.stop()

# Required columns
REQUIRED_COLUMNS = ["store_name", "date", "bill_no", "total_amount", "extracted_text"]

# Initialize session state
if "invoices" not in st.session_state:
    st.session_state.invoices = []
if "invoice_images" not in st.session_state:
    st.session_state.invoice_images = {}

import streamlit as st
import json
from google.cloud import vision
from google.oauth2 import service_account

# Load Google Vision credentials

# Hardcoded Google Vision API credentials
credentials_info = {
    "type": "service_account",
    "project_id": "shinas-452204",
    "private_key_id": "564a40a7e3d8df87b2a226f5733b764877b37a04",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkq...  # REDACTED FOR SECURITY
-----END PRIVATE KEY-----""",
    "client_email": "invoice-managment@shinas-452204.iam.gserviceaccount.com",
    "client_id": "114461827238442857246",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/invoice-managment@shinas-452204.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Initialize Google Cloud credentials
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Initialize the Vision API client
client = vision.ImageAnnotatorClient(credentials=credentials)



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
    """Extract structured invoice data using Gemini API."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Extract the following details from this invoice text:
    - Store Name
    - Date
    - Bill Number
    - Total Amount
    Provide the response strictly in JSON format with keys: "store_name", "date", "bill_no", "total_amount".
    Invoice text:
    {text}
    """
    response = model.generate_content(prompt)
    try:
        return json.loads(response.text.strip())
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON. Raw output: " + response.text}


def check_duplicate(extracted_text, threshold=90):
    """Compare extracted text with stored invoices for duplicate detection."""
    for invoice in st.session_state.invoices:
        similarity_score = fuzz.ratio(extracted_text, invoice["extracted_text"])
        if similarity_score >= threshold:
            return invoice["id"], similarity_score
    return None, 0


def save_invoice(invoice_data, image):
    """Save invoice details and image in session state."""
    invoice_id = len(st.session_state.invoices) + 1
    invoice_data["id"] = invoice_id
    st.session_state.invoices.append(invoice_data)
    st.session_state.invoice_images[invoice_id] = image
    return invoice_id


def process_pdf(uploaded_file):
    """Convert PDF pages to images and extract text."""
    images = convert_from_bytes(uploaded_file.read())
    extracted_texts = []
    progress_bar = st.progress(0)
    for i, image in enumerate(images):
        extracted_texts.append(extract_text(image))
        progress_bar.progress(int((i + 1) / len(images) * 100))
    return " ".join(extracted_texts), images[0]


def calculate_total_amount():
    """Calculate total sum of invoices."""
    return sum(float(invoice["total_amount"]) for invoice in st.session_state.invoices if invoice["total_amount"])


def clear_data():
    """Clear session state invoices and images."""
    st.session_state.invoices.clear()
    st.session_state.invoice_images.clear()


def generate_invoice_pdf():
    """Generate an invoice summary PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Invoice Summary", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    col_widths = [20, 60, 40, 30]
    headers = ["Bill ID", "Store Name", "Date", "Total Amount"]

    for header in headers:
        pdf.cell(col_widths[headers.index(header)], 8, header, border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for invoice in st.session_state.invoices:
        pdf.cell(col_widths[0], 8, str(invoice["id"]), border=1, align="C")
        pdf.cell(col_widths[1], 8, invoice["store_name"], border=1)
        pdf.cell(col_widths[2], 8, invoice["date"], border=1, align="C")
        pdf.cell(col_widths[3], 8, f"{float(invoice['total_amount']):.2f}", border=1, align="C")
        pdf.ln()

    pdf_output_path = "invoices_summary.pdf"
    pdf.output(pdf_output_path)
    st.success("✅ Invoice Summary PDF generated successfully!")
    with open(pdf_output_path, "rb") as pdf_file:
        st.download_button("📄 Download Invoice Summary PDF", data=pdf_file, file_name="invoices_summary.pdf", mime="application/pdf")

# Streamlit UI
st.title("Invoice OCR Scanner")
uploaded_file = st.file_uploader("Upload Invoice Image or PDF", type=["png", "jpg", "jpeg", "pdf"])
if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    image = Image.open(uploaded_file) if file_type in ["png", "jpg", "jpeg"] else None
    extracted_text = extract_text(image) if image else process_pdf(uploaded_file)[0]
    invoice_data = extract_entities(extracted_text)
    invoice_data["extracted_text"] = extracted_text
    st.json(invoice_data)
    duplicate_id, score = check_duplicate(extracted_text)
    if duplicate_id:
        st.warning(f"⚠ Duplicate Invoice Detected! (ID: {duplicate_id}, Similarity Score: {score}%)")
    else:
        saved_id = save_invoice(invoice_data, image)
        st.success(f"✅ Invoice saved with ID: {saved_id}.")
if st.button("Sum of All Invoices"):
    st.success(f"💰 Total sum of invoices: ₹{calculate_total_amount():.2f}")
if st.button("Clear All Data"):
    clear_data()
    st.rerun()
if st.button("Generate Invoice Summary PDF"):
    generate_invoice_pdf()
