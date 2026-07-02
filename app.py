import streamlit as st
import pandas as pd
from datetime import datetime

# ==============================================================================
# APP CONFIGURATION & STATE INITIALIZATION
# ==============================================================================
st.set_page_config(page_title="Rickshaw Hisab", page_icon="🛺", layout="wide")

st.markdown("# 🛺 Rickshaw Hisab")
st.markdown("### Operations & Financial Ledger for Your Loader Rickshaw Business")
st.write("---")

# Initialize default session state values if they don't exist
if "partners" not in st.session_state:
    st.session_state.partners = ["Jazib Ali", "Abdullah Ch", "Agha Changaiz"]

if "initial_investment" not in st.session_state:
    st.session_state.initial_investment = 350000.0  # Default initial cost estimation

if "drivers" not in st.session_state:
    st.session_state.drivers = []

if "ledger" not in st.session_state:
    # Sample starting data structure for income and expenses
    st.session_state.ledger = pd.DataFrame(columns=[
        "Date", "Type", "Category", "Amount", "Description"
    ])

# ==============================================================================
# SIDEBAR: PARTNER MANAGEMENT & GLOBAL INITIAL INVESTMENT
# ==============================================================================
st.sidebar.header("⚙️ Business Settings")

# Initial Asset Cost Setup
st.session_state.initial_investment = st.sidebar.number_input(
    "Total Rickshaw Purchase Price (PKR):",
    min_value=0.0,
    value=st.session_state.initial_investment,
    step=5000.0
)

st.sidebar.write("---")
st.sidebar.subheader("👥 Manage Partners")

# Display current partners
st.sidebar.write("**Current Partners:**")
for p in st.session_state.partners:
    st.sidebar.text(f"• {p}")

# Add Partner Form
with st.sidebar.expander("➕ Add New Partner"):
    new_partner = st.text_input("Partner Name:")
    if st.button("Confirm Add"):
        if new_partner and new_partner not in st.session_state.partners:
            st.session_state.partners.append(new_partner)
            st.rerun()
        elif not new_partner:
            st.error("Name cannot be empty.")
        else:
            st.warning("Partner already exists.")

# Remove Partner Form
with st.sidebar.expander("➖ Remove Partner"):
    if len(st.session_state.partners) > 0:
        partner_to_remove = st.selectbox("Select partner to remove:", st.session_state.partners)
        if st.button("Confirm Remove"):
            st.session_state.partners.remove(partner_to_remove)
            st.rerun()
    else:
        st.write("No partners left to remove.")

# ==============================================================================
# MAIN NAVIGATION TABS
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Financial Dashboard", 
    "📝 Daily Log (Income/Expense)", 
    "🧑🦱 Driver Management", 
    "🚀 Future Modules (Fuel Tracker)"
])

# ------------------------------------------------------------------------------
# TAB 1: FINANCIAL DASHBOARD & PAYBACK TRACKER
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Financial Overview")
    
    # Calculate Core Financial Metrics
    df = st.session_state.ledger
    total_income = float(df[df["Type"] == "Income"]["Amount"].sum())
    total_maintenance = float(df[df["Category"] == "Maintenance"]["Amount"].sum())
    total_other_expense = float(df[(df["Type"] == "Expense") & (df["Category"] != "Maintenance")]["Amount"].sum())
    
    total_expenses = total_maintenance + total_other_expense
    net_profit = total_income - total_expenses
    
    # Target to recover
    investment = st.session_state.initial_investment
    
    # Calculate metrics grid
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Investment", f"PKR {investment:,.2f}")
    col2.metric("Total Income Loaded", f"PKR {total_income:,.2f}")
    col3.metric("Maintenance Spent", f"PKR {total_maintenance:,.2f}", delta=f"-{total_maintenance:,.2f}", delta_color="inverse")
    col4.metric("Net Profit Pool", f"PKR {net_profit:,.2f}")
    
    st.write("---")
    
    # Payback Period Progress Bar
    st.subheader("📉 Payback Progress Tracker")
    if investment > 0:
        progress_percentage = min(max(net_profit / investment, 0.0), 1.0)
        st.progress(progress_percentage)
        st.write(f"**{progress_percentage * 100:.1f}%** of the initial investment recovered.")
    else:
        st.write("Enter initial asset value in the sidebar to calculate progress.")

    st.write("---")

    # Partner Profit Split Calculations
    st.subheader("💰 Partner Profit Distribution")
    num_partners = len(st.session_state.partners)
    
    if num_partners > 0:
        share_per_partner = net_profit / num_partners
        st.info(f"Splitting remaining **PKR {net_profit:,.2f}** equally among **{num_partners}** partners:")
        
        split_data = []
        for partner in st.session_state.partners:
            split_data.append({
                "Partner Name": partner,
                "Share Percentage": f"{100 / num_partners:.1f}%",
                "Payout Amount (PKR)": f"{share_per_partner:,.2f}"
            })
        st.table(pd.DataFrame(split_data))
    else:
        st.warning("Please add partners via the sidebar to view profit split details.")

