import io
import json
import os
import re
import base64
import requests
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
import replicate
from utils import spending_trends


# Configure APIs and credentials
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
credentials = service_account.Credentials.from_service_account_info(st.secrets["GOOGLE_CREDENTIALS"])
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

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
    image_obj = vision.Image(content=img_byte_arr.getvalue())
    response = vision_client.text_detection(image=image_obj)
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
    invoice_id = len(st.session_state.invoices) + 1
    invoice_data["id"] = invoice_id
    st.session_state.invoices.append(invoice_data)
    st.session_state.invoice_images[invoice_id] = image
    return invoice_id

def process_pdf(uploaded_file):
    """Convert PDF pages to images and return the first page image."""
    images = convert_from_bytes(uploaded_file.read())
    return images[0]

def calculate_total_amount():
    """Calculate the sum of total_amount from session_state invoices."""
    total = sum(float(invoice["total_amount"]) for invoice in st.session_state.invoices if invoice["total_amount"])
    return total

def clear_session_state_data():
    """Clear all invoices and images from session state."""
    st.session_state.invoices.clear()
    st.session_state.invoice_images.clear()

def spending_trends():
    invoices_df = pd.DataFrame(st.session_state.invoices)
    invoices_df['date'] = invoices_df['date'].astype(str).str.replace(r'\d+(st|nd|rd|th)', '', regex=True)
    invoices_df['total_amount'] = pd.to_numeric(invoices_df['total_amount'], errors='coerce')
    invoices_df = invoices_df.dropna(subset=['total_amount'])
    spending_by_category = invoices_df.groupby('category').agg({'total_amount': 'sum'}).reset_index()
    threshold_val = spending_by_category['total_amount'].quantile(0.05)
    spending_by_category['category'] = spending_by_category['category'].apply(
        lambda x: x if spending_by_category.loc[spending_by_category['category'] == x, 'total_amount'].values[0] >= threshold_val
        else 'Other'
    )
    spending_by_category = spending_by_category.groupby('category').agg({'total_amount': 'sum'}).reset_index()
    plt.figure(figsize=(8, 6))
    plt.pie(spending_by_category['total_amount'], labels=spending_by_category['category'], autopct='%1.1f%%', startangle=140)
    plt.title("Spending by Category")
    st.pyplot(plt)
    spending_by_date = invoices_df.groupby(invoices_df['date']).agg({'total_amount': 'sum'}).reset_index()
    plt.figure(figsize=(10, 6))
    plt.plot(spending_by_date['date'], spending_by_date['total_amount'], marker='o')
    plt.title("Spending Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Total Amount (₹)")
    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(plt)
    spending_by_store = invoices_df.groupby('store_name').agg({'total_amount': 'sum'}).reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='store_name', y='total_amount', data=spending_by_store, palette='viridis')
    plt.title("Spending by Store")
    plt.xlabel("Store Name")
    plt.ylabel("Total Amount (₹)")
    plt.xticks(rotation=45)
    st.pyplot(plt)
    total_spending = invoices_df['total_amount'].sum()
    st.subheader(f"Total Spending: ₹{total_spending:,.2f}")

def generate_invoice_pdf():
    progress_bar = st.progress(0)
    progress = 0
    progress_bar.progress(progress + 10)
    time.sleep(0.5)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, "Invoice Summary", ln=True, align="C")
    pdf.ln(10)
    total_sum = sum(float(invoice["total_amount"]) for invoice in st.session_state.invoices)
    pdf.set_font("Arial", style='B', size=10)
    col_widths = [20, 50, 30, 30, 30]
    headers = ["Bill ID", "Store Name", "Date", "Category", "Total Amount"]
    progress += 10
    progress_bar.progress(progress + 10)
    time.sleep(0.5)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C")
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for invoice in st.session_state.invoices:
        pdf.cell(col_widths[0], 8, str(invoice["id"]), border=1, align="C")
        pdf.cell(col_widths[1], 8, invoice["store_name"], border=1)
        pdf.cell(col_widths[2], 8, invoice["date"], border=1, align="C")
        pdf.cell(col_widths[3], 8, invoice["category"], border=1, align="C")
        pdf.cell(col_widths[4], 8, f"{float(invoice['total_amount']):.2f}", border=1, align="C")
        pdf.ln()
        progress += 5
        progress_bar.progress(progress)
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(sum(col_widths[:4]), 8, "Total Amount", border=1, align="R")
    pdf.cell(col_widths[4], 8, f"{total_sum:.2f}", border=1, align="C")
    pdf.ln(10)
    spending_trends()
    invoice_df = pd.DataFrame(st.session_state.invoices)
    invoice_df['total_amount'] = pd.to_numeric(invoice_df['total_amount'], errors='coerce')
    spending_by_category = invoice_df.groupby('category').agg({'total_amount': 'sum'}).reset_index()
    pie_chart_path = tempfile.mktemp(suffix=".png")
    plt.figure(figsize=(8, 6))
    plt.pie(spending_by_category['total_amount'], labels=spending_by_category['category'], autopct='%1.1f%%', startangle=140)
    plt.title("Spending by Category")
    plt.savefig(pie_chart_path, format="png")
    plt.close()
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

