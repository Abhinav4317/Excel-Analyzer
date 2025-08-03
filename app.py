import streamlit as st
import polars as pl
from io import BytesIO
import time
import hashlib
from modules.data_loader import load_excel_data
from modules.ui_components import render_operation_ui, OPERATION_OPTIONS
from modules.formula_translator import apply_analysis

# --- Page Configuration ---
st.set_page_config(
    page_title="High-Performance Excel Analyzer",
    page_icon="⚡",
    layout="wide"
)

# --- Initialize Session State ---
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = None
if 'preview_df' not in st.session_state:
    st.session_state.preview_df = None
if 'main_df_name' not in st.session_state:
    st.session_state.main_df_name = None
if 'analysis_definitions' not in st.session_state:
    st.session_state.analysis_definitions = []
if 'active_file_hash' not in st.session_state:
    st.session_state.active_file_hash = None

# --- Sidebar for Controls ---
with st.sidebar:
    st.title("⚙️ Configuration")
    st.caption("Version 11.0 STABLE")

    uploaded_file = st.file_uploader(
        "Upload an Excel file",
        type=["xlsx", "xls"],
        key="file_uploader"
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.md5(file_bytes).hexdigest()

        if st.session_state.active_file_hash != file_hash:
            # This logic is based on the user's trusted version.
            # The data loader now uses the @st.cache_data decorator.
            loaded_dfs = load_excel_data(file_bytes, uploaded_file.name)

            # Update state for the new file
            st.session_state.active_file_hash = file_hash
            st.session_state.dataframes = loaded_dfs
            st.session_state.analysis_definitions = []
            st.session_state.preview_df = None
            
            # CRITICAL FIX: Explicitly check the type and content of loaded_dfs
            if isinstance(loaded_dfs, dict) and loaded_dfs:
                st.session_state.main_df_name = list(loaded_dfs.keys())[0]
            else:
                st.session_state.main_df_name = None
            st.rerun()

    # This part of the sidebar logic will now run reliably after a file is loaded and the script reruns.
    if isinstance(st.session_state.dataframes, dict) and st.session_state.dataframes:
        df_names = list(st.session_state.dataframes.keys())
        
        try:
            current_index = df_names.index(st.session_state.main_df_name)
        except (ValueError, TypeError):
            if df_names:
                st.session_state.main_df_name = df_names[0]
                current_index = 0
            else: 
                st.session_state.main_df_name = None
                current_index = 0

        if st.session_state.main_df_name:
            selected_df_name = st.selectbox(
                "Select main worksheet for analysis",
                options=df_names,
                index=current_index,
                key="main_df_selector"
            )
            if st.session_state.main_df_name != selected_df_name:
                st.session_state.main_df_name = selected_df_name
                st.session_state.preview_df = None
                st.rerun()

# --- Main Application Area ---
st.title("⚡ High-Performance Excel Analyzer")

# CRITICAL FIX: This main condition uses explicit checks to prevent the "truth value" error.
if st.session_state.main_df_name and isinstance(st.session_state.dataframes, dict) and st.session_state.dataframes:
    main_df = st.session_state.dataframes[st.session_state.main_df_name]
    
    st.header(f"Original Data: `{st.session_state.main_df_name}`")
    st.dataframe(main_df, use_container_width=True, height=300)
    
    n_rows, n_cols = main_df.shape
    st.write(f"Shape: **{n_rows:,}** rows, **{n_cols}** columns")

    st.header("Analysis Builder")
    st.info("Define a pipeline of analysis steps below. The steps are not applied until you click 'Generate Preview'.")
    
    def add_analysis_step():
        st.session_state.analysis_definitions.append({'operation_type': 'CONDITIONAL_AGG'})

    st.button("➕ Add New Analysis Step", on_click=add_analysis_step)

    # --- Analysis Pipeline Definition ---
    for i, analysis_def in enumerate(st.session_state.analysis_definitions):
        key_prefix = f"analysis_{i}"
        expander_title = f"Step {i+1}: {analysis_def.get('new_col_name') or 'New Step'}"
        
        with st.expander(expander_title, expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_col_name = st.text_input(
                    "Step Name / New Column Name",
                    value=analysis_def.get('new_col_name', ''),
                    key=f"{key_prefix}_new_col_name"
                )
            with col2:
                if st.button("❌ Remove Step", key=f"{key_prefix}_remove"):
                    st.session_state.analysis_definitions.pop(i)
                    st.rerun()

            operation_keys = list(OPERATION_OPTIONS.keys())
            operation_values = list(OPERATION_OPTIONS.values())
            current_op_key = analysis_def.get('operation_type')
            current_op_index = operation_keys.index(current_op_key) if current_op_key in operation_keys else 0

            selected_op_value = st.selectbox(
                "Select Operation Type",
                options=operation_values,
                index=current_op_index,
                key=f"{key_prefix}_op_type"
            )
            new_op_key = operation_keys[operation_values.index(selected_op_value)]

            st.session_state.analysis_definitions[i]['new_col_name'] = new_col_name
            if new_op_key != current_op_key:
                st.session_state.analysis_definitions[i] = {
                    'new_col_name': new_col_name,
                    'operation_type': new_op_key
                }
                st.rerun()
            
            render_operation_ui(
                st.session_state.analysis_definitions[i],
                st.session_state.dataframes,
                main_df.columns,
                key_prefix
            )
            st.markdown("---")


    # --- Pipeline Execution ---
    if st.session_state.analysis_definitions:
        if st.button("🚀 Generate Preview / Apply All Steps", type="primary"):
            with st.spinner("Applying analysis pipeline... Please wait."):
                start_time = time.time()
                temp_df = main_df.clone()
                error_occured = False
                
                for i, step_def in enumerate(st.session_state.analysis_definitions):
                    try:
                        temp_df = apply_analysis(temp_df, step_def, st.session_state.dataframes)
                    except Exception as e:
                        st.error(f"**Error in Step {i+1} ('{step_def.get('new_col_name', 'N/A')}')**: {e}")
                        error_occured = True
                        break
                
                end_time = time.time()
                duration = end_time - start_time

                if not error_occured:
                    st.session_state.preview_df = temp_df
                    st.success(f"✅ Analysis pipeline completed successfully in {duration:.2f} seconds.")

    # --- Preview and Export Section ---
    if st.session_state.preview_df is not None:
        st.header("📊 Preview of Analyzed Data")
        st.info("This is a preview of your data after applying all steps. Your original data remains unchanged.")
        preview_df = st.session_state.preview_df
        st.dataframe(preview_df, use_container_width=True, height=300)
        
        prev_n_rows, prev_n_cols = preview_df.shape
        st.write(f"Preview Shape: **{prev_n_rows:,}** rows, **{prev_n_cols}** columns")

        st.header("Export Results")
        with BytesIO() as buf:
            preview_df.write_csv(buf)
            csv_data = buf.getvalue()

        st.download_button(
            label="Download Analyzed Data as CSV",
            data=csv_data,
            file_name=f"{st.session_state.main_df_name}_analyzed.csv",
            mime="text/csv",
        )
else:
    st.info("👋 Welcome! Please upload an Excel file using the sidebar to begin.")
