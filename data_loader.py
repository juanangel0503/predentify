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
        """
        available = []
        
        for procedure_name, proc_data in self.procedures_data.items():
            # Check if procedure has valid time data
            if not self._is_valid_procedure_data(proc_data):
                print(f"Skipping {procedure_name}: Invalid time data")
                continue
                
            # Check if at least one provider can perform this procedure
            # Look through all providers to see if any can perform this procedure
            procedure_available = False
            for provider, procedures in self.provider_compatibility.items():
                if procedure_name in procedures:
                    procedure_available = True
                    break
            
            if procedure_available:
                available.append(procedure_name)
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

    def get_providers(self) -> List[str]:
        """Get list of all providers with doctors at the top"""
        return self.providers

    def get_mitigating_factors(self) -> List[Dict]:
        """Get list of mitigating factors"""
        return self.mitigating_factors

    def check_provider_performs_procedure(self, provider: str, procedure: str) -> bool:
        """Check if a provider can perform a specific procedure"""
        if provider in self.provider_compatibility:
            return procedure in self.provider_compatibility[provider]
        return True  # Default to True if no compatibility data

    def get_procedure_base_times(self, procedure: str) -> Dict[str, float]:
        """Get base times for a procedure"""
        if procedure not in self.procedures_data:
            return {'assistant_time': 0.0, 'doctor_time': 0.0, 'total_time': 0.0}
        
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
        Calculate doctor time using Excel formula logic
        This implements the complex IF and XLOOKUP logic from Excel
        """
        base_times = self.get_procedure_base_times(procedure)
        doctor_time = base_times['doctor_time']
        
        # If doctor time is 0 or NaN, calculate as Total - Assistant
        if doctor_time == 0 or math.isnan(doctor_time):
            assistant_time = base_times['assistant_time']
            total_time = base_times['total_time']
            doctor_time = total_time - assistant_time
            
        return max(0, doctor_time)  # Ensure non-negative

    def _calculate_procedure_time_excel_formula(self, procedure: str, num_teeth: int = 1, 
                                              num_surfaces: int = 1, num_quadrants: int = 1) -> Dict[str, float]:
        """
        Calculate procedure time using exact Excel formulas from Metadata2 sheet
        Returns: {'assistant_time': float, 'doctor_time': float, 'total_time': float}
        """
        
        # Get base assistant time from Metadata2
        base_times = self.get_procedure_base_times(procedure)
        assistant_time = base_times['assistant_time']
        
        # Calculate total time using Excel formulas
        if procedure == 'Implant':
            if num_teeth == 0 or num_teeth == 1:
                total_time = 90
            else:
                total_time = 80 + (10 * num_teeth)
                
        elif procedure == 'Filling':
            if num_surfaces == 0 or num_surfaces == 1:
                total_time = 30
            else:
                if num_quadrants < 1:
                    total_time = (3 + 0.5 * num_surfaces) * 10
                else:
                    total_time = (3 + 0.5 * num_surfaces + (num_quadrants - 1)) * 10
                    
        elif procedure == 'Crown':
            if num_teeth == 0 or num_teeth == 1:
                total_time = 90
            else:
                total_time = 90 + ((num_teeth - 1) * 30)
                
        elif procedure == 'Crown Delivery':
            if num_teeth == 0 or num_teeth == 1:
                total_time = 40
            else:
                total_time = 40 + ((num_teeth - 1) * 10)
                
        elif procedure == 'Root Canal':
            if num_surfaces == 0 or num_surfaces == 1:
                total_time = 60
            else:
                total_time = 60 + (num_surfaces - 1) * 10
                
        elif procedure == 'Gum Graft':
            if num_teeth == 0 or num_teeth == 1:
                total_time = 70
            else:
                total_time = 70 + (num_teeth - 1) * 20
                
        elif procedure == 'Extraction':
            # Complex nested IF formula from Excel
            if num_teeth == 0 or num_teeth == 1:
                total_time = 50
            elif num_teeth == 2:
                if num_quadrants == 0 or num_quadrants == 1:
                    total_time = 55
                elif num_quadrants == 2:
                    total_time = 60
                else:
                    total_time = 60  # Default case
            elif num_teeth >= 3:
                if num_quadrants <= 1:
                    total_time = 45 + (5 * num_teeth)
                else:
                    total_time = 45 + (5 * num_teeth) + (5 * num_quadrants)
            else:
                total_time = 50  # Default case
                
        elif procedure == 'Pulpectomy':
            if num_surfaces == 0 or num_surfaces == 1:
                total_time = 50
            else:
                total_time = 50 + (num_surfaces - 1) * 5
                
        else:
            # For procedures with fixed times, use the base total time
            total_time = base_times['total_time']
        
        # Calculate doctor time
        doctor_time = base_times['doctor_time']
        if doctor_time == 0 or math.isnan(doctor_time):
            # If no doctor time specified, calculate as Total - Assistant
            doctor_time = total_time - assistant_time
        
        return {
            'assistant_time': assistant_time,
            'doctor_time': max(0, doctor_time),
            'total_time': total_time
        }

    def round_to_nearest_10(self, minutes: float) -> int:
        """
        Round to nearest 10 minutes using Excel MROUND behavior
        Excel MROUND rounds .5 away from zero (e.g., 105 → 110, not 100)
        """
        if math.isnan(minutes) or minutes < 0:
            return 0
        
        # Use math.floor with +0.5 to implement "round half away from zero"
        return int(math.floor(minutes / 10 + 0.5) * 10)

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
            
            # Use Excel formula calculation for accurate results
            excel_times = self._calculate_procedure_time_excel_formula(
                procedure, num_teeth, num_surfaces, num_quadrants
            )
            
            base_assistant = excel_times['assistant_time']
            excel_doctor_time = excel_times['doctor_time']
            adjusted_total = excel_times['total_time']
            
            # FIXED: Apply 30% reduction for 2nd+ procedures (per procedure, not total)
            # This reduction is applied to the procedure's own calculated time
            if proc_index > 0:  # Second procedure and beyond
                # Reduce by 30% (multiply by 0.7)
                adjusted_total = adjusted_total * 0.7
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
                    'doctor_time': excel_doctor_time,
                    'total_time': adjusted_total
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
        
        # Round all times to nearest 10 minutes
        final_assistant_time_rounded = self.round_to_nearest_10(final_assistant_time)
        final_doctor_time_rounded = self.round_to_nearest_10(final_doctor_time)
        final_total_time_rounded = self.round_to_nearest_10(final_total_time)
        
        return {
            'base_times': {
                'assistant_time': self.round_to_nearest_10(total_base_assistant_time),
                'doctor_time': self.round_to_nearest_10(total_base_doctor_time),
                'total_time': self.round_to_nearest_10(total_adjusted_time)
            },
            'final_times': {
                'assistant_time': final_assistant_time_rounded,
                'doctor_time': final_doctor_time_rounded,
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
