"""
NLP Parser for extracting clinical information from free text
"""
import re
from typing import Dict, List, Optional, Tuple
from .models import CaseRecord, ClinicalFindings, PerioFindings, BridgeFindings, ImplantFindings, OrthoFindings

class ClinicalNLPParser:
    """Extract structured clinical information from free text descriptions"""
    
    def __init__(self):
        # Tooth number patterns
        self.tooth_patterns = [
            r'\b(?:tooth|#)\s*(\d{1,2})\b',
            r'\b(\d{1,2})\s*(?:tooth|#)\b',
            r'\b([1-4][1-8])\b',  # FDI notation
            r'\b([1-3]?[1-8])\s*(?:upper|lower|maxillary|mandibular)\b'
        ]
        
        # Clinical finding patterns
        self.clinical_patterns = {
            'fracture': [
                r'\b(?:fracture|fractured|crack|cracked|split)\b',
                r'\bfracture\s+line\b',
                r'\bvertical\s+root\s+fracture\b'
            ],
            'caries': [
                r'\b(?:caries|decay|cavit|carries)\b',
                r'\brecurrent\s+caries\b',
                r'\b(?:mesial|distal|occlusal|buccal|lingual)\s+caries\b'
            ],
            'rct': [
                r'\b(?:root\s+canal|RCT|endodontic|endo)\b',
                r'\bendodontically\s+treated\b',
                r'\bpulp\s+(?:necrosis|exposure|cap)\b'
            ],
            'crown_existing': [
                r'\bexisting\s+crown\b',
                r'\bprevious\s+crown\b',
                r'\b(?:PFM|porcelain|ceramic|gold|metal)\s+crown\b',
                r'\bcrown\s+(?:placed|inserted|done)\b'
            ],
            'crown_age': [
                r'\b(\d+)\s*(?:years?|yrs?)\s*(?:ago|old)\b',
                r'\bplaced\s+(?:in\s+)?(\d{4}|\d+\s*years?\s*ago)\b'
            ],
            'surfaces': [
                r'\b([MODBL]+)\s*(?:surface|restoration)\b',
                r'\b(?:mesial|distal|occlusal|buccal|lingual|incisal)\b'
            ],
            'perio_diagnosis': [
                r'\b(?:Stage\s+[I-IV]+|Grade\s+[ABC])\b',
                r'\b(?:gingivitis|periodontitis|perio)\b',
                r'\bBOP\s*:?\s*(\d+)%?\b'
            ],
            'implant_site': [
                r'\bimplant\s+(?:at\s+)?(?:site\s+)?(\d{1,2})\b',
                r'\bsite\s+(\d{1,2})\s+implant\b'
            ],
            'extraction_date': [
                r'\bextracted?\s+(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
                r'\bextraction\s+date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
            ]
        }
    
    def parse_clinical_text(self, text: str, procedure_type: str) -> ClinicalFindings:
        """Parse clinical text and extract relevant findings"""
        text_lower = text.lower()
        findings = ClinicalFindings()
        
        # Extract tooth numbers
        tooth_numbers = self._extract_tooth_numbers(text)
        
        # Extract clinical findings based on procedure type
        if procedure_type.upper() in ['CROWN', 'ONLAY', 'VENEER']:
            findings = self._extract_restorative_findings(text_lower, findings)
        elif procedure_type.upper() == 'BRIDGE':
            findings = self._extract_bridge_findings(text_lower, findings)
        elif procedure_type.upper() == 'IMPLANT':
            findings = self._extract_implant_findings(text_lower, findings)
        elif procedure_type.upper() == 'ORTHO':
            findings = self._extract_ortho_findings(text_lower, findings)
        elif procedure_type.upper() == 'ADDITIONAL_SCALING':
            findings = self._extract_perio_findings(text_lower, findings)
        
        return findings
    
    def _extract_tooth_numbers(self, text: str) -> List[str]:
        """Extract tooth numbers from text"""
        tooth_numbers = []
        
        for pattern in self.tooth_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tooth_numbers.extend(matches)
        
        # Remove duplicates and validate
        unique_teeth = list(set(tooth_numbers))
        valid_teeth = [t for t in unique_teeth if self._is_valid_tooth_number(t)]
        
        return valid_teeth
    
    def _is_valid_tooth_number(self, tooth_num: str) -> bool:
        """Validate tooth number (FDI system)"""
        try:
            num = int(tooth_num)
            # FDI system: 11-18, 21-28, 31-38, 41-48
            return (11 <= num <= 18) or (21 <= num <= 28) or (31 <= num <= 38) or (41 <= num <= 48)
        except:
            return False
    
    def _extract_restorative_findings(self, text: str, findings: ClinicalFindings) -> ClinicalFindings:
        """Extract findings for crowns, onlays, veneers"""
        
        # Check for existing restoration
        if any(re.search(pattern, text) for pattern in self.clinical_patterns['crown_existing']):
            findings.restoration_type_existing = "crown"
            
            # Extract crown material
            if re.search(r'\bPFM\b', text):
                findings.existing_crown_material = "PFM"
            elif re.search(r'\bporcelain\b', text):
                findings.existing_crown_material = "porcelain"
            elif re.search(r'\b(?:gold|metal)\b', text):
                findings.existing_crown_material = "metal"
            
            # Extract crown age
            age_matches = []
            for pattern in self.clinical_patterns['crown_age']:
                matches = re.findall(pattern, text)
                age_matches.extend(matches)
            
            if age_matches:
                try:
                    findings.existing_crown_age_years = int(age_matches[0])
                except:
                    pass
        
        # Check for fractures
        if any(re.search(pattern, text) for pattern in self.clinical_patterns['fracture']):
            findings.fracture_present = True
        
        # Check for caries
        if any(re.search(pattern, text) for pattern in self.clinical_patterns['caries']):
            if re.search(r'\brecurrent\b', text):
                findings.caries_present = "recurrent"
            else:
                findings.caries_present = "active"
        
        # Check RCT status
        if any(re.search(pattern, text) for pattern in self.clinical_patterns['rct']):
            findings.rct_status = "yes"
        
        # Extract surfaces
        surface_matches = []
        for pattern in self.clinical_patterns['surfaces']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            surface_matches.extend(matches)
        
        if surface_matches:
            # Convert to standard surface notation
            surfaces = []
            for match in surface_matches:
                if isinstance(match, str) and len(match) <= 5:
                    surfaces.extend(list(match.upper()))
            findings.surfaces_involved = list(set(surfaces))
        
        return findings
    
    def _extract_bridge_findings(self, text: str, findings: ClinicalFindings) -> ClinicalFindings:
        """Extract findings specific to bridges"""
        bridge_findings = BridgeFindings()
        
        # Check if replacement
        if re.search(r'\b(?:replace|replacement|existing\s+bridge)\b', text):
            bridge_findings.is_replacement = True
            
            # Extract previous bridge details
            if re.search(r'\bPFM\b', text):
                bridge_findings.previous_bridge_material = "PFM"
            
            # Extract age
            age_matches = re.findall(r'\b(\d+)\s*(?:years?|yrs?)\s*(?:ago|old)\b', text)
            if age_matches:
                try:
                    bridge_findings.previous_bridge_age_years = int(age_matches[0])
                except:
                    pass
        
        # Extract span information
        span_matches = re.findall(r'\b(\d{1,2})\s*[-to]+\s*(\d{1,2})\b', text)
        if span_matches:
            bridge_findings.span_site = f"{span_matches[0][0]}-{span_matches[0][1]}"
        
        # Extract missing teeth count
        missing_matches = re.findall(r'\b(\d+)\s*missing\s+teeth?\b', text)
        if missing_matches:
            try:
                bridge_findings.missing_teeth_total_mouth = int(missing_matches[0])
            except:
                pass
        
        findings.bridge = bridge_findings
        return findings
    
    def _extract_implant_findings(self, text: str, findings: ClinicalFindings) -> ClinicalFindings:
        """Extract findings specific to implants"""
        implant_findings = ImplantFindings()
        
        # Extract implant site
        site_matches = []
        for pattern in self.clinical_patterns['implant_site']:
            matches = re.findall(pattern, text)
            site_matches.extend(matches)
        
        if site_matches:
            implant_findings.site = site_matches[0]
        
        # Extract extraction date
        date_matches = []
        for pattern in self.clinical_patterns['extraction_date']:
            matches = re.findall(pattern, text)
            date_matches.extend(matches)
        
        if date_matches:
            implant_findings.extraction_date_site = date_matches[0]
        
        # Extract missing teeth count
        missing_matches = re.findall(r'\b(\d+)\s*missing\s+teeth?\b', text)
        if missing_matches:
            try:
                implant_findings.missing_teeth_total_mouth = int(missing_matches[0])
            except:
                pass
        
        # Check for bone graft history
        if re.search(r'\b(?:bone\s+graft|graft|sinus\s+lift)\b', text):
            implant_findings.bone_graft_history = "yes"
        
        findings.implant = implant_findings
        return findings
    
    def _extract_ortho_findings(self, text: str, findings: ClinicalFindings) -> ClinicalFindings:
        """Extract findings specific to orthodontics"""
        ortho_findings = OrthoFindings()
        
        # Extract crowding/spacing
        crowding_matches = re.findall(r'\bcrowding\s*:?\s*(\d+(?:\.\d+)?)\s*mm\b', text)
        if crowding_matches:
            try:
                ortho_findings.crowding_mm = float(crowding_matches[0])
            except:
                pass
        
        spacing_matches = re.findall(r'\bspacing\s*:?\s*(\d+(?:\.\d+)?)\s*mm\b', text)
        if spacing_matches:
            try:
                ortho_findings.spacing_mm = float(spacing_matches[0])
            except:
                pass
        
        # Extract overjet/overbite
        overjet_matches = re.findall(r'\boverjet\s*:?\s*(\d+(?:\.\d+)?)\s*mm\b', text)
        if overjet_matches:
            try:
                ortho_findings.overjet_mm = float(overjet_matches[0])
            except:
                pass
        
        overbite_matches = re.findall(r'\boverbite\s*:?\s*(\d+(?:\.\d+)?)%?\b', text)
        if overbite_matches:
            try:
                ortho_findings.overbite_percent = float(overbite_matches[0])
            except:
                pass
        
        # Extract malocclusion
        if re.search(r'\bclass\s+[I-III]+\b', text, re.IGNORECASE):
            malocclusion_match = re.search(r'\b(class\s+[I-III]+(?:\s+div\s+\d+)?)\b', text, re.IGNORECASE)
            if malocclusion_match:
                ortho_findings.malocclusion = malocclusion_match.group(1)
        
        findings.ortho = ortho_findings
        return findings
    
    def _extract_perio_findings(self, text: str, findings: ClinicalFindings) -> ClinicalFindings:
        """Extract findings specific to periodontal treatment"""
        perio_findings = PerioFindings()
        
        # Extract periodontal diagnosis
        stage_match = re.search(r'\b(Stage\s+[I-IV]+)\b', text, re.IGNORECASE)
        grade_match = re.search(r'\b(Grade\s+[ABC])\b', text, re.IGNORECASE)
        
        if stage_match and grade_match:
            perio_findings.diagnosis = f"{stage_match.group(1)} {grade_match.group(1)}"
        elif stage_match:
            perio_findings.diagnosis = stage_match.group(1)
        elif re.search(r'\b(?:gingivitis|periodontitis)\b', text):
            if re.search(r'\bgingivitis\b', text):
                perio_findings.diagnosis = "gingivitis"
            else:
                perio_findings.diagnosis = "periodontitis"
        
        # Extract BOP percentage
        bop_matches = re.findall(r'\bBOP\s*:?\s*(\d+)%?\b', text, re.IGNORECASE)
        if bop_matches:
            try:
                perio_findings.bop_percent = float(bop_matches[0])
            except:
                pass
        
        # Check for chart availability
        if re.search(r'\b(?:chart|charting)\s+(?:available|done|complete)\b', text):
            perio_findings.chart_available = True
        
        findings.perio = perio_findings
        return findings
