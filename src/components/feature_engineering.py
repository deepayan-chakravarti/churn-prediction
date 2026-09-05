import os
import sys
import pandas as pd

from dataclasses import dataclass

from src.exceptions import CustomException
from src.logger import logging

@dataclass
class FeatureEngineeringConfig:

    members_path: str = os.path.join('data', 'raw', 'kkbox', 'members_v3.csv')
    train_path: str = os.path.join('data', 'raw', 'kkbox', 'train_v2.csv')
    transactions_path: str = os.path.join('data', 'raw', 'kkbox', 'transactions_v2.csv')
    user_logs_path: str = os.path.join('data', 'raw', 'kkbox', 'user_logs_v2.csv')
    output_path: str = os.path.join('artifacts', 'kkbox_final.parquet')

class FeatureEngineering:
    def __init__(self):
        self.config = FeatureEngineeringConfig()

    def load_members_train(self):
        members = pd.read_csv(self.config.members_path) #contains member registration details
        train = pd.read_csv(self.config.train_path)     #classification train data (churn Y/n)
        return members, train

    def aggregate_transactions(self):
        transactions = pd.read_csv(self.config.transactions_path)
        transactions = transactions.sort_values(['msno', 'transaction_date'])

        transanction_agg = transactions.groupby('msno').agg(
            transanction_count = ('msno', 'count'),                      #no. of transactions per user
            first_transaction_date = ('transaction_date', 'min'),
            last_transaction_date = ('transaction_date', 'max'),
            last_plan_days = ('payment_plan_days', 'last'),              #the no. of days the last plan was active per user
            last_plan_price = ('plan_list_price', 'last'),               # the last price listed to an user
            avg_amount_paid = ('actual_amount_paid', 'mean'),            # avergae amount paid for plan per user
            auto_renew_flag = ('is_auto_renew', 'max'),                  #no. of times a user renewed his plan
            cancel_count = ('is_cancel', 'sum')                          #no. of times a user cancelled his plan
        ).reset_index()

        return transanction_agg

    def aggregate_user_logs(self):
        chunks = []

        for chunk in pd.read_csv(self.config.user_logs_path, chunksize=1_000_000):
            agg_chunk = chunk.groupby('msno').agg(
                total_secs = ('total_secs', 'sum'),     #total no. of seconds of music listened per user
                num_unq = ('num_unq', 'sum'),           #no. of unique songs listened by an user
                num_100 = ('num_100', 'sum'),           #no. of songs completely listened by an user
                days_active = ('date', 'count')         #total no. of days active per user
            ).reset_index()
            chunks.append(agg_chunk)

        user_logs_agg = pd.concat(chunks).groupby('msno').sum(numeric_only = True).reset_index()
        return user_logs_agg

    def merge(self, members, train, transaction_agg, user_logs_agg):  #left joining all the tables
        merged_data = train.merge(members, on = 'msno', how = 'left')
        merged_data = merged_data.merge(transaction_agg, on = 'msno', how = 'left')
        merged_data = merged_data.merge(user_logs_agg, on = 'msno', how = 'left')
        return merged_data

    def start_feature_engineering(self):
        logging.info("Started feature engineering for KKBox Music service dataset")
        try:
            members, train = self.load_members_train()
            transanction_agg = self.aggregate_transactions()
            user_logs_agg = self.aggregate_user_logs()
            merged_data = self.merge(members, train, transanction_agg, user_logs_agg)

            os.makedirs(os.path.dirname(self.config.output_path), exist_ok = True)
            merged_data.to_parquet(self.config.output_path, index = False)

            logging.info(f"Feature table saved as parquet to {self.config.output_path}")
            return self.config.output_path

        except Exception as e:
            raise CustomException(e, sys)

if __name__ == '__main__':
    feature_table = FeatureEngineering()
    output_path = feature_table.start_feature_engineering()
    print(f"Done: {output_path}")