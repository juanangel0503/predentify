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
        
        # Get base times - FIXED: Use Duration Total as the primary time
        assistant_time = row.get('Assistant/Hygienist Time', 0)
        doctor_time = row.get('Doctor Time', 0)
        total_time = row.get('Duration Total', 0)
        
        # Handle NaN values
        assistant_time = float(assistant_time) if pd.notna(assistant_time) else 0
        doctor_time = float(doctor_time) if pd.notna(doctor_time) else 0
        total_time = float(total_time) if pd.notna(total_time) else 0
        
        # If doctor time is NaN, estimate it as total - assistant
        if pd.isna(row.get('Doctor Time')) and total_time > 0:
            doctor_time = max(0, total_time - assistant_time)
        
        return {
            'assistant_time': assistant_time,
            'doctor_time': doctor_time,
            'total_time': total_time
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
        # More realistic time adjustments based on dental practice
        time_adjustments = {
            'assistant_time': 0,
            'doctor_time': 0,
            'total_time': 0
        }
        
        # Procedure-specific time calculations - IMPROVED ACCURACY
        if 'filling' in procedure.lower():
            # Fillings: +15 min per additional tooth, +10 min per additional surface
            time_adjustments['assistant_time'] += (num_teeth - 1) * 5
            time_adjustments['doctor_time'] += (num_teeth - 1) * 15
            time_adjustments['total_time'] += (num_teeth - 1) * 20
            
            if num_surfaces > 1:
                time_adjustments['assistant_time'] += (num_surfaces - 1) * 3
                time_adjustments['doctor_time'] += (num_surfaces - 1) * 10
                time_adjustments['total_time'] += (num_surfaces - 1) * 13
                
        elif 'crown' in procedure.lower():
            # Crowns: +25 min per additional tooth
            time_adjustments['assistant_time'] += (num_teeth - 1) * 8
            time_adjustments['doctor_time'] += (num_teeth - 1) * 25
            time_adjustments['total_time'] += (num_teeth - 1) * 33
            
        elif 'root canal' in procedure.lower():
            # Root canals: +30 min per additional canal
            time_adjustments['assistant_time'] += (num_surfaces - 1) * 8
            time_adjustments['doctor_time'] += (num_surfaces - 1) * 30
            time_adjustments['total_time'] += (num_surfaces - 1) * 38
            
        elif 'extraction' in procedure.lower():
            # Extractions: +20 min per additional tooth
            time_adjustments['assistant_time'] += (num_teeth - 1) * 5
            time_adjustments['doctor_time'] += (num_teeth - 1) * 20
            time_adjustments['total_time'] += (num_teeth - 1) * 25
            
        elif 'implant' in procedure.lower():
            # Implants: +45 min per additional implant
            time_adjustments['assistant_time'] += (num_teeth - 1) * 15
            time_adjustments['doctor_time'] += (num_teeth - 1) * 45
            time_adjustments['total_time'] += (num_teeth - 1) * 60
            
        # Quadrant-based adjustments (for procedures that span multiple quadrants)
        if num_quadrants > 1:
            quadrant_multiplier = 1 + (num_quadrants - 1) * 0.3  # 30% increase per additional quadrant
            time_adjustments['assistant_time'] *= quadrant_multiplier
            time_adjustments['doctor_time'] *= quadrant_multiplier
            time_adjustments['total_time'] *= quadrant_multiplier
        
        return time_adjustments
    
    def round_to_nearest_10(self, minutes: float) -> int:
        """Round time to nearest 10 minutes (30, 40, 50, etc.)"""
        return int(round(minutes / 10) * 10)
    
    def calculate_appointment_time(self, procedures: List[Dict], provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """Calculate total appointment time for multiple procedures"""
        if mitigating_factors is None:
            mitigating_factors = []
        
        total_assistant_time = 0
        total_doctor_time = 0
        total_base_time = 0
        procedure_details = []
        
        # Calculate time for each procedure
        for proc_data in procedures:
            procedure = proc_data['procedure']
            num_teeth = proc_data.get('num_teeth', 1)
            num_surfaces = proc_data.get('num_surfaces', 1)
            num_quadrants = proc_data.get('num_quadrants', 1)
            
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
            
            # Calculate teeth/surfaces/canals adjustments
            teeth_adjustments = self.calculate_teeth_surfaces_time(procedure, num_teeth, num_surfaces, num_quadrants)
            
            # Calculate procedure time
            proc_assistant_time = base_times['assistant_time'] + teeth_adjustments['assistant_time']
            proc_doctor_time = base_times['doctor_time'] + teeth_adjustments['doctor_time']
            proc_total_time = base_times['total_time'] + teeth_adjustments['total_time']
            
            # Add to totals
            total_assistant_time += proc_assistant_time
            total_doctor_time += proc_doctor_time
            total_base_time += proc_total_time
            
            procedure_details.append({
                'procedure': procedure,
                'num_teeth': num_teeth,
                'num_surfaces': num_surfaces,
                'num_quadrants': num_quadrants,
                'base_times': base_times,
                'teeth_adjustments': teeth_adjustments,
                'procedure_times': {
                    'assistant_time': proc_assistant_time,
                    'doctor_time': proc_doctor_time,
                    'total_time': proc_total_time
                }
            })
        
        # Apply mitigating factors to total time only
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
        final_assistant_time = total_assistant_time * total_multiplier
        final_doctor_time = total_doctor_time * total_multiplier
        final_total_time = (total_base_time * total_multiplier) + additional_time
        
        # Round to nearest 10 minutes
        final_assistant_time = self.round_to_nearest_10(final_assistant_time)
        final_doctor_time = self.round_to_nearest_10(final_doctor_time)
        final_total_time = self.round_to_nearest_10(final_total_time)
        
        return {
            'success': True,
            'procedures': procedure_details,
            'provider': provider,
            'base_times': {
                'assistant_time': self.round_to_nearest_10(total_assistant_time),
                'doctor_time': self.round_to_nearest_10(total_doctor_time),
                'total_time': self.round_to_nearest_10(total_base_time)
            },
            'final_times': {
                'assistant_time': final_assistant_time,
                'doctor_time': final_doctor_time,
                'total_time': final_total_time
            },
            'applied_factors': applied_factors,
            'total_multiplier': round(total_multiplier, 2),
            'additional_time': int(round(additional_time))
        }
    
    # Backward compatibility method for single procedure
    def calculate_single_appointment_time(self, procedure: str, provider: str, 
                                        mitigating_factors: List[str] = None,
                                        num_teeth: int = 1, num_surfaces: int = 1, 
                                        num_quadrants: int = 1) -> Dict[str, Any]:
        """Calculate appointment time for a single procedure (backward compatibility)"""
        procedures = [{
            'procedure': procedure,
            'num_teeth': num_teeth,
            'num_surfaces': num_surfaces,
            'num_quadrants': num_quadrants
        }]
        
        result = self.calculate_appointment_time(procedures, provider, mitigating_factors)
        
        # Add single procedure fields for backward compatibility
        if result['success'] and len(result['procedures']) > 0:
            proc = result['procedures'][0]
            result['procedure'] = proc['procedure']
            result['num_teeth'] = proc['num_teeth']
            result['num_surfaces'] = proc['num_surfaces']
            result['num_quadrants'] = proc['num_quadrants']
            result['teeth_adjustments'] = proc['teeth_adjustments']
        
        return result
