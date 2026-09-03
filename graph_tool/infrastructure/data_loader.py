import pandas as pd
import numpy as np
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
        base_dir = os.path.realpath(safe_base_dir) if safe_base_dir else os.path.realpath(os.getcwd())
        file_path = os.path.realpath(source)
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

def _apply_2row_header_logic(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the 2-row header logic to a raw DataFrame without headers.
    """
    # Recover merged cells in the first 2 rows
    header_rows = raw.iloc[:2].ffill(axis=1)

    # Build column names
    columns = []

    for col in range(header_rows.shape[1]):
        level1 = str(header_rows.iloc[0, col]).strip()
        level2 = str(header_rows.iloc[1, col]).strip()

        if level1 == level2:
            column_name = level1
        elif level2.lower() == "nan":
            column_name = level1
        elif level1.lower() == "nan":
            column_name = level2
        else:
            column_name = f"{level1}_{level2}"

        column_name = (
            column_name
            .replace("_Line", "")
        )

        columns.append(column_name)

    # Extract data
    df = raw.iloc[2:].copy()
    df.columns = columns
    # reset index just in case
    df = df.reset_index(drop=True)

    return df


def load_excel_with_2row_header(filepath: str) -> pd.DataFrame:
    """
    Load an Excel file where:
      - rows 0 and 1 form the header
      - merged cells may exist in these rows
    """

    # Read everything as raw data
    raw = pd.read_excel(filepath, header=None)

    return _apply_2row_header_logic(raw)

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
    If the loaded data contains an empty column header (denoted by "Unnamed:"),
    it reconstructs the raw dataframe and applies the 2-row header logic.

    Args:
        source (Union[str, pd.DataFrame]): The file path or a pandas DataFrame.
        **kwargs: Additional arguments passed to pandas `read_excel` or `read_csv`.

    Returns:
        pd.DataFrame: The loaded and cleaned DataFrame.
    """
    df = load_data(source, **kwargs)

    # Check if any column name indicates an empty header
    if any("Unnamed:" in str(col) for col in df.columns):
        # Reconstruct the raw dataframe
        raw_cols = [np.nan if "Unnamed:" in str(col) else col for col in df.columns]
        raw_cols_df = pd.DataFrame([raw_cols], columns=df.columns)
        raw_df = pd.concat([raw_cols_df, df], ignore_index=True)
        # Reset column names to match raw pd.read_excel(header=None) format
        raw_df.columns = range(raw_df.shape[1])

        df = _apply_2row_header_logic(raw_df)

    return clean_dataframe(df)

def extract_document_preuve_pairs(
    source: Union[str, pd.DataFrame],
    doc_col: str = "Document",
    preuve_col: str = "Preuve",
    **kwargs
) -> pd.DataFrame:
    """
    Extracts unique pairs of document names and preuve texts from a data source.
    Handles both simple format (columns named 'Documents' and 'Preuves') and
    2-row header formats (columns like '[Métier]_Reference GED PC' and '[Métier]_Preuve de conformité').

    Args:
        source (Union[str, pd.DataFrame]): The data source.
        doc_col (str, optional): The output column name for documents. Defaults to "Document".
        preuve_col (str, optional): The output column name for preuves. Defaults to "Preuve".
        **kwargs: Additional arguments for load_data.

    Returns:
        pd.DataFrame: A dataframe containing unique document and preuve pairs.
    """
    df = load_and_clean_data(source, **kwargs)
    pairs = set()

    # Check for simple format
    if "Documents" in df.columns and "Preuves" in df.columns:
        for _, row in df.iterrows():
            doc = str(row["Documents"]).strip()
            prv = str(row["Preuves"]).strip()
            if doc and prv:
                pairs.add((doc, prv))
    else:
        # Check for 2-row header or combined columns format
        for col in df.columns:
            col_str = str(col)
            if col_str.endswith("_Reference GED PC"):
                prefix = col_str[:-len("_Reference GED PC")]
                preuve_target_col = f"{prefix}_Preuve de conformité"

                if preuve_target_col in df.columns:
                    for _, row in df.iterrows():
                        doc = str(row[col]).strip()
                        prv = str(row[preuve_target_col]).strip()
                        if doc and prv:
                            pairs.add((doc, prv))

    return pd.DataFrame(list(pairs), columns=[doc_col, preuve_col])
