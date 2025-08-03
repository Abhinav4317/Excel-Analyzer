import streamlit as st
import polars as pl
import pandas as pd
from io import BytesIO

# This is the user-provided "last working" version of the data loader.
# It uses the pandas engine, which was working for most files.
# The @st.cache_data decorator is used here as it was in the original trusted version.
@st.cache_data(show_spinner="Loading and caching Excel file...")
def load_excel_data(file_content, file_name):
    """
    Loads all sheets from the content of an uploaded Excel file into a dictionary of Polars DataFrames.
    
    Args:
        file_content (bytes): The byte content of the uploaded file.
        file_name (str): The name of the file, used for display and caching.

    Returns:
        A dictionary where keys are sheet names and values are Polars DataFrames.
        Returns None if the file cannot be processed.
    """
    if file_content is None:
        return None
        
    try:
        file_bytes = BytesIO(file_content)
        
        # Use pandas to read all sheets, as it has a more robust engine for this.
        pd_sheets = pd.read_excel(file_bytes, sheet_name=None, engine='openpyxl')
        
        # Convert the dictionary of pandas DataFrames to Polars DataFrames
        polars_dfs = {sheet_name: pl.from_pandas(df) for sheet_name, df in pd_sheets.items()}
        
        st.success(f"Successfully loaded {len(polars_dfs)} sheets from `{file_name}`.")
        return polars_dfs
        
    except Exception as e:
        st.error(f"Error loading or processing the Excel file: {e}")
        return None
