import pandas as pd
import os
from typing import List, Dict, Any, Union

class SecurityError(Exception):
    """Exception raised for security violations such as path traversal."""
    pass

def load_data(source: Union[str, pd.DataFrame], safe_base_dir: str = None, **kwargs) -> pd.DataFrame:
    """
    Loads data from an Excel/CSV file or returns the provided DataFrame.
    Prevents path traversal by enforcing that the source file is within the `safe_base_dir`.

    Args:
        source (Union[str, pd.DataFrame]): The file path or a pandas DataFrame.
        safe_base_dir (str, optional): The base directory for file loading to prevent path traversal. Defaults to current working directory.
        **kwargs: Additional arguments passed to pandas `read_excel` or `read_csv`.

    Returns:
        pd.DataFrame: The loaded DataFrame.

    Raises:
        SecurityError: If an attempt is made to read outside the allowed base directory.
        ValueError: If the file format is unsupported or the source type is invalid.
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
    """
    Cleans a pandas DataFrame by filling NaN values with empty strings for text processing.

    Args:
        df (pd.DataFrame): The DataFrame to clean.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    return df.fillna("")

def load_and_clean_data(source: Union[str, pd.DataFrame], **kwargs) -> pd.DataFrame:
    """
    Loads data and cleans it by filling NaN values with empty strings.
    This is a convenience function combining `load_data` and `clean_dataframe`.

    Args:
        source (Union[str, pd.DataFrame]): The file path or a pandas DataFrame.
        **kwargs: Additional arguments passed to pandas `read_excel` or `read_csv`.

    Returns:
        pd.DataFrame: The loaded and cleaned DataFrame.
    """
    df = load_data(source, **kwargs)
    return clean_dataframe(df)
