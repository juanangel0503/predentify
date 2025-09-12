import pandas as pd
import numpy as np
from typing import List, Dict, Any

class ProcedureDataLoader:
    """Handles loading and processing procedure duration data from Excel"""
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        self.duration_df = None
        self.load_data()
    
    def load_data(self):
        """Load data from Excel file"""
        try:
            self.df = pd.read_excel(self.excel_path, sheet_name='Metadata2')
            self.duration_df = pd.read_excel(self.excel_path, sheet_name='Duration')
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
    
    def calculate_teeth_surfaces_time(self, procedure: str, num_teeth: int = 1, 
                                    num_surfaces: int = 1, num_quadrants: int = 1) -> Dict[str, float]:
        """Calculate additional time based on number of teeth, surfaces, and quadrants"""
        # Base multipliers for different procedure types
        time_adjustments = {
            'assistant_time': 0,
            'doctor_time': 0,
            'total_time': 0
        }
        
        # Procedure-specific time calculations
        if 'filling' in procedure.lower():
            # Fillings: +5 min per additional tooth, +3 min per additional surface
            time_adjustments['assistant_time'] += (num_teeth - 1) * 3
            time_adjustments['doctor_time'] += (num_teeth - 1) * 5
            time_adjustments['total_time'] += (num_teeth - 1) * 8
            
            if num_surfaces > 1:
                time_adjustments['assistant_time'] += (num_surfaces - 1) * 2
                time_adjustments['doctor_time'] += (num_surfaces - 1) * 3
                time_adjustments['total_time'] += (num_surfaces - 1) * 5
                
        elif 'crown' in procedure.lower():
            # Crowns: +10 min per additional tooth
            time_adjustments['assistant_time'] += (num_teeth - 1) * 5
            time_adjustments['doctor_time'] += (num_teeth - 1) * 10
            time_adjustments['total_time'] += (num_teeth - 1) * 15
            
        elif 'root canal' in procedure.lower():
            # Root canals: +15 min per additional canal
            time_adjustments['assistant_time'] += (num_surfaces - 1) * 5  # surfaces = canals in this context
            time_adjustments['doctor_time'] += (num_surfaces - 1) * 15
            time_adjustments['total_time'] += (num_surfaces - 1) * 20
            
        elif 'extraction' in procedure.lower():
            # Extractions: +8 min per additional tooth
            time_adjustments['assistant_time'] += (num_teeth - 1) * 3
            time_adjustments['doctor_time'] += (num_teeth - 1) * 8
            time_adjustments['total_time'] += (num_teeth - 1) * 11
            
        elif 'implant' in procedure.lower():
            # Implants: +20 min per additional implant
            time_adjustments['assistant_time'] += (num_teeth - 1) * 10
            time_adjustments['doctor_time'] += (num_teeth - 1) * 20
            time_adjustments['total_time'] += (num_teeth - 1) * 30
            
        # Quadrant-based adjustments (for procedures that span multiple quadrants)
        if num_quadrants > 1:
            quadrant_multiplier = 1 + (num_quadrants - 1) * 0.2  # 20% increase per additional quadrant
            time_adjustments['assistant_time'] *= quadrant_multiplier
            time_adjustments['doctor_time'] *= quadrant_multiplier
            time_adjustments['total_time'] *= quadrant_multiplier
        
        return time_adjustments
    
    def calculate_appointment_time(self, procedure: str, provider: str, 
                                 mitigating_factors: List[str] = None,
                                 num_teeth: int = 1, num_surfaces: int = 1, 
                                 num_quadrants: int = 1) -> Dict[str, Any]:
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
        
        # Calculate teeth/surfaces/canals adjustments
        teeth_adjustments = self.calculate_teeth_surfaces_time(procedure, num_teeth, num_surfaces, num_quadrants)
        
        # Apply teeth/surfaces adjustments
        assistant_time += teeth_adjustments['assistant_time']
        doctor_time += teeth_adjustments['doctor_time']
        total_base_time += teeth_adjustments['total_time']
        
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
        
        # Calculate final times - FIXED LOGIC
        # Apply multipliers first, then add additional time
        final_assistant_time = (assistant_time * total_multiplier) + additional_time
        final_doctor_time = doctor_time * total_multiplier
        
        # Total time should be the sum of assistant + doctor time
        final_total_time = final_assistant_time + final_doctor_time
        
        return {
            'success': True,
            'procedure': procedure,
            'provider': provider,
            'num_teeth': num_teeth,
            'num_surfaces': num_surfaces,
            'num_quadrants': num_quadrants,
            'base_times': {
                'assistant_time': int(round(base_times['assistant_time'])),
                'doctor_time': int(round(base_times['doctor_time'])),
                'total_time': int(round(base_times['total_time']))
            },
            'teeth_adjustments': {
                'assistant_time': int(round(teeth_adjustments['assistant_time'])),
                'doctor_time': int(round(teeth_adjustments['doctor_time'])),
                'total_time': int(round(teeth_adjustments['total_time']))
            },
            'final_times': {
                'assistant_time': int(round(final_assistant_time)),
                'doctor_time': int(round(final_doctor_time)),
                'total_time': int(round(final_total_time))
            },
            'applied_factors': applied_factors,
            'total_multiplier': round(total_multiplier, 2),
            'additional_time': int(round(additional_time))
        }
