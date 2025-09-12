"""
Narrative generator for insurer-specific pre-authorization descriptions
"""
from typing import Dict, List, Any
from .models import CaseRecord, ProcedureType, InsurerType
from .config import NARRATIVE_TEMPLATES

class NarrativeGenerator:
    """Generates insurer-specific narrative descriptions"""
    
    def __init__(self):
        self.templates = NARRATIVE_TEMPLATES
    
    def generate_narrative(self, case_record: CaseRecord, artifacts: List[str]) -> str:
        """Generate insurer-specific narrative description"""
        
        if case_record.insurer == InsurerType.CDCP:
            return self._generate_cdcp_narrative(case_record, artifacts)
        else:
            return self._generate_private_narrative(case_record, artifacts)
    
    def _generate_cdcp_narrative(self, case_record: CaseRecord, artifacts: List[str]) -> str:
        """Generate CDCP-specific narrative"""
        
        templates = self.templates.get(InsurerType.CDCP, {})
        procedure_templates = templates.get(case_record.procedure, {})
        
        if case_record.procedure == ProcedureType.CROWN:
            return self._generate_crown_narrative(case_record, procedure_templates, artifacts)
        elif case_record.procedure == ProcedureType.BRIDGE:
            return self._generate_bridge_narrative(case_record, procedure_templates, artifacts)
        elif case_record.procedure == ProcedureType.IMPLANT:
            return self._generate_implant_narrative(case_record, procedure_templates, artifacts)
        elif case_record.procedure == ProcedureType.ORTHO:
            return self._generate_ortho_narrative(case_record, artifacts)
        elif case_record.procedure == ProcedureType.ADDITIONAL_SCALING:
            return self._generate_scaling_narrative(case_record, artifacts)
        elif case_record.procedure in [ProcedureType.ONLAY, ProcedureType.VENEER]:
            return self._generate_aesthetic_narrative(case_record, artifacts)
        
        return self._generate_generic_narrative(case_record, artifacts)
    
    def _generate_private_narrative(self, case_record: CaseRecord, artifacts: List[str]) -> str:
        """Generate private insurance narrative (brief, functional)"""
        
        procedure_name = case_record.procedure.value.lower().replace('_', ' ')
        tooth_info = self._format_tooth_numbers(case_record.tooth_numbers)
        
        # Key clinical findings
        key_findings = self._get_key_clinical_findings(case_record)
        
        # Build narrative
        narrative = f"Authorization requested for {procedure_name} on {tooth_info} due to clinical necessity. "
        
        if key_findings:
            narrative += f"{key_findings} "
        
        narrative += "Treatment is indicated to restore function."
        
        if artifacts:
            narrative += f" Supporting documentation attached: {', '.join(artifacts)}."
        
        return narrative
    
    def _generate_crown_narrative(self, case_record: CaseRecord, templates: Dict, artifacts: List[str]) -> str:
        """Generate crown-specific narrative"""
        
        tooth_numbers = self._format_tooth_numbers(case_record.tooth_numbers)
        findings = case_record.clinical_findings
        
        # Check if replacement
        if findings.restoration_type_existing == "crown" and templates.get("replacement_template"):
            template = templates["replacement_template"]
            
            # Build replacement narrative
            material = findings.existing_crown_material or "unknown material"
            age = findings.existing_crown_age_years or "unknown"
            
            clinical_findings = []
            if findings.caries_present:
                clinical_findings.append(f"{findings.caries_present} caries")
            if findings.fracture_present:
                clinical_findings.append("documented fracture line")
            if findings.surfaces_involved:
                surfaces = "/".join(findings.surfaces_involved)
                clinical_findings.append(f"{surfaces} surfaces involved")
            
            findings_text = ", ".join(clinical_findings) if clinical_findings else "structural compromise"
            
            rct_status = "Tooth is endodontically treated." if findings.rct_status == "yes" else ""
            
            artifacts_text = ", ".join(artifacts) if artifacts else "supporting documentation"
            
            narrative = template.format(
                tooth=tooth_numbers,
                reason="structural compromise",
                material=material,
                age=age,
                findings=findings_text,
                rct_status=rct_status,
                artifacts=artifacts_text
            )
        
        else:
            # New crown narrative
            template = templates.get("template", "")
            
            reason = self._determine_crown_reason(findings)
            clinical_findings_text = self._build_clinical_findings_text(findings)
            
            artifacts_text = ", ".join(artifacts) if artifacts else "supporting documentation"
            
            narrative = template.format(
                action="place",
                tooth=tooth_numbers,
                reason=reason,
                clinical_findings=clinical_findings_text,
                history="",
                purpose="restore function and prevent further breakdown",
                artifacts=artifacts_text
            )
        
        return narrative
    
    def _generate_bridge_narrative(self, case_record: CaseRecord, templates: Dict, artifacts: List[str]) -> str:
        """Generate bridge-specific narrative"""
        
        template = templates.get("template", "")
        bridge_findings = case_record.clinical_findings.bridge
        
        action = "replace" if bridge_findings.is_replacement else "place"
        span = bridge_findings.span_site or "affected area"
        
        # Abutment condition
        abutment_condition = "Abutment teeth are in good condition."
        if case_record.clinical_findings.rct_status == "yes":
            abutment_condition = "Abutment teeth are endodontically treated and stable."
        
        # Extraction history
        extraction_history = ""
        if bridge_findings.extraction_dates:
            dates = list(bridge_findings.extraction_dates.values())
            extraction_history = f"Extraction completed on {dates[0]}."
        
        # Missing teeth info
        missing_count = bridge_findings.missing_teeth_total_mouth or 0
        missing_teeth_info = f"Patient currently has {missing_count} missing teeth total."
        
        artifacts_text = ", ".join(artifacts) if artifacts else "supporting documentation"
        
        narrative = template.format(
            action=action,
            span=span,
            reason="restore function and prevent further complications",
            abutment_condition=abutment_condition,
            extraction_history=extraction_history,
            missing_teeth_info=missing_teeth_info,
            artifacts=artifacts_text
        )
        
        return narrative
    
    def _generate_implant_narrative(self, case_record: CaseRecord, templates: Dict, artifacts: List[str]) -> str:
        """Generate implant-specific narrative"""
        
        template = templates.get("template", "")
        implant_findings = case_record.clinical_findings.implant
        
        site = implant_findings.site or "affected site"
        
        # Extraction info
        extraction_info = ""
        if implant_findings.extraction_date_site:
            extraction_info = f"Site was extracted on {implant_findings.extraction_date_site}."
        
        # Bone condition
        bone_condition = ""
        if implant_findings.bone_graft_history == "yes":
            bone_condition = "Bone graft was previously completed. "
        bone_condition += "Adequate bone volume present for implant placement."
        
        missing_count = implant_findings.missing_teeth_total_mouth or 1
        
        artifacts_text = ", ".join(artifacts) if artifacts else "supporting documentation"
        
        narrative = template.format(
            site=site,
            extraction_info=extraction_info,
            bone_condition=bone_condition,
            missing_count=missing_count,
            artifacts=artifacts_text
        )
        
        return narrative
    
    def _generate_ortho_narrative(self, case_record: CaseRecord, artifacts: List[str]) -> str:
        """Generate orthodontic narrative"""
        
        ortho_findings = case_record.clinical_findings.ortho
        
        # Build clinical findings
        findings = []
        if ortho_findings.crowding_mm:
            findings.append(f"{ortho_findings.crowding_mm}mm crowding")
        if ortho_findings.spacing_mm:
            findings.append(f"{ortho_findings.spacing_mm}mm spacing")
        if ortho_findings.malocclusion:
            findings.append(ortho_findings.malocclusion)
        if ortho_findings.overjet_mm:
            findings.append(f"{ortho_findings.overjet_mm}mm overjet")
        if ortho_findings.overbite_percent:
            findings.append(f"{ortho_findings.overbite_percent}% overbite")
        
        findings_text = ", ".join(findings) if findings else "malocclusion"
        
        artifacts_text = ", ".join(artifacts) if artifacts else "supporting documentation"
        
        narrative = f"Requesting authorization for orthodontic treatment. Patient presents with {findings_text}. "
        narrative += "Treatment is indicated to improve function and oral health. "
        narrative += f"Attached: {artifacts_text}."
        
        return narrative
    
    def _generate_scaling_narrative(self, case_record: CaseRecord, artifacts: List[str]) -> str:
        """Generate scaling/periodontal narrative"""
        
        perio_findings = case_record.clinical_findings.perio
        
        diagnosis = perio_findings.diagnosis or "periodontal disease"
        bop = f"{perio_findings.bop_percent}% BOP" if perio_findings.bop_percent else "elevated BOP"
        
        artifacts_text = ", ".join(artifacts) if artifacts else "periodontal chart and supporting documentation"
        
        narrative = f"Requesting authorization for additional scaling units. Patient diagnosed with {diagnosis} "
        narrative += f"presenting with {bop}. Additional scaling beyond routine prophylaxis is indicated "
        narrative += f"to address periodontal condition. Attached: {artifacts_text}."
        
        return narrative
    
    def _generate_aesthetic_narrative(self, case_record: CaseRecord, artifacts: List[str]) -> str:
        """Generate onlay/veneer narrative"""
        
        procedure_name = case_record.procedure.value.lower()
        tooth_numbers = self._format_tooth_numbers(case_record.tooth_numbers)
        
        # Emphasize structural/functional need
        reason = "structural compromise"
        if case_record.clinical_findings.fracture_present:
            reason = "fracture and structural loss"
        elif case_record.clinical_findings.caries_present:
            reason = "extensive caries and structural loss"
        
        artifacts_text = ", ".join(artifacts) if artifacts else "supporting documentation"
        
        narrative = f"Requesting authorization for {procedure_name} on tooth {tooth_numbers} due to {reason}. "
        narrative += "Conservative restoration is contraindicated due to extent of structural loss. "
        narrative += f"Treatment is indicated to restore function and prevent further breakdown. Attached: {artifacts_text}."
        
        return narrative
    
    def _generate_generic_narrative(self, case_record: CaseRecord, artifacts: List[str]) -> str:
        """Generate generic narrative for unsupported procedures"""
        
        procedure_name = case_record.procedure.value.lower().replace('_', ' ')
        tooth_info = self._format_tooth_numbers(case_record.tooth_numbers)
        
        artifacts_text = ", ".join(artifacts) if artifacts else "supporting documentation"
        
        narrative = f"Requesting authorization for {procedure_name} on {tooth_info} due to clinical necessity. "
        narrative += f"Treatment is medically necessary to restore function. Attached: {artifacts_text}."
        
        return narrative
    
    def _format_tooth_numbers(self, tooth_numbers: List[str]) -> str:
        """Format tooth numbers for narrative"""
        if not tooth_numbers:
            return "affected tooth"
        elif len(tooth_numbers) == 1:
            return f"tooth {tooth_numbers[0]}"
        else:
            return f"teeth {', '.join(tooth_numbers)}"
    
    def _get_key_clinical_findings(self, case_record: CaseRecord) -> str:
        """Get key clinical findings for narrative"""
        findings = []
        
        clinical = case_record.clinical_findings
        
        if clinical.fracture_present:
            findings.append("fracture present")
        if clinical.caries_present:
            findings.append(f"{clinical.caries_present} caries")
        if clinical.wear_present:
            findings.append(f"{clinical.wear_present} wear")
        if clinical.rct_status == "yes":
            findings.append("endodontically treated")
        
        return ". ".join(findings).capitalize() if findings else ""
    
    def _determine_crown_reason(self, findings) -> str:
        """Determine reason for crown treatment"""
        reasons = []
        
        if findings.fracture_present:
            reasons.append("fracture")
        if findings.caries_present:
            reasons.append(f"{findings.caries_present} caries")
        if findings.wear_present:
            reasons.append(f"{findings.wear_present} wear")
        
        return " and ".join(reasons) if reasons else "structural compromise"
    
    def _build_clinical_findings_text(self, findings) -> str:
        """Build clinical findings text"""
        findings_list = []
        
        if findings.surfaces_involved:
            surfaces = "/".join(findings.surfaces_involved)
            findings_list.append(f"{surfaces} surfaces affected")
        
        if findings.fracture_present:
            findings_list.append("fracture line present")
        
        if findings.caries_present:
            findings_list.append(f"{findings.caries_present} caries")
        
        return ", ".join(findings_list) if findings_list else "clinical findings support treatment necessity"
