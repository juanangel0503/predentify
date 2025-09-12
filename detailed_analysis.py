import pandas as pd
import json

def detailed_analysis():
    """Detailed analysis of the new spreadsheet structure and formulas"""
    
    print("🔍 DETAILED ANALYSIS OF NEW SPREADSHEET")
    print("=" * 80)
    
    # Read the Excel file
    excel_file = 'VDH_Procedure_Durations_rev0.2.xlsx'
    
    # Analyze Metadata2 sheet (main data)
    df = pd.read_excel(excel_file, sheet_name='Metadata2')
    
    print("📊 METADATA2 SHEET ANALYSIS")
    print("-" * 50)
    
    # Extract procedure data
    procedures_data = {}
    
    for index, row in df.iterrows():
        if pd.notna(row['Procedure 1']):
            procedure_name = row['Procedure 1']
            
            # Extract base times
            assistant_time = row['Assistant/Hygienist Time'] if pd.notna(row['Assistant/Hygienist Time']) else 0
            doctor_time = row['Doctor Time'] if pd.notna(row['Doctor Time']) else 0
            total_time = row['Duration Total'] if pd.notna(row['Duration Total']) else 0
            
            # Extract provider compatibility (1 = can do, 0 = cannot do)
            provider_compatibility = {}
            providers = ['Miekella', 'Kayla', 'Radin', 'Marina', 'Monse', 'Jessica', 'Amber', 'Kym', 'Natalia', 'Hygiene']
            
            for provider in providers:
                if provider in row and pd.notna(row[provider]):
                    provider_compatibility[provider] = bool(row[provider])
                else:
                    provider_compatibility[provider] = False
            
            procedures_data[procedure_name] = {
                'assistant_time': float(assistant_time),
                'doctor_time': float(doctor_time),
                'total_time': float(total_time),
                'provider_compatibility': provider_compatibility
            }
    
    print(f"📋 Found {len(procedures_data)} procedures in Metadata2")
    print()
    
    # Show procedure details
    for proc_name, proc_data in list(procedures_data.items())[:10]:
        print(f"🦷 {proc_name}:")
        print(f"   Assistant: {proc_data['assistant_time']} min")
        print(f"   Doctor: {proc_data['doctor_time']} min")
        print(f"   Total: {proc_data['total_time']} min")
        
        # Show which providers can do this procedure
        available_providers = [p for p, can_do in proc_data['provider_compatibility'].items() if can_do]
        print(f"   Providers: {available_providers}")
        print()
    
    # Analyze mitigating factors
    print("🔧 MITIGATING FACTORS ANALYSIS")
    print("-" * 50)
    
    mitigating_factors = {}
    for index, row in df.iterrows():
        if pd.notna(row['Mitigating Factor']):
            factor_name = row['Mitigating Factor'].strip()
            duration_multiplier = row['Duration or Multiplier']
            
            if pd.notna(duration_multiplier):
                # Determine if it's a multiplier (>1) or additive (<=1)
                is_multiplier = duration_multiplier > 1.0
                mitigating_factors[factor_name] = {
                    'value': float(duration_multiplier),
                    'is_multiplier': is_multiplier
                }
    
    print(f"📋 Found {len(mitigating_factors)} mitigating factors:")
    for factor_name, factor_data in mitigating_factors.items():
        factor_type = "Multiplier" if factor_data['is_multiplier'] else "Additive"
        print(f"   • {factor_name}: {factor_data['value']} ({factor_type})")
    
    print()
    
    # Analyze Metadata1 sheet for additional logic
    print("📊 METADATA1 SHEET ANALYSIS")
    print("-" * 50)
    
    df_meta1 = pd.read_excel(excel_file, sheet_name='Metadata1')
    print(f"📏 Metadata1 dimensions: {df_meta1.shape}")
    print(f"📝 Columns: {list(df_meta1.columns)}")
    print()
    
    # Show provider data
    print("👥 PROVIDER DATA:")
    for index, row in df_meta1.iterrows():
        if pd.notna(row['Provider']):
            provider = row['Provider']
            teeth = row['No. Teeth'] if pd.notna(row['No. Teeth']) else 'N/A'
            surfaces = row['No. Surfaces'] if pd.notna(row['No. Surfaces']) else 'N/A'
            quadrants = row['No. Quadrants'] if pd.notna(row['No. Quadrants']) else 'N/A'
            print(f"   • {provider}: Teeth={teeth}, Surfaces={surfaces}, Quadrants={quadrants}")
    
    print()
    
    # Compare with existing data
    print("🔄 COMPARISON WITH EXISTING DATA")
    print("-" * 50)
    
    try:
        with open('data/procedures.json', 'r') as f:
            existing_procedures = json.load(f)
        
        print(f"📊 Existing procedures: {len(existing_procedures)}")
        print(f"📊 New spreadsheet procedures: {len(procedures_data)}")
        
        # Check for new procedures
        existing_names = set(existing_procedures.keys())
        new_names = set(procedures_data.keys())
        
        new_procedures = new_names - existing_names
        removed_procedures = existing_names - new_names
        
        if new_procedures:
            print(f"🆕 New procedures: {list(new_procedures)}")
        if removed_procedures:
            print(f"❌ Removed procedures: {list(removed_procedures)}")
        
        # Check for time changes
        print("\n🕐 TIME CHANGES:")
        for proc_name in existing_names & new_names:
            existing = existing_procedures[proc_name]
            new = procedures_data[proc_name]
            
            if (existing['assistant_time'] != new['assistant_time'] or 
                existing['doctor_time'] != new['doctor_time'] or 
                existing['total_time'] != new['total_time']):
                print(f"   • {proc_name}:")
                print(f"     Existing: A={existing['assistant_time']}, D={existing['doctor_time']}, T={existing['total_time']}")
                print(f"     New:      A={new['assistant_time']}, D={new['doctor_time']}, T={new['total_time']}")
    
    except Exception as e:
        print(f"❌ Error comparing with existing data: {e}")

if __name__ == "__main__":
    detailed_analysis()
