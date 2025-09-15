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
            
            # Build list of all providers with doctors at the top
            all_providers = set()
            for providers_list in self.provider_compatibility.values():
                all_providers.update(providers_list)
            
            # Sort providers with doctors first, then alphabetically
            all_providers_list = list(all_providers)
            doctors = ['Dr. Miekella', 'Dr. Kayla', 'Dr. Radin']
            other_providers = [p for p in all_providers_list if p not in doctors]
            
            # Put doctors at the top, then sort the rest alphabetically
            self.providers = doctors + sorted(other_providers)
            
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
        4. Primary procedures only (exclude secondary-only procedures like Procedure 2 items)
        """
        available = []
        
        for procedure_name, proc_data in self.procedures_data.items():
            # Exclude secondary-only procedures from the main list
            section = proc_data.get('section', 'procedure1')
            if section == 'procedure2':
                continue

            # Check if procedure has valid time data
            if not self._is_valid_procedure_data(proc_data):
                print(f"Skipping {procedure_name}: Invalid time data")
                continue
                
            # Check if at least one provider can perform this procedure
            if procedure_name in self.provider_compatibility:
                providers = self.provider_compatibility[procedure_name]
                if providers and len(providers) > 0:
                    available.append(procedure_name)
                else:
                    print(f"Skipping {procedure_name}: No providers available")
            else:
                print(f"Skipping {procedure_name}: No provider compatibility data")
        
        return sorted(available)

    def _is_valid_procedure_data(self, proc_data: Dict) -> bool:
        """Check if procedure data is valid"""
        try:
            assistant_time = proc_data.get('assistant_time', 0)
            doctor_time = proc_data.get('doctor_time', 0)
            total_time = proc_data.get('total_time', 0)
            
            # Check for NaN or negative values
            if math.isnan(assistant_time) or math.isnan(doctor_time) or math.isnan(total_time):
                return False
            if assistant_time < 0 or doctor_time < 0 or total_time < 0:
                return False
            if total_time == 0:
                return False
                
            return True
        except (TypeError, ValueError):
            return False

    def get_procedures(self) -> List[str]:
        """Get list of available procedures"""
        return self.available_procedures


    def get_procedures2(self) -> List[str]:
        """Get list of procedure 2 items only"""
        procedure2_items = []
        for procedure_name, proc_data in self.procedures_data.items():
            section = proc_data.get('section', 'procedure1')
            if section == 'procedure2':
                procedure2_items.append(procedure_name)
        return sorted(procedure2_items)
    def get_providers(self) -> List[str]:
        """Get list of all providers with doctors at the top"""
        return self.providers

    def get_mitigating_factors(self) -> List[Dict]:
        """Get list of mitigating factors"""
        return self.mitigating_factors

    def check_provider_performs_procedure(self, provider: str, procedure: str) -> bool:
        """Check if a provider can perform a specific procedure"""
        if procedure in self.provider_compatibility:
            return provider in self.provider_compatibility[procedure]
        return True  # Default to True if no compatibility data

    def get_procedure_base_times(self, procedure: str) -> Dict[str, float]:
        # Handle aliases
        if procedure == "Implant":
            procedure = "Implant surgery"
        elif procedure == "Crown":
            procedure = "Crown preparation"
        
        if procedure not in self.procedures_data:
            return {"assistant_time": 0.0, "doctor_time": 0.0, "total_time": 0.0}
        proc_data = self.procedures_data[procedure]
        assistant_time = float(proc_data.get('assistant_time', 0))
        doctor_time = float(proc_data.get('doctor_time', 0))
        total_time = float(proc_data.get('total_time', 0))
        
        # Handle NaN values
        if math.isnan(assistant_time):
            assistant_time = 0.0
        if math.isnan(doctor_time):
            doctor_time = 0.0
        if math.isnan(total_time):
            total_time = 0.0
        
        return {
            'assistant_time': assistant_time,
            'doctor_time': doctor_time,
            'total_time': total_time
        }

    def _calculate_doctor_time_excel_logic(self, procedure: str) -> float:
        """
        Calculate doctor time using Excel logic: use base doctor time only.
        If the base doctor time cell is blank/zero, doctor time is 0.
        """
        base_times = self.get_procedure_base_times(procedure)
        doctor_time = base_times['doctor_time']
        # No fallback to Total - Assistant; Excel uses explicit doctor time
        if math.isnan(doctor_time) or doctor_time < 0:
            return 0.0
        return doctor_time

    def round_to_nearest_10(self, minutes: float) -> int:
        """
        Round to nearest 10 minutes using Excel MROUND behavior
        Excel MROUND rounds .5 away from zero (e.g., 105 → 110, not 100)
        """
        if math.isnan(minutes) or minutes < 0:
            return 0
        
        # Use math.floor with +0.5 to implement "round half away from zero"
        return int(math.floor(minutes / 10 + 0.5) * 10)

    def round_up_to_10(self, minutes: float) -> int:
        """Always round up to the next multiple of 10 (CEILING to 10)."""
        if math.isnan(minutes) or minutes < 0:
            return 0
        return int(math.ceil(minutes / 10.0) * 10)

    def calculate_appointment_time(self, procedures: List[Dict], provider: str, 
                                 mitigating_factors: List[str] = None) -> Dict[str, Any]:
        """
        Calculate appointment time using EXCEL FORMULA LOGIC
        
        FIXED: Time adjustment rule for multiple procedures:
        - First procedure: calculate normally
        - Second and subsequent procedures: reduce by 30%, then round to nearest 10 minutes
        """
        if mitigating_factors is None:
            mitigating_factors = []
            
        total_base_assistant_time = 0.0
        total_base_doctor_time = 0.0
        total_adjusted_time = 0.0
        procedure_details = []
        
        for proc_index, proc_data in enumerate(procedures):
            procedure = proc_data['procedure']
            num_teeth = int(proc_data.get('num_teeth', 1))
            num_surfaces = int(proc_data.get('num_surfaces', 1))
            num_quadrants = int(proc_data.get('num_quadrants', 1))
            
            # Get base times from procedure data (Metadata2 equivalent)
            base_times = self.get_procedure_base_times(procedure)
            base_assistant = base_times['assistant_time']
            base_doctor = base_times['doctor_time']
            base_total = base_times['total_time']
            
            # Calculate doctor time using Excel formula logic (no fallback)
            excel_doctor_time = self._calculate_doctor_time_excel_logic(procedure)
            
            # Start with base total time
            adjusted_total = base_total
            
            # Apply teeth/surfaces/quadrants adjustments to TOTAL TIME ONLY
            if procedure == 'Implant surgery' or procedure == 'Implant':  # alias for safety
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 10
                    adjusted_total += teeth_adjustment
                
            elif procedure == 'Filling':
                if num_surfaces > 1:
                    surface_adjustment = (num_surfaces - 1) * 5
                    adjusted_total += surface_adjustment
                
            elif procedure == 'Crown preparation' or procedure == 'Crown':
                # Crown preparation: Base time + 30 minutes per additional tooth (FIXED)
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 30
                    adjusted_total += teeth_adjustment
                
            elif procedure == 'Crown Delivery':
                # Crown Delivery: Base time + 10 minutes per additional tooth (FIXED)
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 10
                    adjusted_total += teeth_adjustment
                
            elif procedure == 'Root Canal':
                if num_surfaces > 1:
                    surface_adjustment = (num_surfaces - 1) * 10
                    adjusted_total += surface_adjustment
                
            elif procedure == 'Extraction':
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 5
                    adjusted_total += teeth_adjustment
                
            else:
                # For other procedures, use base times with simple teeth adjustment
                if num_teeth > 1:
                    teeth_adjustment = (num_teeth - 1) * 5
                    adjusted_total += teeth_adjustment
            
            # FIXED: Apply 30% reduction for 2nd+ procedures (per procedure, not total)
            # This reduction is applied to the procedure's own calculated time
            # EXCEPTION: Sedation should not have 30% reduction applied
            if proc_index > 0 and procedure != "Sedation":  # Second procedure and beyond, but not Sedation
                # Reduce by 30% (multiply by 0.7)
                adjusted_total = adjusted_total * 0.7
                print(f"Applied 30% reduction to procedure {proc_index + 1} ({procedure}): {adjusted_total / 0.7:.1f} → {adjusted_total:.1f}")
                print(f"Applied 30% reduction to procedure {proc_index + 1} ({procedure}): {adjusted_total / 0.7:.1f} → {adjusted_total:.1f}")
            
            # Add to totals
            total_base_assistant_time += base_assistant
            total_base_doctor_time += excel_doctor_time
            total_adjusted_time += adjusted_total
            
            # Store procedure details
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
                    'assistant_time': base_assistant,
                    'doctor_time': excel_doctor_time,
                    'total_time': adjusted_total
                }
            })
        
        # Apply mitigating factors to the TOTAL ADJUSTED TIME (once)
        final_total_time = total_adjusted_time
        applied_factors = []
        
        for factor_name in mitigating_factors:
            factor_data = next((f for f in self.mitigating_factors if f['name'] == factor_name), None)
            if factor_data:
                value = factor_data['value']
                if factor_data['is_multiplier']:
                    # Apply multiplier to total time
                    final_total_time *= value
                else:
                    # Add time to total
                    final_total_time += value
                
                applied_factors.append({
                    "name": factor_name,
                    "multiplier": value
                })
        
        # Calculate final times BEFORE rounding
        final_assistant_time = total_base_assistant_time
        final_doctor_time = total_base_doctor_time
        
        # Always round up to next 10 minutes (like CEILING function)
        final_total_time_rounded = self.round_up_to_10(final_total_time)
        
        return {
            'base_times': {
                'assistant_time': total_base_assistant_time,
                'doctor_time': total_base_doctor_time,
                'total_time': total_adjusted_time
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