# NEW FUNCTION: Automated fake invoice detection using Replicate's ManTra-Net API
def detect_forgery_replicate(image):
    """Detect forgery in the invoice image using Replicate's ManTra-Net API via the official Python client."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    data_url = f"data:image/png;base64,{img_str}"
    
    # Extract API key correctly
    API_KEY = st.secrets["REPLICATE_API_KEY"]["value"]
    client = replicate.Client(api_token=API_KEY)
    
    # Use the correct model identifier (verify on Replicate's model page)
    model_identifier = "highwaywu/image-forgery-detection:ab6f81afdf0de95354d44b61c18f4dfe31dc0ad83da8b0406d57afff8f6ace08"
    
    try:
        output = client.run(model_identifier, input={"image": data_url})
        return output
    except Exception as e:
        st.error("Error running forgery detection model: " + str(e))
        return None

# Streamlit UI
st.title("Invoice Management System")
uploaded_file = st.file_uploader("Upload Invoice Image or PDF", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    # Extract the image from the uploaded file (for PDFs, use first page)
    if file_type in ["png", "jpg", "jpeg"]:
        image = Image.open(uploaded_file)
    elif file_type == "pdf":
        image = process_pdf(uploaded_file)
    
    # First: Send the image for forgery detection
    st.subheader("Forgery Detection Result")
    forgery_output = detect_forgery_replicate(image)
    
    forgery_image = None
    if forgery_output:
        # Convert the output to a PIL image if necessary
        if hasattr(forgery_output, "read"):
            try:
                image_data = forgery_output.read()
                forgery_image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                st.error("Error processing output image: " + str(e))
        elif isinstance(forgery_output, str) and forgery_output.startswith("http"):
            try:
                response = requests.get(forgery_output)
                forgery_image = Image.open(io.BytesIO(response.content))
            except Exception as e:
                st.error("Error downloading output image: " + str(e))
        elif isinstance(forgery_output, Image.Image):
            forgery_image = forgery_output
        else:
            # If the output is a URL-like string, try downloading it
            try:
                response = requests.get(forgery_output)
                forgery_image = Image.open(io.BytesIO(response.content))
            except Exception as e:
                st.error("Error processing forgery detection output: " + str(e))
    
    if forgery_image is not None:
        st.image(forgery_image, caption="Forgery Detection Heatmap", use_column_width=True)
        # Analyze heatmap intensity
        try:
            heatmap_response = requests.get(forgery_output)
            heatmap_img = Image.open(io.BytesIO(heatmap_response.content))
            gray_heatmap = heatmap_img.convert("L")
            pixels = list(gray_heatmap.getdata())
            avg_intensity = sum(pixels) / len(pixels)
            st.write(f"Heatmap average intensity: {avg_intensity:.2f}")
        except Exception as e:
            st.error("Error analyzing heatmap intensity: " + str(e))
            avg_intensity = 0
        THRESHOLD_INTENSITY = 150  # Adjust as needed
        if avg_intensity > THRESHOLD_INTENSITY:
            st.error("Invoice appears to be forged based on heatmap intensity!")
            if not st.button("Proceed to Accept Invoice Anyway"):
                st.stop()  # Stop processing if user does not override
        else:
            st.success("No significant forgery detected.")
    else:
        st.success("No forgery detected.")

    # If forgery check passed (or user overrode), proceed with invoice processing
    extracted_text = extract_text(image)
    st.subheader("Extracted Invoice Raw Text")
    st.text(extracted_text)
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
    generate_invoice_pdf()from groq import Groq

# client = Groq()
# completion = client.chat.completions.create(
#     model="meta-llama/llama-4-scout-17b-16e-instruct",
#     messages=[
#       {
#         "role": "system",
#         "content": "Extract the following details from this invoice text:\n   - Store Name\n   - Date (if the date is in a different format, convert it to DD/MM/YYYY format)\n   - Bill Number\n   - Total Amount\n   - Category (choose from: Food, Travel, Office Supplies, Utilities, Others)\n   - GSTIN\n\n   Use the following **keywords for category classification**:\n   - **Food**: restaurant, cafe, grocery, food, beverage, bakery, supermarket\n   - **Travel**: flight, airline, hotel, taxi, fuel, petrol, Uber, Ola, bus, train\n   - **Office Supplies**: stationery, printer, ink, paper, pen, laptop, computer,mouse, keyboard\n   - **Utilities**: electricity, water, internet, mobile bill, phone bill, broadband,gas\n   - **Others**: (use this if no relevant category is found)\n\n   Provide ONLY a JSON response with these keys: \"store_name\", \"date\",\"bill_no\", \"total_amount\", \"category\", \"gstin\".\n   Do NOT include any additional text, explanation, or formatting outside of theJSON object.\n\n    Invoice text:"
#       },
#       {
#         "role": "user",
#         "content": "Booked from\nPRAYAGRAJ JN. (PRYJ)\nStart Date* 29-May-2023\nPNR\n2742721020\nQuota\nGENERAL (GN)\nPassenger Details\n# Name\n1. UTKARSH TIWARI\nAcronyms:\nBoarding At\nPRAYAGRAJ JN. (PRYJ)\nDeparture* 16:37 29-May-2023\nTrain No./Name\n22435/VANDE BHARAT EX\nDistance\n636 KM\nTo\nNEW DELHI (NDLS)\nArrival* 23:00 29-May-2023\nClass\nEXECUTIVE CLASS\n(EC)\nBooking Date\n27-May-2023 15:41:51 HRS\n24\nAge\nGender\nM\nFood Choice\nVEG\nRLWL: REMOTE LOCATION WAITLIST\nBooking Status\nWL/33\nPQWL: POOLED QUOTA WAITLIST\nCurrent Status\nWL/18\nRSWL: ROAD-SIDE WAITLIST\nTransaction ID: 100004196299688\nIR recovers only 57% of cost of travel on an average.\nPayment Details\nTicket Fare\nCatering Charges (Incl. of GST)\nIRCTC Convenience Fee (Incl. of GST)\nTotal Fare (all inclusive)\nPG Charges as applicable (Additional)\n2,581.00\n369.00\n35.40\n₹2,985.40\nIRCTC Convenience Fee is charged per e-ticket irrespective of number of passengers on the ticket.\n* The printed Departure and Arrival Times are liable to change. Please Check correct departure, arrival from Railway Station Enquiry or Dial 139 or SMS RAIL to 139.\nNo Linen will be provided in AC Economy (3E) class.\nThis ticket is booked on a personal User ID, its sale/purchase is an offence u/s 143 of the Railways Act, 1989.\nPrescribed original ID proof is required while travelling along with SMS/ VRM/ERS otherwise will be treated as without ticket and penalized as per Railway Rules.\nIndian Railways GST Details:\nInvoice Number:\nSupplier Information:\nPS23274272102011\nAddress:\nIndian Railways New Delhi\nSAC Code:\n996421\nRecipient Information:\nGSTIN:\n07AAAGM0289C1ZL"
#       }
#     ],
#     temperature=0.18,
#     max_completion_tokens=1024,
#     top_p=1,
#     stream=False,
#     response_format={"type": "json_object"},
#     stop=None,
# )

# print(completion.choices[0].message)
