# 🛡️ CausaRecon: Autonomous Fintech Reconciliation & Ticketing Pipeline

> An AI-driven investigation and deterministic treasury/accounting routing platform designed to autonomously audit payment discrepancies, trace system telemetry, and generate compliant operational remediation tickets.

---

## 🏗️ System Architecture

1. **Node A (AI Forensic Investigator):** Powered by Groq's high-speed LPU inference (`openai/gpt-oss-20b`), Node A analyzes raw system logs, payment states, and settlement records to output structured JSON post-mortem reports.
2. **Deterministic Python Guardrail:** Intercepts LLM outputs to programmatically enforce exact mathematical deltas, preventing financial hallucinations and securing audit integrity.
3. **Node B (Deterministic Routing & Ticketing):** Classifies operational fixes, strictly separating internal **Accounting Ledger Adjustments** from external **Physical Cash Movements** (bank wires, ACH, gateway payouts, or clawbacks).
4. **Streamlit Control Center (`app.py`):** An executive-grade interactive dashboard providing live data visualization, one-click dataset simulation, automated pipeline orchestration, and Human-in-the-Loop (HITL) approval gates.

---

## 📂 Project Structure

```text
CausaRecon/
├── data/                      # Output datasets, discrepancy CSVs, and logs
├── node/                      # Node A (AI forensic investigator) & Node B routing logic
├── reconciliation/            # Reconciliation and mathematical guardrail modules
├── simulator/                 # Synthetic transaction and settlement data generator
├── tools/                     # Utility scripts and helper functions
├── venv/                      # Python virtual environment
├── .env                       # Environment variables (API keys - gitignored)
├── .env.exmaple               # Template for environment configuration
├── .gitignore                 # Excludes caches, reports, tickets, and secrets
├── app.py                     # Streamlit executive dashboard control center
├── config.py                  # Central configuration paths and environment constants
├── main_simulator.py          # Entry point for generating synthetic discrepancies
└── main.py                    # Core pipeline orchestrator execution script
```
## 🚀 Getting Started

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/raj-adi00/CausaRecon.git
cd CausaRecon

python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a .env file in the root directory and securely add your Groq API key:
```
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

## 🕹️ Running the Application
### Option A: Via Streamlit Dashboard (Recommended for Demos)
Launch the interactive control center to generate synthetic data, execute the pipeline visually, inspect reports, and approve tickets:
```bash
streamlit run app.py
```

### Option B: Via Terminal CLI
Run the simulator to generate fresh multi-merchant discrepancy records:
```bash
python main_simulator.py
```
Execute the core forensic investigation and ticketing pipeline:
```bash
python main.py
```

## 🛡️ Key Technical Features
1. Sub-Second Cloud Inference: Integrated with Groq's high-speed LPU infrastructure (openai/gpt-oss-20b) for instantaneous pipeline execution during live pitches and audits.

2. Zero-Trust Financial Math: Bypasses LLM calculation vulnerabilities by pairing AI text generation with strict programmatic Pythonic validation.

3. Separation of Concerns: Cleanly delineates paper-only ledger entries (fee updates, tax adjustments) from real-world banking movements (gateway payouts, recovery clawbacks).

4. Human-in-the-Loop (HITL) Governance: Interactive approval workflows ensuring high-risk treasury actions require explicit administrative sign-off before locks and dispatches.

## PPT Link: https://docs.google.com/presentation/d/1v6_0zmzmFkmVMMyTtSfQrwZrHvf6YWrXeMuLh_TUx1Q/edit?usp=sharing