# ------------------------------------------------------------------------------
# TAB 2: DAILY LEDGER ENTRY (INCOME & MAINTENANCE)
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Log a Transaction")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        log_date = st.date_input("Transaction Date", datetime.today())
        trans_type = st.selectbox("Transaction Type", ["Income", "Expense"])
        
        if trans_type == "Income":
            category = st.selectbox("Category", ["Daily Rent", "Direct Booking Gigs", "Other"])
        else:
            category = st.selectbox("Category", ["Maintenance", "Fuel", "Token Tax / Route Permit", "Other"])
            
        amount = st.number_input("Amount (PKR):", min_value=0.0, step=100.0)
        description = st.text_input("Notes / Description:", placeholder="e.g., Engine oil shift, Ride from Badami Bagh")
        
        if st.button("Add Record to Ledger"):
            new_row = pd.DataFrame([{
                "Date": log_date.strftime("%Y-%m-%d"),
                "Type": trans_type,
                "Category": category,
                "Amount": amount,
                "Description": description
            }])
            st.session_state.ledger = pd.concat([st.session_state.ledger, new_row], ignore_index=True)
            st.success("Record submitted successfully!")
            st.rerun()

    with col_f2:
        st.subheader("Recent History Log")
        if not st.session_state.ledger.empty:
            st.dataframe(st.session_state.ledger.sort_index(ascending=False), use_container_width=True)
            
            if st.button("Clear Whole Ledger Logs"):
                st.session_state.ledger = pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Description"])
                st.rerun()
        else:
            st.write("No transaction entries found yet.")

# ------------------------------------------------------------------------------
# TAB 3: DRIVER MANAGEMENT & COMPLIANCE DATA
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("🧑🦱 Driver Profiling & Vault")
    
    with st.expander("➕ Onboard a New Driver", expanded=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_name = st.text_input("Driver Full Name:")
            d_cnic = st.text_input("CNIC Number (e.g., 35201-XXXXXXX-X):")
            d_license = st.text_input("Driving License Category / Number:")
            d_residence = st.text_area("Permanent/Current Residential Address:")
        with col_d2:
            d_pic = st.file_uploader("Upload Driver Profile Picture", type=["jpg", "jpeg", "png"])
            
        if st.button("Save Driver Profile"):
            if d_name and d_cnic:
                driver_profile = {
                    "name": d_name,
                    "cnic": d_cnic,
                    "license": d_license,
                    "residence": d_residence,
                    "picture": d_pic  # Stores file object in state memory
                }
                st.session_state.drivers.append(driver_profile)
                st.success(f"Driver Profile for {d_name} saved successfully!")
                st.rerun()
            else:
                st.error("Name and CNIC are required fields to build the folder.")

    # Render registered drivers list
    st.write("---")
    st.subheader("Registered Driver Records")
    
    if len(st.session_state.drivers) == 0:
        st.write("No drivers currently on file.")
    else:
        for idx, driver in enumerate(st.session_state.drivers):
            with st.container():
                c1, c2 = st.columns([1, 3])
                with c1:
                    if driver["picture"] is not None:
                        st.image(driver["picture"], width=130)
                    else:
                        st.info("No Photo Uploaded")
                with c2:
                    st.markdown(f"### {driver['name']}")
                    st.text(f"🪪 CNIC: {driver['cnic']}")
                    st.text(f"🛺 License: {driver['license']}")
                    st.text(f"🏠 Address: {driver['residence']}")
                    if st.button(f"Remove Profile {driver['name']}", key=f"del_drv_{idx}"):
                        st.session_state.drivers.pop(idx)
                        st.rerun()
                st.write("---")

# ------------------------------------------------------------------------------
# TAB 4: ADVANCED SCALING AND FUTURE MODULES
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("⚙️ Fuel Efficiency & Logistics Optimization Preview")
    st.write(
        "This section calculates the fuel operational efficiency of your asset "
        "to discover engine issues or resource leakage before it harms margins."
    )
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        km_driven = st.number_input("Kilometers Driven (on trip meter):", min_value=0.0, value=0.0, step=10.0)
        fuel_liters = st.number_input("Fuel Consumed (Liters):", min_value=0.0, value=0.0, step=1.0)
        
        if km_driven > 0 and fuel_liters > 0:
            efficiency = km_driven / fuel_liters
            st.metric("Calculated Fleet Mileage", f"{efficiency:.2f} Km/L")
            
            if efficiency < 18:
                st.error("⚠️ Efficiency is critically low. Inspect fuel health, engine tuning, or look out for fuel skimming.")
            elif efficiency >= 18 and efficiency <= 26:
                st.success("✅ Operational mileage is running within healthy standard parameters.")
            else:
                st.warning("⚡ Exceptionally high mileage logged. Double check manual distance calculations.")
        else:
            st.write("Input kilometers and fuel volume metrics to assess real-time vehicle mileage.")
            
    with col_t2:
        st.info(
            "💡 **Future Expansion Ideas:**\n"
            "- Add structural links to Google Sheets via `st.connection()` for cloud sync storage.\n"
            "- Build automated reminder functions for Route Permit, Token Tax, and Fitness Certificate dates.\n"
            "- Add a digital 'Bilty' (Receipt) PDF renderer using `fpdf2` directly from the ledger transactions."
        )
