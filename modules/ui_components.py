import streamlit as st

# A dictionary to map operation names to their display text
OPERATION_OPTIONS = {
    "CONDITIONAL_AGG": "Conditional Aggregation (SUMIF, COUNTIF, etc.)",
    "VLOOKUP": "VLOOKUP (Join across sheets)",
    "IF": "IF Condition (Categorize)",
    "MATH": "Calculate from other columns (Math)",
}

def render_vlookup_builder(analysis_def, all_dfs, main_df_columns, key_prefix):
    """Renders UI for VLOOKUP operation."""
    st.subheader("VLOOKUP Configuration")
    st.info("This operation joins data from another sheet based on a matching key, similar to Excel's VLOOKUP.")
    col1, col2, col3 = st.columns(3)

    with col1:
        analysis_def['left_on'] = st.selectbox(
            "Left Column (from this sheet)",
            options=main_df_columns,
            index=main_df_columns.index(analysis_def.get('left_on')) if analysis_def.get('left_on') in main_df_columns else 0,
            key=f"{key_prefix}_vlookup_left_on"
        )

    with col2:
        df_names = list(all_dfs.keys())
        selected_df_name = st.selectbox(
            "Lookup Table (Sheet to get data from)",
            options=df_names,
            index=df_names.index(analysis_def.get('lookup_df_name')) if analysis_def.get('lookup_df_name') in df_names else 0,
            key=f"{key_prefix}_vlookup_df"
        )
        analysis_def['lookup_df_name'] = selected_df_name
        lookup_df_cols = all_dfs[selected_df_name].columns

    with col3:
        analysis_def['right_on'] = st.selectbox(
            "Right Column (from lookup table)",
            options=lookup_df_cols,
            index=lookup_df_cols.index(analysis_def.get('right_on')) if analysis_def.get('right_on') in lookup_df_cols else 0,
            key=f"{key_prefix}_vlookup_right_on"
        )

    analysis_def['value_col'] = st.selectbox(
        "Column to Return (from lookup table)",
        options=lookup_df_cols,
        index=lookup_df_cols.index(analysis_def.get('value_col')) if analysis_def.get('value_col') in lookup_df_cols else 0,
        key=f"{key_prefix}_vlookup_value_col"
    )

def render_math_builder(analysis_def, main_df_columns, key_prefix):
    """Renders UI for Math operation."""
    st.subheader("Math Calculation")
    col1, col2, col3 = st.columns(3)

    with col1:
        analysis_def['first_col'] = st.selectbox(
            "First Column",
            options=main_df_columns,
            index=main_df_columns.index(analysis_def.get('first_col')) if analysis_def.get('first_col') in main_df_columns else 0,
            key=f"{key_prefix}_math_first_col"
        )
    with col2:
        analysis_def['operator'] = st.selectbox(
            "Operator",
            options=['+', '-', '*', '/'],
            index=['+', '-', '*', '/'].index(analysis_def.get('operator')) if analysis_def.get('operator') in ['+', '-', '*', '/'] else 0,
            key=f"{key_prefix}_math_op"
        )
    with col3:
        analysis_def['second_col'] = st.selectbox(
            "Second Column",
            options=main_df_columns,
            index=main_df_columns.index(analysis_def.get('second_col')) if analysis_def.get('second_col') in main_df_columns else 0,
            key=f"{key_prefix}_math_second_col"
        )

def render_if_builder(analysis_def, main_df_columns, key_prefix):
    """Renders UI for IF Condition operation."""
    st.subheader("IF Condition (Categorization)")
    st.info("This creates a new column with one of two values, based on a condition.")
    col1, col2, col3 = st.columns(3)

    with col1:
        analysis_def['if_col'] = st.selectbox(
            "Column to Check",
            options=main_df_columns,
            index=main_df_columns.index(analysis_def.get('if_col')) if analysis_def.get('if_col') in main_df_columns else 0,
            key=f"{key_prefix}_if_col"
        )
    with col2:
        operators = ['==', '!=', '>', '<', '>=', '<=']
        analysis_def['if_operator'] = st.selectbox(
            "Operator",
            options=operators,
            index=operators.index(analysis_def.get('if_operator')) if analysis_def.get('if_operator') in operators else 0,
            key=f"{key_prefix}_if_op"
        )
    with col3:
        # UI to choose between comparing to a value or another column
        compare_type = st.radio(
            "Compare Against",
            ["Absolute Value", "Another Column"],
            key=f"{key_prefix}_if_compare_type",
            horizontal=True,
            index=["Absolute Value", "Another Column"].index(analysis_def.get('if_compare_type', 'Absolute Value'))
        )
        analysis_def['if_compare_type'] = compare_type

        if compare_type == "Absolute Value":
            analysis_def['if_value'] = st.text_input(
                "Value",
                value=analysis_def.get('if_value', ''),
                key=f"{key_prefix}_if_val"
            )
        else:
            other_cols = [c for c in main_df_columns if c != analysis_def.get('if_col')]
            analysis_def['if_compare_col'] = st.selectbox(
                "Column to Compare Against",
                options=other_cols,
                index=other_cols.index(analysis_def.get('if_compare_col')) if analysis_def.get('if_compare_col') in other_cols else 0,
                key=f"{key_prefix}_if_compare_col_select"
            )


    col4, col5 = st.columns(2)
    with col4:
        analysis_def['value_if_true'] = st.text_input(
            "Value if TRUE",
            value=analysis_def.get('value_if_true', ''),
            key=f"{key_prefix}_if_true"
        )
    with col5:
        analysis_def['value_if_false'] = st.text_input(
            "Value if FALSE",
            value=analysis_def.get('value_if_false', ''),
            key=f"{key_prefix}_if_false"
        )

