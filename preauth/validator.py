"""
Validation engine for pre-authorization requests
"""
from typing import List, Dict, Any
from .models import CaseRecord, ValidationResult, ProcedureType, InsurerType
from .config import INSURER_CONFIGS, VALIDATION_RULES

class PreAuthValidator:
    """Validates pre-authorization requests against insurer requirements"""
    
    def __init__(self):
        self.configs = INSURER_CONFIGS
        self.rules = VALIDATION_RULES
    
    def validate_case(self, case_record: CaseRecord) -> ValidationResult:
        """Validate a case record against insurer and procedure requirements"""
        
        missing_fields = []
        warnings = []
        required_artifacts = []
        
        # Get insurer configuration
        insurer_config = self.configs.get(case_record.insurer, {})
        procedure_config = insurer_config.get(case_record.procedure, {})
        
        # If no specific config, use defaults for private insurance
        if not procedure_config and case_record.insurer == InsurerType.PRIVATE:
            procedure_config = insurer_config.get("defaults", {})
        
        # Validate required fields
        required_fields = procedure_config.get("required_fields", [])
        for field_path in required_fields:
            if not self._get_nested_value(case_record, field_path):
                missing_fields.append(self._format_field_name(field_path))
        
        # Check replacement-specific requirements
        if self._is_replacement_procedure(case_record):
            replacement_fields = procedure_config.get("replacement_required_fields", [])
            for field_path in replacement_fields:
                if not self._get_nested_value(case_record, field_path):
                    missing_fields.append(self._format_field_name(field_path))
        
        # Get required artifacts
        required_artifacts = procedure_config.get("checklist", [])
        
        # Apply procedure-specific validation rules
        procedure_warnings = self._apply_procedure_rules(case_record)
        warnings.extend(procedure_warnings)
        
        # Check for policy flags
        policy_flags = self._check_policy_flags(case_record)
        warnings.extend(policy_flags)
        
        is_valid = len(missing_fields) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            missing_fields=missing_fields,
            warnings=warnings,
            required_artifacts=required_artifacts
        )
    
    def get_missing_info_prompts(self, case_record: CaseRecord, validation: ValidationResult) -> List[str]:
        """Generate prompts for missing information"""
        prompts = []
        
        # Get procedure-specific prompts
        procedure_rules = self.rules.get(case_record.procedure, {})
        base_prompts = procedure_rules.get("prompts", [])
        
        # Map missing fields to specific prompts
        field_prompt_map = {
            "existing_crown_age_years": "Age of existing crown in years",
            "rct_status": "Please confirm RCT status for this tooth",
            "missing_teeth_total_mouth": "Total number of missing teeth in mouth",
            "extraction_date_site": "Extraction date for implant site",
            "perio_diagnosis": "Periodontal diagnosis (stage/grade)",
            "bop_percent": "Bleeding on probing percentage",
            "malocclusion": "Bite classification and malocclusion type",
            "crowding_mm": "Crowding measurement in millimeters",
            "overjet_mm": "Overjet measurement in millimeters",
            "overbite_percent": "Overbite percentage"
        }
        
        # Add specific prompts for missing fields
        for missing_field in validation.missing_fields:
            field_key = missing_field.lower().replace(" ", "_")
            if field_key in field_prompt_map:
                prompts.append(field_prompt_map[field_key])
        
        # Add general prompts based on procedure
        if case_record.procedure in [ProcedureType.ONLAY, ProcedureType.VENEER]:
            if not case_record.clinical_findings.fracture_present:
                prompts.append("Evidence of structural loss or fracture lines")
        
        if case_record.procedure == ProcedureType.CROWN:
            if self._is_replacement_procedure(case_record) and not case_record.clinical_findings.existing_crown_age_years:
                prompts.append("Age of existing crown in years")
        
        return list(set(prompts))  # Remove duplicates
    
    def _get_nested_value(self, obj: Any, field_path: str) -> Any:
        """Get nested attribute value using dot notation"""
        try:
            value = obj
            for attr in field_path.split('.'):
                value = getattr(value, attr)
            return value
        except (AttributeError, TypeError):
            return None
    
    def _format_field_name(self, field_path: str) -> str:
        """Format field path into readable name"""
        parts = field_path.split('.')
        last_part = parts[-1]
        
        # Convert snake_case to Title Case
        formatted = last_part.replace('_', ' ').title()
        
        # Handle special cases
        replacements = {
            'Rct Status': 'RCT Status',
            'Bop Percent': 'BOP Percentage',
            'Existing Crown Age Years': 'Existing Crown Age (Years)',
            'Missing Teeth Total Mouth': 'Total Missing Teeth in Mouth',
            'Extraction Date Site': 'Extraction Date for Site'
        }
        
        return replacements.get(formatted, formatted)
    
    def _is_replacement_procedure(self, case_record: CaseRecord) -> bool:
        """Check if this is a replacement procedure"""
        if case_record.procedure == ProcedureType.CROWN:
            return case_record.clinical_findings.restoration_type_existing == "crown"
        elif case_record.procedure == ProcedureType.BRIDGE:
            return case_record.clinical_findings.bridge.is_replacement
        return False
    
    def _apply_procedure_rules(self, case_record: CaseRecord) -> List[str]:
        """Apply procedure-specific validation rules"""
        warnings = []
        
        if case_record.procedure == ProcedureType.CROWN:
            # Flag aesthetics-only rationale
            if not case_record.clinical_findings.fracture_present and \
               not case_record.clinical_findings.caries_present and \
               not case_record.clinical_findings.wear_present:
                warnings.append("Consider providing clinical justification beyond aesthetics")
        
        elif case_record.procedure in [ProcedureType.ONLAY, ProcedureType.VENEER]:
            # Flag cosmetic-only justifications
            if not case_record.clinical_findings.fracture_present and \
               not case_record.clinical_findings.caries_present:
                warnings.append("Cosmetic-only justifications may not be covered")
        
        elif case_record.procedure == ProcedureType.IMPLANT:
            # Check if plan might exclude implants
            warnings.append("Verify implant coverage under patient's plan")
        
        return warnings
    
    def _check_policy_flags(self, case_record: CaseRecord) -> List[str]:
        """Check for policy-related flags"""
        flags = []
        
        # General exclusion warnings
        if case_record.procedure in [ProcedureType.ONLAY, ProcedureType.VENEER]:
            flags.append("Ensure treatment is not purely cosmetic")
        
        if case_record.procedure == ProcedureType.IMPLANT:
            flags.append("Confirm implant coverage and limitations")
        
        return flags
