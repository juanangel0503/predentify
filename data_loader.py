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
    
    def _apply_procedure_name_changes(self, procedure: str) -> str:
        """Apply procedure name changes as requested"""
        name_changes = {
            'Crown': 'Crown preparation',
            'Implant': 'Implant surgery'
        }
        return name_changes.get(procedure, procedure)
    
    def get_procedures(self, provider: str = None) -> List[str]:
        """Get list of all available procedures, optionally filtered by provider"""
        if self.df is None:
            return []
        
        procedures = self.df['Procedure 1'].dropna().unique().tolist()
        procedure_list = sorted([str(proc) for proc in procedures if str(proc) != 'nan'])
        
        # Apply procedure name changes
        procedure_list = [self._apply_procedure_name_changes(proc) for proc in procedure_list]
        
        # Filter by provider if specified
        if provider:
            procedure_list = [proc for proc in procedure_list if self.check_provider_performs_procedure(proc, provider)]
        
        return procedure_list
    
    def get_providers(self, procedure: str = None) -> List[str]:
        """Get list of all available providers, optionally filtered by procedure"""
        # Based on the Excel analysis, these are the provider columns
        providers = ['Miekella', 'Kayla', 'Radin', 'Marina', 'Monse', 
                    'Jessica', 'Amber', 'Kym', 'Natalia', 'Hygiene']
        
        # Filter by procedure if specified
        if procedure:
            # Convert back to original name for lookup
            original_procedure = self._get_original_procedure_name(procedure)
            providers = [prov for prov in providers if self.check_provider_performs_procedure(original_procedure, prov)]
        
        return providers
    
    def _get_original_procedure_name(self, display_name: str) -> str:
        """Convert display name back to original name for Excel lookup"""
        reverse_changes = {
            'Crown preparation': 'Crown',
            'Implant surgery': 'Implant'
        }
        return reverse_changes.get(display_name, display_name)
    
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
            
            # Determine if it's a multiplier or additional time
            is_multiplier = isinstance(multiplier, (int, float)) and multiplier > 0 and multiplier != 1
            
            factors.append({
                'name': factor_name,
                'multiplier': multiplier if is_multiplier else 1,
                'additional_time': 0 if is_multiplier else multiplier,
                'is_multiplier': is_multiplier
            })
        
        return factors
    
    def get_procedure_base_times(self, procedure: str) -> Dict[str, float]:
        """Get base times for a procedure from the first available provider"""
        if self.df is None:
            return {'assistant_time': 0, 'doctor_time': 0, 'total_time': 0}
        
        # Convert display name back to original for lookup
        original_procedure = self._get_original_procedure_name(procedure)
        
        # Find the procedure row
        procedure_row = self.df[self.df['Procedure 1'] == original_procedure]
        
        if procedure_row.empty:
            return {'assistant_time': 0, 'doctor_time': 0, 'total_time': 0}
        
        row = procedure_row.iloc[0]
        
        # Get times from Duration Total column (this is the correct total time)
        total_time = row.get('Duration Total', 0)
        assistant_time = row.get('Assistant Time', 0)
        doctor_time = row.get('Doctor Time', 0)
        
        # Convert to float and handle NaN values
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
        
        # Convert display name back to original for lookup
        original_procedure = self._get_original_procedure_name(procedure)
        
        # Find the procedure row
        procedure_row = self.df[self.df['Procedure 1'] == original_procedure]
        
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
        
        # Convert display name back to original for lookup
        original_procedure = self._get_original_procedure_name(procedure)
        
        # Procedure-specific time calculations - IMPROVED ACCURACY
        if 'filling' in original_procedure.lower():
            # Fillings: +15 min per additional tooth, +10 min per additional surface
            time_adjustments['assistant_time'] += (num_teeth - 1) * 3
            time_adjustments['doctor_time'] += (num_teeth - 1) * 12
            time_adjustments['assistant_time'] += (num_surfaces - 1) * 2
            time_adjustments['doctor_time'] += (num_surfaces - 1) * 8
            time_adjustments['total_time'] += (num_teeth - 1) * 15 + (num_surfaces - 1) * 10
            
        elif 'crown' in original_procedure.lower():
            # Crowns: +20 min per additional tooth
            time_adjustments['assistant_time'] += (num_teeth - 1) * 4
            time_adjustments['doctor_time'] += (num_teeth - 1) * 16
            time_adjustments['total_time'] += (num_teeth - 1) * 20
            
        elif 'root canal' in original_procedure.lower():
            # Root canals: +15 min per additional tooth, +20 min per additional canal
            time_adjustments['assistant_time'] += (num_teeth - 1) * 3
            time_adjustments['doctor_time'] += (num_teeth - 1) * 12
            time_adjustments['assistant_time'] += (num_surfaces - 1) * 4  # surfaces = canals for root canals
            time_adjustments['doctor_time'] += (num_surfaces - 1) * 16
            time_adjustments['total_time'] += (num_teeth - 1) * 15 + (num_surfaces - 1) * 20
            
        elif 'extraction' in original_procedure.lower():
            # Extractions: +15 min per additional tooth (3 assistant + 12 doctor)
            time_adjustments['assistant_time'] += (num_teeth - 1) * 3
            time_adjustments['doctor_time'] += (num_teeth - 1) * 12
            time_adjustments['total_time'] += (num_teeth - 1) * 15
            
        elif 'implant' in original_procedure.lower():
            # Implants: +30 min per additional tooth
            time_adjustments['assistant_time'] += (num_teeth - 1) * 6
            time_adjustments['doctor_time'] += (num_teeth - 1) * 24
            time_adjustments['total_time'] += (num_teeth - 1) * 30
        
        # Quadrant adjustment: 30% increase per additional quadrant
        if num_quadrants > 1:
            quadrant_multiplier = 1 + (num_quadrants - 1) * 0.3
            time_adjustments['assistant_time'] *= quadrant_multiplier
            time_adjustments['doctor_time'] *= quadrant_multiplier
            time_adjustments['total_time'] *= quadrant_multiplier
        
        return time_adjustments
    
    def round_to_nearest_10(self, minutes: float) -> int:
        """Round time to the nearest multiple of 10 minutes"""
        return int(round(minutes / 10) * 10)
    
    def calculate_appointment_time(self, procedures: List[Dict], provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """Calculate total appointment time for multiple procedures"""
        if not procedures:
            return {'success': False, 'error': 'No procedures specified'}
        
        if not provider:
            return {'success': False, 'error': 'No provider specified'}
        
        total_assistant_time = 0
        total_doctor_time = 0
        total_base_time = 0
        
        procedure_details = []
        
        for i, proc_data in enumerate(procedures):
            procedure = proc_data.get('procedure', '')
            num_teeth = int(proc_data.get('num_teeth', 1))
            num_surfaces = int(proc_data.get('num_surfaces', 1))
            num_quadrants = int(proc_data.get('num_quadrants', 1))
            
            if not procedure:
                continue
            
            # Get base times
            base_times = self.get_procedure_base_times(procedure)
            if base_times['total_time'] == 0:
                continue
            
            # Calculate teeth/surfaces adjustments
            teeth_adjustments = self.calculate_teeth_surfaces_time(
                procedure, num_teeth, num_surfaces, num_quadrants
            )
            
            # Calculate individual procedure time
            proc_assistant_time = base_times['assistant_time'] + teeth_adjustments['assistant_time']
            proc_doctor_time = base_times['doctor_time'] + teeth_adjustments['doctor_time']
            proc_total_time = proc_assistant_time + proc_doctor_time
            
            # Apply 30% reduction for 2nd+ procedures
            if i > 0:  # Second procedure and beyond
                reduction_factor = 0.7  # 30% reduction
                proc_assistant_time *= reduction_factor
                proc_doctor_time *= reduction_factor
                proc_total_time *= reduction_factor
            
            # Round to nearest 10 minutes
            proc_assistant_time = self.round_to_nearest_10(proc_assistant_time)
            proc_doctor_time = self.round_to_nearest_10(proc_doctor_time)
            proc_total_time = self.round_to_nearest_10(proc_total_time)
            
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
                'individual_times': {
                    'assistant_time': proc_assistant_time,
                    'doctor_time': proc_doctor_time,
                    'total_time': proc_total_time
                },
                'is_reduced': i > 0
            })
        
        # Apply mitigating factors to total time
        total_multiplier = 1.0
        additional_time = 0
        
        if mitigating_factors:
            for factor_name in mitigating_factors:
                factors = self.get_mitigating_factors()
                for factor in factors:
                    if factor['name'] == factor_name:
                        if factor['is_multiplier']:
                            total_multiplier *= factor['multiplier']
                        else:
                            additional_time += factor['additional_time']
        
        # Calculate final times
        final_assistant_time = self.round_to_nearest_10(total_assistant_time * total_multiplier)
        final_doctor_time = self.round_to_nearest_10(total_doctor_time * total_multiplier)
        final_total_time = self.round_to_nearest_10((total_base_time * total_multiplier) + additional_time)
        
        return {
            'success': True,
            'provider': provider,
            'procedures': procedure_details,
            'base_times': {
                'assistant_time': total_assistant_time,
                'doctor_time': total_doctor_time,
                'total_time': total_base_time
            },
            'final_times': {
                'assistant_time': final_assistant_time,
                'doctor_time': final_doctor_time,
                'total_time': final_total_time
            },
            'mitigating_factors': {
                'multiplier': total_multiplier,
                'additional_time': additional_time
            }
        }
    
    def calculate_single_appointment_time(self, procedure: str, provider: str, 
                                        num_teeth: int = 1, num_surfaces: int = 1, 
                                        num_quadrants: int = 1, 
                                        mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """Calculate appointment time for a single procedure (backward compatibility)"""
        procedures = [{
            'procedure': procedure,
            'num_teeth': num_teeth,
            'num_surfaces': num_surfaces,
            'num_quadrants': num_quadrants
        }]
        
        return self.calculate_appointment_time(procedures, provider, mitigating_factors)
