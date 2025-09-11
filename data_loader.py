import pandas as pd
import numpy as np
from typing import List, Dict, Any

class ProcedureDataLoader:
    """Handles loading and processing procedure duration data from Excel"""
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load data from Excel file"""
        try:
            self.df = pd.read_excel(self.excel_path, sheet_name='Metadata2')
            print(f"Loaded {len(self.df)} procedures from {self.excel_path}")
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            raise
    
    def get_procedures(self) -> List[str]:
        """Get list of all available procedures"""
        if self.df is None:
            return []
        
        procedures = self.df['Procedure 1'].dropna().unique().tolist()
        return sorted([str(proc) for proc in procedures if str(proc) != 'nan'])
    
    def get_providers(self) -> List[str]:
        """Get list of all available providers"""
        # Based on the Excel analysis, these are the provider columns
        providers = ['Miekella', 'Kayla', 'Radin', 'Marina', 'Monse', 
                    'Jessica', 'Amber', 'Kym', 'Natalia', 'Hygiene']
        return providers
    
    def get_mitigating_factors(self) -> List[Dict[str, Any]]:
        """Get list of all mitigating factors with their multipliers"""
        if self.df is None:
            return []
        
        # Extract mitigating factors
        factors_df = self.df[['Mitigating Factor', 'Duration or Multiplier']].dropna()
        factors = []
        
        for _, row in factors_df.iterrows():
            factor_name = str(row['Mitigating Factor']).strip()
            multiplier = row['Duration or Multiplier']
            
            if factor_name and factor_name != 'nan':
                factors.append({
                    'name': factor_name,
                    'multiplier': float(multiplier) if pd.notna(multiplier) else 1.0
                })
        
        return factors
    
    def get_procedure_base_times(self, procedure: str) -> Dict[str, Any]:
        """Get base times for a specific procedure"""
        if self.df is None:
            return {}
        
        # Find the procedure row
        procedure_row = self.df[self.df['Procedure 1'] == procedure]
        
        if procedure_row.empty:
            return {}
        
        row = procedure_row.iloc[0]
        
        # Get base times
        assistant_time = row.get('Assistant/Hygienist Time', 0)
        doctor_time = row.get('Doctor Time', 0)
        total_time = row.get('Duration Total', 0)
        
        # Handle NaN values
        assistant_time = float(assistant_time) if pd.notna(assistant_time) else 0
        doctor_time = float(doctor_time) if pd.notna(doctor_time) else 0
        total_time = float(total_time) if pd.notna(total_time) else assistant_time + doctor_time
        
        return {
            'assistant_time': assistant_time,
            'doctor_time': doctor_time,
            'total_time': total_time if total_time > 0 else assistant_time + doctor_time
        }
    
    def check_provider_performs_procedure(self, procedure: str, provider: str) -> bool:
        """Check if a provider performs a specific procedure"""
        if self.df is None:
            return False
        
        # Find the procedure row
        procedure_row = self.df[self.df['Procedure 1'] == procedure]
        
        if procedure_row.empty or provider not in procedure_row.columns:
            return False
        
        # Check if provider performs this procedure (1 = yes, 0 = no)
        performs = procedure_row.iloc[0].get(provider, 0)
        return bool(performs) if pd.notna(performs) else False
    
    def calculate_appointment_time(self, procedure: str, provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """Calculate total appointment time with all factors"""
        if mitigating_factors is None:
            mitigating_factors = []
        
        # Get base times
        base_times = self.get_procedure_base_times(procedure)
        
        if not base_times:
            return {
                'error': f'Procedure "{procedure}" not found',
                'success': False
            }
        
        # Check if provider can perform this procedure
        can_perform = self.check_provider_performs_procedure(procedure, provider)
        
        if not can_perform:
            return {
                'error': f'Provider "{provider}" does not perform "{procedure}"',
                'success': False,
                'warning': True
            }
        
        # Start with base times
        assistant_time = base_times['assistant_time']
        doctor_time = base_times['doctor_time']
        total_base_time = base_times['total_time']
        
        # Apply mitigating factors
        total_multiplier = 1.0
        additional_time = 0.0
        applied_factors = []
        
        all_factors = self.get_mitigating_factors()
        factor_lookup = {f['name']: f['multiplier'] for f in all_factors}
        
        for factor_name in mitigating_factors:
            if factor_name in factor_lookup:
                multiplier = factor_lookup[factor_name]
                applied_factors.append({
                    'name': factor_name,
                    'multiplier': multiplier
                })
                
                # If multiplier > 2, treat as additional minutes
                # If multiplier <= 2, treat as a multiplier
                if multiplier > 2:
                    additional_time += multiplier
                else:
                    total_multiplier *= multiplier
        
        # Calculate final times
        final_assistant_time = assistant_time * total_multiplier + additional_time
        final_doctor_time = doctor_time * total_multiplier
        final_total_time = total_base_time * total_multiplier + additional_time
        
        return {
            'success': True,
            'procedure': procedure,
            'provider': provider,
            'base_times': {
                'assistant_time': assistant_time,
                'doctor_time': doctor_time,
                'total_time': total_base_time
            },
            'final_times': {
                'assistant_time': round(final_assistant_time, 1),
                'doctor_time': round(final_doctor_time, 1),
                'total_time': round(final_total_time, 1)
            },
            'applied_factors': applied_factors,
            'total_multiplier': round(total_multiplier, 2),
            'additional_time': round(additional_time, 1)
        } 