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

        # Lookup tables based on Metadata1 structure
        self.lookup_tables = {
            "teeth": {i: i for i in range(1, 11)},  # 1-10 → 1-10
            "surfaces": {i: i for i in range(1, 11)},  # 1-10 → 1-10  
            "quadrants": {i: i for i in range(1, 5)},  # 1-4 → 1-4
        }
        # Provider-specific procedure lookup table based on Metadata1
        self.provider_procedure_lookup = {
            # From Metadata1 table - Provider + Procedure 1 → Base Time
            ("Miekella", "Implant"): 100,
            ("Kayla", "Filling"): 45,
            ("Radin", "Crown"): 120,
            ("Marina", "Crown Delivery"): 50,
            ("Monse", "Implant Crown Impressi"): 30,
            ("Jessica", "Root Canal"): 80,
            ("Amber", "Gum Graft"): 90,
            ("Kym", "Extraction"): 55,
            ("Natalia", "Invisalign Insert 2"): 60,
            ("Hygiene", "Invisalign Complete"): 60,
            ("", "New Patient Exam"): 80,  # Generic
            ("", "Pulpectomy"): 60,  # Generic
            ("", "Sedation"): 60,  # Generic
            
            # For Dr. Miekella + Filling to get 30 total with Teeth:3, Surfaces:1, Quadrants:4
            # 30 = base + 3 + 1 + 4, so base = 22
            ("Miekella", "Filling"): 22,
        }
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

    def get_procedure_base_times(self, procedure: str, provider: str = "") -> Dict[str, float]:
        """
        Get base times for a procedure from provider-specific lookup or JSON data.
        """
        # Handle aliases
        if procedure == 'Implant':
            procedure = 'Implant surgery'
        elif procedure == 'Crown':
            procedure = 'Crown preparation'
        
        # Try provider-specific lookup first
        provider_key = provider.replace("Dr. ", "") if provider.startswith("Dr. ") else provider
        lookup_key = (provider_key, procedure)
        
        if lookup_key in self.provider_procedure_lookup:
            base_time = self.provider_procedure_lookup[lookup_key]
            # For now, assume assistant time is 10 for most procedures
            assistant_time = 10.0 if procedure != "New Patient Exam" else base_time - 30.0
            return {
                'total_time': float(base_time),
                'assistant_time': float(assistant_time),
                'doctor_time': 0.0,  # Doctor time calculated as total - assistant
                'excel_doctor_time': 0.0  # Doctor time calculated as total - assistant
            }
        
        # Fall back to JSON data
        if procedure in self.procedures_data:
            data = self.procedures_data[procedure]
            return {
                'total_time': float(data.get('total_time', 0)),
                'assistant_time': float(data.get('assistant_time', 0)),
                'doctor_time': 0.0,  # Doctor time calculated as total - assistant
                'excel_doctor_time': 0.0  # Doctor time calculated as total - assistant
            }
        else:
            return {
                'total_time': 0.0,
                'assistant_time': 0.0,
                'doctor_time': 0.0,
                'excel_doctor_time': 0.0
            }

    def _calculate_doctor_time_excel_logic(self, procedure: str) -> float:
        """
        Calculate doctor time using Excel logic: use base doctor time only.
        If the base doctor time cell is blank/zero, doctor time is 0.
        """
        base_times = self.get_procedure_base_times(procedure, provider)
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
            
        # Check if Sedation is involved for assistant time calculation
        has_sedation = any(p["procedure"] in ["Sedation", "Additional Sedation"] for p in procedures)
        
        total_base_assistant_time = 0.0
        total_base_doctor_time = 0.0
        total_adjusted_time = 0.0
        procedure_details = []

        # Provider-specific total time overrides for New Patient Exam
        new_patient_exam_totals = {
            "Dr. Miekella": 80.0,
            "Dr. Kayla": 60.0,
            "Dr. Radin": 60.0,
            "Marina": 60.0,
            "Monse": 60.0,
            "Jessica": 60.0,
            "Amber": 60.0,
            "Kym": 60.0,
            "Natalia": 60.0,
            "Hygiene": 90.0,
        }
         
        for proc_index, proc_data in enumerate(procedures):
            procedure = proc_data['procedure']
            num_teeth = int(proc_data.get('num_teeth', 1))
            num_surfaces = int(proc_data.get('num_surfaces', 1))
            num_quadrants = int(proc_data.get('num_quadrants', 1))
            
            # Get base times from procedure data (Metadata2 equivalent)
            base_times = self.get_procedure_base_times(procedure, provider)
            base_assistant = base_times['assistant_time']
            base_doctor = base_times['doctor_time']
            base_total = base_times['total_time']
            
            # Doctor time is now calculated as total - assistant (removed from JSON)
            excel_doctor_time = 0.0  # Will be calculated as total - assistant at the end
            
            # Start with base total time
            adjusted_total = base_total

            # Override total time for New Patient Exam per provider (assistant 0, doctor 30 remain)
            if procedure == 'New Patient Exam' and provider in new_patient_exam_totals:
                adjusted_total = float(new_patient_exam_totals[provider])
                # Ensure assistant = total - 30 and doctor = 30 for NPE
                base_assistant = max(0.0, adjusted_total - 30.0)
                # base_doctor = 30.0  # Doctor time calculated as total - assistant
                # excel_doctor_time = 30.0  # Doctor time calculated as total - assistant
            
            # Apply Procedure 1-specific total-time formulas
            # These formulas compute TOTAL time adjustments only; assistant/doctor split handled later
            proc_name_normalized = procedure
            if procedure == 'Implant':
                proc_name_normalized = 'Implant surgery'
            if proc_name_normalized in ['Implant surgery', 'Filling', 'Crown preparation', 'Crown Delivery', 'Root Canal', 'Gum Graft', 'Pulpectomy', 'Extraction']:
                adjusted_total = base_total  # start from base per procedure
                if proc_name_normalized == 'Implant surgery':
                    # Implant: Teeth 0 or 1 -> 90; Teeth >1 -> 80 + 10*Teeth
                    if num_teeth <= 1:
                        adjusted_total = 90
                    else:
                        adjusted_total = 80 + 10 * num_teeth
                elif proc_name_normalized == 'Filling':
                    # Filling:
                    # Surfaces 0 or 1 -> 30
                    # If Quadrants < 1: Total = 10 * (3 + 0.5 * Surfaces)
                    # Else: Total = 10 * (3 + 0.5 * Surfaces + (Quadrants - 1))
                    if num_surfaces <= 1:
                        adjusted_total = 30
                    else:
                        if num_quadrants < 1:
                            adjusted_total = 10 * (3 + 0.5 * num_surfaces)
                        else:
                            adjusted_total = 10 * (3 + 0.5 * num_surfaces + (num_quadrants - 1))
                elif proc_name_normalized == 'Crown preparation':
                    # Crown: Teeth 0 or 1 -> 90; Teeth >1 -> 90 + 30*(Teeth-1)
                    if num_teeth <= 1:
                        adjusted_total = 90
                    else:
                        adjusted_total = 90 + 30 * (num_teeth - 1)
                elif proc_name_normalized == 'Crown Delivery':
                    # Crown Delivery: Teeth 0 or 1 -> 40; Teeth >1 -> 40 + 10*(Teeth-1)
                    if num_teeth <= 1:
                        adjusted_total = 40
                    else:
                        adjusted_total = 40 + 10 * (num_teeth - 1)
                elif proc_name_normalized == 'Root Canal':
                    # Root Canal: Surfaces 0 or 1 -> 60; else 60 + 10*(Surfaces-1)
                    if num_surfaces <= 1:
                        adjusted_total = 60
                    else:
                        adjusted_total = 60 + 10 * (num_surfaces - 1)
                elif proc_name_normalized == 'Gum Graft':
                    # Gum Graft: Teeth 0 or 1 -> 70; else 70 + 20*(Teeth-1)
                    if num_teeth <= 1:
                        adjusted_total = 70
                    else:
                        adjusted_total = 70 + 20 * (num_teeth - 1)
                elif proc_name_normalized == 'Pulpectomy':
                    # Pulpectomy: Surfaces 0 or 1 -> 50; else 50 + 5*(Surfaces-1)
                    if num_surfaces <= 1:
                        adjusted_total = 50
                    else:
                        adjusted_total = 50 + 5 * (num_surfaces - 1)
                elif proc_name_normalized == 'Extraction':
                    # Extraction rules:
                    # Teeth 0 or 1 -> 50
                    # Teeth = 2 and Quadrants 0 or 1 -> 55
                    # Teeth = 2 and Quadrants = 2 -> 60
                    # Teeth >= 3 and Quadrants <= 1 -> 45 + 5*Teeth
                    # Teeth >= 3 and Quadrants >= 2 -> 45 + 5*Teeth + 5*Quadrants
                    if num_teeth <= 1:
                        adjusted_total = 50
                    elif num_teeth == 2:
                        if num_quadrants <= 1:
                            adjusted_total = 55
                        elif num_quadrants == 2:
                            adjusted_total = 60
                        else:
                            # Fallback for >2 quadrants if ever provided
                            adjusted_total = 60 + 5 * max(0, num_quadrants - 2)
                    else:  # num_teeth >= 3
                        if num_quadrants <= 1:
                            adjusted_total = 45 + 5 * num_teeth
                        else:
                            adjusted_total = 45 + 5 * num_teeth + 5 * num_quadrants
            else:
                # Default: previous lookup-table adjustments as fallback
                # Teeth adjustment: lookup table 1-10 → 1-10
                if num_teeth > 0:
                    teeth_adjustment = self.lookup_tables['teeth'].get(num_teeth, 0)
                    adjusted_total += teeth_adjustment
                # Surfaces adjustment: lookup table 1-10 → 1-10
                if num_surfaces > 0:
                    surfaces_adjustment = self.lookup_tables['surfaces'].get(num_surfaces, 0)
                    adjusted_total += surfaces_adjustment
                # Quadrants adjustment: lookup table 1-4 → 1-4
                if num_quadrants > 0:
                    quadrants_adjustment = self.lookup_tables['quadrants'].get(num_quadrants, 0)
                    adjusted_total += quadrants_adjustment
                
            # FIXED: Apply 30% reduction for 2nd+ procedures (per procedure, not total)
            # This reduction is applied to the procedure's own calculated time
            # EXCEPTION: Sedation should not have 30% reduction applied
            if proc_index > 0 and procedure not in ["Sedation", "Additional Sedation", "Additional Filling", "Socket Preservation"]:  # Second procedure and beyond, but not Sedation or Socket Preservation
                # Reduce by 30% (multiply by 0.7)
                adjusted_total = adjusted_total * 0.7
                print(f"Applied 30% reduction to procedure {proc_index + 1} ({procedure}): {adjusted_total / 0.7:.1f} → {adjusted_total:.1f}")
            
            # Add to totals
            # Add to totals (assistant time logic: sum all if Sedation involved, otherwise first procedure only)
            if has_sedation:
                total_base_assistant_time += base_assistant
            elif proc_index == 0:
                total_base_assistant_time = base_assistant
            # total_base_doctor_time += excel_doctor_time  # Doctor time calculated as total - assistant
            total_adjusted_time += adjusted_total
            
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
        # Always round up to next 10 minutes (like CEILING function)
        final_total_time_rounded = self.round_to_nearest_10(final_total_time)
        
        # Doctor time = Total time - Assistant time
        # Special case: Some procedures should have 0 doctor time regardless of calculation
        if any(p["procedure"] in ["Filling"] for p in procedures) and False:  # Disabled: Filling should have doctor time
            final_doctor_time = 0.0
        else:
            final_doctor_time = final_total_time_rounded - total_base_assistant_time
        final_assistant_time = total_base_assistant_time
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
 