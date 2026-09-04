import os
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
from config import (
    EXPECTED_SETTLEMENT_PATH,
    OBSERVED_SETTLEMENT_PATH,
    RECONCILIATION_REPORT_PATH,
    DISCREPANCIES_REPORT_PATH,
    RECONCILIATION_CASES_PATH
)

class ReconciliationEngine:
    def __init__(self):
        pass

    def load_data(self, path):
        if not os.path.exists(path):
            print(f"CSV not found at {path}")
            return None
        return pd.read_csv(path)

    def save_to_csv(self, path, df):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        print(f"Data saved successfully to {path}")

    def reconciliation_engine(
            self,
            expected_settlement_path=EXPECTED_SETTLEMENT_PATH,
            observed_transaction_path=OBSERVED_SETTLEMENT_PATH,
            reconciliation_data_path=RECONCILIATION_REPORT_PATH,
            discrepancy_data_path=DISCREPANCIES_REPORT_PATH,
            cases_data_path=RECONCILIATION_CASES_PATH
        ):

        df_expected = self.load_data(expected_settlement_path)
        df_observed = self.load_data(observed_transaction_path)

        if df_expected is None or df_observed is None:
            print("Missing source data for reconciliation.")
            return None

        # Group observed settlement by settlement_id
        successful_observed = df_observed[df_observed['transaction_status'] == 'SUCCESS']

        df_observed_grouped = successful_observed[['settlement_id', 'amount']].groupby('settlement_id', as_index=False).sum()

        df_observed_count = (
            df_observed
            .groupby('settlement_id')
            .size()
            .reset_index(name='observed_transaction_count')
        )

        df_observed_grouped = pd.merge(df_observed_grouped, df_observed_count, on='settlement_id', how='left')

        # Group expected settlement by settlement_id
        df_expected_grouped = df_expected[['settlement_id', 'net_settlement_amount']].groupby('settlement_id', as_index=False).sum()

        # Merge expected and observed
        df_reconciliation = pd.merge(
            df_expected_grouped,
            df_observed_grouped,
            on='settlement_id',
            how='outer'
        )

        # Rename columns for clarity and consistency
        df_reconciliation = df_reconciliation.rename(columns={
            'net_settlement_amount': 'expected_amount',
            'amount': 'observed_amount'
        })

        # Fill Missing amounts
        df_reconciliation['observed_amount'] = df_reconciliation['observed_amount'].fillna(0)
        df_reconciliation['expected_amount'] = df_reconciliation['expected_amount'].fillna(0)
        df_reconciliation['observed_transaction_count'] = df_reconciliation['observed_transaction_count'].fillna(0).astype(int)

        # Calculate exact discrepancy amount
        df_reconciliation['discrepancy_amount'] = (df_reconciliation['expected_amount'] - df_reconciliation['observed_amount']).round(2)

        # Add status column
        df_reconciliation['status'] = np.where(
            df_reconciliation['discrepancy_amount'] == 0,
            'MATCH',
            'MISMATCH'
        )

        # Save complete reconciliation report
        self.save_to_csv(path=reconciliation_data_path, df=df_reconciliation)

        # Isolate discrepancies
        df_mismatch = df_reconciliation[df_reconciliation['status'] == 'MISMATCH']
        self.save_to_csv(path=discrepancy_data_path, df=df_mismatch)

        # ==========================================
        # AGENT ENVIRONMENT TRIGGER (NEW)
        # ==========================================
        self.generate_agent_cases(df_mismatch, cases_data_path)

        return df_reconciliation

    def generate_agent_cases(self, df_mismatch, cases_data_path):
        """
        Transforms mismatches into actionable cases for the AI Agent's environment ledger.
        It checks for existing cases to avoid duplicating work on subsequent runs.
        """
        if df_mismatch.empty:
            print("No discrepancies found. No AI cases generated.")
            return

        # Load existing cases to ensure we don't recreate pending cases
        if os.path.exists(cases_data_path):
            df_existing_cases = pd.read_csv(cases_data_path)
            existing_settlement_ids = set(df_existing_cases['settlement_id'].tolist())
        else:
            df_existing_cases = pd.DataFrame()
            existing_settlement_ids = set()

        new_cases = []
        
        for _, row in df_mismatch.iterrows():
            if row['settlement_id'] not in existing_settlement_ids:
                new_cases.append({
                    'case_id': f"CASE-{str(uuid.uuid4())[:8].upper()}",
                    'settlement_id': row['settlement_id'],
                    'expected_amount': row['expected_amount'],
                    'observed_amount': row['observed_amount'],
                    'discrepancy_amount': row['discrepancy_amount'],
                    'case_status': 'PENDING_INVESTIGATION',  # This alerts the Deterministic Shell to route it to Node A
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'risk_level': 'UNASSIGNED',
                    'action_taken': 'NONE',
                    'agent_confidence': 0.0
                })

        if new_cases:
            df_new_cases = pd.DataFrame(new_cases)
            if not df_existing_cases.empty:
                df_combined = pd.concat([df_existing_cases, df_new_cases], ignore_index=True)
            else:
                df_combined = df_new_cases
            
            self.save_to_csv(cases_data_path, df_combined)
            print(f"Generated {len(new_cases)} new case(s) for the AI Incident Response Agent.")
        else:
            print("Discrepancies found, but cases already exist in the ledger. No new AI cases generated.")