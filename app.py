import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. DATABASE & USER SETUP
# ==============================================================================
st.set_page_config(page_title="Rickshaw Hisab - Secure", page_icon="🛺", layout="wide")

# Hardcoded partner credentials (In a real app, never put passwords in plain text!)
USER_CREDENTIALS = {
    "jazib": {"name": "Jazib Ali", "password": "jazibpassword123", "email": "jazib@example.com"},
    "abdullah": {"name": "Abdullah Ch", "password": "abdullahpassword123", "email": "abdullah@example.com"},
    "changaiz": {"name": "Agha Changaiz", "password": "agha_password123", "email": "changaiz@example.com"}
}

# System Gmail credentials for sending alerts (GET AN APP PASSWORD FROM GMAIL)
SYSTEM_EMAIL = "your_startup_email@gmail.com" 
SYSTEM_APP_PASSWORD = "your_16_digit_app_password_here"

# Initialize Session States
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "ledger" not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=[
        "Timestamp", "Logged By", "Type", "Category", "Amount", "Description"
    ])

if "initial_investment" not in st.session_state:
    st.session_state.initial_investment = 350000.0

# ==============================================================================
# 2. LOGIN SYSTEM
# ==============================================================================
if st.session_state.logged_in_user is None:
    st.markdown("## 🛺 Rickshaw Hisab - Partner Login")
    st.write("Please log in to access the business dashboard.")
    
    username = st.text_input("Username").lower()
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
            st.session_state.logged_in_user = USER_CREDENTIALS[username]["name"]
            st.success(f"Welcome back, {st.session_state.logged_in_user}!")
            st.rerun()
        else:
            st.error("Invalid username or password. Try again.")
    st.stop() # Stops the rest of the code from running until logged in

# ==============================================================================
# 3. MAIN APP (ONLY VISIBLE IF LOGGED IN)
# ==============================================================================
st.sidebar.header(f"👤 Logged in as: {st.session_state.logged_in_user}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in_user = None
    st.rerun()

st.markdown("# 🛺 Rickshaw Hisab")
st.write("---")

tab1, tab2 = st.tabs(["📝 Daily Log & Audit", "📊 Financial Dashboard"])

# ------------------------------------------------------------------------------
# TAB 1: DAILY LEDGER & AUDIT TRAIL
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Log a New Transaction")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        trans_type = st.selectbox("Transaction Type", ["Income", "Expense"])
        if trans_type == "Income":
            category = st.selectbox("Category", ["Daily Rent", "Direct Booking Gigs", "Other"])
        else:
            category = st.selectbox("Category", ["Maintenance", "Fuel", "Token Tax / Route Permit", "Other"])
            
        amount = st.number_input("Amount (PKR):", min_value=0.0, step=100.0)
        description = st.text_input("Notes / Description:")
        
        if st.button("Submit Record"):
            # The Digital Fingerprint: Captures exact time and the logged-in user
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            new_row = pd.DataFrame([{
                "Timestamp": current_time,
                "Logged By": st.session_state.logged_in_user,
                "Type": trans_type,
                "Category": category,
                "Amount": amount,
                "Description": description
            }])
            
            st.session_state.ledger = pd.concat([st.session_state.ledger, new_row], ignore_index=True)
            st.success("Record permanently submitted!")
            st.rerun()

    with col2:
        st.subheader("Secure Audit Ledger")
        st.write("Notice: Entries cannot be deleted once submitted.")
        if not st.session_state.ledger.empty:
            # Show ledger with newest items at the top
            st.dataframe(st.session_state.ledger.iloc[::-1], use_container_width=True)
        else:
            st.write("No transactions logged yet.")

    st.write("---")
    
    # --------------------------------------------------------------------------
    # THE EMAIL ALERT SYSTEM
    # --------------------------------------------------------------------------
    st.subheader("📩 Send Daily Report")
    st.write("Click this at the end of the day to email the current ledger summary to all partners.")
    
    if st.button("Send Email to All Partners"):
        if st.session_state.ledger.empty:
            st.warning("Ledger is empty. Nothing to send.")
        else:
            try:
                # Calculate daily totals to put in the email
                df = st.session_state.ledger
                total_income = df[df["Type"] == "Income"]["Amount"].sum()
                total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
                net = total_income - total_expense
                
                # Build the email content
                email_body = f"""
                Rickshaw Hisab - Daily Summary
                Report Generated By: {st.session_state.logged_in_user}
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                Total Income: PKR {total_income:,.2f}
                Total Expenses: PKR {total_expense:,.2f}
                Net Cash Flow: PKR {net:,.2f}
                
                Please log into the app to see the full audit trail.
                """
                
                msg = MIMEMultipart()
                msg['From'] = SYSTEM_EMAIL
                msg['Subject'] = f"🛺 Daily Rickshaw Report - {datetime.now().strftime('%Y-%m-%d')}"
                msg.attach(MIMEText(email_body, 'plain'))
                
                # Connect to Gmail Server
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(SYSTEM_EMAIL, SYSTEM_APP_PASSWORD)
                
                # Send to all partners
                for user, details in USER_CREDENTIALS.items():
                    msg['To'] = details["email"]
                    server.send_message(msg)
                    
                server.quit()
                st.success("✅ Emails successfully sent to Jazib, Abdullah, and Changaiz!")
                
            except Exception as e:
                st.error(f"Failed to send email. Check your Gmail App Password. Error: {e}")

# ------------------------------------------------------------------------------
# TAB 2: FINANCIAL DASHBOARD
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Financial Overview")
    df = st.session_state.ledger
    
    total_income = float(df[df["Type"] == "Income"]["Amount"].sum()) if not df.empty else 0.0
    total_expenses = float(df[df["Type"] == "Expense"]["Amount"].sum()) if not df.empty else 0.0
    net_profit = total_income - total_expenses
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {total_income:,.2f}")
    col2.metric("Total Expenses", f"PKR {total_expenses:,.2f}", delta=f"-{total_expenses:,.2f}", delta_color="inverse")
    col3.metric("Net Profit Pool", f"PKR {net_profit:,.2f}")
    
    st.write("---")
    st.subheader("💰 Equal Profit Split (3 Partners)")
    share = net_profit / 3
    st.info(f"Current individual share: **PKR {share:,.2f}** per partner.")
