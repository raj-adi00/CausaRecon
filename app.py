import streamlit as st
import pandas as pd
import os
import json
import glob
import subprocess
from config import (
    RECONCILIATION_CASES_PATH,
    INVESTIGATION_REPORTS_DIR,
    TICKETS_DIR
)

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Fintech Forensic Reconciliation Engine",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
    <style>
    /* Custom Tabs with Increased Font Size */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1f2937;
        border-radius: 8px;
        color: #9ca3af;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 1.15rem; /* Increased font size here */
        border: 1px solid #374151;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: white !important;
        border-color: #6366f1 !important;
        box-shadow: 0 0 15px rgba(79, 70, 229, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Autonomous Fintech Forensic Reconciliation & Ticketing Pipeline")
st.markdown("Sub-second AI-driven forensic investigations paired with deterministic treasury routing and human-in-the-loop oversight.")

# ==========================================
# SIDEBAR NAVIGATION & CONTROLS
# ==========================================
st.sidebar.markdown('<p style="font-size: 1.3rem; border: 2rem; font-weight: 700; color: #ffffff; margin-bottom: 0px;">🕹️ Pipeline Control Center</p>', unsafe_allow_html=True)

if st.sidebar.button("⚙️ 1. Generate Dataset (`main_simulator.py`)", use_container_width=True):
    with st.spinner("Running settlement and log simulator..."):
        try:
            result = subprocess.run(["python", "main_simulator.py"], capture_output=True, text=True, check=True)
            st.sidebar.success("Dataset generated successfully!")
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"Simulator failed: {e.stderr}")

if st.sidebar.button("🚀 2. Run Pipeline (`main.py`)", use_container_width=True, type="primary"):
    with st.spinner("Running Node A investigations and Node B deterministic routing..."):
        try:
            result = subprocess.run(["python", "main.py"], capture_output=True, text=True, check=True)
            st.sidebar.success("Pipeline executed successfully!")
            st.rerun()
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"Pipeline failed: {e.stderr}")

st.sidebar.markdown("---")

# ==========================================
# MAIN INTERFACE TABS
# ==========================================
tab_overview, tab_tickets, tab_reports = st.tabs([
    "📊 Dataset & Case Ledger", 
    "🎫 Remediation Tickets (Node B)", 
    "🕵️‍♂️ Forensic Audit Reports (Node A)"
])

# ==========================================
# TAB 1: DATASET & CASE LEDGER
# ==========================================
with tab_overview:
    st.header("Discrepancy Case Ledger")
    st.markdown("Live view of reconciliation anomalies tracked from the CSV database.")

    if os.path.exists(RECONCILIATION_CASES_PATH):
        df_cases = pd.read_csv(RECONCILIATION_CASES_PATH)
        
        # Metrics Overview
        col1, col2, col3, col4 = st.columns(4)
        total_cases = len(df_cases)
        pending_cases = len(df_cases[df_cases['case_status'] == 'PENDING_INVESTIGATION'])
        completed_cases = len(df_cases[df_cases['case_status'] == 'INVESTIGATION_COMPLETE'])
        total_exposure = df_cases['discrepancy_amount'].abs().sum()

        col1.metric("Total Cases Tracked", total_cases)
        col2.metric("Pending Investigation", pending_cases)
        col3.metric("Completed Investigations", completed_cases)
        col4.metric("Total Exposure Value", f"${total_exposure:,.2f}")

        st.markdown("### Detailed Case Table")
        
        # Interactive filters
        status_filter = st.selectbox("Filter by Case Status", ["ALL"] + list(df_cases['case_status'].unique()))
        if status_filter != "ALL":
            df_filtered = df_cases[df_cases['case_status'] == status_filter]
        else:
            df_filtered = df_cases

        st.dataframe(
            df_filtered,
            use_container_width=True,
            column_config={
                "expected_amount": st.column_config.NumberColumn("Expected ($)", format="$%.2f"),
                "observed_amount": st.column_config.NumberColumn("Observed ($)", format="$%.2f"),
                "discrepancy_amount": st.column_config.NumberColumn("Gap ($)", format="$%.2f"),
            }
        )
    else:
        st.warning(f"No case ledger found at `{RECONCILIATION_CASES_PATH}`. Click **Generate Dataset** in the sidebar to initialize.")

