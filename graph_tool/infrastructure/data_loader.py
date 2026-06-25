import pandas as pd
from typing import List, Dict, Any, Union

def load_data(source: Union[str, pd.DataFrame], **kwargs) -> pd.DataFrame:
    """
    Loads data from an Excel file or returns the provided DataFrame.
    """
    if isinstance(source, pd.DataFrame):
        return source.copy()
    elif isinstance(source, str):
        if source.endswith(('.xls', '.xlsx')):
            return pd.read_excel(source, **kwargs)
        elif source.endswith('.csv'):
            return pd.read_csv(source, **kwargs)
        else:
            raise ValueError("Unsupported file format. Please provide .xls, .xlsx, or .csv")
    else:
        raise ValueError("Source must be a file path string or a pandas DataFrame.")

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Fills NaN values with empty strings for text processing."""
    return df.fillna("")

def load_and_clean_data(source: Union[str, pd.DataFrame], **kwargs) -> pd.DataFrame:
    """
    Loads data and cleans it by filling NaN values with empty strings.
    Convenience function combining load_data and clean_dataframe.
    """
    df = load_data(source, **kwargs)
    return clean_dataframe(df)
