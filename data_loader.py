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

    def check_provider_performs_procedure(self, procedure: str, provider: str) -> bool:
        if procedure in self.provider_compatibility:
            return provider in self.provider_compatibility[procedure]
        return True  # Default to true if no specific compatibility data

    def round_to_nearest_10(self, minutes: float) -> int:
        if math.isnan(minutes):
            return 0
        if minutes < 0:
            return 0
        return int(math.floor(minutes / 10 + 0.5) * 10)

    def calculate_appointment_time(self, procedures: List[Dict], provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """
        Calculate appointment time using EXACT Excel formulas from Cal.xlsx formula report
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
            
            # Apply EXACT Excel formulas from Cal.xlsx formula report
            if procedure == 'Implant':
                if num_teeth == 0 or num_teeth == 1:
                    adjusted_total = 90
                else:
                    adjusted_total = 80 + (10 * num_teeth)
                # Keep assistant/doctor ratio from base
                if base_total > 0:
                    ratio = adjusted_total / base_total
                    adjusted_assistant = base_assistant * ratio
                    adjusted_doctor = base_doctor * ratio
                else:
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
                
            elif procedure == 'Crown':
                if num_teeth == 0 or num_teeth == 1:
                    adjusted_total = 90
                else:
                    adjusted_total = 90 + ((num_teeth - 1) * 30)
                # Keep assistant/doctor ratio from base
                if base_total > 0:
                    ratio = adjusted_total / base_total
                    adjusted_assistant = base_assistant * ratio
                    adjusted_doctor = base_doctor * ratio
                else:
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
                
            elif procedure == 'Crown Delivery':
                if num_teeth == 0 or num_teeth == 1:
                    adjusted_total = 40
                else:
                    adjusted_total = 40 + ((num_teeth - 1) * 10)
                # Keep assistant/doctor ratio from base
                if base_total > 0:
                    ratio = adjusted_total / base_total
                    adjusted_assistant = base_assistant * ratio
                    adjusted_doctor = base_doctor * ratio
                else:
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
                
            elif procedure == 'Extraction':
                if num_teeth == 0 or num_teeth == 1:
                    adjusted_total = 50
                elif num_teeth == 2 and (num_quadrants == 0 or num_quadrants == 1):
                    adjusted_total = 55
                elif num_teeth == 2 and num_quadrants == 2:
                    adjusted_total = 60
                elif num_teeth >= 3 and num_quadrants <= 1:
                    adjusted_total = 45 + (5 * num_teeth)
                elif num_teeth >= 3 and num_quadrants >= 2:
                    adjusted_total = 45 + (5 * num_teeth) + (5 * num_quadrants)
                else:
                    adjusted_total = base_total  # fallback
                # Keep assistant/doctor ratio from base
                if base_total > 0:
                    ratio = adjusted_total / base_total
                    adjusted_assistant = base_assistant * ratio
                    adjusted_doctor = base_doctor * ratio
                else:
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
                
            elif procedure == 'Root Canal':
                if num_surfaces == 0 or num_surfaces == 1:
                    adjusted_total = 60
                else:
                    adjusted_total = 60 + (num_surfaces - 1) * 10
                # Keep assistant/doctor ratio from base
                if base_total > 0:
                    ratio = adjusted_total / base_total
                    adjusted_assistant = base_assistant * ratio
                    adjusted_doctor = base_doctor * ratio
                else:
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
                
            elif procedure == 'Filling':
                if num_surfaces == 0 or num_surfaces == 1:
                    adjusted_total = 30
                elif num_quadrants < 1:
                    adjusted_total = (3 + 0.5 * num_surfaces) * 10
                else:
                    adjusted_total = (3 + 0.5 * num_surfaces + (num_quadrants - 1)) * 10
                # Keep assistant/doctor ratio from base
                if base_total > 0:
                    ratio = adjusted_total / base_total
                    adjusted_assistant = base_assistant * ratio
                    adjusted_doctor = base_doctor * ratio
                else:
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
                
            else:
                # For other procedures, use base times with simple teeth adjustment
                if num_teeth > 1:
                    # Simple adjustment: add 10 minutes per additional tooth
                    teeth_adjustment = (num_teeth - 1) * 10
                    adjusted_total = base_total + teeth_adjustment
                    adjusted_assistant = base_assistant + (teeth_adjustment * 0.3)  # 30% to assistant
                    adjusted_doctor = base_doctor + (teeth_adjustment * 0.7)  # 70% to doctor
                else:
                    adjusted_total = base_total
                    adjusted_assistant = base_assistant
                    adjusted_doctor = base_doctor
            
            # Round to nearest 10 minutes (Excel MROUND behavior)
            adjusted_assistant = self.round_to_nearest_10(adjusted_assistant)
            adjusted_doctor = self.round_to_nearest_10(adjusted_doctor)
            adjusted_total = self.round_to_nearest_10(adjusted_total)
            
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
