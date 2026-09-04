import json
import os
from pydantic import BaseModel, Field
from typing import List, Literal
from openai import OpenAI
from config import INVESTIGATION_REPORTS_DIR

# ==========================================
# 1. STRICT OUTPUT SCHEMA
# ==========================================
class InvestigationResult(BaseModel):
    observations: List[str] = Field(description="Explicit math and cited exact UUIDs")
    primary_cause: str = Field(description="Your deduced root cause of the anomaly")
    requires_financial_adjustment: bool = Field(
        description="True if a debit/credit or retry is required to balance the merchant's account. False if it was successfully resolved or requires no action."
    )
    adjustment_reasoning: str = Field(
        description="One sentence explaining WHY an adjustment is or isn't needed."
    )
    discrepancy_explained: bool
    evidence_chain: List[str]
    evidence_sufficiency: Literal["SUFFICIENT", "INSUFFICIENT"]
    missing_data: List[str]

# ==========================================
# 2. NODE A: EVIDENCE INVESTIGATOR (LOCAL)
# ==========================================
class NodeA_Investigator:
    def __init__(self, model_name: str = "llama3.2"):
        # Points to your local Arch Linux Ollama instance
        self.client = OpenAI(
            base_url="http://localhost:11434/v1", 
            api_key="ollama" 
        )
        self.model_name = model_name


    def analyze_evidence(self, case_record: dict, evidence_bundle: dict) -> InvestigationResult:
        system_prompt = (
            "You are a Lead Financial Forensic Auditor and Distributed Systems Expert. "
            "Your objective is to investigate a settlement discrepancy by analyzing raw system telemetry and payment ledger data.\n\n"
            "Forensic Investigation Framework:\n"
            "1. **Quantify the Gap:** Calculate the exact mathematical delta: (Expected 'net_settlement_amount') - (Sum of 'amount' for SUCCESSFUL 'observed_transactions').\n"
            "2. **Trace the Telemetry:** Examine the 'event_logs' for infrastructure anomalies. Look for dollar values or transaction failures that match your calculated delta.\n"
            "3. **Inspect the Ledger:** Check 'related_payments' for asynchronous state changes (e.g., reversed/refunded payments).\n"
            "4. **Synthesize the Root Cause:** Combine the mathematical delta, ledger state, and system telemetry to deduce the operational reality.\n\n"
            "Strict Directives:\n"
            "- Your 'primary_cause' must read like a professional post-mortem finding.\n"
            "- You MUST explicitly show the mathematical calculation in your report (e.g., 'Expected 5000 - Observed 0 = Gap 5000').\n"
            "- You MUST explicitly cite the exact UUIDs (payment_id, txn_id, or log_id) of the problematic entities.\n"
            "- Only declare evidence as 'INSUFFICIENT' if the mathematical gap is genuinely untraceable.\n"
            "You must output a JSON object with EXACTLY these keys:\n"
            "{\n"
            '  "observations": ["Explicit math: Expected X - Observed Y = Gap Z", "Cited exact UUID of anomaly in logs or payments"],\n'
            '  "primary_cause": "Your deduced root cause of the anomaly",\n'
            '  "requires_financial_adjustment": true,\n'
            '  "adjustment_reasoning": "One sentence explaining WHY an adjustment is needed based on the gap.",\n'
            '  "discrepancy_explained": true,\n'
            '  "evidence_chain": ["Step 1: Expected [amount] minus Observed [amount] equals [gap]", "Step 2: Log ID [uuid] shows anomaly for Txn/Payment ID [uuid]"],\n'
            '  "evidence_sufficiency": "SUFFICIENT",\n'
            '  "missing_data": []\n'
            "}"
        )

        user_prompt = f"""Case ID: {case_record.get('case_id')}
        Settlement ID: {case_record.get('settlement_id')}
        Discrepancy Amount: {case_record.get('discrepancy_amount')}
        Evidence Bundle:
        {json.dumps(evidence_bundle, separators=(',', ':'))}
        """
        
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            extra_body={
                "options": {
                    "num_ctx": 8192,
                    "num_predict": 512
                }
            }
        )

        raw_json_str = completion.choices[0].message.content
        result = InvestigationResult.model_validate_json(raw_json_str)
        return result

    def save_report(self, case_record: dict, investigation_result: InvestigationResult) -> str:
        """
        Saves the complete case details and AI findings to a JSON file for Node B to consume.
        """
        os.makedirs(INVESTIGATION_REPORTS_DIR, exist_ok=True)
        
        case_id = case_record.get('case_id', 'UNKNOWN_CASE')
        report_filepath = os.path.join(INVESTIGATION_REPORTS_DIR, f"{case_id}_report.json")
        
        full_report = {
            "case_details": case_record,
            "investigation_result": investigation_result.model_dump()
        }
        
        with open(report_filepath, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=4)
            
        return report_filepath