def render_conditional_agg_builder(analysis_def, main_df_columns, key_prefix):
    """Renders UI for a powerful conditional aggregation (SUMIF, COUNTIF, etc.)."""
    st.subheader("Conditional Aggregation")
    st.info("This calculates a result (like a sum or count) on a column, but only for rows that meet specific criteria.")

    # --- Step 1: Define the condition ---
    st.write("##### **Condition (Rows to Include)**")
    col1, col2, col3 = st.columns(3)
    with col1:
        analysis_def['cond_agg_if_col'] = st.selectbox(
            "Column to Check",
            options=main_df_columns,
            index=main_df_columns.index(analysis_def.get('cond_agg_if_col')) if analysis_def.get('cond_agg_if_col') in main_df_columns else 0,
            key=f"{key_prefix}_cond_agg_if_col"
        )
    with col2:
        operators = ['==', '!=', '>', '<', '>=', '<=']
        analysis_def['cond_agg_operator'] = st.selectbox(
            "Operator",
            options=operators,
            index=operators.index(analysis_def.get('cond_agg_operator')) if analysis_def.get('cond_agg_operator') in operators else 0,
            key=f"{key_prefix}_cond_agg_op"
        )
    with col3:
        compare_type = st.radio(
            "Compare Against",
            ["Absolute Value", "Another Column"],
            key=f"{key_prefix}_cond_agg_compare_type",
            horizontal=True,
            index=["Absolute Value", "Another Column"].index(analysis_def.get('cond_agg_compare_type', 'Absolute Value'))
        )
        analysis_def['cond_agg_compare_type'] = compare_type

        if compare_type == "Absolute Value":
            analysis_def['cond_agg_value'] = st.text_input(
                "Value",
                value=analysis_def.get('cond_agg_value', ''),
                key=f"{key_prefix}_cond_agg_val"
            )
        else:
            other_cols = [c for c in main_df_columns if c != analysis_def.get('cond_agg_if_col')]
            analysis_def['cond_agg_compare_col'] = st.selectbox(
                "Column to Compare Against",
                options=other_cols,
                index=other_cols.index(analysis_def.get('cond_agg_compare_col')) if analysis_def.get('cond_agg_compare_col') in other_cols else 0,
                key=f"{key_prefix}_cond_agg_compare_col_select"
            )


    # --- Step 2: Define the calculation ---
    st.write("##### **Calculation (On the Rows That Match)**")
    col4, col5 = st.columns(2)
    with col4:
        agg_functions = ['Sum', 'Count', 'Average', 'Min', 'Max']
        analysis_def['cond_agg_function'] = st.selectbox(
            "Calculation to Perform",
            options=agg_functions,
            index=agg_functions.index(analysis_def.get('cond_agg_function')) if analysis_def.get('cond_agg_function') in agg_functions else 0,
            key=f"{key_prefix}_cond_agg_func"
        )

    with col5:
        if analysis_def.get('cond_agg_function', 'Sum') != 'Count':
            analysis_def['cond_agg_calc_col'] = st.selectbox(
                f"Column to {analysis_def.get('cond_agg_function', 'Sum')}",
                options=main_df_columns,
                index=main_df_columns.index(analysis_def.get('cond_agg_calc_col')) if analysis_def.get('cond_agg_calc_col') in main_df_columns else 0,
                key=f"{key_prefix}_cond_agg_calc_col"
            )
        else:
            analysis_def['cond_agg_calc_col'] = None

    # --- Step 3: Define the output location ---
    st.write("##### **Output Location**")
    st.info("By default, the result is added as a new column. You can optionally specify a row range or a single cell to place the result in.")
    
    col6, col7, col8 = st.columns(3)
    with col6:
        analysis_def['output_start_row'] = st.number_input(
            "Start Row (Optional, 1-based)",
            min_value=1,
            step=1,
            value=analysis_def.get('output_start_row'),
            key=f"{key_prefix}_output_start_row"
        )
    with col7:
        analysis_def['output_end_row'] = st.number_input(
            "End Row (Optional, 1-based)",
            min_value=1,
            step=1,
            value=analysis_def.get('output_end_row'),
            key=f"{key_prefix}_output_end_row"
        )
    with col8:
        # If start row is specified, we can target an existing column instead of creating a new one
        if analysis_def.get('output_start_row'):
             analysis_def['output_target_col'] = st.selectbox(
                "Target Column (Optional)",
                options=[None] + main_df_columns,
                index=0,
                key=f"{key_prefix}_output_target_col"
            )


def render_operation_ui(analysis_def, all_dfs, main_df_columns, key_prefix):
    """
    Renders the specific UI parameters for the selected operation type.
    This function is designed to be called INSIDE a st.form.
    It modifies the analysis_def dictionary in place.
    """
    op_type = analysis_def.get('operation_type')

    if op_type == 'VLOOKUP':
        render_vlookup_builder(analysis_def, all_dfs, main_df_columns, key_prefix)
    elif op_type == 'MATH':
        render_math_builder(analysis_def, main_df_columns, key_prefix)
    elif op_type == 'IF':
        render_if_builder(analysis_def, main_df_columns, key_prefix)
    elif op_type == 'CONDITIONAL_AGG':
        render_conditional_agg_builder(analysis_def, main_df_columns, key_prefix)

