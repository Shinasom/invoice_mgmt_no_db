import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import google.generativeai as genai

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Custom CSS for full-width layout
st.markdown(
    """
    <style>
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Ensure session state is initialized
st.session_state.setdefault("invoices", [])

if "invoices" in st.session_state and st.session_state.invoices:
    df = pd.DataFrame(st.session_state.invoices)
    
    # Ensure total_amount is numeric
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    
    # Total invoices
    total_invoices = len(df)
    
    # Total spending
    total_spending = df["total_amount"].sum()
    
    # Average invoice value
    average_invoice = total_spending / total_invoices if total_invoices else 0
    
    # Highest expense category calculation: group by category and sum amounts
    category_totals = df.groupby("category")["total_amount"].sum().reset_index()
    if not category_totals.empty:
        highest = category_totals.loc[category_totals["total_amount"].idxmax()]
        highest_category = highest["category"]
        highest_amount = highest["total_amount"]
    else:
        highest_category = "N/A"
        highest_amount = 0

    # Create 4 columns for the KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Invoices", total_invoices)
    col2.metric("Total Spending", f"₹{total_spending:,.2f}")
    col3.metric("Average Invoice", f"₹{average_invoice:,.2f}")
    col4.metric("Highest Expense Category", f"{highest_category} (₹{highest_amount:,.2f})")
else:
    st.info("No invoice data available to compute KPIs.")

# Create Tabs
tab1, tab2, tab3 = st.tabs(["📈 Charts", "📋 Tables", "🤖 AI Insights"])

with tab1:
    st.subheader("Spending Trends")
    
    if st.session_state.invoices:
        from utils import spending_trends
        spending_trends()
    else:
        st.warning("No invoice data available. Upload invoices to view spending trends.")

with tab2:
    st.subheader("Interactive Invoice Data")
    
    if st.session_state.invoices:
        df = pd.DataFrame(st.session_state.invoices)
        columns_order = ["id", "store_name", "gstin", "date", "category", "total_amount"]
        df = df[columns_order]
        
        # Rename columns for display
        df = df.rename(columns={
            "id": "Bill ID",
            "store_name": "Store Name",
            "gstin": "GSTIN",
            "date": "Date",
            "category": "Category",
            "total_amount": "Total Amount"
        })
        
        # Convert "Total Amount" column to numeric type
        df["Total Amount"] = pd.to_numeric(df["Total Amount"], errors="coerce")
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(editable=False, filter=True, sortable=True)
        
        # Set column widths and specify numeric type for "Total Amount"
        gb.configure_column("Bill ID", width=100)
        gb.configure_column("Store Name", width=250)
        gb.configure_column("GSTIN", width=200)
        gb.configure_column("Date", width=100)
        gb.configure_column("Category", width=120)
        gb.configure_column("Total Amount", 
                            type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                            custom_format_string="$0,0.00",
                            width=150)
        
        gridOptions = gb.build()
        gridOptions["domLayout"] = "autoHeight"
        
        AgGrid(df, gridOptions=gridOptions, height=500, fit_columns_on_grid_load=True)
    else:
        st.info("No invoice data available.")


with tab3:
    st.subheader("AI Insights")
    
    def generate_ai_insights(invoices):
        if not invoices:
            return "No data available for insights."
        
        invoice_df = pd.DataFrame(invoices)
        invoice_text = invoice_df.to_string(index=False)
        
        # Revised prompt: provide insights and recommendations relevant to the client's spending patterns.
        prompt = (
            "Analyze the following invoice data and provide 5 to 10 bullet-point insights along with actionable recommendations for the client. "
            "Focus on identifying key spending trends, anomalies, and cost drivers, and include only those insights that are directly useful for "
            "making financial decisions (e.g., high spending areas, opportunities for vendor negotiation, unusual spikes in costs). "
            "Exclude suggestions about internal data standardization, invoice formatting issues, or unclear notations unless they significantly impact "
            "the spending or payment process. Output only bullet points.\n\n"
            "Invoice Data:\n"
            f"{invoice_text}"
        )
        
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        insight = response.text.strip()
        return insight

    insights = generate_ai_insights(st.session_state.invoices)
    st.markdown(insights)
