import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import tempfile

def spending_trends(silent=False):
    invoices_df = pd.DataFrame(st.session_state.invoices)
    # Convert/clean data as needed
    invoices_df['date'] = invoices_df['date'].astype(str).str.replace(r'\d+(st|nd|rd|th)', '', regex=True)
    invoices_df['total_amount'] = pd.to_numeric(invoices_df['total_amount'], errors='coerce')
    invoices_df = invoices_df.dropna(subset=['total_amount'])

    # Create and save charts in temp files
    # (Pie chart)
    pie_chart_path = tempfile.mkstemp(suffix=".png")[1]
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    spending_by_category = invoices_df.groupby('category')['total_amount'].sum().reset_index()
    ax1.pie(spending_by_category['total_amount'], labels=spending_by_category['category'], autopct='%1.1f%%', startangle=140)
    ax1.set_title("Spending by Category")
    fig1.savefig(pie_chart_path)
    plt.close(fig1)

    # (Line chart)
    line_chart_path = tempfile.mkstemp(suffix=".png")[1]
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    spending_by_date = invoices_df.groupby('date')['total_amount'].sum().reset_index()
    ax2.plot(spending_by_date['date'], spending_by_date['total_amount'], marker='o')
    ax2.set_title("Spending Trends Over Time")
    plt.xticks(rotation=45)
    fig2.savefig(line_chart_path)
    plt.close(fig2)

    # (Bar chart)
    bar_chart_path = tempfile.mkstemp(suffix=".png")[1]
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    spending_by_store = invoices_df.groupby('store_name')['total_amount'].sum().reset_index()
    sns.barplot(x='store_name', y='total_amount', data=spending_by_store, ax=ax3, palette='viridis')
    ax3.set_title("Spending by Store")
    plt.xticks(rotation=45)
    fig3.savefig(bar_chart_path)
    plt.close(fig3)

    # Return paths for PDF generation
    if silent:
        return pie_chart_path, line_chart_path, bar_chart_path

    # Otherwise, display charts in UI
    st.image(pie_chart_path, caption="Spending by Category")
    st.image(line_chart_path, caption="Spending Trends Over Time")
    st.image(bar_chart_path, caption="Spending by Store")

    # No return if we are displaying

