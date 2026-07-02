import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import uuid

# ==============================================================================
# 1. DATABASE & SECURE STORAGE SETUP
# ==============================================================================
st.set_page_config(page_title="Rickshaw Hisab - Pro", page_icon="🛺", layout="wide")

# System Gmail credentials for sending daily alerts
SYSTEM_EMAIL = "your_startup_email@gmail.com" 
SYSTEM_APP_PASSWORD = "your_16_digit_app_password_here"

# Default users if the JSON file doesn't exist yet
DEFAULT_USERS = {
    "jazib": {"name": "Jazib Ali", "password": "jazibpassword123", "email": "jazibrana7@gmail.com", "photo": "🧑🏽‍💻"},
    "abdullah": {"name": "Abdullah Ch", "password": "abdullahpassword123", "email": "pakroast@gmail.com", "photo": "🧑🏻‍🔧"},
    "changaiz": {"name": "Agha Changaiz", "password": "agha_password123", "email": "halakukhan027@gmail.com", "photo": "🧑🏻‍💼"}
}

# Load or create the permanent users file
USER_FILE = "users_data.json"
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as file:
            return json.load(file)
    else:
        with open(USER_FILE, "w") as file:
            json.dump(DEFAULT_USERS, file)
        return DEFAULT_USERS

def save_users(users_dict):
    with open(USER_FILE, "w") as file:
        json.dump(users_dict, file)

# Initialize Session States
if "users" not in st.session_state:
    st.session_state.users = load_users()

if "selected_login_user" not in st.session_state:
    st.session_state.selected_login_user = None

if "logged_in_user_key" not in st.session_state:
    st.session_state.logged_in_user_key = None

if "initial_investment" not in st.session_state:
    st.session_state.initial_investment = 350000.0

# The Ledger now includes an ID, Status, and Deletion tracking
if "ledger" not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=[
        "ID", "Timestamp", "Logged By", "Type", "Category", "Amount", "Description", "Status", "Deleted By", "Deleted At"
    ])

# ==============================================================================
# 2. TWO-STEP VISUAL LOGIN SYSTEM
# ==============================================================================
if st.session_state.logged_in_user_key is None:
    st.markdown("## 🛺 Rickshaw Hisab - Access Portal")
    st.write("Select your profile to log in.")
    
    # STEP 1: Select User
    if st.session_state.selected_login_user is None:
        cols = st.columns(len(st.session_state.users))
        
        # Dynamically create a profile card for each user
        for idx, (user_key, user_info) in enumerate(st.session_state.users.items()):
            with cols[idx]:
                st.markdown(f"### {user_info['photo']}")
                st.markdown(f"**{user_info['name']}**")
                if st.button(f"Log in as {user_info['name']}", key=f"btn_{user_key}"):
                    st.session_state.selected_login_user = user_key
                    st.rerun()
                    
    # STEP 2: Enter Password
    else:
        user_key = st.session_state.selected_login_user
        user_name = st.session_state.users[user_key]['name']
        photo = st.session_state.users[user_key]['photo']
        
        st.markdown(f"### {photo} Welcome, {user_name}")
        st.write("Please enter your password to continue.")
        
        password_attempt = st.text_input("Password", type="password")
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Submit"):
                if password_attempt == st.session_state.users[user_key]["password"]:
                    st.session_state.logged_in_user_key = user_key
                    st.success("Access Granted.")
                    st.rerun()
                else:
                    st.error("Incorrect Password.")
        with col2:
            if st.button("Cancel / Back"):
                st.session_state.selected_login_user = None
                st.rerun()
                
    st.stop() # Halts code execution until login is successful

# ==============================================================================
# 3. MAIN APP & SETTINGS
# ==============================================================================
current_user = st.session_state.users[st.session_state.logged_in_user_key]

