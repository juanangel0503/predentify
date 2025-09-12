import json
import os
import math
from typing import Dict, List, Any

class ProcedureDataLoader:
    def __init__(self, data_directory: str = 'data'):
        self.data_dir = data_directory
        self.procedures_data = {}
        self.mitigating_factors = []
        self.provider_compatibility = {}
        self.providers = []
        self.load_data()

    def load_data(self):
        try:
            with open(os.path.join(self.data_dir, 'procedures.json'), 'r') as f:
                self.procedures_data = json.load(f)
            with open(os.path.join(self.data_dir, 'mitigating_factors.json'), 'r') as f:
                self.mitigating_factors = json.load(f)
            with open(os.path.join(self.data_dir, 'provider_compatibility.json'), 'r') as f:
                self.provider_compatibility = json.load(f)
            all_providers = set()
            for providers_list in self.provider_compatibility.values():
                all_providers.update(providers_list)
            self.providers = sorted(list(all_providers))
            print(f"Loaded {len(self.procedures_data)} procedures from JSON data")
        except FileNotFoundError as e:
            print(f"Error loading JSON data: {e}")
            print("Please ensure JSON data files exist in the data/ directory")
            raise

    def get_procedures(self) -> List[str]:
        return list(self.procedures_data.keys())

    def get_providers(self) -> List[str]:
        return self.providers

    def get_mitigating_factors(self) -> List[Dict]:
        return self.mitigating_factors

    def get_procedure_base_times(self, procedure: str) -> Dict[str, float]:
        if procedure in self.procedures_data:
            proc_data = self.procedures_data[procedure]
            return {
                'assistant_time': proc_data['assistant_time'],
                'doctor_time': proc_data['doctor_time'],
                'total_time': proc_data['total_time']
            }
        return {'assistant_time': 0.0, 'doctor_time': 0.0, 'total_time': 0.0}

    def check_provider_performs_procedure(self, provider: str, procedure: str) -> bool:
        if procedure in self.provider_compatibility:
            return provider in self.provider_compatibility[procedure]
        return True  # Default to True if no compatibility data

    def round_to_nearest_10(self, minutes: float) -> int:
        """Round to nearest 10 minutes (Excel MROUND behavior)"""
        if math.isnan(minutes) or minutes < 0:
            return 0
        return int(round(minutes / 10) * 10)

    def calculate_appointment_time(self, procedures: List[Dict], provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """
        Calculate appointment time using CORRECTED formulas for assistant and doctor times
        """
        if mitigating_factors is None:
            mitigating_factors = []
            
        total_assistant_time = 0.0
        total_doctor_time = 0.0
        procedure_details = []
        
        for proc_data in procedures:
            procedure = proc_data['procedure']
            num_teeth = int(proc_data.get('num_teeth', 1))
            num_surfaces = int(proc_data.get('num_surfaces', 1))
            num_quadrants = int(proc_data.get('num_quadrants', 1))
            
            # Get base times from procedure data
            base_times = self.get_procedure_base_times(procedure)
            base_assistant = base_times['assistant_time']
            base_doctor = base_times['doctor_time']
            base_total = base_times['total_time']
            
            # Calculate assistant and doctor times using CORRECTED formulas
            if procedure == 'Implant surgery':
                if num_teeth == 0 or num_teeth == 1:
                    # Base case: 90 minutes total
                    adjusted_total = 90
                    # Assistant time: 30% of total (27 min), Doctor time: 70% of total (63 min)
                    adjusted_assistant = 27
                    adjusted_doctor = 63
                else:
                    # Multiple teeth: 80 + (10 * num_teeth)
                    adjusted_total = 80 + (10 * num_teeth)
                    # Assistant time: 30% of total, Doctor time: 70% of total
                    adjusted_assistant = adjusted_total * 0.3
                    adjusted_doctor = adjusted_total * 0.7
                
            elif procedure == 'Crown preparation':
                if num_teeth == 0 or num_teeth == 1:
                    # Base case: 90 minutes total
                    adjusted_total = 90
                    # Assistant time: 10% of total (9 min), Doctor time: 90% of total (81 min)
                    adjusted_assistant = 9
                    adjusted_doctor = 81
                else:
                    # Multiple teeth: 90 + ((num_teeth - 1) * 30)
                    adjusted_total = 90 + ((num_teeth - 1) * 30)
                    # Assistant time: 10% of total, Doctor time: 90% of total
                    adjusted_assistant = adjusted_total * 0.1
                    adjusted_doctor = adjusted_total * 0.9
                
            elif procedure == 'Crown Delivery':
                if num_teeth == 0 or num_teeth == 1:
                    # Base case: 40 minutes total
                    adjusted_total = 40
                    # Assistant time: 25% of total (10 min), Doctor time: 75% of total (30 min)
                    adjusted_assistant = 10
                    adjusted_doctor = 30
                else:
                    # Multiple teeth: 40 + ((num_teeth - 1) * 10)
                    adjusted_total = 40 + ((num_teeth - 1) * 10)
                    # Assistant time: 25% of total, Doctor time: 75% of total
                    adjusted_assistant = adjusted_total * 0.25
                    adjusted_doctor = adjusted_total * 0.75
                
            elif procedure == 'Extraction':
                if num_teeth == 0 or num_teeth == 1:
                    # Base case: 50 minutes total
                    adjusted_total = 50
                    # Assistant time: 20% of total (10 min), Doctor time: 80% of total (40 min)
                    adjusted_assistant = 10
                    adjusted_doctor = 40
                elif num_teeth == 2 and (num_quadrants == 0 or num_quadrants == 1):
                    # 2 teeth, 1 quadrant: 55 minutes total
                    adjusted_total = 55
                    adjusted_assistant = 11  # 20% of total
                    adjusted_doctor = 44     # 80% of total
                elif num_teeth == 2 and num_quadrants == 2:
                    # 2 teeth, 2 quadrants: 60 minutes total
                    adjusted_total = 60
                    adjusted_assistant = 12  # 20% of total
                    adjusted_doctor = 48     # 80% of total
                elif num_teeth >= 3 and num_quadrants <= 1:
                    # 3+ teeth, 1 quadrant: 45 + (5 * num_teeth)
                    adjusted_total = 45 + (5 * num_teeth)
                    adjusted_assistant = adjusted_total * 0.2  # 20% of total
                    adjusted_doctor = adjusted_total * 0.8     # 80% of total
                elif num_teeth >= 3 and num_quadrants >= 2:
                    # 3+ teeth, 2+ quadrants: 45 + (5 * num_teeth) + (5 * num_quadrants)
                    adjusted_total = 45 + (5 * num_teeth) + (5 * num_quadrants)
                    adjusted_assistant = adjusted_total * 0.2  # 20% of total
                    adjusted_doctor = adjusted_total * 0.8     # 80% of total
                else:
                    # Fallback to base times
                    adjusted_total = base_total
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
                
            elif procedure == 'Root Canal':
                if num_surfaces == 0 or num_surfaces == 1:
                    # Base case: 60 minutes total
                    adjusted_total = 60
                    # Assistant time: 33% of total (20 min), Doctor time: 67% of total (40 min)
                    adjusted_assistant = 20
                    adjusted_doctor = 40
                else:
                    # Multiple surfaces: 60 + (num_surfaces - 1) * 10
                    adjusted_total = 60 + (num_surfaces - 1) * 10
                    # Assistant time: 33% of total, Doctor time: 67% of total
                    adjusted_assistant = adjusted_total * (20/60)  # 33.33%
                    adjusted_doctor = adjusted_total * (40/60)     # 66.67%
                
            elif procedure == 'Filling':
                if num_surfaces == 0 or num_surfaces == 1:
                    # Base case: 30 minutes total
                    adjusted_total = 30
                    # Assistant time: 0% of total (0 min), Doctor time: 100% of total (30 min)
                    adjusted_assistant = 0
                    adjusted_doctor = 30
                elif num_quadrants < 1:
                    # Formula: (3 + 0.5 * num_surfaces) * 10
                    adjusted_total = (3 + 0.5 * num_surfaces) * 10
                    adjusted_assistant = 0  # Fillings are typically doctor-only
                    adjusted_doctor = adjusted_total
                else:
                    # Formula: (3 + 0.5 * num_surfaces + (num_quadrants - 1)) * 10
                    adjusted_total = (3 + 0.5 * num_surfaces + (num_quadrants - 1)) * 10
                    adjusted_assistant = 0  # Fillings are typically doctor-only
                    adjusted_doctor = adjusted_total
                
            else:
                # For other procedures, use base times with simple teeth adjustment
                if num_teeth > 1:
                    # Simple adjustment: add 10 minutes per additional tooth
                    teeth_adjustment = (num_teeth - 1) * 10
                    adjusted_total = base_total + teeth_adjustment
                    # Distribute adjustment based on base ratio
                    if base_total > 0:
                        assistant_ratio = base_assistant / base_total
                        doctor_ratio = base_doctor / base_total
                        adjusted_assistant = base_assistant + (teeth_adjustment * assistant_ratio)
                        adjusted_doctor = base_doctor + (teeth_adjustment * doctor_ratio)
                    else:
                        adjusted_assistant = base_assistant
                        adjusted_doctor = base_doctor
                else:
                    adjusted_total = base_total
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
            
            # Round to nearest 10 minutes (Excel MROUND behavior)
            adjusted_assistant = self.round_to_nearest_10(adjusted_assistant)
            adjusted_doctor = self.round_to_nearest_10(adjusted_doctor)
            adjusted_total = self.round_to_nearest_10(adjusted_total)
            
            # Apply 30% reduction for 2nd+ procedures
            procedure_index = len(procedure_details)  # 0-based index
            if procedure_index > 0:  # 2nd procedure and beyond (index 1, 2, 3...)
                # Reduce by 30% and round to nearest 10
                adjusted_assistant = self.round_to_nearest_10(adjusted_assistant * 0.7)
                adjusted_doctor = self.round_to_nearest_10(adjusted_doctor * 0.7)
                adjusted_total = adjusted_assistant + adjusted_doctor
            
            # Add to totals
            total_assistant_time += adjusted_assistant
            total_doctor_time += adjusted_doctor
            
            # Store procedure details
            procedure_details.append({
                'procedure': procedure,
                'num_teeth': num_teeth,
                'num_surfaces': num_surfaces,
                'num_quadrants': num_quadrants,
                'base_times': {
                    'assistant_time': self.round_to_nearest_10(base_assistant),
                    'doctor_time': self.round_to_nearest_10(base_doctor),
                    'total_time': self.round_to_nearest_10(base_total)
                },
                'adjusted_times': {
                    'assistant_time': adjusted_assistant,
                    'doctor_time': adjusted_doctor,
                    'total_time': adjusted_total
                }
            })
        
        # Calculate base total time
        total_base_time = total_assistant_time + total_doctor_time
        
        # Apply mitigating factors to the TOTAL time (once)
        final_assistant_time = total_assistant_time
        final_doctor_time = total_doctor_time
        final_total_time = total_base_time
        applied_factors = []
        
        for factor_name in mitigating_factors:
            factor_data = next((f for f in self.mitigating_factors if f['name'] == factor_name), None)
            if factor_data:
                value = factor_data['value']
                if factor_data['is_multiplier']:
                    # Apply multiplier to total time
                    final_total_time *= value
                    # Distribute proportionally to assistant and doctor
                    if total_base_time > 0:
                        assistant_ratio = total_assistant_time / total_base_time
                        doctor_ratio = total_doctor_time / total_base_time
                        final_assistant_time = final_total_time * assistant_ratio
                        final_doctor_time = final_total_time * doctor_ratio
                else:
                    # Add time to total
                    final_total_time += value
                    # Add proportionally to assistant and doctor
                    if total_base_time > 0:
                        assistant_ratio = total_assistant_time / total_base_time
                        doctor_ratio = total_doctor_time / total_base_time
                        final_assistant_time += value * assistant_ratio
                        final_doctor_time += value * doctor_ratio
                
                applied_factors.append({
                    "name": factor_name,
                    "multiplier": value
                })
        
        # Final rounding
        final_assistant_time = self.round_to_nearest_10(final_assistant_time)
        final_doctor_time = self.round_to_nearest_10(final_doctor_time)
        final_total_time = self.round_to_nearest_10(final_total_time)
        
        return {
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
            'procedure_details': procedure_details,
            'applied_factors': applied_factors,
            'provider': provider
        }

    def calculate_single_appointment_time(self, procedure: str, provider: str, mitigating_factors: List[str], 
                                        num_teeth: int = 1, num_surfaces: int = 1, num_quadrants: int = 1) -> Dict:
        """
        Calculate appointment time for a single procedure (backward compatibility)
        """
        procedures_data = [{
            'procedure': procedure,
            'num_teeth': num_teeth,
            'num_surfaces': num_surfaces,
            'num_quadrants': num_quadrants
        }]
        
        return self.calculate_appointment_time(procedures_data, provider, mitigating_factors)
