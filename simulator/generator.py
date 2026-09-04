import uuid
from faker import Faker
import random
from datetime import datetime,timedelta
import csv
import os
from config import PAYMENT_DATA_PATH

class Generator:
    def __init__(self):
        self.fake=Faker()
        self.merchants=[]
        self.customers=[]
        self.orders=[]
        self.payments=[]
        self.payment_status=["SUCCESS","FAILED","TIMEOUT"]
        self.base_time=datetime.now()-timedelta(days=7)

    def create_merchant(self,count:int):

        for _ in range(count):

            merchant_name=self.fake.company()
            merchant_id=str(uuid.uuid4())

            self.merchants.append({
                'merchant_name':merchant_name,
                'merchant_id':merchant_id,
                })
            
        return self.merchants


    def create_customer(self,count:int):

        for _ in range(count):

            customer_name=self.fake.name()
            customer_id=str(uuid.uuid4())

            self.customers.append({
                'customer_name':customer_name,
                'customer_id':customer_id,
            })

        return self.customers


    def create_order(self,count:int):

        for _ in range(count):

            order_id=str(uuid.uuid4())
            amount=random.randint(500,50000)
            
            customer=random.choice(self.customers)
            merchant=random.choice(self.merchants)

            random_minutes_offset = random.randint(1, 10000)
            order_time = self.base_time + timedelta(minutes=random_minutes_offset)

            data={
                'order_id':order_id,

                'merchant_name':merchant['merchant_name'],
                'merchant_id':merchant['merchant_id'],

                'customer_id':customer['customer_id'],
                'customer_name':customer['customer_name'],

                'amount':amount,

                'order_created_at':order_time,
                }
            self.orders.append(data)
        return self.orders


    def create_payment(self):

        for order in self.orders:

            payment_id=str(uuid.uuid4())
            payment_status=random.choices(
                self.payment_status,
                weights=[80,10,10],
                k=1
            )[0]

            payment_time = order['order_created_at'] + timedelta(seconds=random.randint(5, 120))

            data={
                **order,
                'payment_id':payment_id,
                'payment_status':payment_status,
                'payment_created_at':payment_time,
                'payment_updated_at':payment_time+timedelta(seconds=2)
            }

            self.payments.append(data)

        return self.payments
    

    def save_to_csv(self):

        if not self.payments:
            print("No Payment Data FOund")
            return
        
        file_path=PAYMENT_DATA_PATH

        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        
        fieldnames=self.payments[0].keys()

        with open(file_path,mode='w',newline="",encoding='utf-8') as csv_file:

            writer=csv.DictWriter(csv_file,fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.payments)

        print(f"Payment Data saved successfullly to {file_path}")


    def generate_payment_event(self,num_merchants=100,num_customers=200,num_orders=2000):

        self.create_merchant(num_merchants)
        self.create_customer(num_customers)
        self.create_order(num_orders)
        self.create_payment()
        self.save_to_csv()

        return self.payments