import pandas as pd
from alpha_vantage.timeseries import TimeSeries

def get_data(symbol, api_key, time_series):
    ts = TimeSeries(key=api_key, output_format='pandas')

    try:
        data, _ = ts.get_daily(symbol=symbol, outputsize='full')  # Simplified for testing
    except Exception as e:
        print(f"API call error: {e}")
        return None

    if data.empty:
        print(f"No data available for symbol {symbol}")
        return None

    return data


def filter_by_date_range(data, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    data = data.sort_index()
    return data.loc[start_date:end_date]

def get_stock_symbols(filename):
    df = pd.read_csv(filename)
    return df['Symbol'].tolist()
