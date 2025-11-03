# model.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os

DATA_PATH = 'data/household_power_consumption.txt'  # from UCI

def load_and_clean(path=DATA_PATH, nrows=None):
    # file is semicolon separated; missing values are '?'
    df = pd.read_csv(path, sep=';', parse_dates={'dt':['Date','Time']},
                     na_values='?', low_memory=False, nrows=nrows)
    df.rename(columns={
        'Global_active_power':'global_active_power',
        'Global_reactive_power':'global_reactive_power',
        'Voltage':'voltage',
        'Global_intensity':'global_intensity',
        'Sub_metering_1':'sub_1',
        'Sub_metering_2':'sub_2',
        'Sub_metering_3':'sub_3'
    }, inplace=True)
    # convert numeric columns
    for col in ['global_active_power','global_reactive_power','voltage','global_intensity','sub_1','sub_2','sub_3']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['global_active_power'], inplace=True)
    df.set_index('dt', inplace=True)
    return df

def aggregate_monthly(df):
    # Submeterings are in watt-hour of active energy (per minute in dataset)
    # Convert to kWh per timestamp: dataset's global_active_power is in kilowatts averaged per minute
    # We'll aggregate submeterings to monthly kWh (sub_* are in watt-hour, so sum/1000 to kWh)
    monthly = {}
    # Resample to hourly sums first for stability, then monthly
    hourly = df[['sub_1','sub_2','sub_3','global_active_power']].resample('H').sum()
    hourly['total_kwh'] = hourly['global_active_power']  # since global_active_power * minutes => original units; here it's approximate
    monthly_df = hourly.resample('M').sum()
    # Convert sub-metering from Wh to kWh
    monthly_df['zone_A_kwh'] = monthly_df['sub_1'] / 1000.0
    monthly_df['zone_B_kwh'] = monthly_df['sub_2'] / 1000.0
    monthly_df['zone_C_kwh'] = monthly_df['sub_3'] / 1000.0
    monthly_df['total_kwh_est'] = monthly_df['zone_A_kwh'] + monthly_df['zone_B_kwh'] + monthly_df['zone_C_kwh']
    monthly_df = monthly_df[['zone_A_kwh','zone_B_kwh','zone_C_kwh','total_kwh_est']]
    monthly_df = monthly_df.dropna()
    monthly_df.reset_index(inplace=True)
    monthly_df['month'] = monthly_df['dt'].dt.strftime('%Y-%m')
    return monthly_df

def train_and_save(monthly_df, out_path='model.pkl'):
    # We'll train a toy regressor that maps (zone A,B,C kWh) -> total monthly kWh (which is trivial)
    X = monthly_df[['zone_A_kwh','zone_B_kwh','zone_C_kwh']].values
    y = monthly_df['total_kwh_est'].values
    model = LinearRegression()
    model.fit(X, y)
    joblib.dump(model, out_path)
    print(f"Model saved to {out_path}")

if __name__ == '__main__':
    print("Loading data (this may take some time)...")
    df = load_and_clean()
    print("Aggregating monthly...")
    monthly = aggregate_monthly(df)
    monthly.to_csv('data/monthly_usage_sample.csv', index=False)
    print("Saved monthly aggregates to data/monthly_usage_sample.csv")
    print("Training toy model...")
    train_and_save(monthly)
    print("Done.")
