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
        self.available_procedures = []  # Only procedures that are actually available
        self.load_data()

    def load_data(self):
        try:
            with open(os.path.join(self.data_dir, 'procedures.json'), 'r') as f:
                self.procedures_data = json.load(f)
            with open(os.path.join(self.data_dir, 'mitigating_factors.json'), 'r') as f:
                self.mitigating_factors = json.load(f)
            with open(os.path.join(self.data_dir, 'provider_compatibility.json'), 'r') as f:
                self.provider_compatibility = json.load(f)
            
            # Build list of all providers
            all_providers = set()
            for providers_list in self.provider_compatibility.values():
                all_providers.update(providers_list)
            self.providers = sorted(list(all_providers))
            
            # Filter to only available procedures
            self.available_procedures = self._filter_available_procedures()
            
            print(f"Loaded {len(self.procedures_data)} total procedures from JSON data")
            print(f"Found {len(self.available_procedures)} available procedures")
        except FileNotFoundError as e:
            print(f"Error loading JSON data: {e}")
            print("Please ensure JSON data files exist in the data/ directory")
            raise

    def _filter_available_procedures(self) -> List[str]:
        """
        Filter procedures to only include those that are:
        1. Valid (have proper time data)
        2. Available (have at least one provider who can perform them)
        3. Active (not deprecated or inactive)
        """
        available = []
        
        for procedure_name, proc_data in self.procedures_data.items():
            # Check if procedure has valid time data
            if not self._is_valid_procedure_data(proc_data):
                print(f"Skipping {procedure_name}: Invalid time data")
                continue
                
            # Check if procedure has at least one provider who can perform it
            if not self._has_available_providers(procedure_name):
                print(f"Skipping {procedure_name}: No available providers")
                continue
                
            # Check if procedure is active (not deprecated)
            if not self._is_active_procedure(procedure_name, proc_data):
                print(f"Skipping {procedure_name}: Inactive/deprecated")
                continue
                
            available.append(procedure_name)
        
        return sorted(available)

    def _is_valid_procedure_data(self, proc_data: Dict) -> bool:
        """Check if procedure has valid time data"""
        try:
            assistant_time = float(proc_data.get('assistant_time', 0))
            doctor_time = float(proc_data.get('doctor_time', 0))
            total_time = float(proc_data.get('total_time', 0))
            
            # Check for valid numeric values
            if math.isnan(assistant_time) or math.isnan(doctor_time) or math.isnan(total_time):
                return False
                
            # Check for reasonable time values (not negative, not zero total)
            if total_time <= 0 or assistant_time < 0 or doctor_time < 0:
                return False
                
            return True
        except (ValueError, TypeError):
            return False

    def _has_available_providers(self, procedure_name: str) -> bool:
        """Check if procedure has at least one provider who can perform it"""
        if procedure_name not in self.provider_compatibility:
            return False
            
        providers = self.provider_compatibility[procedure_name]
        return len(providers) > 0 and all(provider.strip() for provider in providers)

    def _is_active_procedure(self, procedure_name: str, proc_data: Dict) -> bool:
        """Check if procedure is active (not deprecated or inactive)"""
        # Check for deprecated/inactive indicators
        section = proc_data.get('section', '')
        
        # Skip procedures in deprecated sections
        if section in ['deprecated', 'inactive', 'old']:
            return False
            
        # Skip procedures with specific names that indicate they're not active
        inactive_keywords = ['old', 'deprecated', 'inactive', 'test', 'temp']
        if any(keyword in procedure_name.lower() for keyword in inactive_keywords):
            return False
            
        return True

    def get_procedures(self) -> List[str]:
        """Return only available procedures"""
        return self.available_procedures

    def get_all_procedures(self) -> List[str]:
        """Return all procedures (including unavailable ones) - for debugging"""
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
        """Round to nearest 10 minutes (Excel MROUND behavior) - FIXED"""
        if math.isnan(minutes) or minutes < 0:
            return 0
        
        # Excel MROUND behavior: round to nearest multiple of 10
        # For values exactly halfway (like 105), round up
        # Use math.floor and add 0.5 to get "round half away from zero" behavior
        return int(math.floor(minutes / 10 + 0.5) * 10)

    def calculate_appointment_time(self, procedures: List[Dict], provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """
        Calculate appointment time using NEW SPREADSHEET LOGIC (rev0.2)
        Based on the updated VDH_Procedure_Durations_rev0.2.xlsx
        
        FIXED: Proper rounding logic to match Excel behavior
        """
        if mitigating_factors is None:
            mitigating_factors = []
            
        total_assistant_time = 0.0
        total_doctor_time = 0.0
        total_overhead_time = 0.0  # Additional time beyond assistant + doctor
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
            
            # Calculate overhead time (time beyond assistant + doctor)
            base_overhead = base_total - base_assistant - base_doctor
            
            # Start with base times
            adjusted_assistant = base_assistant
            adjusted_doctor = base_doctor
            adjusted_overhead = base_overhead
            adjusted_total = base_total
            
            # Apply teeth/surfaces/quadrants adjustments based on procedure type
            if procedure == 'Implant':
                # Implant: Base time + 10 minutes per additional tooth
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 10
                    adjusted_total += teeth_adjustment
                    # Distribute adjustment: 70% to assistant, 30% to overhead
                    adjusted_assistant += teeth_adjustment * 0.7
                    adjusted_overhead += teeth_adjustment * 0.3
                
            elif procedure == 'Filling':
                # Filling: Base time + 5 minutes per additional surface
                if num_surfaces > 1:
                    surface_adjustment = (num_surfaces - 1) * 5
                    adjusted_total += surface_adjustment
                    # Distribute adjustment: 100% to assistant (fillings are assistant-heavy)
                    adjusted_assistant += surface_adjustment
                
            elif procedure == 'Crown Preparation':
                # Crown Preparation: Base time + 15 minutes per additional tooth
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 15
                    adjusted_total += teeth_adjustment
                    # Distribute adjustment: 60% to assistant, 40% to overhead
                    adjusted_assistant += teeth_adjustment * 0.6
                    adjusted_overhead += teeth_adjustment * 0.4
                
            elif procedure == 'Crown Delivery':
                # Crown Delivery: Base time + 5 minutes per additional tooth
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 5
                    adjusted_total += teeth_adjustment
                    # Distribute adjustment: 80% to assistant, 20% to overhead
                    adjusted_assistant += teeth_adjustment * 0.8
                    adjusted_overhead += teeth_adjustment * 0.2
                
            elif procedure == 'Root Canal':
                # Root Canal: Base time + 10 minutes per additional surface
                if num_surfaces > 1:
                    surface_adjustment = (num_surfaces - 1) * 10
                    adjusted_total += surface_adjustment
                    # Distribute adjustment: 70% to assistant, 30% to overhead
                    adjusted_assistant += surface_adjustment * 0.7
                    adjusted_overhead += surface_adjustment * 0.3
                
            elif procedure == 'Extraction':
                # Extraction: Base time + 5 minutes per additional tooth
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 5
                    adjusted_total += teeth_adjustment
                    # Distribute adjustment: 60% to assistant, 40% to overhead
                    adjusted_assistant += teeth_adjustment * 0.6
                    adjusted_overhead += teeth_adjustment * 0.4
                
            else:
                # For other procedures, use base times with simple teeth adjustment
                if num_teeth > 1:
                    # Simple adjustment: add 5 minutes per additional tooth
                    teeth_adjustment = (num_teeth - 1) * 5
                    adjusted_total += teeth_adjustment
                    # Distribute adjustment: 70% to assistant, 30% to overhead
                    adjusted_assistant += teeth_adjustment * 0.7
                    adjusted_overhead += teeth_adjustment * 0.3
            
            # Apply 30% reduction for 2nd+ procedures
            procedure_index = len(procedure_details)  # 0-based index
            if procedure_index > 0:  # 2nd procedure and beyond (index 1, 2, 3...)
                # Reduce by 30%
                adjusted_assistant = adjusted_assistant * 0.7
                adjusted_doctor = adjusted_doctor * 0.7
                adjusted_overhead = adjusted_overhead * 0.7
                adjusted_total = adjusted_assistant + adjusted_doctor + adjusted_overhead
            
            # Add to totals
            total_assistant_time += adjusted_assistant
            total_doctor_time += adjusted_doctor
            total_overhead_time += adjusted_overhead
            
            # Store procedure details (don't round here)
            procedure_details.append({
                'procedure': procedure,
                'num_teeth': num_teeth,
                'num_surfaces': num_surfaces,
                'num_quadrants': num_quadrants,
                'base_times': {
                    'assistant_time': base_assistant,
                    'doctor_time': base_doctor,
                    'total_time': base_total
                },
                'adjusted_times': {
                    'assistant_time': adjusted_assistant,
                    'doctor_time': adjusted_doctor,
                    'total_time': adjusted_total
                }
            })
        
        # Calculate base total time
        total_base_time = total_assistant_time + total_doctor_time + total_overhead_time
        
        # Apply mitigating factors to the TOTAL time (once)
        final_assistant_time = total_assistant_time
        final_doctor_time = total_doctor_time
        final_overhead_time = total_overhead_time
        final_total_time = total_base_time
        applied_factors = []
        
        for factor_name in mitigating_factors:
            factor_data = next((f for f in self.mitigating_factors if f['name'] == factor_name), None)
            if factor_data:
                value = factor_data['value']
                if factor_data['is_multiplier']:
                    # Apply multiplier to total time
                    final_total_time *= value
                    # Distribute proportionally to assistant, doctor, and overhead
                    if total_base_time > 0:
                        assistant_ratio = total_assistant_time / total_base_time
                        doctor_ratio = total_doctor_time / total_base_time
                        overhead_ratio = total_overhead_time / total_base_time
                        final_assistant_time = final_total_time * assistant_ratio
                        final_doctor_time = final_total_time * doctor_ratio
                        final_overhead_time = final_total_time * overhead_ratio
                else:
                    # Add time to total
                    final_total_time += value
                    # Add proportionally to assistant, doctor, and overhead
                    if total_base_time > 0:
                        assistant_ratio = total_assistant_time / total_base_time
                        doctor_ratio = total_doctor_time / total_base_time
                        overhead_ratio = total_overhead_time / total_base_time
                        final_assistant_time += value * assistant_ratio
                        final_doctor_time += value * doctor_ratio
                        final_overhead_time += value * overhead_ratio
                
                applied_factors.append({
                    "name": factor_name,
                    "multiplier": value
                })
        
        # FIXED: Round the total time first, then distribute proportionally
        final_total_time_rounded = self.round_to_nearest_10(final_total_time)
        
        # Distribute the rounded total proportionally
        if final_total_time > 0:
            assistant_ratio = final_assistant_time / final_total_time
            doctor_ratio = final_doctor_time / final_total_time
            overhead_ratio = final_overhead_time / final_total_time
            
            final_assistant_time = final_total_time_rounded * assistant_ratio
            final_doctor_time = final_total_time_rounded * doctor_ratio
            final_overhead_time = final_total_time_rounded * overhead_ratio
        else:
            final_assistant_time = 0
            final_doctor_time = 0
            final_overhead_time = 0
        
        # Round individual components
        final_assistant_time = self.round_to_nearest_10(final_assistant_time)
        final_doctor_time = self.round_to_nearest_10(final_doctor_time)
        
        return {
            'base_times': {
                'assistant_time': self.round_to_nearest_10(total_assistant_time),
                'doctor_time': self.round_to_nearest_10(total_doctor_time),
                'total_time': self.round_to_nearest_10(total_base_time)
            },
            'final_times': {
                'assistant_time': final_assistant_time,
                'doctor_time': final_doctor_time,
                'total_time': final_total_time_rounded
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
