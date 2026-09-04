import pandas as pd
from reconcilation.reconcilation_engine import ReconciliationEngine
from tools.investigation_tools import InvestigationTools 
from node.node_a import NodeA_Investigator
from config import RECONCILIATION_CASES_PATH
import json

def run_pipeline():
    print("==================================================")
    print("1. RUNNING DETERMINISTIC RECONCILIATION ENGINE")
    print("==================================================")
    
    recon_engine = ReconciliationEngine()
    recon_engine.reconciliation_engine()

    print("\n==================================================")
    print("2. INITIALIZING AI INCIDENT RESPONSE SHELL")
    print("==================================================")
    
    tools = InvestigationTools()
    node_a = NodeA_Investigator(model_name="llama3.2")

    try:
        cases_df = pd.read_csv(RECONCILIATION_CASES_PATH)
    except FileNotFoundError:
        print(f"Error: {RECONCILIATION_CASES_PATH} not found. Run main_simulator.py first.")
        return

    pending_mask = cases_df['case_status'] == 'PENDING_INVESTIGATION'
    pending_cases = cases_df[pending_mask]

    if pending_cases.empty:
        print("No pending cases to investigate. System is fully reconciled.")
        return

    print(f"Found {len(pending_cases)} pending case(s). Starting execution loop...\n")

    for index, case in pending_cases.iterrows():
        settlement_id = case['settlement_id']
        case_id = case['case_id']
        case_dict=case.to_dict()
        
        print(f" Investigating Case: {case_id} | Missing Amount: {case['discrepancy_amount']}")
        print("[Shell] Gathering deterministic evidence bundle...")
        evidence_bundle = tools.investigate_settlement_data(settlement_id)

        bundle_str=json.dumps(evidence_bundle)
        print(f"[Shell] Evidence gathered! Payload size: {len(bundle_str)} characters.", flush=True)
 
        try:
            investigation_result = node_a.analyze_evidence(case_dict, evidence_bundle)

            saved_path = node_a.save_report(case_dict, investigation_result)
            
            print("\n" + "-"*40)
            print(" NODE A: INVESTIGATION REPORT")
            print("-"*40)
            print(f"  Primary Cause: {investigation_result.primary_cause}")
            print(f"  Math Matches Discrepancy: {investigation_result.discrepancy_explained}")
            print(f"  Evidence Sufficiency: {investigation_result.evidence_sufficiency}")
            print("\n Evidence Chain:")
            for step in investigation_result.evidence_chain:
                print(f"  -> {step}")
            print("-"*40 + "\n")

            cases_df.at[index, 'case_status'] = 'INVESTIGATION_COMPLETE'
            cases_df.at[index, 'risk_level'] = investigation_result.primary_cause
            
        except Exception as e:
            print(f"\n[Error] LLM Analysis failed for {case_id}: {str(e)}\n")
            cases_df.at[index, 'case_status'] = 'INVESTIGATION_FAILED'

    print("[Shell] Saving updated case ledger to disk...")
    cases_df.to_csv(RECONCILIATION_CASES_PATH, index=False)
    print("Run complete.")

if __name__ == "__main__":
    run_pipeline()