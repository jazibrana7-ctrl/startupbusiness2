import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# ==============================================================================
# APP CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="Rickshaw Hisab", page_icon="🛺", layout="wide")

st.markdown("# 🛺 Rickshaw Hisab")
st.markdown("### Operations & Financial Ledger for Your Loader Rickshaw Business")
st.write("---")

LEDGER_COLUMNS = ["Date", "Type", "Category", "Amount", "Description"]

# ==============================================================================
# SESSION STATE INITIALIZATION
# (all defaults set once, never re-created inside widgets — avoids the
#  "value keeps resetting" bug from before)
# ==============================================================================
if "partners" not in st.session_state:
    st.session_state.partners = ["Jazib Ali", "Abdullah Ch", "Agha Changaiz"]

if "initial_investment" not in st.session_state:
    st.session_state.initial_investment = 350000.0

if "drivers" not in st.session_state:
    st.session_state.drivers = []  # each item: dict with name, cnic, license, residence, picture (bytes)

if "ledger" not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=LEDGER_COLUMNS)

# ==============================================================================
# SIDEBAR: SETTINGS + PARTNER MANAGEMENT
# ==============================================================================
st.sidebar.header("⚙️ Business Settings")

st.session_state.initial_investment = st.sidebar.number_input(
    "Total Rickshaw Purchase Price (PKR):",
    min_value=0.0,
    value=st.session_state.initial_investment,
    step=5000.0,
    key="initial_investment_input",
)

st.sidebar.write("---")
st.sidebar.subheader("👥 Manage Partners")

st.sidebar.write("**Current Partners:**")
for p in st.session_state.partners:
    st.sidebar.text(f"• {p}")

# --- Add Partner ---
# Using st.form here fixes the old bug where the text box kept showing the
# previously typed name after clicking "Add" (because a plain button + rerun
# does not clear a widget's value — a form's clear_on_submit does).
with st.sidebar.expander("➕ Add New Partner"):
    with st.form("add_partner_form", clear_on_submit=True):
        new_partner = st.text_input("Partner Name:")
        submitted = st.form_submit_button("Confirm Add")
        if submitted:
            cleaned = new_partner.strip()
            if not cleaned:
                st.error("Name cannot be empty.")
            elif cleaned in st.session_state.partners:
                st.warning("Partner already exists.")
            else:
                st.session_state.partners.append(cleaned)
                st.success(f"Added {cleaned}.")
                st.rerun()

# --- Remove Partner ---
with st.sidebar.expander("➖ Remove Partner"):
    if st.session_state.partners:
        partner_to_remove = st.selectbox(
            "Select partner to remove:", st.session_state.partners, key="partner_remove_select"
        )
        if st.button("Confirm Remove", key="confirm_remove_partner"):
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
    "🧑‍🦱 Driver Management",
    "⚙️ Fuel Tracker",
])

# ------------------------------------------------------------------------------
# TAB 1: FINANCIAL DASHBOARD
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Financial Overview")

    df = st.session_state.ledger

    # Guard against an empty ledger so .sum() on a missing/empty column never
    # throws — this was the main crash risk on a fresh deploy.
    if df.empty:
        total_income = 0.0
        total_maintenance = 0.0
        total_other_expense = 0.0
    else:
        total_income = float(df.loc[df["Type"] == "Income", "Amount"].sum())
        total_maintenance = float(df.loc[df["Category"] == "Maintenance", "Amount"].sum())
        total_other_expense = float(
            df.loc[(df["Type"] == "Expense") & (df["Category"] != "Maintenance"), "Amount"].sum()
        )

    total_expenses = total_maintenance + total_other_expense
    net_profit = total_income - total_expenses
    investment = st.session_state.initial_investment

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Investment", f"PKR {investment:,.2f}")
    col2.metric("Total Income Loaded", f"PKR {total_income:,.2f}")
    col3.metric(
        "Maintenance Spent",
        f"PKR {total_maintenance:,.2f}",
        delta=f"-{total_maintenance:,.2f}",
        delta_color="inverse",
    )
    col4.metric("Net Profit Pool", f"PKR {net_profit:,.2f}")

    st.write("---")

    st.subheader("📉 Payback Progress Tracker")
    if investment > 0:
        progress_percentage = min(max(net_profit / investment, 0.0), 1.0)
        st.progress(progress_percentage)
        st.write(f"**{progress_percentage * 100:.1f}%** of the initial investment recovered.")
    else:
        st.write("Enter initial asset value in the sidebar to calculate progress.")

    st.write("---")

    st.subheader("💰 Partner Profit Distribution")
    num_partners = len(st.session_state.partners)

    if num_partners > 0:
        share_per_partner = net_profit / num_partners
        st.info(f"Splitting remaining **PKR {net_profit:,.2f}** equally among **{num_partners}** partners:")
        split_data = [
            {
                "Partner Name": partner,
                "Share Percentage": f"{100 / num_partners:.1f}%",
                "Payout Amount (PKR)": f"{share_per_partner:,.2f}",
            }
            for partner in st.session_state.partners
        ]
        st.table(pd.DataFrame(split_data))
    else:
        st.warning("Please add partners via the sidebar to view profit split details.")