st.sidebar.markdown(f"### {current_user['photo']} {current_user['name']}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in_user_key = None
    st.session_state.selected_login_user = None
    st.rerun()

st.sidebar.write("---")

# Profile Settings (Change Username/Password)
with st.sidebar.expander("⚙️ Profile Settings"):
    st.write("Update your credentials here.")
    new_username = st.text_input("New Username (Login ID)", value=st.session_state.logged_in_user_key)
    new_password = st.text_input("New Password", type="password")
    
    if st.button("Save Changes"):
        old_key = st.session_state.logged_in_user_key
        
        # Update the dictionary
        if new_username and new_password:
            # Create new key if username changed, copy data over
            st.session_state.users[new_username] = st.session_state.users.pop(old_key)
            st.session_state.users[new_username]["password"] = new_password
            
            # Save to the JSON file permanently
            save_users(st.session_state.users)
            
            # Update session memory to the new key
            st.session_state.logged_in_user_key = new_username
            st.success("Credentials updated successfully!")
            st.rerun()
        else:
            st.error("Fields cannot be empty.")

st.markdown("# 🛺 Rickshaw Hisab")
st.write("---")

tab1, tab2 = st.tabs(["📝 Daily Log & Audit", "📊 Financial Dashboard"])

# ------------------------------------------------------------------------------
# TAB 1: DAILY LEDGER & SOFT DELETE AUDIT
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Log a New Transaction")
    
    col_input, col_view = st.columns([1, 2])
    
    with col_input:
        trans_type = st.selectbox("Transaction Type", ["Income", "Expense"])
        if trans_type == "Income":
            category = st.selectbox("Category", ["Daily Rent", "Direct Booking Gigs", "Other"])
        else:
            category = st.selectbox("Category", ["Maintenance", "Fuel", "Token Tax / Route Permit", "Other"])
            
        amount = st.number_input("Amount (PKR):", min_value=0.0, step=100.0)
        description = st.text_input("Notes / Description:")
        
        if st.button("Submit Record"):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            unique_id = str(uuid.uuid4())[:8] # Generates a short unique ID
            
            new_row = pd.DataFrame([{
                "ID": unique_id,
                "Timestamp": current_time,
                "Logged By": current_user["name"],
                "Type": trans_type,
                "Category": category,
                "Amount": amount,
                "Description": description,
                "Status": "Active",
                "Deleted By": "-",
                "Deleted At": "-"
            }])
            
            st.session_state.ledger = pd.concat([st.session_state.ledger, new_row], ignore_index=True)
            st.success("Record submitted!")
            st.rerun()

    with col_view:
        st.subheader("Secure Audit Ledger")
        
        # Display the ledger, sorting newest first
        if not st.session_state.ledger.empty:
            display_df = st.session_state.ledger.iloc[::-1].copy()
            # Highlight deleted rows visually
            st.dataframe(
                display_df.style.apply(
                    lambda x: ['background-color: #ffcccc; color: black' if x['Status'] == 'Deleted' else '' for i in x], 
                    axis=1
                ),
                use_container_width=True
            )
            
            st.write("---")
            st.write("**Delete an Entry (Requires Audit)**")
            
            # Form to delete an entry
            active_ids = st.session_state.ledger[st.session_state.ledger["Status"] == "Active"]["ID"].tolist()
            
            if active_ids:
                id_to_delete = st.selectbox("Select the ID of the record to delete:", active_ids)
                if st.button("Delete Record"):
                    # Find the row and update its status instead of removing it
                    idx = st.session_state.ledger.index[st.session_state.ledger["ID"] == id_to_delete].tolist()[0]
                    st.session_state.ledger.at[idx, "Status"] = "Deleted"
                    st.session_state.ledger.at[idx, "Deleted By"] = current_user["name"]
                    st.session_state.ledger.at[idx, "Deleted At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    st.warning(f"Record {id_to_delete} marked as deleted. The team can see this action.")
                    st.rerun()
            else:
                st.write("No active records available to delete.")
        else:
            st.write("No transactions logged yet.")

# ------------------------------------------------------------------------------
# TAB 2: FINANCIAL DASHBOARD (FILTERS OUT DELETED ITEMS)
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Financial Overview")
    
    # Only calculate amounts for ACTIVE records
    df = st.session_state.ledger
    active_df = df[df["Status"] == "Active"]
    
    total_income = float(active_df[active_df["Type"] == "Income"]["Amount"].sum()) if not active_df.empty else 0.0
    total_expenses = float(active_df[active_df["Type"] == "Expense"]["Amount"].sum()) if not active_df.empty else 0.0
    net_profit = total_income - total_expenses
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Active Income", f"PKR {total_income:,.2f}")
    col2.metric("Total Active Expenses", f"PKR {total_expenses:,.2f}")
    col3.metric("Net Profit Pool", f"PKR {net_profit:,.2f}")
    
    st.write("---")
    st.subheader("💰 Equal Profit Split (3 Partners)")
    share = net_profit / 3
    st.info(f"Current individual share: **PKR {share:,.2f}** per partner.")