# ==========================================
# TAB 2: REMEDIATION TICKETS
# ==========================================
with tab_tickets:
    st.header("Deterministic Remediation Tickets")
    st.markdown("Node B generated operational tickets separating physical treasury movements from internal ledger adjustments.")

    ticket_files = glob.glob(os.path.join(TICKETS_DIR, "*.json"))

    if not ticket_files:
        st.info("No remediation tickets found. Execute the pipeline (`main.py`) to generate tickets.")
    else:
        ticket_records = []
        for file in ticket_files:
            with open(file, 'r', encoding='utf-8') as f:
                loaded_ticket = json.load(f)
                ticket_records.append(loaded_ticket)

        df_tickets = pd.DataFrame(ticket_records)

        # Ticket Metrics
        t1, t2, t3 = st.columns(3)
        t1.metric("Total Generated Tickets", len(df_tickets))
        t2.metric("Pending Human Review", len(df_tickets[df_tickets['status'] == 'PENDING_HUMAN_REVIEW']))
        t3.metric("Cash Movement Required", len(df_tickets[df_tickets['requires_cash_movement'] == True]))

        st.markdown("### Ticket Index")
        action_filter = st.selectbox("Filter by Action Type", ["ALL"] + list(df_tickets['action_type'].unique()))
        if action_filter != "ALL":
            df_t_filtered = df_tickets[df_tickets['action_type'] == action_filter]
        else:
            df_t_filtered = df_tickets

        st.dataframe(
            df_t_filtered,
            use_container_width=True,
            column_config={
                "amount": st.column_config.NumberColumn("Amount ($)", format="$%.2f"),
            }
        )

        st.markdown("### Interactive Ticket Inspector & Approval Gate")
        selected_ticket_id = st.selectbox("Select Ticket ID to Inspect", df_tickets['ticket_id'].tolist())

        if selected_ticket_id:
            current_ticket = next((t for t in ticket_records if t['ticket_id'] == selected_ticket_id), None)
            if current_ticket:
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    st.json(current_ticket)
                with col_b:
                    st.markdown(f"#### Action: `{current_ticket['action_type']}`")
                    st.markdown(f"**Amount:** `${current_ticket['amount']:,.2f}`")
                    st.markdown(f"**Physical Cash Transfer:** `{current_ticket['requires_cash_movement']}`")
                    st.markdown(f"**Justification:** {current_ticket['justification']}")
                    st.markdown(f"**Current Status:** `{current_ticket['status']}`")

                    if current_ticket['status'] == "PENDING_HUMAN_REVIEW":
                        if st.button(f"✅ Approve & Dispatch {selected_ticket_id}", type="primary"):
                            current_ticket['status'] = "APPROVED"
                            target_path = os.path.join(TICKETS_DIR, f"{selected_ticket_id}.json")
                            with open(target_path, 'w', encoding='utf-8') as f:
                                json.dump(current_ticket, f, indent=4)
                            st.success(f"Ticket {selected_ticket_id} successfully approved and locked for execution!")
                            st.rerun()
                    else:
                        st.success("Ticket is already reviewed/closed.")

# ==========================================
# TAB 3: FORENSIC AUDIT REPORTS
# ==========================================
with tab_reports:
    st.header("Node A Forensic Investigation Reports")
    st.markdown("Deep-dive into AI post-mortem analyses, mathematical verification steps, and transaction UUID telemetry traces.")

    report_files = glob.glob(os.path.join(INVESTIGATION_REPORTS_DIR, "*_report.json"))

    if not report_files:
        st.info("No investigation reports found. Execute the pipeline (`main.py`) to generate reports.")
    else:
        report_ids = [os.path.basename(f).replace("_report.json", "") for f in report_files]
        selected_report_id = st.selectbox("Select Case Report", report_ids)

        if selected_report_id:
            target_report_path = os.path.join(INVESTIGATION_REPORTS_DIR, f"{selected_report_id}_report.json")
            with open(target_report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)

            details = report_data.get("case_details", {})
            result = report_data.get("investigation_result", {})

            col_meta1, col_meta2, col_meta3 = st.columns(3)
            col_meta1.metric("Case ID", details.get("case_id"))
            col_meta2.metric("Merchant ID", details.get("merchant_id", "N/A")[:12] + "...")
            col_meta3.metric("Discrepancy Gap", f"${details.get('discrepancy_amount', 0):,.2f}")

            st.markdown("---")
            st.subheader("🤖 AI Forensic Findings")
            st.info(f"**Root Cause / Post-Mortem:** {result.get('primary_cause')}")
            st.markdown(f"**Adjustment Reasoning:** {result.get('adjustment_reasoning')}")

            col_bool1, col_bool2, col_bool3 = st.columns(3)
            col_bool1.metric("Requires Financial Adjustment", str(result.get("requires_financial_adjustment")))
            col_bool2.metric("Requires Cash Movement", str(result.get("requires_physical_cash_movement")))
            col_bool3.metric("Evidence Sufficiency", result.get("evidence_sufficiency"))

            st.markdown("### Observations & Audit Trail")
            for obs in result.get("observations", []):
                st.markdown(f"- {obs}")

            st.markdown("### Step-by-Step Evidence Chain")
            for step in result.get("evidence_chain", []):
                st.markdown(f"1. `{step}`")