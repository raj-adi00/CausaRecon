import os
import json
import pandas as pd
from config import (
    EXPECTED_SETTLEMENT_PATH, 
    OBSERVED_SETTLEMENT_PATH, 
    PAYMENT_DATA_PATH,
    EVENT_LOGS_PATH
)

class InvestigationTools:
    def __init__(self):
        pass

    def load_data(self, path):
        if not os.path.exists(path=path):
            print(f"CSV not found at {path}")
            return None
        df = pd.read_csv(path)
        return df
         
    def get_expected_settlement(self, settlement_id):
        df = self.load_data(EXPECTED_SETTLEMENT_PATH)
        if df is None or df.empty:
            return None

        match = df[df['settlement_id'] == settlement_id]
        if match.empty:
            return None

        return match.to_dict(orient='records')[0]

    def get_observed_transactions(self, settlement_id):
        df = self.load_data(OBSERVED_SETTLEMENT_PATH)
        if df is None or df.empty:
            return []

        match = df[df['settlement_id'] == settlement_id]
        if match.empty:
            return []

        return match.to_dict(orient='records')
    
    def get_related_payments(self, settlement_id):
        expected_settlement = self.get_expected_settlement(settlement_id=settlement_id)
        if not expected_settlement:
            return []

        payment_ids_str = expected_settlement.get('payment_ids')
        if not payment_ids_str:
            return []

        if isinstance(payment_ids_str, str):
            try:
                payment_ids = json.loads(payment_ids_str)
            except json.JSONDecodeError:
                payment_ids = []
                print(f"Failed to parse payment_ids JSON for settlement {settlement_id}")
        else:
            payment_ids = payment_ids_str

        df_payments = self.load_data(PAYMENT_DATA_PATH)
        if df_payments is None or df_payments.empty:
            return []

        related_payments = df_payments[df_payments['payment_id'].isin(payment_ids)]
        return related_payments.to_dict(orient='records')

    # ==========================================
    # FORENSIC LOG FETCHER
    # ==========================================
    def get_event_logs(self, settlement_id):
        df = self.load_data(EVENT_LOGS_PATH)
        if df is None or df.empty:
            return []

        match = df[df['settlement_id'] == settlement_id]
        if match.empty:
            return []

        return match.to_dict(orient='records')

    # ==========================================
    # DATA BUNDLER FOR THE LLM NODE
    # ==========================================
    def investigate_settlement_data(self, settlement_id):
        """
        Gathers all deterministic evidence for a specific settlement.
        This dictionary becomes the exact JSON payload passed to Node A (The LLM).
        """
        expected = self.get_expected_settlement(settlement_id)
        observed = self.get_observed_transactions(settlement_id)
        raw_payments = self.get_related_payments(settlement_id)
        logs = self.get_event_logs(settlement_id)

        if expected:
            expected.pop('constituent_payments_raw',None)
            expected.pop('payment_ids',None)

        # Slim down related payments to just essential fields to prevent token bloat
        slim_payments = [
            {
                'payment_id': p.get('payment_id'),
                'order_created_at':p.get('order_created_at'),
                'payment_created_at':p.get('payment_created_at'),
                'payment_updated_at':p.get('payment_updated_at'),
                'amount': p.get('amount'),
                'status': p.get('payment_status')
            }
            for p in raw_payments
        ]

        data = {
            'expected_settlement': [expected] if expected else [],
            'observed_transactions': observed,
            'related_payments': slim_payments,
            'event_logs': logs
        }

        # print(f"Evidence bundle for {settlement_id}:{data}")
        return data