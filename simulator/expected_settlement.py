import uuid
import csv
import os
from datetime import datetime
from collections import defaultdict

class ExpectedSettlementGenerator:
    def __init__(self):
        self.successful_payments=[]
        self.expected_settlements=[]
    

    def filter_payments(self,payments):

        for payment in payments:
            
            if payment['payment_status'] == 'SUCCESS':
                self.successful_payments.append(payment.copy())
        
        return self.successful_payments
    

    def calculate_fee(self,fee_charge=0.02):

        for payment in self.successful_payments:

            payment['platform_fee']=fee_charge*payment['amount']
            payment['final_settlement']=payment['amount']-payment['platform_fee']
        
        return self.successful_payments
    
    
    def create_batch_settlements(self):

        merchant_payments=defaultdict(list)

        for payment in self.successful_payments:
            merchant_id=payment['merchant_id']
            merchant_payments[merchant_id].append(payment)

        for merchant_id,payments in merchant_payments.items():

            gross_amout=sum(
                payment['amount'] for payment in payments
            )

            total_platform_fee=sum(
                payment['platform_fee'] for payment in payments
            )

            net_settlement_amout=sum(
                payment['final_settlement'] for payment in payments
            )

            settlement={
                'settlement_id': str(uuid.uuid4()),
                'merchant_id': merchant_id,

                'gross_amount':gross_amout,
                'total_platform_fee':total_platform_fee,
                'net_settlement_amount':net_settlement_amout,

                'payment_count':len(payments),

                'payment_ids':[
                    payment['payment_id'] for payment in payments
                ],

                'settlement_status':'CREATED',
                'settlement_created_at':datetime.now()
            }

            self.expected_settlements.append(settlement)
        return self.expected_settlements
    

    def save_to_csv(self,filename="expected_settlement.csv",folder="data"):

        if not self.expected_settlements:
            print("No Payment Data FOund")
            return
        
        os.makedirs(folder,exist_ok=True)
        file_path=os.path.join(folder,filename)
        
        fieldnames=self.expected_settlements[0].keys()

        with open(file_path,mode='w',newline="",encoding='utf-8') as csv_file:

            writer=csv.DictWriter(csv_file,fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.expected_settlements)

        print(f"Expected Settlement Data saved successfullly to {file_path}")


    def settlement_management(self,fee_charge,payments):

        self.filter_payments(payments=payments)
        self.calculate_fee(fee_charge=fee_charge)
        self.create_batch_settlements()
        self.save_to_csv()
        return self.expected_settlements