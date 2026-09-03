import uuid
import random
import csv
import os
import json
from datetime import datetime, timedelta
from config import OBSERVED_SETTLEMENT_PATH, GROUND_TRUTH_PATH, EVENT_LOGS_PATH

class SettlementExecutor:
    def __init__(self):
        self.correct_bank_transactions = []
        self.observed_bank_transactions = []
        self.ground_truth = []
        self.event_logs = []

    def generate_correct_settlements(self, expected_settlements):
        for settlement in expected_settlements:
            self.correct_bank_transactions.append(settlement)
        return self.correct_bank_transactions

    def log_event(self, settlement_id, entity_id, entity_type, event_type, timestamp, details=""):
        self.event_logs.append({
            'log_id': str(uuid.uuid4()),
            'settlement_id': settlement_id,
            'entity_id': entity_id,
            'entity_type': entity_type,
            'event_type': event_type,
            'timestamp': timestamp,
            'details': details
        })

    # ==========================================
    # 1. NORMAL
    # ==========================================
    def normal_transaction(self, settlement):
        txn_time = settlement['settlement_created_at'] + timedelta(hours=12)
        txn_id = str(uuid.uuid4())
        return [{
            'bank_transaction_id': txn_id,
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': settlement['net_settlement_amount'],
            'transaction_status': 'SUCCESS',
            'transaction_created_at': txn_time
        }]

    # ==========================================
    # 2. PARTIAL SETTLEMENT (Chargeback/Reversal)
    # ==========================================
    def partial_settlement(self, settlement):
        txn_time = settlement['settlement_created_at'] + timedelta(hours=12)
        payments = json.loads(settlement.get('constituent_payments_raw', '[]'))
        
        if not payments:
            return self.normal_transaction(settlement)

        reversed_payment = random.choice(payments)
        new_amount = round(settlement['net_settlement_amount'] - reversed_payment['net_amount'], 2)
        txn_id = str(uuid.uuid4())

        # FORENSIC LOG: Reversal happens after settlement is generated
        reversal_time = settlement['settlement_created_at'] + timedelta(hours=1)
        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=reversed_payment['payment_id'],
            entity_type='PAYMENT',
            event_type='PAYMENT_REVERSED',
            timestamp=reversal_time,
            details=f"Customer chargeback received. Amount reversed: {reversed_payment['net_amount']}"
        )

        return [{
            'bank_transaction_id': txn_id,
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': new_amount,
            'transaction_status': 'SUCCESS',
            'transaction_created_at': txn_time
        }]

    # ==========================================
    # 3. MISSING BANK CREDIT (Timeout)
    # ==========================================
    def missing_bank_credit(self, settlement):
        fail_time = settlement['settlement_created_at'] + timedelta(hours=12)
        attempted_txn_id = str(uuid.uuid4())
        
        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=attempted_txn_id,
            entity_type='BANK_TRANSACTION',
            event_type='GATEWAY_TIMEOUT',
            timestamp=fail_time,
            details="No response from core banking system during batch dispatch."
        )
        return []

    # ==========================================
    # 4. DUPLICATE BANK CREDIT
    # ==========================================
    def duplicate_bank_credit(self, settlement):
        txn_time = settlement['settlement_created_at'] + timedelta(hours=12)
        txn_id_1 = str(uuid.uuid4())
        txn_id_2 = str(uuid.uuid4())
        
        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=settlement['settlement_id'],
            entity_type='SETTLEMENT',
            event_type='RETRY_WORKER_ERROR',
            timestamp=txn_time - timedelta(minutes=5),
            details=f"Orphaned cron job restarted. Resulted in duplicate transactions: {txn_id_1} and {txn_id_2}."
        )

        return [
            {
                'bank_transaction_id': txn_id_1,
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'amount': settlement['net_settlement_amount'],
                'transaction_status': 'SUCCESS',
                'transaction_created_at': txn_time
            },
            {
                'bank_transaction_id': txn_id_2,
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'amount': settlement['net_settlement_amount'],
                'transaction_status': 'SUCCESS',
                'transaction_created_at': txn_time + timedelta(seconds=2)
            }
        ]

    # ==========================================
    # 5. FAILED BANK TRANSFER
    # ==========================================
    def failed_bank_transfer(self, settlement):
        txn_time = settlement['settlement_created_at'] + timedelta(hours=12)
        txn_id = str(uuid.uuid4())
        
        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=txn_id,
            entity_type='BANK_TRANSACTION',
            event_type='BENEFICIARY_ACCOUNT_INVALID',
            timestamp=txn_time,
            details="Bank rejected transfer. Merchant account marked as frozen or invalid."
        )

        return [{
            'bank_transaction_id': txn_id,
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': settlement['net_settlement_amount'],
            'transaction_status': 'FAILED',
            'transaction_created_at': txn_time
        }]

    # ==========================================
    # 6. SPLIT SETTLEMENT
    # ==========================================
    def split_settlement(self, settlement):
        txn_time = settlement['settlement_created_at'] + timedelta(hours=12)
        percentage = random.uniform(0.3, 0.7)
        first_amount = round(settlement['net_settlement_amount'] * percentage, 2)
        second_amount = round(settlement['net_settlement_amount'] - first_amount, 2)

        txn_id_1 = str(uuid.uuid4())
        txn_id_2 = str(uuid.uuid4())

        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=settlement['settlement_id'],
            entity_type='SETTLEMENT',
            event_type='TRANCHE_SPLIT_TRIGGERED',
            timestamp=txn_time - timedelta(minutes=10),
            details=f"Amount exceeded single-transfer routing limits. Split into tranches: {txn_id_1} and {txn_id_2}."
        )

        return [
            {
                'bank_transaction_id': txn_id_1,
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'amount': first_amount,
                'transaction_status': 'SUCCESS',
                'transaction_created_at': txn_time
            },
            {
                'bank_transaction_id': txn_id_2,
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'amount': second_amount,
                'transaction_status': 'SUCCESS',
                'transaction_created_at': txn_time + timedelta(minutes=5)
            }
        ]

    # ==========================================
    # 7. DELAYED SETTLEMENT
    # ==========================================
    def delayed_settlement(self, settlement):
        delay_days = random.randint(1, 3)
        expected_time = settlement['settlement_created_at'] + timedelta(hours=12)
        delayed_txn_time = expected_time + timedelta(days=delay_days)
        txn_id = str(uuid.uuid4())

        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=txn_id,
            entity_type='BANK_TRANSACTION',
            event_type='CLEARING_NETWORK_DELAY',
            timestamp=expected_time + timedelta(hours=1),
            details="Bank network holiday or outage. Transfer queued for next business day."
        )

        return [{
            'bank_transaction_id': txn_id,
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': settlement['net_settlement_amount'],
            'transaction_status': 'SUCCESS',
            'transaction_created_at': delayed_txn_time
        }]

    # ==========================================
    # 8. OVERPAYMENT
    # ==========================================
    def overpayment(self, settlement):
        txn_time = settlement['settlement_created_at'] + timedelta(hours=12)
        extra_amount = round(settlement['net_settlement_amount'] * random.uniform(0.05, 0.10), 2)
        total_amount = round(settlement['net_settlement_amount'] + extra_amount, 2)
        txn_id = str(uuid.uuid4())

        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=settlement['settlement_id'],
            entity_type='SETTLEMENT',
            event_type='MANUAL_CREDIT_ADJUSTMENT',
            timestamp=txn_time - timedelta(hours=2),
            details=f"Manual operations credit of {extra_amount} applied prior to dispatch."
        )

        return [{
            'bank_transaction_id': txn_id,
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': total_amount,
            'transaction_status': 'SUCCESS',
            'transaction_created_at': txn_time
        }]

    # ==========================================
    # 9. REFUND DEDUCTION
    # ==========================================
    def refund_deduction(self, settlement):
        txn_time = settlement['settlement_created_at'] + timedelta(hours=12)
        payments = json.loads(settlement.get('constituent_payments_raw', '[]'))
        
        if not payments:
            return self.normal_transaction(settlement)

        refunded_payment = random.choice(payments)
        new_amount = round(settlement['net_settlement_amount'] - refunded_payment['net_amount'], 2)
        txn_id = str(uuid.uuid4())

        # FORENSIC LOG: Refund initiated by merchant after batching
        refund_time = settlement['settlement_created_at'] + timedelta(hours=2)
        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=refunded_payment['payment_id'],
            entity_type='PAYMENT',
            event_type='MERCHANT_INITIATED_REFUND',
            timestamp=refund_time,
            details=f"Merchant approved refund via dashboard. Amount deducted from active settlement: {refunded_payment['net_amount']}"
        )

        return [{
            'bank_transaction_id': txn_id,
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': new_amount,
            'transaction_status': 'SUCCESS',
            'transaction_created_at': txn_time
        }]

    # ==========================================
    # 10. SYSTEM FEE / TAX ADJUSTMENT
    # ==========================================
    def fee_adjustment(self, settlement):
        txn_time = settlement['settlement_created_at'] + timedelta(hours=12)
        
        extra_fee = round(settlement['gross_amount'] * 0.005, 2)
        new_amount = round(settlement['net_settlement_amount'] - extra_fee, 2)
        txn_id = str(uuid.uuid4())

        self.log_event(
            settlement_id=settlement['settlement_id'],
            entity_id=settlement['settlement_id'],
            entity_type='SETTLEMENT',
            event_type='SYSTEM_FEE_ADJUSTMENT',
            timestamp=txn_time - timedelta(hours=1),
            details=f"Late cross-border/tax fee evaluation prior to dispatch. Additional deduction: {extra_fee}"
        )

        return [{
            'bank_transaction_id': txn_id,
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': new_amount,
            'transaction_status': 'SUCCESS',
            'transaction_created_at': txn_time
        }]

    # ==========================================
    # MAIN OBSERVED DATA GENERATOR
    # ==========================================
    def generate_observed_settlements(self):
        scenarios = [
            'NORMAL', 'PARTIAL_SETTLEMENT', 'MISSING_BANK_CREDIT', 
            'SPLIT_SETTLEMENT', 'DELAYED_SETTLEMENT', 'DUPLICATE_BANK_CREDIT', 
            'OVERPAYMENT', 'FAILED_BANK_TRANSFER', 'REFUND_DEDUCTION', 'FEE_ADJUSTMENT'
        ]
        
        # Weights totaling 100%
        weights = [54, 7, 6, 6, 6, 5, 4, 3, 5, 4]

        for settlement in self.correct_bank_transactions:
            scenario = random.choices(scenarios, weights=weights, k=1)[0]
            transactions = []

            if scenario == 'NORMAL': transactions = self.normal_transaction(settlement)
            elif scenario == 'PARTIAL_SETTLEMENT': transactions = self.partial_settlement(settlement)
            elif scenario == 'MISSING_BANK_CREDIT': transactions = self.missing_bank_credit(settlement)
            elif scenario == 'SPLIT_SETTLEMENT': transactions = self.split_settlement(settlement)
            elif scenario == 'DELAYED_SETTLEMENT': transactions = self.delayed_settlement(settlement)
            elif scenario == 'DUPLICATE_BANK_CREDIT': transactions = self.duplicate_bank_credit(settlement)
            elif scenario == 'OVERPAYMENT': transactions = self.overpayment(settlement)
            elif scenario == 'FAILED_BANK_TRANSFER': transactions = self.failed_bank_transfer(settlement)
            elif scenario == 'REFUND_DEDUCTION': transactions = self.refund_deduction(settlement)
            elif scenario == 'FEE_ADJUSTMENT': transactions = self.fee_adjustment(settlement)

            self.observed_bank_transactions.extend(transactions)

            # Clean hidden column before appending to ground truth
            if 'constituent_payments_raw' in settlement:
                del settlement['constituent_payments_raw']

            self.ground_truth.append({
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'expected_amount': settlement['net_settlement_amount'],
                'scenario': scenario
            })

    def save_to_csv(self, data, file_path):
        if not data:
            return
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        fieldnames = data[0].keys()
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Data saved successfully to {file_path}")

    # ==========================================
    # ORCHESTRATOR
    # ==========================================
    def settlement_executor(self, expected_settlements):
        self.generate_correct_settlements(expected_settlements)
        self.generate_observed_settlements()
        
        self.save_to_csv(data=self.observed_bank_transactions, file_path=OBSERVED_SETTLEMENT_PATH)
        self.save_to_csv(data=self.ground_truth, file_path=GROUND_TRUTH_PATH)
        self.save_to_csv(data=self.event_logs, file_path=EVENT_LOGS_PATH)

        return self.observed_bank_transactions