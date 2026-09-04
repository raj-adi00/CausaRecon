from simulator.generator import Generator
from simulator.expected_settlement import ExpectedSettlementGenerator
from simulator.settlement_executor import SettlementExecutor
from config import DEFAULT_FEE_CHARGE

def generate_synthetic_dataset():
    print("🚀 Starting Synthetic Data Generation...")

    # 1. Generate Raw Customers, Orders, and Payments
    print("\n[1/3] Generating raw payments...")
    payment_gen = Generator()
    payments = payment_gen.generate_payment_event(
        num_merchants=20, 
        num_customers=100, 
        num_orders=400
    )

    # 2. Roll payments up into Expected Settlements
    print("\n[2/3] Calculating expected settlements and fees...")
    expected_gen = ExpectedSettlementGenerator()
    expected_settlements = expected_gen.settlement_management(
        fee_charge=DEFAULT_FEE_CHARGE, 
        payments=payments
    )

    # 3. Execute Bank Transfers & Inject Anomalies (The Ground Truth & Logs)
    print("\n[3/3] Executing bank transfers and injecting operational anomalies...")
    executor = SettlementExecutor()
    executor.settlement_executor(expected_settlements)

    print("\n Dataset generation complete! Check the 'data/' directory.")

if __name__ == "__main__":
    generate_synthetic_dataset()