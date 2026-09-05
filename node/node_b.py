import os
import json
import glob
from pydantic import BaseModel
from typing import Literal
from config import TICKETS_DIR, INVESTIGATION_REPORTS_DIR

# ==========================================
# 1. TICKET OUTPUT SCHEMA
# ==========================================
class RemediationTicket(BaseModel):
    ticket_id: str
    case_id: str
    merchant_id: str
    action_type: Literal[
        "TREASURY_PAYOUT_TICKET",          # Real money wired to merchant
        "TREASURY_RECOVERY_TICKET",        # Real money clawed back from merchant
        "INTERNAL_LEDGER_ADJUSTMENT",      # Books updated, ZERO cash moves (fees/taxes)
        "RESOLVED_NO_ACTION", 
        "ESCALATE_TO_HUMAN"
    ]
    amount: float
    requires_cash_movement: bool
    justification: str
    status: str

# ==========================================
# 2. DETERMINISTIC ROUTING LOGIC
# ==========================================
def process_report(report_file: str):
    with open(report_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    case = data.get("case_details", {})
    ai_report = data.get("investigation_result", {})
    
    case_id = case.get("case_id")
    merchant_id = case.get("merchant_id")
    
    try:
        gap = float(case.get("discrepancy_amount", 0.0))
    except (ValueError, TypeError):
        gap = 0.0
        
    requires_adj = ai_report.get("requires_financial_adjustment", False)
    requires_cash = ai_report.get("requires_physical_cash_movement", False)
    is_explained = ai_report.get("discrepancy_explained", False)

    # STEP 1: Core Ticketing Logic (Treasury vs Ledger separation)
    if requires_adj:
        if requires_cash:
            if gap > 0:
                action_type = "TREASURY_PAYOUT_TICKET"    # We owe the merchant real cash
                amount = gap
            elif gap < 0:
                action_type = "TREASURY_RECOVERY_TICKET"  # Merchant owes us real cash back
                amount = abs(gap)
            else:
                action_type = "ESCALATE_TO_HUMAN"
                amount = 0.0
        else:
            # Ledger-only update (e.g., internal fees, tax adjustments) - NO cash moves!
            action_type = "INTERNAL_LEDGER_ADJUSTMENT"
            amount = abs(gap)
    else:
        if is_explained:
            action_type = "RESOLVED_NO_ACTION"
            amount = 0.0
            requires_cash = False
        else:
            action_type = "ESCALATE_TO_HUMAN"
            amount = abs(gap)
            requires_cash = False

    # STEP 2: Generate the Ticket
    ticket = RemediationTicket(
        ticket_id=f"TKT-{case_id}",
        case_id=case_id,
        merchant_id=merchant_id,
        action_type=action_type,
        amount=amount,
        requires_cash_movement=requires_cash,
        justification=ai_report.get("primary_cause", "No cause provided"),
        status="PENDING_HUMAN_REVIEW" if action_type != "RESOLVED_NO_ACTION" else "CLOSED"
    )
    
    # STEP 3: Save to Disk
    os.makedirs(TICKETS_DIR, exist_ok=True)
    ticket_path = os.path.join(TICKETS_DIR, f"{ticket.ticket_id}.json")
    
    with open(ticket_path, 'w', encoding='utf-8') as f:
        f.write(ticket.model_dump_json(indent=4))
        
    print(f"Ticket {ticket.ticket_id} | {action_type: <28} | Cash Move: {str(requires_cash): <5} | Amount: ${amount:.2f}")
    return ticket

# ==========================================
# 3. NODE B ORCHESTRATOR
# ==========================================
def run_node_b():
    print("==================================================")
    print(" NODE B: DETERMINISTIC TICKETING & HITL ROUTING")
    print("==================================================")
    
    report_files = glob.glob(os.path.join(INVESTIGATION_REPORTS_DIR, "*_report.json"))
    
    if not report_files:
        print(f"No investigation reports found in {INVESTIGATION_REPORTS_DIR}.")
        return
        
    print(f"Found {len(report_files)} investigation reports to process.\n")
    
    for report_file in report_files:
        process_report(report_file)
        
    print("\nNode B execution complete. Tickets are ready for human review.")