# 🧾 Invoice Verification and Management System

An AI-powered Streamlit web app for automating the extraction, verification, visualization, and analysis of invoice data. Built with modern data science tools, this project aims to eliminate manual invoice tracking, detect duplicates, and provide actionable financial insights for individuals and businesses.

🔗 **[Live Demo](https://invoicemanagmentnodb.streamlit.app/)**

---

## 📌 Abstract

The **Invoice Management System** is an AI-driven solution designed to automate the extraction, organization, and analysis of invoice data. It supports both image (PNG, JPG, JPEG) and PDF invoice uploads, extracting key details such as:

- Store Name
- Bill Number
- Total Amount
- Date
- Category

The system uses **AI-powered text extraction**, detects **duplicate invoices via fuzzy matching**, and offers visual **spending analytics** through pie, bar, and line charts. A downloadable **summary PDF** with tables, charts, and invoice images is also generated for financial recordkeeping.

---

## 🚀 Features

✅ AI-based invoice data extraction (PDF & image formats)  
🧠 Duplicate invoice detection using fuzzy logic  
📊 Spending analytics with interactive visualizations  
📋 Interactive invoice table with filtering and sorting (AgGrid)  
📄 Invoice summary PDF with charts, tables & thumbnails  
🤖 AI-generated financial insights using Google Gemini  
🔐 No database needed — works with session state  
🔮 Planned: cloud sync, expense forecasting, mobile support

---

## 🎥 Live Demo

👉 [Try it now on Streamlit!](https://invoicemanagmentnodb.streamlit.app/)



## 🧰 Tech Stack

| Layer | Tools |
|-------|-------|
| Frontend | Streamlit, HTML/CSS |
| Backend | Python, FastAPI (planned) |
| Data Handling | Pandas, FuzzyWuzzy |
| Visualization | Seaborn, Matplotlib, AgGrid |
| AI & OCR | Google Gemini API, Google Vision API |
| File Handling | tempfile, PDF generation with reportlab (or similar) |

---

📁 Folder Structure

├── Home.py                 # Entry point: Upload & manage invoices
├── pages/
│   └── dashboard.py        # Visuals, tables, and AI analysis
├── utils.py                # Charting & processing logic
├── requirements.txt        # Dependencies   
└── README.md



**📈 Sample Use Cases**

Automate receipt tracking for freelancers & consultants

Analyze company expenses and vendor costs

Generate monthly or quarterly invoice summary PDFs

Detect suspicious reimbursement claims

---

**📌 Future Enhancements**

☁️ Cloud integration for invoice storage

🤖 Predictive analytics for expense forecasting

📱 Mobile-friendly interface

🧠 Advanced fake bill detection

---

**🛡️ Security & Privacy**

API keys handled via environment variables

No external database — invoice data lives in memory

No sensitive info stored or transmitted

---


**🤝 Contributing**

Want to improve the project?

Bug reports, feature suggestions, and PRs are welcome!

Fork this repo

Create a new branch

Make changes and commit

Submit a pull request

---

**Built with ❤️ by Shinas O M**
