import uuid
import csv
import os
import json
from datetime import datetime,timedelta
from collections import defaultdict
from config import EXPECTED_SETTLEMENT_PATH, DEFAULT_FEE_CHARGE

class ExpectedSettlementGenerator:
    def __init__(self):
        self.successful_payments=[]
        self.expected_settlements=[]
    

    def filter_payments(self,payments):

        for payment in payments:
            
            if payment['payment_status'] == 'SUCCESS':
                self.successful_payments.append(payment.copy())
        
        return self.successful_payments
    

    def calculate_fee(self,fee_charge=DEFAULT_FEE_CHARGE):

        for payment in self.successful_payments:

            payment['platform_fee']=round(fee_charge*payment['amount'],2)
            payment['final_settlement']=round(payment['amount']-payment['platform_fee'],2)
        
        return self.successful_payments
    
    
    def create_batch_settlements(self):

        merchant_payments=defaultdict(list)

        for payment in self.successful_payments:
            merchant_id=payment['merchant_id']
            merchant_payments[merchant_id].append(payment)

        for merchant_id,payments in merchant_payments.items():

            last_payment_time = max([p['payment_updated_at'] for p in payments])
            settlement_time = last_payment_time + timedelta(hours=2)

            gross_amout=sum(
                payment['amount'] for payment in payments
            )

            total_platform_fee=sum(
                payment['platform_fee'] for payment in payments
            )

            net_settlement_amout=sum(
                payment['final_settlement'] for payment in payments
            )

            constituent_payments=[
                {'payment_id':p['payment_id'],'net_amount':p['final_settlement']}
                for p in payments
            ]

            settlement={
                'settlement_id': str(uuid.uuid4()),
                'merchant_id': merchant_id,

                'gross_amount':gross_amout,
                'total_platform_fee':total_platform_fee,
                'net_settlement_amount':net_settlement_amout,

                'payment_count':len(payments),

                'payment_ids':json.dumps(
                    [p['payment_id'] for p in payments]
                ),
                'constituent_payments_raw': json.dumps(constituent_payments),

                'settlement_status':'CREATED',
                'settlement_created_at':settlement_time
            }

            self.expected_settlements.append(settlement)
        return self.expected_settlements
    

    def save_to_csv(self):

        if not self.expected_settlements:
            print("No Payment Data FOund")
            return
        
        file_path=EXPECTED_SETTLEMENT_PATH

        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        
        fieldnames=self.expected_settlements[0].keys()

        with open(file_path,mode='w',newline="",encoding='utf-8') as csv_file:

            writer=csv.DictWriter(csv_file,fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.expected_settlements)

        print(f"Expected Settlement Data saved successfullly to {file_path}")


    def settlement_management(self,payments,fee_charge=DEFAULT_FEE_CHARGE):

        self.filter_payments(payments=payments)
        self.calculate_fee(fee_charge=fee_charge)
        self.create_batch_settlements()
        self.save_to_csv()
        return self.expected_settlements