# ------------------------------------------------------------------------------
# TAB 2: DAILY LEDGER ENTRY
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Log a Transaction")

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        # Wrapped in a form: pressing "Add Record" now submits everything at
        # once and clears the inputs afterward, instead of leaving stale
        # amounts/notes sitting in the boxes after a rerun.
        with st.form("add_transaction_form", clear_on_submit=True):
            log_date = st.date_input("Transaction Date", datetime.today())
            trans_type = st.selectbox("Transaction Type", ["Income", "Expense"])

            if trans_type == "Income":
                category = st.selectbox("Category", ["Daily Rent", "Direct Booking Gigs", "Other"])
            else:
                category = st.selectbox(
                    "Category", ["Maintenance", "Fuel", "Token Tax / Route Permit", "Other"]
                )

            amount = st.number_input("Amount (PKR):", min_value=0.0, step=100.0)
            description = st.text_input(
                "Notes / Description:", placeholder="e.g., Engine oil shift, Ride from Badami Bagh"
            )

            add_record = st.form_submit_button("Add Record to Ledger")
            if add_record:
                if amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    new_row = pd.DataFrame([{
                        "Date": log_date.strftime("%Y-%m-%d"),
                        "Type": trans_type,
                        "Category": category,
                        "Amount": amount,
                        "Description": description,
                    }])
                    st.session_state.ledger = pd.concat(
                        [st.session_state.ledger, new_row], ignore_index=True
                    )
                    st.success("Record submitted successfully!")
                    st.rerun()

    with col_f2:
        st.subheader("Recent History Log")
        if not st.session_state.ledger.empty:
            st.dataframe(st.session_state.ledger.sort_index(ascending=False), use_container_width=True)

            # Export so data survives a Streamlit Cloud restart (session_state
            # is wiped whenever the app sleeps/redeploys — this was the
            # biggest source of "my data disappeared" issues last time).
            csv_bytes = st.session_state.ledger.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Ledger as CSV (backup)",
                data=csv_bytes,
                file_name="rickshaw_ledger.csv",
                mime="text/csv",
            )

            if st.button("Clear Whole Ledger Logs"):
                st.session_state.ledger = pd.DataFrame(columns=LEDGER_COLUMNS)
                st.rerun()
        else:
            st.write("No transaction entries found yet.")

        st.write("---")
        st.subheader("⬆️ Restore Ledger from CSV")
        uploaded_csv = st.file_uploader("Upload a previously downloaded ledger CSV", type=["csv"])
        if uploaded_csv is not None:
            try:
                restored_df = pd.read_csv(uploaded_csv)
                missing_cols = set(LEDGER_COLUMNS) - set(restored_df.columns)
                if missing_cols:
                    st.error(f"CSV is missing required columns: {missing_cols}")
                else:
                    if st.button("Replace current ledger with this file"):
                        st.session_state.ledger = restored_df[LEDGER_COLUMNS]
                        st.success("Ledger restored.")
                        st.rerun()
            except Exception as e:
                st.error(f"Could not read this file: {e}")

# ------------------------------------------------------------------------------
# TAB 3: DRIVER MANAGEMENT
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("🧑‍🦱 Driver Profiling & Vault")

    with st.expander("➕ Onboard a New Driver", expanded=True):
        # A form here fixes two bugs from the previous version:
        # 1) The uploaded picture (an UploadedFile) was stored directly in
        #    session_state. Its internal buffer gets consumed on first read,
        #    so re-rendering it later (e.g. after adding a second driver)
        #    could show a broken image. We now read it into raw bytes with
        #    .getvalue() immediately, which is stable across reruns.
        # 2) All fields now reset together on submit via clear_on_submit,
        #    instead of leaving old text sitting in the boxes.
        with st.form("add_driver_form", clear_on_submit=True):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                d_name = st.text_input("Driver Full Name:")
                d_cnic = st.text_input("CNIC Number (e.g., 35201-XXXXXXX-X):")
                d_license = st.text_input("Driving License Category / Number:")
                d_residence = st.text_area("Permanent/Current Residential Address:")
            with col_d2:
                d_pic = st.file_uploader("Upload Driver Profile Picture", type=["jpg", "jpeg", "png"])

            save_driver = st.form_submit_button("Save Driver Profile")
            if save_driver:
                name_clean = d_name.strip()
                cnic_clean = d_cnic.strip()
                existing_cnics = [d["cnic"] for d in st.session_state.drivers]

                if not name_clean or not cnic_clean:
                    st.error("Name and CNIC are required fields to build the folder.")
                elif cnic_clean in existing_cnics:
                    st.error("A driver with this CNIC is already on file.")
                else:
                    picture_bytes = d_pic.getvalue() if d_pic is not None else None
                    driver_profile = {
                        "name": name_clean,
                        "cnic": cnic_clean,
                        "license": d_license.strip(),
                        "residence": d_residence.strip(),
                        "picture": picture_bytes,
                    }
                    st.session_state.drivers.append(driver_profile)
                    st.success(f"Driver Profile for {name_clean} saved successfully!")
                    st.rerun()

    st.write("---")
    st.subheader("Registered Driver Records")

    if not st.session_state.drivers:
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
                    if st.button(f"Remove Profile: {driver['name']}", key=f"del_drv_{idx}"):
                        st.session_state.drivers.pop(idx)
                        st.rerun()
                st.write("---")

# ------------------------------------------------------------------------------
# TAB 4: FUEL EFFICIENCY TRACKER
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("⚙️ Fuel Efficiency & Logistics Optimization")
    st.write(
        "This section calculates the fuel operational efficiency of your asset "
        "to spot engine issues or resource leakage before it harms margins."
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        km_driven = st.number_input("Kilometers Driven (on trip meter):", min_value=0.0, value=0.0, step=10.0)
        fuel_liters = st.number_input("Fuel Consumed (Liters):", min_value=0.0, value=0.0, step=1.0)

        if km_driven > 0 and fuel_liters > 0:
            efficiency = km_driven / fuel_liters
            st.metric("Calculated Fleet Mileage", f"{efficiency:.2f} Km/L")

            if efficiency < 18:
                st.error("⚠️ Efficiency is critically low. Inspect fuel health, engine tuning, or check for fuel skimming.")
            elif efficiency <= 26:
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
