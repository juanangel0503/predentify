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
    
    def get_provider_procedure_compatibility(self) -> Dict[str, List[str]]:
        """Get provider -> procedures compatibility matrix"""
        compatibility = {}
        providers = self.get_providers()
        procedures = self.get_procedures()
        
        for provider in providers:
            compatibility[provider] = []
            for procedure in procedures:
                if self.check_provider_performs_procedure(procedure, provider):
                    compatibility[provider].append(procedure)
        
        return compatibility
    
    def get_procedure_provider_compatibility(self) -> Dict[str, List[str]]:
        """Get procedure -> providers compatibility matrix"""
        compatibility = {}
        procedures = self.get_procedures()
        providers = self.get_providers()
        
        for procedure in procedures:
            compatibility[procedure] = []
            for provider in providers:
                if self.check_provider_performs_procedure(procedure, provider):
                    compatibility[procedure].append(provider)
        
        return compatibility
    
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
    
    def calculate_teeth_surfaces_time(self, procedure: str, num_teeth: int, 
                                    num_surfaces: int, num_quadrants: int) -> Dict[str, Any]:
        """
        Calculate time adjustments based on teeth, surfaces, and quadrants
        Using EXACT formulas extracted from the Excel spreadsheet
        Returns either adjustments or absolute overrides
        """
        result = {
            'assistant_time': 0,
            'doctor_time': 0,
            'total_time': 0,
            'is_absolute_override': False  # Flag to indicate if this should replace base times completely
        }
        
        procedure_lower = procedure.lower()
        
        # EXACT EXCEL FORMULAS IMPLEMENTATION - These calculate ABSOLUTE times, not adjustments
        
        if 'crown' in procedure_lower and 'delivery' not in procedure_lower:
            # CROWN FORMULA (D2): =IF(OR(E2=0, E2=1), 90, 80 + (10*E2))
            if num_teeth <= 1:
                total_time = 90
            else:
                total_time = 80 + (10 * num_teeth)
            
            result['total_time'] = total_time
            result['assistant_time'] = total_time * 0.11  # Based on your data: 10/90 = 11%
            result['doctor_time'] = total_time * 0.89     # Based on your data: 80/90 = 89%
            result['is_absolute_override'] = True
            
        elif 'filling' in procedure_lower:
            # FILLING FORMULA (D3): Complex formula based on surfaces and quadrants
            if num_surfaces <= 1:
                total_time = 30
            elif num_quadrants < 1:
                total_time = (3 + 0.5 * num_surfaces) * 10
            else:
                total_time = (3 + 0.5 * num_surfaces + (num_quadrants - 1)) * 10
                
            result['total_time'] = total_time
            result['assistant_time'] = total_time * 0.33  # Based on your data: 10/30 = 33%
            result['doctor_time'] = total_time * 0.67     # Based on your data: 20/30 = 67%
            result['is_absolute_override'] = True
            
        elif 'bridge' in procedure_lower:
            # BRIDGE FORMULA (D4): =IF(OR(E2=0, E2=1), 90, 90 + ((E2-1)*30))
            if num_teeth <= 1:
                total_time = 90
            else:
                total_time = 90 + ((num_teeth - 1) * 30)
                
            result['total_time'] = total_time
            result['assistant_time'] = total_time * 0.25  # Estimate: bridges are doctor-heavy
            result['doctor_time'] = total_time * 0.75
            result['is_absolute_override'] = True
            
        elif 'extraction' in procedure_lower:
            # EXTRACTION FORMULA (D10): Complex formula
            if num_teeth <= 1:
                total_time = 50
            elif num_teeth == 2 and num_quadrants <= 1:
                total_time = 55
            elif num_teeth == 2 and num_quadrants == 2:
                total_time = 60
            elif num_teeth >= 3 and num_quadrants <= 1:
                total_time = 45 + (5 * num_teeth)
            elif num_teeth >= 3 and num_quadrants >= 2:
                total_time = 45 + (5 * num_teeth) + (5 * num_quadrants)
            else:
                total_time = 50  # fallback
                
            result['total_time'] = total_time
            result['assistant_time'] = total_time * 0.2   # Based on your data: 10/50 = 20%
            result['doctor_time'] = total_time * 0.8      # Based on your data: 40/50 = 80%
            result['is_absolute_override'] = True
            
        elif 'root canal' in procedure_lower:
            # ROOT CANAL FORMULA (D8): =IF(OR(F2=0, F2=1), 60, 60 + (F2-1)*10)
            if num_surfaces <= 1:
                total_time = 60
            else:
                total_time = 60 + ((num_surfaces - 1) * 10)
                
            result['total_time'] = total_time
            result['assistant_time'] = total_time * 0.17  # Root canals are very doctor-heavy
            result['doctor_time'] = total_time * 0.83
            result['is_absolute_override'] = True
            
        elif 'implant' in procedure_lower and 'crown' not in procedure_lower:
            # IMPLANT FORMULA (D9): =IF(OR(E2=0, E2=1), 70, 70 + (E2-1)*20)
            if num_teeth <= 1:
                total_time = 70
            else:
                total_time = 70 + ((num_teeth - 1) * 20)
                
            result['total_time'] = total_time
            result['assistant_time'] = total_time * 0.33  # Based on your data: 30/90 ≈ 33%
            result['doctor_time'] = total_time * 0.67     # Based on your data: 60/90 ≈ 67%
            result['is_absolute_override'] = True
        
        # For other procedures, return no adjustments (use base times from Excel data)
        return result
    
    def round_to_nearest_10(self, minutes: float) -> int:
        """Round time to nearest 10 minutes using Excel MROUND behavior (always rounds .5 up)"""
        # Excel MROUND behavior - always rounds .5 away from zero (up for positive numbers)
        return int((minutes + 5) // 10 * 10)
    
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
        for idx, proc_data in enumerate(procedures):
            procedure = proc_data['procedure']
            num_teeth = proc_data.get('num_teeth', 1)
            num_surfaces = proc_data.get('num_surfaces', 1)
            num_quadrants = proc_data.get('num_quadrants', 1)
            
            # Get base times
            base_times = self.get_procedure_base_times(procedure)
            
            if not base_times:
                # For multiple procedures, allow procedures even if provider can't do them
                # but use default times and add a warning
                base_times = {'assistant_time': 15, 'doctor_time': 30, 'total_time': 45}
                warning_added = True
            else:
                warning_added = False
            
            # For multiple procedures, don't enforce provider compatibility
            # Just calculate the time and let the user know if there's an issue
            can_perform = self.check_provider_performs_procedure(procedure, provider)
            
            # Calculate teeth/surfaces/canals adjustments
            teeth_adjustments = self.calculate_teeth_surfaces_time(procedure, num_teeth, num_surfaces, num_quadrants)
            
            # Calculate procedure time - handle absolute overrides from Excel formulas
            if teeth_adjustments.get('is_absolute_override', False):
                # Use absolute times from Excel formulas
                proc_assistant_time = teeth_adjustments['assistant_time']
                proc_doctor_time = teeth_adjustments['doctor_time']
                proc_total_time = teeth_adjustments['total_time']
            else:
                # Use base times + adjustments (traditional approach)
                proc_assistant_time = base_times['assistant_time'] + teeth_adjustments['assistant_time']
                proc_doctor_time = base_times['doctor_time'] + teeth_adjustments['doctor_time']
                proc_total_time = base_times['total_time'] + teeth_adjustments['total_time']
            
            # Apply 30% reduction for 2nd+ procedures and round to nearest 10
            is_first_procedure = (idx == 0)
            if not is_first_procedure:
                # Reduce by 30% and round to nearest 10
                reduced_total = proc_total_time * 0.7
                reduced_total_rounded = self.round_to_nearest_10(reduced_total)
                
                # Maintain the assistant/doctor ratio for the reduced time
                if proc_total_time > 0:
                    assistant_ratio = proc_assistant_time / proc_total_time
                    doctor_ratio = proc_doctor_time / proc_total_time
                    
                    proc_assistant_time = reduced_total_rounded * assistant_ratio
                    proc_doctor_time = reduced_total_rounded * doctor_ratio
                    proc_total_time = reduced_total_rounded
            
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
                },
                'is_first_procedure': is_first_procedure,
                'provider_can_perform': can_perform,
                'time_reduced': not is_first_procedure
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
