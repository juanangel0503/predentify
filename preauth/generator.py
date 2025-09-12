"""
Main Pre-Authorization Generator
"""
from typing import Dict, List, Any
from .models import (
    CaseRecord, PreAuthResult, InsurerType, ProcedureType, 
    ToothSystem, ClinicalFindings, RequiredArtifacts
)
from .nlp_parser import ClinicalNLPParser
from .validator import PreAuthValidator
from .narrative_generator import NarrativeGenerator

class PreAuthGenerator:
    """Main class for generating pre-authorization requests"""
    
    def __init__(self):
        self.parser = ClinicalNLPParser()
        self.validator = PreAuthValidator()
        self.narrative_generator = NarrativeGenerator()
    
    def generate_preauth(self, clinical_text: str, procedure_type: str, 
                        insurer_type: str) -> PreAuthResult:
        """
        Generate complete pre-authorization from clinical text
        
        Args:
            clinical_text: Free-text clinical description
            procedure_type: Type of procedure (CROWN, BRIDGE, etc.)
            insurer_type: Type of insurer (CDCP, PRIVATE)
        
        Returns:
            PreAuthResult with narrative, checklist, and prompts
        """
        
        try:
            # Parse inputs
            procedure = ProcedureType(procedure_type.upper())
            insurer = InsurerType(insurer_type.upper())
            
            # Extract clinical information
            clinical_findings = self.parser.parse_clinical_text(clinical_text, procedure_type)
            tooth_numbers = self.parser._extract_tooth_numbers(clinical_text)
            
            # Create case record
            case_record = CaseRecord(
                insurer=insurer,
                procedure=procedure,
                tooth_numbers=tooth_numbers,
                tooth_system=ToothSystem.FDI,
                clinical_findings=clinical_findings,
                artifacts=RequiredArtifacts(),
                original_text=clinical_text
            )
            
            # Validate case
            validation = self.validator.validate_case(case_record)
            
            # Generate missing info prompts
            missing_prompts = self.validator.get_missing_info_prompts(case_record, validation)
            
            # Generate checklist
            checklist = self._generate_checklist(validation.required_artifacts, case_record)
            
            # Generate narrative (even if validation fails, for preview)
            artifacts_list = [item['name'] for item in checklist]
            narrative = self.narrative_generator.generate_narrative(case_record, artifacts_list)
            
            # Generate policy flags
            policy_flags = validation.warnings
            
            return PreAuthResult(
                success=True,
                narrative=narrative,
                checklist=checklist,
                missing_info_prompts=missing_prompts,
                policy_flags=policy_flags,
                validation=validation,
                case_record=case_record
            )
            
        except Exception as e:
            return PreAuthResult(
                success=False,
                narrative=f"Error generating pre-authorization: {str(e)}",
                checklist=[],
                missing_info_prompts=[],
                policy_flags=[f"Error: {str(e)}"],
                case_record=None
            )
    
    def regenerate_with_edits(self, case_record: CaseRecord, edits: Dict[str, Any]) -> PreAuthResult:
        """
        Regenerate pre-authorization with manual edits
        
        Args:
            case_record: Original case record
            edits: Dictionary of field edits
        
        Returns:
            Updated PreAuthResult
        """
        
        try:
            # Apply edits to case record
            updated_case = self._apply_edits(case_record, edits)
            
            # Re-validate
            validation = self.validator.validate_case(updated_case)
            
            # Regenerate components
            missing_prompts = self.validator.get_missing_info_prompts(updated_case, validation)
            checklist = self._generate_checklist(validation.required_artifacts, updated_case)
            artifacts_list = [item['name'] for item in checklist]
            narrative = self.narrative_generator.generate_narrative(updated_case, artifacts_list)
            
            return PreAuthResult(
                success=True,
                narrative=narrative,
                checklist=checklist,
                missing_info_prompts=missing_prompts,
                policy_flags=validation.warnings,
                validation=validation,
                case_record=updated_case
            )
            
        except Exception as e:
            return PreAuthResult(
                success=False,
                narrative=f"Error regenerating pre-authorization: {str(e)}",
                checklist=[],
                missing_info_prompts=[],
                policy_flags=[f"Error: {str(e)}"],
                case_record=case_record
            )
    
    def _generate_checklist(self, required_artifacts: List[str], case_record: CaseRecord) -> List[Dict[str, Any]]:
        """Generate checklist with checkboxes and upload placeholders"""
        
        checklist = []
        
        # Artifact name mapping
        artifact_names = {
            'periapical_radiograph': 'Periapical Radiograph',
            'bitewing_radiograph': 'Bitewing Radiograph',
            'panoramic': 'Panoramic Radiograph',
            'ceph': 'Cephalometric Radiograph',
            'intraoral_photos': 'Intraoral Photographs',
            'perio_chart': 'Periodontal Chart',
            'study_models_or_scans': 'Study Models or Digital Scans'
        }
        
        for artifact in required_artifacts:
            checklist_item = {
                'id': artifact,
                'name': artifact_names.get(artifact, artifact.replace('_', ' ').title()),
                'required': True,
                'completed': False,
                'file_upload': True,
                'description': self._get_artifact_description(artifact, case_record)
            }
            checklist.append(checklist_item)
        
        # Add procedure-specific items
        procedure_items = self._get_procedure_specific_checklist(case_record)
        checklist.extend(procedure_items)
        
        return checklist
    
    def _get_artifact_description(self, artifact: str, case_record: CaseRecord) -> str:
        """Get description for artifact requirements"""
        
        descriptions = {
            'periapical_radiograph': 'Clear, diagnostic quality periapical radiograph of affected tooth/teeth',
            'bitewing_radiograph': 'Recent bitewing radiographs showing interproximal areas',
            'panoramic': 'Panoramic radiograph showing overall oral condition',
            'ceph': 'Lateral cephalometric radiograph for orthodontic analysis',
            'intraoral_photos': 'Clinical photographs showing current condition',
            'perio_chart': 'Complete periodontal chart with pocket depths and BOP',
            'study_models_or_scans': 'Diagnostic models or digital scans for treatment planning'
        }
        
        return descriptions.get(artifact, 'Required supporting documentation')
    
    def _get_procedure_specific_checklist(self, case_record: CaseRecord) -> List[Dict[str, Any]]:
        """Get procedure-specific checklist items"""
        
        items = []
        
        if case_record.procedure == ProcedureType.CROWN:
            if case_record.clinical_findings.rct_status == "yes":
                items.append({
                    'id': 'rct_report',
                    'name': 'Root Canal Treatment Report',
                    'required': True,
                    'completed': False,
                    'file_upload': True,
                    'description': 'Documentation of completed endodontic treatment'
                })
        
        elif case_record.procedure == ProcedureType.BRIDGE:
            if case_record.clinical_findings.bridge.extraction_dates:
                items.append({
                    'id': 'extraction_records',
                    'name': 'Extraction Records',
                    'required': True,
                    'completed': False,
                    'file_upload': True,
                    'description': 'Documentation of extraction dates and healing'
                })
        
        elif case_record.procedure == ProcedureType.IMPLANT:
            items.append({
                'id': 'surgical_guide',
                'name': 'Surgical Planning (Optional)',
                'required': False,
                'completed': False,
                'file_upload': True,
                'description': 'CBCT or surgical guide if available'
            })
        
        elif case_record.procedure == ProcedureType.ORTHO:
            items.append({
                'id': 'treatment_plan',
                'name': 'Orthodontic Treatment Plan',
                'required': True,
                'completed': False,
                'file_upload': True,
                'description': 'Detailed treatment plan with timeline and objectives'
            })
        
        return items
    
    def _apply_edits(self, case_record: CaseRecord, edits: Dict[str, Any]) -> CaseRecord:
        """Apply manual edits to case record"""
        
        # Create a copy of the case record
        import copy
        updated_case = copy.deepcopy(case_record)
        
        # Apply edits based on field paths
        for field_path, value in edits.items():
            self._set_nested_value(updated_case, field_path, value)
        
        return updated_case
    
    def _set_nested_value(self, obj: Any, field_path: str, value: Any):
        """Set nested attribute value using dot notation"""
        
        attrs = field_path.split('.')
        current_obj = obj
        
        # Navigate to the parent object
        for attr in attrs[:-1]:
            current_obj = getattr(current_obj, attr)
        
        # Set the final attribute
        setattr(current_obj, attrs[-1], value)
    
    def get_supported_procedures(self) -> List[str]:
        """Get list of supported procedure types"""
        return [procedure.value for procedure in ProcedureType]
    
    def get_supported_insurers(self) -> List[str]:
        """Get list of supported insurer types"""
        return [insurer.value for insurer in InsurerType]
