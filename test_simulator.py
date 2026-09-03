from simulator.generator import Generator
from simulator.expected_settlement import ExpectedSettlementGenerator
from simulator.settlement_executor import SettlementExecutor

def run_simulation_pipeline():
    print("==========================================")
    print("STEP 1: Generating Raw Payment Events")
    print("==========================================")
    generator = Generator()
    payments = generator.generate_payment_event(
        num_merchants=10, 
        num_customers=50, 
        num_orders=200
    )
    print(f"-> Generated {len(payments)} total payments.\n")

    print("==========================================")
    print("STEP 2: Processing Expected Settlements")
    print("==========================================")
    settlement_gen = ExpectedSettlementGenerator()
    expected_settlements = settlement_gen.settlement_management(
        fee_charge=0.02, 
        payments=payments
    )
    print(f"-> Generated {len(expected_settlements)} expected batch settlements.\n")

    print("==========================================")
    print("STEP 3: Executing Bank Reconciliation & Scenarios")
    print("==========================================")
    executor = SettlementExecutor()
    observed_transactions = executor.settlement_executor(
        expected_settlements=expected_settlements
    )
    print(f"-> Generated {len(observed_transactions)} observed bank transactions.")
    print("-> Ground truth scenario distribution recorded.")
    
    print("\n==========================================")
    print("PIPELINE COMPLETE! All CSVs saved to /data")
    print("==========================================")

if __name__ == "__main__":
    run_simulation_pipeline()