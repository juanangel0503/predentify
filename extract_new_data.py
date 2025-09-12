import pandas as pd
import json
import os

def extract_new_data():
    """Extract data from the new spreadsheet and create updated JSON files"""
    
    print("🔄 EXTRACTING DATA FROM NEW SPREADSHEET")
    print("=" * 60)
    
    # Read the Excel file
    excel_file = 'VDH_Procedure_Durations_rev0.2.xlsx'
    
    # Extract procedures data from Metadata2
    df = pd.read_excel(excel_file, sheet_name='Metadata2')
    
    procedures_data = {}
    provider_compatibility = {}
    
    for index, row in df.iterrows():
        if pd.notna(row['Procedure 1']):
            procedure_name = row['Procedure 1']
            
            # Extract base times
            assistant_time = row['Assistant/Hygienist Time'] if pd.notna(row['Assistant/Hygienist Time']) else 0
            doctor_time = row['Doctor Time'] if pd.notna(row['Doctor Time']) else 0
            total_time = row['Duration Total'] if pd.notna(row['Duration Total']) else 0
            
            # Store procedure data
            procedures_data[procedure_name] = {
                'assistant_time': float(assistant_time),
                'doctor_time': float(doctor_time),
                'total_time': float(total_time),
                'section': 'procedure1'  # Default section
            }
            
            # Extract provider compatibility
            providers = ['Miekella', 'Kayla', 'Radin', 'Marina', 'Monse', 'Jessica', 'Amber', 'Kym', 'Natalia', 'Hygiene']
            compatible_providers = []
            
            for provider in providers:
                if provider in row and pd.notna(row[provider]) and row[provider] == 1:
                    compatible_providers.append(provider)
            
            provider_compatibility[procedure_name] = compatible_providers
    
    # Extract mitigating factors
    mitigating_factors = []
    for index, row in df.iterrows():
        if pd.notna(row['Mitigating Factor']):
            factor_name = row['Mitigating Factor'].strip()
            duration_multiplier = row['Duration or Multiplier']
            
            if pd.notna(duration_multiplier):
                is_multiplier = duration_multiplier > 1.0
                mitigating_factors.append({
                    'name': factor_name,
                    'value': float(duration_multiplier),
                    'is_multiplier': is_multiplier
                })
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Save procedures data
    with open('data/procedures.json', 'w') as f:
        json.dump(procedures_data, f, indent=2)
    
    # Save provider compatibility
    with open('data/provider_compatibility.json', 'w') as f:
        json.dump(provider_compatibility, f, indent=2)
    
    # Save mitigating factors
    with open('data/mitigating_factors.json', 'w') as f:
        json.dump(mitigating_factors, f, indent=2)
    
    # Create summary
    summary = {
        'total_procedures': len(procedures_data),
        'total_providers': len(set().union(*provider_compatibility.values())),
        'total_mitigating_factors': len(mitigating_factors),
        'extraction_date': pd.Timestamp.now().isoformat(),
        'source_file': excel_file
    }
    
    with open('data/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Extracted {len(procedures_data)} procedures")
    print(f"✅ Extracted {len(set().union(*provider_compatibility.values()))} providers")
    print(f"✅ Extracted {len(mitigating_factors)} mitigating factors")
    print()
    
    # Show sample data
    print("📋 SAMPLE PROCEDURES:")
    for i, (proc_name, proc_data) in enumerate(list(procedures_data.items())[:5]):
        print(f"   {i+1}. {proc_name}: A={proc_data['assistant_time']}, D={proc_data['doctor_time']}, T={proc_data['total_time']}")
    
    print()
    print("📋 SAMPLE MITIGATING FACTORS:")
    for i, factor in enumerate(mitigating_factors[:5]):
        factor_type = "Multiplier" if factor['is_multiplier'] else "Additive"
        print(f"   {i+1}. {factor['name']}: {factor['value']} ({factor_type})")
    
    print()
    print("📋 PROVIDER COMPATIBILITY SAMPLE:")
    for i, (proc_name, providers) in enumerate(list(provider_compatibility.items())[:5]):
        print(f"   {i+1}. {proc_name}: {providers}")

if __name__ == "__main__":
    extract_new_data()
