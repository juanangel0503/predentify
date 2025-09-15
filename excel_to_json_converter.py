#!/usr/bin/env python3
"""
Excel to JSON Converter for PreDentify
Converts VDH_Procedure_Durations_rev0.2.xlsx to JSON format
"""

import pandas as pd
import json
import os
from typing import Dict, List, Any

def convert_excel_to_json():
    """Convert Excel file to JSON format"""
    
    # Read the Excel file
    excel_file = "VDH_Procedure_Durations_rev0.2.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found!")
        return
    
    print(f"Reading {excel_file}...")
    
    # Read all sheets from the Excel file
    excel_data = pd.read_excel(excel_file, sheet_name=None)
    
    print(f"Found {len(excel_data)} sheets: {list(excel_data.keys())}")
    
    # Process each sheet
    for sheet_name, df in excel_data.items():
        print(f"\nProcessing sheet: {sheet_name}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"First few rows:")
        print(df.head())
        
        # Convert to JSON
        json_data = df.to_dict('records')
        
        # Save to JSON file
        json_filename = f"data/{sheet_name.lower().replace(' ', '_')}.json"
        os.makedirs("data", exist_ok=True)
        
        with open(json_filename, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"Saved {len(json_data)} records to {json_filename}")

def analyze_excel_structure():
    """Analyze the Excel file structure in detail"""
    
    excel_file = "VDH_Procedure_Durations_rev0.2.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found!")
        return
    
    print(f"Analyzing {excel_file} structure...")
    
    # Read all sheets
    excel_data = pd.read_excel(excel_file, sheet_name=None)
    
    for sheet_name, df in excel_data.items():
        print(f"\n{'='*50}")
        print(f"SHEET: {sheet_name}")
        print(f"{'='*50}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"\nData types:")
        print(df.dtypes)
        print(f"\nFirst 10 rows:")
        print(df.head(10))
        print(f"\nLast 5 rows:")
        print(df.tail(5))
        
        # Check for any non-null values
        print(f"\nNon-null counts:")
        print(df.count())
        
        # Check for unique values in key columns
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 20:  # Only show if not too many
                    print(f"\nUnique values in '{col}': {list(unique_vals)}")

if __name__ == "__main__":
    print("Excel to JSON Converter for PreDentify")
    print("="*50)
    
    # First analyze the structure
    analyze_excel_structure()
    
    print("\n" + "="*50)
    print("Converting to JSON...")
    
    # Then convert to JSON
    convert_excel_to_json()
    
    print("\nConversion complete!")
