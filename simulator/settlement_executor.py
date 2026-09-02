import uuid
import random
import csv
import os
from datetime import datetime, timedelta
from collections import Counter


class SettlementExecutor:

    def __init__(self):
        self.correct_bank_transactions = []
        self.observed_bank_transactions = []
        self.ground_truth = []


    def generate_correct_settlements(self, expected_settlements):

        for settlement in expected_settlements:

            transaction = {
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'amount': settlement['net_settlement_amount'],
            }

            self.correct_bank_transactions.append(transaction)

        return self.correct_bank_transactions


    # ==========================================
    # NORMAL
    # ==========================================

    def normal_transaction(self, settlement):

        return [{
            'bank_transaction_id': str(uuid.uuid4()),
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': settlement['amount'],
            'transaction_status': 'SUCCESS',
            'transaction_created_at': datetime.now()
        }]


    # ==========================================
    # PARTIAL SETTLEMENT
    # ==========================================

    def partial_settlement(self, settlement):

        percentage = random.uniform(0.5, 0.9)

        amount = round(
            settlement['amount'] * percentage,
            2
        )

        return [{
            'bank_transaction_id': str(uuid.uuid4()),
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': amount,
            'transaction_status': 'SUCCESS',
            'transaction_created_at': datetime.now()
        }]


    # ==========================================
    # MISSING BANK CREDIT
    # ==========================================

    def missing_bank_credit(self, settlement):

        # Expected settlement exists,
        # but no observed bank transaction
        return []


    # ==========================================
    # SPLIT SETTLEMENT
    # ==========================================

    def split_settlement(self, settlement):

        total_amount = settlement['amount']

        percentage = random.uniform(0.3, 0.7)

        first_amount = round(
            total_amount * percentage,
            2
        )

        second_amount = round(
            total_amount - first_amount,
            2
        )

        return [
            {
                'bank_transaction_id': str(uuid.uuid4()),
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'amount': first_amount,
                'transaction_status': 'SUCCESS',
                'transaction_created_at': datetime.now()
            },
            {
                'bank_transaction_id': str(uuid.uuid4()),
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'amount': second_amount,
                'transaction_status': 'SUCCESS',
                'transaction_created_at': datetime.now()
            }
        ]


    # ==========================================
    # DELAYED SETTLEMENT
    # ==========================================

    def delayed_settlement(self, settlement):

        delay_days = random.randint(1, 7)

        return [{
            'bank_transaction_id': str(uuid.uuid4()),
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': settlement['amount'],
            'transaction_status': 'SUCCESS',
            'transaction_created_at':
                datetime.now() + timedelta(days=delay_days)
        }]


    # ==========================================
    # DUPLICATE BANK CREDIT
    # ==========================================

    def duplicate_bank_credit(self, settlement):

        transaction_1 = {
            'bank_transaction_id': str(uuid.uuid4()),
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': settlement['amount'],
            'transaction_status': 'SUCCESS',
            'transaction_created_at': datetime.now()
        }

        transaction_2 = {
            'bank_transaction_id': str(uuid.uuid4()),
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': settlement['amount'],
            'transaction_status': 'SUCCESS',
            'transaction_created_at': datetime.now()
        }

        return [transaction_1, transaction_2]


    # ==========================================
    # OVERPAYMENT
    # ==========================================

    def overpayment(self, settlement):

        percentage = random.uniform(1.05, 1.30)

        amount = round(
            settlement['amount'] * percentage,
            2
        )

        return [{
            'bank_transaction_id': str(uuid.uuid4()),
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': amount,
            'transaction_status': 'SUCCESS',
            'transaction_created_at': datetime.now()
        }]


    # ==========================================
    # FAILED BANK TRANSFER
    # ==========================================

    def failed_bank_transfer(self, settlement):

        return [{
            'bank_transaction_id': str(uuid.uuid4()),
            'settlement_id': settlement['settlement_id'],
            'merchant_id': settlement['merchant_id'],
            'amount': settlement['amount'],
            'transaction_status': 'FAILED',
            'transaction_created_at': datetime.now()
        }]


    # ==========================================
    # MAIN OBSERVED DATA GENERATOR
    # ==========================================

    def generate_observed_settlements(self):

        scenarios = [
            'NORMAL',
            'PARTIAL_SETTLEMENT',
            'MISSING_BANK_CREDIT',
            'SPLIT_SETTLEMENT',
            'DELAYED_SETTLEMENT',
            'DUPLICATE_BANK_CREDIT',
            'OVERPAYMENT',
            'FAILED_BANK_TRANSFER'
        ]

        weights = [
            60,  # NORMAL
            8,   # PARTIAL
            7,   # MISSING
            7,   # SPLIT
            6,   # DELAYED
            5,   # DUPLICATE
            4,   # OVERPAYMENT
            3    # FAILED
        ]


        for settlement in self.correct_bank_transactions:

            scenario = random.choices(
                scenarios,
                weights=weights,
                k=1
            )[0]


            if scenario == 'NORMAL':
                transactions = self.normal_transaction(settlement)

            elif scenario == 'PARTIAL_SETTLEMENT':
                transactions = self.partial_settlement(settlement)

            elif scenario == 'MISSING_BANK_CREDIT':
                transactions = self.missing_bank_credit(settlement)

            elif scenario == 'SPLIT_SETTLEMENT':
                transactions = self.split_settlement(settlement)

            elif scenario == 'DELAYED_SETTLEMENT':
                transactions = self.delayed_settlement(settlement)

            elif scenario == 'DUPLICATE_BANK_CREDIT':
                transactions = self.duplicate_bank_credit(settlement)

            elif scenario == 'OVERPAYMENT':
                transactions = self.overpayment(settlement)

            elif scenario == 'FAILED_BANK_TRANSFER':
                transactions = self.failed_bank_transfer(settlement)


            self.observed_bank_transactions.extend(transactions)


            # Hidden ground truth
            self.ground_truth.append({
                'settlement_id': settlement['settlement_id'],
                'merchant_id': settlement['merchant_id'],
                'expected_amount': settlement['amount'],
                'scenario': scenario
            })

        print(
            Counter(
                item['scenario'] for item in self.ground_truth
            )
        )


        return self.observed_bank_transactions


    # ==========================================
    # SAVE OBSERVED DATA
    # ==========================================

    def save_to_csv(
        self,
        data,
        filename="observed_settlements.csv",
        folder="data",
    ):

        if not data:
            print("No observed settlement data found")
            return

        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, filename)

        fieldnames = data[0].keys()

        with open(
            file_path,
            mode='w',
            newline='',
            encoding='utf-8'
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames
            )

            writer.writeheader()
            writer.writerows(
                data
            )

        print(
            f"Data saved successfully to {file_path}"
        )


    # ==========================================
    # ORCHESTRATOR
    # ==========================================

    def settlement_executor(self, expected_settlements):

        self.generate_correct_settlements(
            expected_settlements
        )

        self.generate_observed_settlements()

        self.save_to_csv(
            data=self.observed_bank_transactions,
            filename="observed_settlements.csv",
            folder="data",
        )

        self.save_to_csv(
            data=self.ground_truth,
            filename="ground_truth.csv",
            folder="data"
        )

        return self.observed_bank_transactions