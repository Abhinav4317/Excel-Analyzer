import polars as pl
import streamlit as st

def apply_analysis(main_df, analysis_def, all_dfs):
    """
    Applies a single analysis step to the main DataFrame.
    Acts as a router to the specific analysis function.
    """
    op_type = analysis_def.get('operation_type')

    # A new column is not always created now, but we need a name for the step
    if not analysis_def.get('new_col_name'):
        st.error("Please provide a name for the new column or analysis step.")
        return main_df

    try:
        if op_type == 'VLOOKUP':
            return apply_vlookup(main_df, analysis_def, all_dfs)
        elif op_type == 'MATH':
            return apply_math(main_df, analysis_def)
        elif op_type == 'IF':
            return apply_if_condition(main_df, analysis_def)
        elif op_type == 'CONDITIONAL_AGG':
            return apply_conditional_agg(main_df, analysis_def)
        else:
            st.warning(f"Operation '{op_type}' is not yet implemented.")
            return main_df
    except Exception as e:
        st.error(f"An error occurred during the '{op_type}' operation: {e}")
        return main_df

def apply_vlookup(main_df, analysis_def, all_dfs):
    """Performs a left join, similar to VLOOKUP."""
    lookup_df = all_dfs[analysis_def['lookup_df_name']]
    new_col_name = analysis_def['new_col_name']

    lookup_subset = lookup_df.select([
        analysis_def['right_on'],
        analysis_def['value_col']
    ])

    result_df = main_df.join(
        lookup_subset,
        left_on=analysis_def['left_on'],
        right_on=analysis_def['right_on'],
        how='left'
    )

    return result_df.rename({analysis_def['value_col']: new_col_name})

def apply_math(main_df, analysis_def):
    """Performs a basic arithmetic operation between two columns."""
    new_col_name = analysis_def['new_col_name']
    op = analysis_def['operator']

    col1 = pl.col(analysis_def['first_col']).cast(pl.Float64, strict=False)
    col2 = pl.col(analysis_def['second_col']).cast(pl.Float64, strict=False)

    if op == '+': expression = col1 + col2
    elif op == '-': expression = col1 - col2
    elif op == '*': expression = col1 * col2
    elif op == '/': expression = col1 / col2
    else: raise ValueError(f"Unsupported operator: {op}")

    return main_df.with_columns(expression.alias(new_col_name))

def _attempt_cast(value_str):
    """Helper to cast string input to numeric if possible."""
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return value_str

def apply_if_condition(main_df, analysis_def):
    """Applies a conditional (IF) expression."""
    new_col_name = analysis_def['new_col_name']
    if_col = pl.col(analysis_def['if_col'])
    op = analysis_def['if_operator']
    compare_type = analysis_def.get('if_compare_type', 'Absolute Value')

    # Handle comparison to either a value or another column
    if compare_type == 'Absolute Value':
        compare_val = _attempt_cast(analysis_def['if_value'])
    else: # Compare to another column
        compare_val = pl.col(analysis_def['if_compare_col'])

    true_val = _attempt_cast(analysis_def['value_if_true'])
    false_val = _attempt_cast(analysis_def['value_if_false'])

    if op == '==': condition = (if_col == compare_val)
    elif op == '!=': condition = (if_col != compare_val)
    elif op == '>': condition = (if_col > compare_val)
    elif op == '<': condition = (if_col < compare_val)
    elif op == '>=': condition = (if_col >= compare_val)
    elif op == '<=': condition = (if_col <= compare_val)
    else: raise ValueError(f"Unsupported operator: {op}")

    expression = pl.when(condition).then(pl.lit(true_val)).otherwise(pl.lit(false_val))

    return main_df.with_columns(expression.alias(new_col_name))


def apply_conditional_agg(main_df, analysis_def):
    """
    Performs a conditional aggregation (SUMIF, COUNTIF, etc.) on the main DataFrame.
    The result can be broadcast to a new column or placed in a specific cell/range.
    """
    new_col_name = analysis_def['new_col_name']
    if_col = pl.col(analysis_def['cond_agg_if_col'])
    op = analysis_def['cond_agg_operator']
    compare_type = analysis_def.get('cond_agg_compare_type', 'Absolute Value')
    agg_func = analysis_def['cond_agg_function']
    calc_col_name = analysis_def.get('cond_agg_calc_col')

    # Step 1: Build the filter condition (handles value or column comparison)
    if compare_type == 'Absolute Value':
        compare_val = _attempt_cast(analysis_def['cond_agg_value'])
    else: # Compare to another column
        compare_val = pl.col(analysis_def['cond_agg_compare_col'])
    
    if op == '==': condition = (if_col == compare_val)
    elif op == '!=': condition = (if_col != compare_val)
    elif op == '>': condition = (if_col > compare_val)
    elif op == '<': condition = (if_col < compare_val)
    elif op == '>=': condition = (if_col >= compare_val)
    elif op == '<=': condition = (if_col <= compare_val)
    else: raise ValueError(f"Unsupported operator: {op}")

    # Step 2: Filter the DataFrame
    filtered_df = main_df.filter(condition)

    # Step 3: Perform the aggregation
    result_value = 0
    if filtered_df.height > 0:
        if agg_func == 'Count':
            result_value = filtered_df.height
        elif calc_col_name:
            calc_col = pl.col(calc_col_name)
            if agg_func == 'Sum': result_value = filtered_df.select(calc_col.sum()).item()
            elif agg_func == 'Average': result_value = filtered_df.select(calc_col.mean()).item()
            elif agg_func == 'Min': result_value = filtered_df.select(calc_col.min()).item()
            elif agg_func == 'Max': result_value = filtered_df.select(calc_col.max()).item()
        else:
            st.error(f"For '{agg_func}', you must select a column to calculate on.")
            return main_df

    # Step 4: Handle the output location
    start_row = analysis_def.get('output_start_row')
    end_row = analysis_def.get('output_end_row')
    target_col = analysis_def.get('output_target_col')

    # If no specific location is given, use the default broadcast behavior
    if not start_row:
        return main_df.with_columns(pl.lit(result_value).alias(new_col_name))

    # --- Logic for targeted output ---
    # Adjust for 0-based indexing
    start_idx = start_row - 1
    # If no end row, it's a single cell
    end_idx = (end_row - 1) if end_row else start_idx

    if start_idx >= main_df.height:
        st.error(f"Error: Start row {start_row} is beyond the end of the table ({main_df.height} rows).")
        return main_df

    # Determine the column to place the result in
    output_col_name = target_col if target_col else new_col_name
    
    # Create a boolean mask for the rows to be updated
    row_indices = pl.arange(0, main_df.height)
    mask = (row_indices >= start_idx) & (row_indices <= end_idx)

    # If the target column doesn't exist, create it with nulls
    if output_col_name not in main_df.columns:
        main_df = main_df.with_columns(pl.lit(None).alias(output_col_name))

    # Use pl.when/then/otherwise to update the specific range
    return main_df.with_columns(
        pl.when(mask)
        .then(pl.lit(result_value))
        .otherwise(pl.col(output_col_name))
        .alias(output_col_name)
    )
