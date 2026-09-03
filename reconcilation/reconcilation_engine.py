import os
import pandas as pd
import numpy as np

class ReconciliationEngine:
    def __init__(self):
        pass


    def load_data(self,path):
        if not os.path.exists(path):
            print(f"CSV not found at {path}")
            return None
        df=pd.read_csv(path)
        return df


    def save_to_csv(self, path, df):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        print(f"Data saved successfully to {path}")


    def reconcilation_engine(
            self,
            expected_settlement_path="data/expected_settlement.csv",
            observed_transaction_path="data/observed_settlements.csv",
            reconcilation_data_path="data/reconciliation_report.csv",
            discrepancy_data_path="data/discrepancies_report.csv"
        ):

        df_expected=self.load_data(expected_settlement_path)
        df_observed=self.load_data(observed_transaction_path)

        if df_expected is None or df_observed is None:
            return None

        #Group observed settlement by settlement_id
        df_observed_grouped= df_observed[['settlement_id','amount']].groupby('settlement_id',as_index=False).sum()

        df_observed_count = (
            df_observed
            .groupby('settlement_id')
            .size()
            .reset_index(name='observed_transaction_count')
        )

        df_observed_grouped = pd.merge(df_observed_grouped,df_observed_count,on='settlement_id',how='left')

        #Group expected settlement by settlement_id
        df_expected_grouped= df_expected[['settlement_id','net_settlement_amount']].groupby('settlement_id',as_index=False).sum()

        df_reconcilation = pd.merge(
            df_expected_grouped,
            df_observed_grouped,
            on='settlement_id',
            how='outer'
        )

        # Rename columns for clarity and consistency
        df_reconcilation = df_reconcilation.rename(columns={
            'net_settlement_amount': 'expected_amount',
            'amount': 'observed_amount'
        })

        #Fill Missing amounts
        df_reconcilation['observed_amount']=df_reconcilation['observed_amount'].fillna(0)
        df_reconcilation['expected_amount']=df_reconcilation['expected_amount'].fillna(0)
        df_reconcilation['observed_transaction_count']=df_reconcilation['observed_transaction_count'].fillna(0).astype(int)

        #Add status column
        df_reconcilation['status']=np.where(
            df_reconcilation['expected_amount'].round(2)==df_reconcilation['observed_amount'].round(2),
            'MATCH',
            'MISMATCH'
        )

        df_reconcilation['settlement_required']=df_reconcilation['expected_amount']-df_reconcilation['observed_amount']

        self.save_to_csv(path=reconcilation_data_path,df=df_reconcilation)

        df_mismatch = df_reconcilation[df_reconcilation['status']=='MISMATCH']
        self.save_to_csv(path=discrepancy_data_path,df=df_mismatch)

        return df_reconcilation
