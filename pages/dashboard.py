import streamlit as st
from utils import spending_trends  # Import the function

# Ensure session state is initialized
if "invoices" not in st.session_state:
    st.session_state.invoices = []

# Set page title
st.title("📊 Dashboard - Spending Analysis")

# Call the function to display the charts
if st.session_state.invoices:  # Only run if invoices exist
    spending_trends()
else:
    st.warning("No invoice data available. Please upload invoices on the Home page.")
