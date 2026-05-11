import pandas as pd
import numpy as np


# ==========================================
# 1. DICTIONARY MAPPINGS (For Charts & Labels)
# ==========================================

imker_methode_dict = {
    1: 'Controlled',
    2: 'Natural',
    3: 'Regulier',
    4: 'Unknown and Mixed'
}

winter_food_dict = {
    1: 'Sugar',
    2: 'Mixed',
    3: 'Honey'
}

varroa_treatment_dict = {
    1: '3 gangenmenu full treatment',
    2: 'alternatieve behandeling',
    3: 'alleen in the winter',
    4: 'alleen in the zomer',
    5: 'Nee'
}

aziatische_hoornaar_dict = {
    1: "Nee", 2: "Weinig", 3: "Matig", 4:"Veel", 5:"Weet het niet"
    } 

deformed_wings_dict = {
    1: "Nee", 2: "Weinig", 3: "Matig", 4:"Veel", 5:"Weet het niet"
    }

varroa_observation_dict = {
    1: "Nee", 2: "Weinig", 3: "Matig", 4:"Veel", 5:"Weet het niet"
    }


# ==========================================
# 2. DATA LOADING & PREPARATION
# ==========================================

def load_data(filepath):
    """
    Loads the CSV data, skipping row 2 (which contains your text definitions).
    This ensures all your numerical columns remain as clean numbers for regression.
    """
    # skiprows=[1] skips the second row (Python starts counting at 0)
    df = pd.read_csv(filepath, skiprows=[1])
    return df

def get_labeled_data(df, column_name, mapping_dict):
    """
    Creates a copy of the dataframe where a specific numerical column 
    is replaced with its readable text labels (useful for charting without altering base data).
    """
    df_chart = df.copy()
    # Create a new column with '_label' added to the name
    df_chart[f"{column_name}_label"] = df_chart[column_name].map(mapping_dict)
    return df_chart


# ==========================================
# 3. MORTALITY CALCULATIONS
# ==========================================

def winter_mortality_user_input(df):
    """
    Calculates the baseline winter mortality rate for the entire dataset.
    """
    total_in = df['2025_winter_in'].sum()
    total_uit = df['2026_winter_uit'].sum()
    
    if total_in == 0:
        return 0
        
    mortality_rate = ((total_in - total_uit) / total_in) * 100
    
    return {
        'Total Hives In': total_in,
        'Total Hives Out': total_uit,
        'Total Deaths': total_in - total_uit,
        'Mortality Rate (%)': round(mortality_rate, 2)
    }

def winter_mortality_user_input_by_group(df, group_col, mapping_dict=None):
    """
    Calculates winter mortality grouped by any specific variable (e.g., 'province' or 'winter_food').
    Optionally applies a dictionary to label the groups clearly in the output table.
    """
    # Group the data and sum the 'in' and 'uit' hives for each category
    grouped = df.groupby(group_col)[['2025_winter_in', '2026_winter_uit']].sum().reset_index()
    
    # Calculate total deaths per group
    grouped['deaths'] = grouped['2025_winter_in'] - grouped['2026_winter_uit']
    
    # Calculate mortality rate (avoiding division by zero if a group has 0 hives)
    grouped['mortality_rate_%'] = np.where(
        grouped['2025_winter_in'] > 0,
        (grouped['deaths'] / grouped['2025_winter_in']) * 100,
        0
    )
    
    # Round the percentages to 2 decimal places
    grouped['mortality_rate_%'] = grouped['mortality_rate_%'].round(2)
    
    # Apply text labels to the grouping column if a dictionary is provided
    if mapping_dict:
        grouped[group_col] = grouped[group_col].map(mapping_dict)
        
    return grouped