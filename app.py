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

# ⚠️ Hardcoded Gemini API Key
GEMINI_API_KEY = "AIzaSyDUqJdPpP8E51hfJ-UhxDKqiJVgJau2j0E"  
genai.configure(api_key=GEMINI_API_KEY)

# ⚠️ Hardcoded Google Vision API credentials
credentials_info = {
  "type": "service_account",
  "project_id": "shinas-452204",
  "private_key_id": "564a40a7e3d8df87b2a226f5733b764877b37a04",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCxVBPXKr9vncTm\nMBaPJ5PEH3oi81pKxKKTIGgxHk4XWjkB7isM51BUL/u2uVMlYLI6HiDlAPib6rzi\nW1HIHrMikHwSLGInOoB+J2xYXcOPMt9ZsJmXhbpBZBMPEiz8i3Qwjt/wgD815pQT\ncbphAdg9DEilfjpVR7JjR8o4nuh8Zix2jAGOWGUQbJVmEzsYI6WkwLzlr7glwjfe\nSGlMFaDlU+sPcHF6kzArQYzveG0UAmyVpSJ3te8hSOAFhGzzF9blQ+5xnWjY4Fnd\n4Vurk/wTK7DVEHrmN+sOXMht2Wx4afcbVnv7Pa86NEMSUlVLp14Mi/OW1pIfEeV2\ngcRv04bvAgMBAAECggEAD09KfTpYF9C1ELNDJ1iL5elad/eu/83f7rg5YVA+qWkl\nNdj0XONVqJxnQjHYOghnVXmHboNkc2r9+W8CmGFU0Z2he0eGBowC+aFOtdxhMhT6\nz+QIMVr0JzQhfxzFxzIFCzIypwbI2Pmk0X7xT/HC/muilAMvZxskYspDwnAEc2+R\nO09Er6KzHtYr/X0Wmdx17XDpLGrPOtrtfSL8xBZPcuM96n3Zh51TD/dDLOMlQWXW\nV5riZ7ursj2WDLZHUnEeAxeFx0k24Rark+x3VFMQ740bmGUF7Q1Pxz79LVjm/K++\nMQXKDproXVl94AzJXtfWwkeIpymE6JI7SqL07Kw4rQKBgQDoen5cWAJE1uw5RRLl\nN9c/hALChWPxbHrSVTBEF+uccPOvRI/BDpwNaATHD/siVirjOsCV0vuCAn9qRy6F\nA4aUOxxc6E+HqlSD290Z3SkPibhbAp9eptUmoUkuosdvfoNUMuOwljir8/2cWj6h\nR9X9c9Bon5BCi/4xVeglrZO7NQKBgQDDRR922zJmxDUS10WpKm2xeMHXW3aSHLny\nf7b48aLseULfD6rPSZvgo9aVDC8QygYHgaRPO+qRxa43nfiUmdErjOj6lGl6jdBA\nwfTJgOlLclnwYlYKK0lc2/NnxJjDc5caMqCbvAaqYz6FaOg6GxBiC+8d7P0lxa8Y\nDjCB21xaEwKBgDFf6rx0GK9EMlGLgRLbxESCJg/oQqzAzGklnKWpqunD941u81Ue\nZDhYskMQ+tZ1FJDEJqjrcW1QWH1a9t9bO1b6IvD8if+XRnHm3VOj7BeXuWbi7LQu\nnLCiqqdT/SWJ6hyU3lTf4tNqc5+kbw7T8ffthALkeMAZeXhC9ZYjAnBNAoGAdRxa\nr4Ts6HdaQU98huVcXmjHEKrZJO43kzmHeiwpg1uCgJc74RALfaGlS0TAYXhYP15A\nNgkAOKbvQonqkOzjZxQeklI6JHcy4/OvJL68rDQLvsCrS3QEjr2XcK+W0vnbMKoW\navBMqxnUYFy3kkmy/KqdoTwF4wZ5aZrw+qCd9aMCgYB2eHpusTbuaHCcplHbHVrG\ni/L0njMfnc9qpGFRRUIIac2S2a6GKebimMc8EeiieE0U0VsePMQUQf0w08S+BlrY\n2cCD13ButPqKiWLMCXIbCUzgwdcdFZQfm8QjL76EQj+tntmuKypjR5WEnSe0uh9B\n2p5c/9hbc0eExB8WROlRfg==\n-----END PRIVATE KEY-----\n",
  "client_email": "invoice-managment@shinas-452204.iam.gserviceaccount.com",
  "client_id": "114461827238442857246",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/invoice-managment%40shinas-452204.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}


# Initialize Google Cloud credentials
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Initialize the Vision API client
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
    """Extract structured invoice data using Gemini API."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Extract the following details from this invoice text:
    - Store Name
    - Date
    - Bill Number
    - Total Amount
    
    Provide ONLY a JSON response with these keys: "store_name", "date", "bill_no", "total_amount".
    Do NOT include any additional text, explanation, or formatting outside of the JSON object.

    Invoice text:
    {text}
    """

    response = model.generate_content(prompt)

    # Ensure response is valid JSON
    try:
        json_text = response.text.strip()
        if json_text.startswith("```json"):  # Handle Markdown JSON block
            json_text = json_text[7:-3].strip()
        return json.loads(json_text)
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
