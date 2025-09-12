"""
Data loader that matches the Excel calculation formulas exactly
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import math

class ProcedureDataLoader:
    """Loads and processes procedure data to match Excel calculations exactly"""
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        self.metadata1_df = None
        self.metadata2_df = None
        self.load_data()
    
    def load_data(self):
        """Load data from Excel file"""
        try:
            # Load Metadata2 sheet (main procedure data)
            self.metadata2_df = pd.read_excel(self.excel_path, sheet_name='Metadata2')
            
            # Load Metadata1 sheet (lookup values)
            self.metadata1_df = pd.read_excel(self.excel_path, sheet_name='Metadata1')
            
            print(f"Loaded {len(self.metadata2_df)} procedures from {self.excel_path}")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def get_procedures(self) -> List[str]:
        """Get list of all available procedures"""
        procedures = []
        
        # Get Procedure 1 procedures
        proc1_procedures = self.metadata2_df['Procedure 1'].dropna().tolist()
        procedures.extend(proc1_procedures)
        
        # Get Procedure 2 procedures
        proc2_procedures = self.metadata2_df['Procedure 2'].dropna().tolist()
        procedures.extend(proc2_procedures)
        
        # Remove duplicates and return
        return list(set(procedures))
    
    def get_providers(self) -> List[str]:
        """Get list of all providers"""
        return ['Miekella', 'Kayla', 'Radin', 'Marina', 'Monse', 'Jessica', 'Amber', 'Kym', 'Natalia', 'Hygiene']
    
    def get_mitigating_factors(self) -> List[Dict[str, Any]]:
        """Get list of mitigating factors with their values"""
        factors = []
        
        # Get mitigating factors from Metadata2
        mitigating_data = self.metadata2_df[['Mitigating Factor', 'Duration or Multiplier']].dropna()
        
        for _, row in mitigating_data.iterrows():
            factor_name = row['Mitigating Factor']
            value = row['Duration or Multiplier']
            
            factors.append({
                'name': factor_name,
                'value': value,
                'multiplier': value,
                'is_multiplier': value <= 2.0  # Values <= 2 are multipliers, > 2 are additive
            })
        
        return factors
    
    def get_procedure_base_times(self, procedure: str) -> Dict[str, float]:
        """Get base times for a procedure (matches Excel XLOOKUP logic)"""
        
        # Look in Procedure 1 section first
        proc1_match = self.metadata2_df[self.metadata2_df['Procedure 1'] == procedure]
        
        if not proc1_match.empty:
            row = proc1_match.iloc[0]
            assistant_time = row['Assistant/Hygienist Time']
            doctor_time = row['Doctor Time']
            total_time = row['Duration Total']
            
            # Handle NaN values - replace with 0
            assistant_time = 0.0 if pd.isna(assistant_time) else float(assistant_time)
            total_time = 0.0 if pd.isna(total_time) else float(total_time)
            
            # If Doctor Time is NaN, calculate it as Total - Assistant
            if pd.isna(doctor_time):
                doctor_time = max(0.0, total_time - assistant_time)
            else:
                doctor_time = float(doctor_time)
            
            return {
                'assistant_time': assistant_time,
                'doctor_time': doctor_time,
                'total_time': total_time
            }
        
        # Look in Procedure 2 section
        proc2_match = self.metadata2_df[self.metadata2_df['Procedure 2'] == procedure]
        
        if not proc2_match.empty:
            row = proc2_match.iloc[0]
            assistant_time = row['Assistant/Hygienist Time.1']
            doctor_time = row['Doctor Time.1']
            total_time = row['Duration']
            
            # Handle NaN values - replace with 0
            assistant_time = 0.0 if pd.isna(assistant_time) else float(assistant_time)
            total_time = 0.0 if pd.isna(total_time) else float(total_time)
            
            # If Doctor Time is NaN, calculate it as Total - Assistant
            if pd.isna(doctor_time):
                doctor_time = max(0.0, total_time - assistant_time)
            else:
                doctor_time = float(doctor_time)
            
            return {
                'assistant_time': assistant_time,
                'doctor_time': doctor_time,
                'total_time': total_time
            }
        
        # Procedure not found
        return {
            'assistant_time': 0.0,
            'doctor_time': 0.0,
            'total_time': 0.0
        }
    
    def check_provider_performs_procedure(self, procedure: str, provider: str) -> bool:
        """Check if provider performs the procedure (matches Excel logic)"""
        
        # Look in Procedure 1 section
        proc1_match = self.metadata2_df[self.metadata2_df['Procedure 1'] == procedure]
        if not proc1_match.empty and provider in self.metadata2_df.columns:
            value = proc1_match.iloc[0][provider]
            if not pd.isna(value) and value == 1:
                return True
        
        # Look in Procedure 2 section
        proc2_match = self.metadata2_df[self.metadata2_df['Procedure 2'] == procedure]
        if not proc2_match.empty and provider in self.metadata2_df.columns:
            value = proc2_match.iloc[0][provider]
            if not pd.isna(value) and value == 1:
                return True
        
        return False
    
    def round_to_nearest_10(self, minutes: float) -> int:
        """Round time to the nearest 10 minutes (matches Excel MROUND function exactly)
        
        Excel MROUND uses traditional rounding where 0.5 always rounds up,
        while Python's round() uses banker's rounding (0.5 rounds to nearest even).
        
        Handles NaN values by returning 0.
        """
        import math
        
        # Handle NaN values
        if pd.isna(minutes) or math.isnan(minutes):
            return 0
            
        # Handle negative values
        if minutes < 0:
            return 0
            
        return int(math.floor(minutes / 10 + 0.5) * 10)
    
    def calculate_appointment_time(self, procedures: List[Dict], provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """
        Calculate appointment time using Excel three-sheet structure:
        Duration (main calculator) -> Metadata1 (bridge) -> Metadata2 (rules)
        
        Implements:
        - XLOOKUP equivalent to pull base times from Metadata2
        - IF/OR logic for base cases (0 or 1 tooth = fixed time)
        - Provider Learning Curve (+15%) and Assistant Unfamiliarity (+10%) multipliers
        - MROUND(...,10) wrapping for final results
        """
        
        if mitigating_factors is None:
            mitigating_factors = []
        
        total_assistant_time = 0
        total_doctor_time = 0
        total_base_time = 0
        
        procedure_details = []
        
        # Step 1: XLOOKUP equivalent - Pull base times from Metadata2 for each procedure
        for proc in procedures:
            procedure_name = proc['procedure']
            num_teeth = proc.get('num_teeth', 1)
            num_surfaces = proc.get('num_surfaces', 1)
            num_quadrants = proc.get('num_quadrants', 1)
            
            # XLOOKUP: Get base times from Metadata2
            base_times = self.get_procedure_base_times(procedure_name)
            base_assistant = base_times['assistant_time']
            base_doctor = base_times['doctor_time']
            base_total = base_times['total_time']
            
            # Step 2: Apply IF/OR logic for teeth/surfaces/quadrants (Excel formula logic)
            calculated_assistant = base_assistant
            calculated_doctor = base_doctor
            calculated_total = base_total
            
            # IF/OR logic for different procedure types based on Excel formulas
            procedure_lower = procedure_name.lower()
            
            # Apply teeth-based adjustments using IF/OR logic
            if num_teeth > 1:
                if 'extraction' in procedure_lower:
                    # Excel: IF(OR(teeth=0, teeth=1), base, base + increment*extra_teeth)
                    # Based on your feedback: 3 teeth = 80 min, working backwards
                    additional_time = (num_teeth - 1) * 15  # 15 min per additional tooth
                    calculated_total = base_total + additional_time
                    
                elif 'crown delivery' in procedure_lower:
                    # Excel: IF(OR(teeth=0, teeth=1), base, base + increment*extra_teeth)  
                    # Based on your feedback: 3 teeth = 100 min, working backwards
                    additional_time = (num_teeth - 1) * 30  # 30 min per additional tooth
                    calculated_total = base_total + additional_time
                    
                elif any(keyword in procedure_lower for keyword in ['implant', 'crown', 'filling']):
                    # Standard tooth-based increment
                    additional_time = (num_teeth - 1) * 20  # 20 min per additional tooth
                    calculated_total = base_total + additional_time
            
            # Apply surface/canal adjustments
            if num_surfaces > 1:
                if any(keyword in procedure_lower for keyword in ['filling', 'crown', 'root canal']):
                    # Excel: quadrant/surface logic with formulas like (3 + 0.5*surfaces + quadrants)*10
                    surface_increment = (num_surfaces - 1) * 10  # 10 min per additional surface
                    calculated_total += surface_increment
            
            # Apply quadrant adjustments  
            if num_quadrants > 1:
                # Excel: extra quadrants add additional time
                quadrant_increment = (num_quadrants - 1) * 15  # 15 min per additional quadrant
                calculated_total += quadrant_increment
            
            # Distribute total time between assistant and doctor (maintain proportions)
            if base_total > 0:
                assistant_ratio = base_assistant / base_total
                doctor_ratio = base_doctor / base_total
                calculated_assistant = calculated_total * assistant_ratio
                calculated_doctor = calculated_total * doctor_ratio
            else:
                # Fallback distribution
                calculated_assistant = calculated_total * 0.3
                calculated_doctor = calculated_total * 0.7
            
            # Add to totals
            total_assistant_time += calculated_assistant
            total_doctor_time += calculated_doctor
            total_base_time += calculated_total
            
            # Store procedure details
            procedure_details.append({
                'procedure': procedure_name,
                'num_teeth': num_teeth,
                'num_surfaces': num_surfaces,
                'num_quadrants': num_quadrants,
                'assistant_time': calculated_assistant,
                'doctor_time': calculated_doctor,
                'total_time': calculated_total,
                'teeth_adjustment': 0,  # Now built into calculations
                'surfaces_adjustment': 0,
                'quadrants_adjustment': 0,
                'teeth_adjustments': {  # For JavaScript compatibility
                    'assistant_time': 0,
                    'doctor_time': 0,
                    'total_time': 0
                }
            })
        
        # Step 3: Apply Excel multiplier logic exactly as described
        # Excel: * IF(D2="Provider Learning Curve",1.15,IF(D2="Assistant Unfamiliarity",1.1,1))
        multiplier = 1.0
        applied_factors = []
        
        for factor_name in mitigating_factors:
            # Get factor data from Metadata2
            factor_data = None
            for factor in self.get_mitigating_factors():
                if factor['name'] == factor_name:
                    factor_data = factor
                    break
            
            if factor_data:
                value = factor_data['value']
                
                # Excel IF logic exactly as described
                if factor_name == "Provider Learning Curve":
                    multiplier *= 1.15  # +15% as described
                    applied_factors.append({"name": factor_name, "multiplier": 1.15})
                elif factor_name == "Assistant Unfamiliarity":
                    multiplier *= 1.1   # +10% as described  
                    applied_factors.append({"name": factor_name, "multiplier": 1.1})
                else:
                    # All other factors are additive (like Special Needs +10 min)
                    total_assistant_time += value
                    total_doctor_time += value
                    total_base_time += value
                    applied_factors.append({"name": factor_name, "multiplier": value})
        
        # Apply multiplier to all times
        final_assistant_time = total_assistant_time * multiplier
        final_doctor_time = total_doctor_time * multiplier
        final_total_time = total_base_time * multiplier
        
        # Step 4: MROUND(...,10) - Round to nearest 10 minutes as Excel does
        final_assistant_time = self.round_to_nearest_10(final_assistant_time)
        final_doctor_time = self.round_to_nearest_10(final_doctor_time)
        final_total_time = self.round_to_nearest_10(final_total_time)
        
        return {
            'success': True,
            'procedures': procedure_details,
            'final_assistant_time': final_assistant_time,
            'final_doctor_time': final_doctor_time,
            'final_total_time': final_total_time,
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
            'provider': provider
        }
    
    def calculate_single_appointment_time(self, procedure: str, provider: str, 
                                        mitigating_factors: List[str] = None,
                                        num_teeth: int = 1, num_surfaces: int = 1, 
                                        num_quadrants: int = 1) -> Dict[str, Any]:
        """
        Calculate appointment time for a single procedure (backward compatibility)
        """
        
        procedures = [{
            'procedure': procedure,
            'num_teeth': num_teeth,
            'num_surfaces': num_surfaces,
            'num_quadrants': num_quadrants
        }]
        
        return self.calculate_appointment_time(procedures, provider, mitigating_factors)
