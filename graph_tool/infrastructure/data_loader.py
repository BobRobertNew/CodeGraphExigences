import pandas as pd
import os
from typing import List, Dict, Any, Union

class SecurityError(Exception):
    """Exception raised for security violations such as path traversal."""
    pass

def load_data(source: Union[str, pd.DataFrame], safe_base_dir: str = None, **kwargs) -> pd.DataFrame:
    """
    Loads data from an Excel file or returns the provided DataFrame.
    Prevents path traversal by enforcing that the source file is within the safe_base_dir.
    """
    if isinstance(source, pd.DataFrame):
        return source.copy()
    elif isinstance(source, str):
        base_dir = os.path.abspath(safe_base_dir) if safe_base_dir else os.path.abspath(os.getcwd())
        file_path = os.path.abspath(source)
        if os.path.commonpath([base_dir, file_path]) != base_dir:
            raise SecurityError(f"Path traversal detected: Attempted to access a file outside of the allowed base directory: {base_dir}")

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
