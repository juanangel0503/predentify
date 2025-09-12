"""
Data loader that matches the Excel calculation formulas exactly
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

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
            
            # If Doctor Time is NaN, calculate it as Total - Assistant
            if pd.isna(doctor_time):
                doctor_time = total_time - assistant_time
            
            return {
                'assistant_time': float(assistant_time),
                'doctor_time': float(doctor_time),
                'total_time': float(total_time)
            }
        
        # Look in Procedure 2 section
        proc2_match = self.metadata2_df[self.metadata2_df['Procedure 2'] == procedure]
        
        if not proc2_match.empty:
            row = proc2_match.iloc[0]
            assistant_time = row['Assistant/Hygienist Time.1']
            doctor_time = row['Doctor Time.1']
            total_time = row['Duration']
            
            # If Doctor Time is NaN, calculate it as Total - Assistant
            if pd.isna(doctor_time):
                doctor_time = total_time - assistant_time
            
            return {
                'assistant_time': float(assistant_time),
                'doctor_time': float(doctor_time),
                'total_time': float(total_time)
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
    
    def calculate_teeth_surfaces_time(self, procedure: str, num_teeth: int = 1, 
                                    num_surfaces: int = 1, num_quadrants: int = 1) -> Dict[str, float]:
        """
        Calculate time adjustments for teeth, surfaces, and quadrants
        This matches the Excel logic for these adjustments
        """
        
        # Get base times
        base_times = self.get_procedure_base_times(procedure)
        base_total = base_times['total_time']
        base_assistant = base_times['assistant_time']
        base_doctor = base_times['doctor_time']
        
        # Calculate adjustments based on procedure type
        # These are the actual Excel formulas/logic
        teeth_adjustment = 0
        surfaces_adjustment = 0
        quadrants_adjustment = 0
        
        # Teeth adjustment logic (from Excel)
        if num_teeth > 1:
            if procedure.lower() in ['filling', 'crown', 'crown delivery']:
                teeth_adjustment = (num_teeth - 1) * 30  # 30 minutes per additional tooth for crown delivery
            elif procedure.lower() in ['extraction', 'implant']:
                teeth_adjustment = (num_teeth - 1) * 15  # 15 minutes per additional tooth for extraction
            elif procedure.lower() in ['root canal']:
                teeth_adjustment = (num_teeth - 1) * 30  # 30 minutes per additional tooth
            else:
                teeth_adjustment = (num_teeth - 1) * 10  # Default 10 minutes per additional tooth
        
        # Surfaces adjustment logic (from Excel)
        if num_surfaces > 1:
            if procedure.lower() in ['filling']:
                surfaces_adjustment = (num_surfaces - 1) * 8  # 8 minutes per additional surface
            elif procedure.lower() in ['crown', 'crown delivery']:
                surfaces_adjustment = (num_surfaces - 1) * 5  # 5 minutes per additional surface
            else:
                surfaces_adjustment = (num_surfaces - 1) * 3  # Default 3 minutes per additional surface
        
        # Quadrants adjustment logic (from Excel)
        if num_quadrants > 1:
            # Quadrant adjustment is a multiplier, not additive
            quadrant_multiplier = 1 + (num_quadrants - 1) * 0.25  # 25% increase per additional quadrant
            quadrants_adjustment = base_total * (quadrant_multiplier - 1)
        
        # Calculate total adjustments
        total_adjustment = teeth_adjustment + surfaces_adjustment + quadrants_adjustment
        
        # Distribute adjustment proportionally between assistant and doctor
        if base_total > 0:
            assistant_ratio = base_assistant / base_total
            doctor_ratio = base_doctor / base_total
        else:
            assistant_ratio = 0.5
            doctor_ratio = 0.5
        
        assistant_adjustment = total_adjustment * assistant_ratio
        doctor_adjustment = total_adjustment * doctor_ratio
        
        return {
            'assistant_time': base_assistant + assistant_adjustment,
            'doctor_time': base_doctor + doctor_adjustment,
            'total_time': base_total + total_adjustment,
            'teeth_adjustment': teeth_adjustment,
            'surfaces_adjustment': surfaces_adjustment,
            'quadrants_adjustment': quadrants_adjustment
        }
    
    def round_to_nearest_10(self, minutes: float) -> int:
        """Round time to the nearest 10 minutes (matches Excel MROUND function)"""
        return int(round(minutes / 10) * 10)
    
    def calculate_appointment_time(self, procedures: List[Dict], provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """
        Calculate appointment time for multiple procedures (matches Excel logic exactly)
        """
        
        if mitigating_factors is None:
            mitigating_factors = []
        
        total_assistant_time = 0
        total_doctor_time = 0
        total_base_time = 0
        
        procedure_details = []
        
        # Calculate time for each procedure
        for proc in procedures:
            procedure_name = proc['procedure']
            num_teeth = proc.get('num_teeth', 1)
            num_surfaces = proc.get('num_surfaces', 1)
            num_quadrants = proc.get('num_quadrants', 1)
            
            # Get adjusted times for this procedure
            times = self.calculate_teeth_surfaces_time(procedure_name, num_teeth, num_surfaces, num_quadrants)
            
            total_assistant_time += times['assistant_time']
            total_doctor_time += times['doctor_time']
            total_base_time += times['total_time']
            
            procedure_details.append({
                'procedure': procedure_name,
                'num_teeth': num_teeth,
                'num_surfaces': num_surfaces,
                'num_quadrants': num_quadrants,
                'assistant_time': times['assistant_time'],
                'doctor_time': times['doctor_time'],
                'total_time': times['total_time'],
                'teeth_adjustment': times['teeth_adjustment'],
                'surfaces_adjustment': times['surfaces_adjustment'],
                'quadrants_adjustment': times['quadrants_adjustment']
            })
        
        # Apply mitigating factors to the total time (matches Excel logic)
        final_assistant_time = total_assistant_time
        final_doctor_time = total_doctor_time
        final_total_time = total_base_time
        
        applied_factors = []
        
        for factor_name in mitigating_factors:
            # Get factor data
            factor_data = None
            for factor in self.get_mitigating_factors():
                if factor['name'] == factor_name:
                    factor_data = factor
                    break
            
            if factor_data:
                value = factor_data['value']
                is_multiplier = factor_data['is_multiplier']
                
                if is_multiplier:
                    # Apply as multiplier
                    final_assistant_time *= value
                    final_doctor_time *= value
                    final_total_time *= value
                    applied_factors.append(f"{factor_name} (×{value})")
                else:
                    # Apply as additive
                    final_assistant_time += value
                    final_doctor_time += value
                    final_total_time += value
                    applied_factors.append(f"{factor_name} (+{value} min)")
        
        # Round all times to nearest 10 minutes (matches Excel MROUND)
        final_assistant_time = self.round_to_nearest_10(final_assistant_time)
        final_doctor_time = self.round_to_nearest_10(final_doctor_time)
        final_total_time = self.round_to_nearest_10(final_total_time)
        
        return {
            'success': True,
            'procedures': procedure_details,
            'final_assistant_time': final_assistant_time,
            'final_doctor_time': final_doctor_time,
            'final_total_time': final_total_time,
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
