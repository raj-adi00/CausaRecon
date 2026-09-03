import os

# Base project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directory and file paths
DATA_DIR = os.path.join(BASE_DIR, "data")

PAYMENT_DATA_PATH = os.path.join(DATA_DIR, "payment_data.csv")
EXPECTED_SETTLEMENT_PATH = os.path.join(DATA_DIR, "expected_settlement.csv")
OBSERVED_SETTLEMENT_PATH = os.path.join(DATA_DIR, "observed_settlements.csv")
GROUND_TRUTH_PATH = os.path.join(DATA_DIR, "ground_truth.csv")
RECONCILIATION_REPORT_PATH = os.path.join(DATA_DIR, "reconciliation_report.csv")
DISCREPANCIES_REPORT_PATH = os.path.join(DATA_DIR, "discrepancies_report.csv")
EVENT_LOGS_PATH = os.path.join(DATA_DIR, "event_logs.csv")
RECONCILIATION_CASES_PATH = os.path.join(DATA_DIR, "reconciliation_cases.csv")

# Simulation Parameters
DEFAULT_FEE_CHARGE = 0.02