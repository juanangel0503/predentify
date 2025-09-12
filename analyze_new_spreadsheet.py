import pandas as pd
import json
import os

def analyze_spreadsheet():
    """Analyze the new VDH_Procedure_Durations_rev0.2.xlsx spreadsheet"""
    
    print("🔍 ANALYZING NEW SPREADSHEET: VDH_Procedure_Durations_rev0.2.xlsx")
    print("=" * 70)
    
    # Read the Excel file
    excel_file = 'VDH_Procedure_Durations_rev0.2.xlsx'
    
    try:
        # Get all sheet names
        xl_file = pd.ExcelFile(excel_file)
        sheet_names = xl_file.sheet_names
        print(f"📊 Sheet Names: {sheet_names}")
        print()
        
        # Analyze each sheet
        for sheet_name in sheet_names:
            print(f"📋 ANALYZING SHEET: {sheet_name}")
            print("-" * 50)
            
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            print(f"📏 Dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
            print(f"📝 Columns: {list(df.columns)}")
            print()
            
            # Show first few rows
            print("📄 First 10 rows:")
            print(df.head(10).to_string())
            print()
            
            # Check for formulas or special values
            print("🔍 Data Analysis:")
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check for formula-like strings
                    formula_count = df[col].astype(str).str.contains('=', na=False).sum()
                    if formula_count > 0:
                        print(f"  • {col}: {formula_count} formula-like entries")
                    
                    # Check for unique values
                    unique_count = df[col].nunique()
                    print(f"  • {col}: {unique_count} unique values")
                    
                    # Show sample values
                    sample_values = df[col].dropna().head(5).tolist()
                    print(f"    Sample values: {sample_values}")
                else:
                    # Numeric columns
                    print(f"  • {col}: numeric, range {df[col].min():.2f} to {df[col].max():.2f}")
            
            print()
            print("=" * 70)
            print()
    
    except Exception as e:
        print(f"❌ Error analyzing spreadsheet: {e}")
        return
    
    # Compare with existing data
    print("🔄 COMPARING WITH EXISTING DATA")
    print("=" * 70)
    
    try:
        # Load existing procedures data
        with open('data/procedures.json', 'r') as f:
            existing_procedures = json.load(f)
        
        print(f"📊 Existing procedures: {len(existing_procedures)}")
        print(f"📊 New spreadsheet procedures: {len(df) if 'df' in locals() else 'Unknown'}")
        
        # Show existing procedure names
        existing_names = list(existing_procedures.keys())
        print(f"📝 Existing procedure names: {existing_names[:10]}...")
        
    except Exception as e:
        print(f"❌ Error comparing with existing data: {e}")

if __name__ == "__main__":
    analyze_spreadsheet()
