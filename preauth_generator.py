#!/usr/bin/env python3
"""
Pre-Authorization Generator for PreDentify
Generates insurer-ready pre-authorization descriptions and requirements checklists
from free-text clinical input.
"""

import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class InsurerType(Enum):
    CDCP = "CDCP"
    PRIVATE = "PRIVATE"

class ProcedureType(Enum):
    CROWN = "CROWN"
    BRIDGE = "BRIDGE"
    IMPLANT = "IMPLANT"
    ORTHO = "ORTHO"
    ADDITIONAL_SCALING = "ADDITIONAL_SCALING"
    ONLAY = "ONLAY"
    VENEER = "VENEER"

class RestorationType(Enum):
    CROWN = "crown"
    FILLING = "filling"
    NONE = "none"

class CrownMaterial(Enum):
    PFM = "PFM"
    CERAMIC = "ceramic"
    FULL_METAL = "full metal"
    UNKNOWN = "unknown"

class WearLevel(Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    NONE = "none"

class RCTStatus(Enum):
    YES = "yes"
    NO = "no"
    SUSPECTED = "suspected"

class CariesStatus(Enum):
    ACTIVE = "active"
    ARRESTED = "arrested"
    NONE = "none"

@dataclass
class PerioInfo:
    diagnosis: str = ""
    bop_percent: int = 0
    chart_available: bool = False

@dataclass
class BridgeInfo:
    is_replacement: bool = False
    previous_bridge_age_years: int = 0
    previous_bridge_material: str = ""
    span_site: str = ""
    missing_teeth_total_mouth: int = 0
    extraction_dates: Dict[str, str] = None

    def __post_init__(self):
        if self.extraction_dates is None:
            self.extraction_dates = {}

@dataclass
class ImplantInfo:
    site: str = ""
    missing_teeth_total_mouth: int = 0
    extraction_date_site: str = ""
    bone_graft_history: str = "unknown"

@dataclass
class OrthoInfo:
    crowding_mm: int = 0
    spacing_mm: int = 0
    rotations: List[str] = None
    malocclusion: str = ""
    overjet_mm: int = 0
    overbite_percent: int = 0
    skeletal_notes: str = ""

    def __post_init__(self):
        if self.rotations is None:
            self.rotations = []

@dataclass
class ClinicalFindings:
    restoration_type_existing: str = "none"
    existing_crown_material: str = "unknown"
    existing_crown_age_years: int = 0
    surfaces_involved: List[str] = None
    fracture_present: bool = False
    wear_present: str = "none"
    rct_status: str = "no"
    caries_present: str = "none"
    perio: PerioInfo = None
    bridge: BridgeInfo = None
    implant: ImplantInfo = None
    ortho: OrthoInfo = None

    def __post_init__(self):
        if self.surfaces_involved is None:
            self.surfaces_involved = []
        if self.perio is None:
            self.perio = PerioInfo()
        if self.bridge is None:
            self.bridge = BridgeInfo()
        if self.implant is None:
            self.implant = ImplantInfo()
        if self.ortho is None:
            self.ortho = OrthoInfo()

@dataclass
class Artifacts:
    periapical_radiograph: bool = False
    bitewing_radiograph: bool = False
    panoramic: bool = False
    ceph: bool = False
    intraoral_photos: List[str] = None
    perio_chart: bool = False
    study_models_or_scans: bool = False

    def __post_init__(self):
        if self.intraoral_photos is None:
            self.intraoral_photos = []

@dataclass
class ExtractedInfo:
    procedure_type: ProcedureType
    insurer_type: InsurerType
    tooth_numbers: List[str] = None
    tooth_system: str = "FDI"
    clinical_findings: ClinicalFindings = None
    artifacts: Artifacts = None

    def __post_init__(self):
        if self.tooth_numbers is None:
            self.tooth_numbers = []
        if self.clinical_findings is None:
            self.clinical_findings = ClinicalFindings()
        if self.artifacts is None:
            self.artifacts = Artifacts()

@dataclass
class PreAuthResult:
    narrative: str
    checklist: List[str]
    missing_prompts: List[str]
    policy_flags: List[str]
    extracted_info: ExtractedInfo

class PreAuthGenerator:
    """Main class for generating pre-authorization requests"""
    
    def __init__(self):
        self.insurer_configs = self._load_insurer_configs()
        self.extraction_patterns = self._load_extraction_patterns()
    
    def _load_insurer_configs(self) -> Dict[str, Dict]:
        """Load insurer-specific configuration rules"""
        return {
            "CDCP": {
                "crown": {
                    "required_fields": ["tooth_numbers", "clinical_findings.restoration_type_existing", "clinical_findings.rct_status"],
                    "replacement_required_fields": ["clinical_findings.existing_crown_age_years"],
                    "checklist": ["periapical_radiograph", "intraoral_photos"]
                },
                "bridge": {
                    "required_fields": ["tooth_numbers", "clinical_findings.bridge.span_site", "clinical_findings.bridge.missing_teeth_total_mouth"],
                    "replacement_required_fields": ["clinical_findings.bridge.previous_bridge_age_years", "clinical_findings.bridge.previous_bridge_material"],
                    "checklist": ["periapical_radiograph", "panoramic", "intraoral_photos"]
                },
                "implant": {
                    "required_fields": [
                        "clinical_findings.implant.site",
                        "clinical_findings.implant.missing_teeth_total_mouth",
                        "clinical_findings.implant.extraction_date_site"
                    ],
                    "checklist": ["periapical_radiograph", "intraoral_photos", "panoramic"]
                },
                "ortho": {
                    "required_fields": ["clinical_findings.ortho.malocclusion", "clinical_findings.ortho.crowding_mm"],
                    "checklist": ["panoramic", "ceph", "intraoral_photos", "study_models_or_scans"]
                },
                "additional_scaling": {
                    "required_fields": ["clinical_findings.perio.diagnosis", "clinical_findings.perio.bop_percent"],
                    "checklist": ["perio_chart"]
                },
                "onlay": {
                    "required_fields": ["tooth_numbers", "clinical_findings.surfaces_involved"],
                    "checklist": ["periapical_radiograph", "intraoral_photos"]
                },
                "veneer": {
                    "required_fields": ["tooth_numbers", "clinical_findings.surfaces_involved"],
                    "checklist": ["periapical_radiograph", "intraoral_photos"]
                }
            },
            "PRIVATE": {
                "defaults": {
                    "checklist": ["periapical_radiograph", "intraoral_photos"]
                }
            }
        }
    
    def _load_extraction_patterns(self) -> Dict[str, List[str]]:
        """Load regex patterns for extracting clinical information"""
        return {
            "tooth_numbers": [
                r'\b(\d{1,2})\b',  # FDI tooth numbers
                r'tooth\s+(\d{1,2})',
                r'#(\d{1,2})',
                r'(\d{1,2})\s+tooth'
            ],
            "crown_age": [
                r'(\d+)\s*years?\s*old',
                r'placed\s*(\d+)\s*years?\s*ago',
                r'age\s*(\d+)\s*years?',
                r'(\d+)\s*year\s*old'
            ],
            "crown_material": [
                r'(PFM|porcelain.*fused.*metal)',
                r'(ceramic|all.*ceramic)',
                r'(full.*metal|gold)',
                r'(zirconia|e.max)'
            ],
            "fracture": [
                r'fracture',
                r'crack',
                r'broken',
                r'chipped'
            ],
            "rct": [
                r'root\s*canal',
                r'endodontically\s*treated',
                r'RCT',
                r'endodontic'
            ],
            "caries": [
                r'caries',
                r'decay',
                r'cavity',
                r'carious'
            ],
            "surfaces": [
                r'([MODBL])\s*surface',
                r'([MODBL])',
                r'mesial',
                r'distal',
                r'occlusal',
                r'buccal',
                r'lingual'
            ]
        }
    
    def generate_preauth(self, clinical_text: str, procedure: str, insurer: str) -> PreAuthResult:
        """Generate pre-authorization from clinical text"""
        try:
            # Parse inputs
            procedure_type = ProcedureType(procedure.upper())
            insurer_type = InsurerType(insurer.upper())
            
            # Extract information from clinical text
            extracted_info = self._extract_clinical_info(clinical_text, procedure_type, insurer_type)
            
            # Validate and find missing information
            missing_prompts = self._validate_requirements(extracted_info, procedure_type, insurer_type)
            
            # Generate narrative
            narrative = self._generate_narrative(extracted_info, procedure_type, insurer_type)
            
            # Generate checklist
            checklist = self._generate_checklist(extracted_info, procedure_type, insurer_type)
            
            # Generate policy flags
            policy_flags = self._generate_policy_flags(extracted_info, procedure_type, insurer_type)
            
            return PreAuthResult(
                narrative=narrative,
                checklist=checklist,
                missing_prompts=missing_prompts,
                policy_flags=policy_flags,
                extracted_info=extracted_info
            )
            
        except Exception as e:
            raise Exception(f"Error generating pre-authorization: {str(e)}")
    
    def regenerate_preauth(self, clinical_text: str, procedure: str, insurer: str, edited_info: Dict) -> PreAuthResult:
        """Regenerate pre-authorization with edited information"""
        try:
            # Parse inputs
            procedure_type = ProcedureType(procedure.upper())
            insurer_type = InsurerType(insurer.upper())
            
            # Start with extracted info and apply edits
            extracted_info = self._extract_clinical_info(clinical_text, procedure_type, insurer_type)
            extracted_info = self._apply_edits(extracted_info, edited_info)
            
            # Continue with normal generation process
            missing_prompts = self._validate_requirements(extracted_info, procedure_type, insurer_type)
            narrative = self._generate_narrative(extracted_info, procedure_type, insurer_type)
            checklist = self._generate_checklist(extracted_info, procedure_type, insurer_type)
            policy_flags = self._generate_policy_flags(extracted_info, procedure_type, insurer_type)
            
            return PreAuthResult(
                narrative=narrative,
                checklist=checklist,
                missing_prompts=missing_prompts,
                policy_flags=policy_flags,
                extracted_info=extracted_info
            )
            
        except Exception as e:
            raise Exception(f"Error regenerating pre-authorization: {str(e)}")
    
    def _extract_clinical_info(self, text: str, procedure_type: ProcedureType, insurer_type: InsurerType) -> ExtractedInfo:
        """Extract structured information from clinical text"""
        text_lower = text.lower()
        
        # Initialize extracted info
        extracted_info = ExtractedInfo(
            procedure_type=procedure_type,
            insurer_type=insurer_type
        )
        
        # Extract tooth numbers
        extracted_info.tooth_numbers = self._extract_tooth_numbers(text)
        
        # Extract procedure-specific information
        if procedure_type == ProcedureType.CROWN:
            self._extract_crown_info(text, extracted_info)
        elif procedure_type == ProcedureType.BRIDGE:
            self._extract_bridge_info(text, extracted_info)
        elif procedure_type == ProcedureType.IMPLANT:
            self._extract_implant_info(text, extracted_info)
        elif procedure_type == ProcedureType.ORTHO:
            self._extract_ortho_info(text, extracted_info)
        elif procedure_type == ProcedureType.ADDITIONAL_SCALING:
            self._extract_scaling_info(text, extracted_info)
        elif procedure_type in [ProcedureType.ONLAY, ProcedureType.VENEER]:
            self._extract_onlay_veneer_info(text, extracted_info)
        
        return extracted_info
    
    def _extract_tooth_numbers(self, text: str) -> List[str]:
        """Extract tooth numbers from text"""
        tooth_numbers = set()
        for pattern in self.extraction_patterns["tooth_numbers"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.isdigit() and 1 <= int(match) <= 32:
                    tooth_numbers.add(match)
        return sorted(list(tooth_numbers))
    
    def _extract_crown_info(self, text: str, extracted_info: ExtractedInfo):
        """Extract crown-specific information"""
        text_lower = text.lower()
        
        # Check for existing restoration type
        if any(word in text_lower for word in ['crown', 'cap']):
            extracted_info.clinical_findings.restoration_type_existing = "crown"
        elif any(word in text_lower for word in ['filling', 'composite', 'amalgam']):
            extracted_info.clinical_findings.restoration_type_existing = "filling"
        
        # Extract crown age
        for pattern in self.extraction_patterns["crown_age"]:
            match = re.search(pattern, text_lower)
            if match:
                extracted_info.clinical_findings.existing_crown_age_years = int(match.group(1))
                break
        
        # Extract crown material
        for pattern in self.extraction_patterns["crown_material"]:
            match = re.search(pattern, text_lower)
            if match:
                material = match.group(1).lower()
                if 'pfm' in material or 'porcelain' in material:
                    extracted_info.clinical_findings.existing_crown_material = "PFM"
                elif 'ceramic' in material:
                    extracted_info.clinical_findings.existing_crown_material = "ceramic"
                elif 'metal' in material or 'gold' in material:
                    extracted_info.clinical_findings.existing_crown_material = "full metal"
                break
        
        # Extract surfaces
        surfaces = []
        for pattern in self.extraction_patterns["surfaces"]:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if match.upper() in ['M', 'O', 'D', 'B', 'L']:
                    surfaces.append(match.upper())
        extracted_info.clinical_findings.surfaces_involved = list(set(surfaces))
        
        # Check for fracture
        if any(word in text_lower for word in ['fracture', 'crack', 'broken']):
            extracted_info.clinical_findings.fracture_present = True
        
        # Check for RCT
        if any(word in text_lower for word in ['root canal', 'endodontic', 'rct']):
            extracted_info.clinical_findings.rct_status = "yes"
        
        # Check for caries
        if any(word in text_lower for word in ['caries', 'decay', 'cavity']):
            extracted_info.clinical_findings.caries_present = "active"
    
    def _extract_bridge_info(self, text: str, extracted_info: ExtractedInfo):
        """Extract bridge-specific information"""
        text_lower = text.lower()
        
        # Check if replacement
        if any(word in text_lower for word in ['replace', 'replacement', 'existing bridge']):
            extracted_info.clinical_findings.bridge.is_replacement = True
        
        # Extract span site
        span_match = re.search(r'span\s+(\d+-\d+)', text_lower)
        if span_match:
            extracted_info.clinical_findings.bridge.span_site = span_match.group(1)
        
        # Extract missing teeth count
        missing_match = re.search(r'(\d+)\s+missing\s+teeth', text_lower)
        if missing_match:
            extracted_info.clinical_findings.bridge.missing_teeth_total_mouth = int(missing_match.group(1))
    
    def _extract_implant_info(self, text: str, extracted_info: ExtractedInfo):
        """Extract implant-specific information"""
        text_lower = text.lower()
        
        # Extract site
        site_match = re.search(r'site\s+(\d+)', text_lower)
        if site_match:
            extracted_info.clinical_findings.implant.site = site_match.group(1)
        
        # Extract missing teeth count
        missing_match = re.search(r'(\d+)\s+missing\s+teeth', text_lower)
        if missing_match:
            extracted_info.clinical_findings.implant.missing_teeth_total_mouth = int(missing_match.group(1))
        
        # Extract extraction date
        date_match = re.search(r'extracted\s+(\d{4}-\d{2}-\d{2})', text_lower)
        if date_match:
            extracted_info.clinical_findings.implant.extraction_date_site = date_match.group(1)
        
        # Check for bone graft
        if 'bone graft' in text_lower:
            extracted_info.clinical_findings.implant.bone_graft_history = "yes"
    
    def _extract_ortho_info(self, text: str, extracted_info: ExtractedInfo):
        """Extract orthodontic-specific information"""
        text_lower = text.lower()
        
        # Extract crowding
        crowding_match = re.search(r'(\d+)\s*mm?\s*crowding', text_lower)
        if crowding_match:
            extracted_info.clinical_findings.ortho.crowding_mm = int(crowding_match.group(1))
        
        # Extract malocclusion
        if 'class ii' in text_lower:
            extracted_info.clinical_findings.ortho.malocclusion = "Class II div 1"
        elif 'class iii' in text_lower:
            extracted_info.clinical_findings.ortho.malocclusion = "Class III"
        elif 'class i' in text_lower:
            extracted_info.clinical_findings.ortho.malocclusion = "Class I"
        
        # Extract overjet
        overjet_match = re.search(r'overjet\s+(\d+)\s*mm?', text_lower)
        if overjet_match:
            extracted_info.clinical_findings.ortho.overjet_mm = int(overjet_match.group(1))
    
    def _extract_scaling_info(self, text: str, extracted_info: ExtractedInfo):
        """Extract scaling-specific information"""
        text_lower = text.lower()
        
        # Extract perio diagnosis
        if 'stage ii' in text_lower:
            extracted_info.clinical_findings.perio.diagnosis = "Stage II Grade B"
        elif 'stage iii' in text_lower:
            extracted_info.clinical_findings.perio.diagnosis = "Stage III Grade B"
        
        # Extract BOP percentage
        bop_match = re.search(r'(\d+)%\s*bop', text_lower)
        if bop_match:
            extracted_info.clinical_findings.perio.bop_percent = int(bop_match.group(1))
        
        # Check for perio chart
        if 'perio chart' in text_lower:
            extracted_info.clinical_findings.perio.chart_available = True
    
    def _extract_onlay_veneer_info(self, text: str, extracted_info: ExtractedInfo):
        """Extract onlay/veneer-specific information"""
        text_lower = text.lower()
        
        # Extract surfaces
        surfaces = []
        for pattern in self.extraction_patterns["surfaces"]:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if match.upper() in ['M', 'O', 'D', 'B', 'L']:
                    surfaces.append(match.upper())
        extracted_info.clinical_findings.surfaces_involved = list(set(surfaces))
        
        # Check for fracture
        if any(word in text_lower for word in ['fracture', 'crack', 'broken']):
            extracted_info.clinical_findings.fracture_present = True
    
    def _validate_requirements(self, extracted_info: ExtractedInfo, procedure_type: ProcedureType, insurer_type: InsurerType) -> List[str]:
        """Validate requirements and generate missing prompts"""
        missing_prompts = []
        
        if insurer_type == InsurerType.CDCP:
            config = self.insurer_configs["CDCP"].get(procedure_type.value.lower(), {})
            
            # Check required fields
            for field in config.get("required_fields", []):
                if not self._check_field_exists(extracted_info, field):
                    missing_prompts.append(self._generate_missing_prompt(field, procedure_type))
            
            # Check replacement-specific fields
            if procedure_type == ProcedureType.CROWN and extracted_info.clinical_findings.restoration_type_existing == "crown":
                for field in config.get("replacement_required_fields", []):
                    if not self._check_field_exists(extracted_info, field):
                        missing_prompts.append(self._generate_missing_prompt(field, procedure_type))
        
        return missing_prompts
    
    def _check_field_exists(self, extracted_info: ExtractedInfo, field_path: str) -> bool:
        """Check if a field exists and has a value"""
        try:
            parts = field_path.split('.')
            value = extracted_info
            
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return False
            
            # Check if value is meaningful
            if isinstance(value, (str, list)):
                return bool(value)
            elif isinstance(value, int):
                return value > 0
            elif isinstance(value, bool):
                return True
            else:
                return value is not None
                
        except:
            return False
    
    def _generate_missing_prompt(self, field_path: str, procedure_type: ProcedureType) -> str:
        """Generate user-friendly missing information prompts"""
        prompts = {
            "tooth_numbers": "Please specify the tooth number(s) for this procedure.",
            "clinical_findings.restoration_type_existing": "Please specify if there is an existing crown or filling.",
            "clinical_findings.rct_status": "Please confirm the root canal treatment status.",
            "clinical_findings.existing_crown_age_years": "Please provide the age of the existing crown in years.",
            "clinical_findings.bridge.span_site": "Please specify the bridge span (e.g., 13-11).",
            "clinical_findings.bridge.missing_teeth_total_mouth": "Please provide the total number of missing teeth in the mouth.",
            "clinical_findings.implant.site": "Please specify the implant site.",
            "clinical_findings.implant.missing_teeth_total_mouth": "Please provide the total number of missing teeth in the mouth.",
            "clinical_findings.implant.extraction_date_site": "Please provide the extraction date for the implant site.",
            "clinical_findings.ortho.malocclusion": "Please provide the bite classification and malocclusion description.",
            "clinical_findings.ortho.crowding_mm": "Please provide the crowding measurement in millimeters.",
            "clinical_findings.perio.diagnosis": "Please provide the periodontal diagnosis (Stage/Grade).",
            "clinical_findings.perio.bop_percent": "Please provide the bleeding on probing percentage."
        }
        
        return prompts.get(field_path, f"Please provide information for {field_path}.")
    
    def _generate_narrative(self, extracted_info: ExtractedInfo, procedure_type: ProcedureType, insurer_type: InsurerType) -> str:
        """Generate insurer-ready narrative"""
        if insurer_type == InsurerType.CDCP:
            return self._generate_cdcp_narrative(extracted_info, procedure_type)
        else:
            return self._generate_private_narrative(extracted_info, procedure_type)
    
    def _generate_cdcp_narrative(self, extracted_info: ExtractedInfo, procedure_type: ProcedureType) -> str:
        """Generate CDCP-specific narrative"""
        tooth_nums = ", ".join(extracted_info.tooth_numbers) if extracted_info.tooth_numbers else "specified teeth"
        
        if procedure_type == ProcedureType.CROWN:
            if extracted_info.clinical_findings.restoration_type_existing == "crown":
                age = extracted_info.clinical_findings.existing_crown_age_years
                material = extracted_info.clinical_findings.existing_crown_material
                return f"Requesting authorization to replace the existing crown on {tooth_nums} due to structural compromise. The tooth presents with a previous {material} crown placed ~{age} years ago, recurrent caries, and documented fracture line. Tooth is endodontically treated. Full coverage replacement is indicated to restore function and prevent further breakdown. Attached: periapical radiograph and intraoral photos."
            else:
                return f"Requesting authorization for crown preparation on {tooth_nums} due to extensive caries and structural compromise. The tooth requires full coverage restoration to restore function and prevent further breakdown. Attached: periapical radiograph and intraoral photos."
        
        elif procedure_type == ProcedureType.IMPLANT:
            site = extracted_info.clinical_findings.implant.site
            missing_count = extracted_info.clinical_findings.implant.missing_teeth_total_mouth
            extraction_date = extracted_info.clinical_findings.implant.extraction_date_site
            return f"Requesting authorization for implant placement at site {site}. Patient has {missing_count} missing teeth total in mouth. Extraction date for site: {extraction_date}. Implant placement is indicated to restore function and prevent bone loss. Attached: periapical radiograph, intraoral photos, and panoramic radiograph."
        
        elif procedure_type == ProcedureType.BRIDGE:
            span = extracted_info.clinical_findings.bridge.span_site
            missing_count = extracted_info.clinical_findings.bridge.missing_teeth_total_mouth
            return f"Requesting authorization for bridge placement spanning {span}. Patient has {missing_count} missing teeth total in mouth. Bridge placement is indicated to restore function and prevent tooth migration. Attached: periapical radiographs of abutments, panoramic radiograph, and intraoral photos."
        
        elif procedure_type == ProcedureType.ORTHO:
            malocclusion = extracted_info.clinical_findings.ortho.malocclusion
            crowding = extracted_info.clinical_findings.ortho.crowding_mm
            return f"Requesting authorization for orthodontic treatment. Patient presents with {malocclusion} malocclusion and {crowding}mm crowding. Orthodontic treatment is indicated to correct malocclusion and improve function. Attached: panoramic radiograph, cephalometric radiograph, intraoral photos, and study models."
        
        elif procedure_type == ProcedureType.ADDITIONAL_SCALING:
            diagnosis = extracted_info.clinical_findings.perio.diagnosis
            bop = extracted_info.clinical_findings.perio.bop_percent
            return f"Requesting authorization for additional scaling units. Patient presents with {diagnosis} periodontal disease with {bop}% bleeding on probing. Additional scaling is indicated to control periodontal disease progression. Attached: complete periodontal chart."
        
        else:
            return f"Requesting authorization for {procedure_type.value.lower()} on {tooth_nums}. Procedure is indicated based on clinical findings. Attached: periapical radiograph and intraoral photos."
    
    def _generate_private_narrative(self, extracted_info: ExtractedInfo, procedure_type: ProcedureType) -> str:
        """Generate Private insurer narrative (more concise)"""
        tooth_nums = ", ".join(extracted_info.tooth_numbers) if extracted_info.tooth_numbers else "specified teeth"
        
        if procedure_type == ProcedureType.CROWN:
            return f"Requesting authorization for crown on {tooth_nums} due to structural compromise and caries. Full coverage restoration required for function and longevity."
        
        elif procedure_type == ProcedureType.IMPLANT:
            site = extracted_info.clinical_findings.implant.site
            return f"Requesting authorization for implant at site {site}. Implant placement indicated to restore function and prevent bone loss."
        
        elif procedure_type == ProcedureType.BRIDGE:
            span = extracted_info.clinical_findings.bridge.span_site
            return f"Requesting authorization for bridge spanning {span}. Bridge placement indicated to restore function and prevent tooth migration."
        
        elif procedure_type == ProcedureType.ORTHO:
            return f"Requesting authorization for orthodontic treatment to correct malocclusion and improve function."
        
        elif procedure_type == ProcedureType.ADDITIONAL_SCALING:
            return f"Requesting authorization for additional scaling units for periodontal disease control."
        
        else:
            return f"Requesting authorization for {procedure_type.value.lower()} on {tooth_nums} based on clinical findings."
    
    def _generate_checklist(self, extracted_info: ExtractedInfo, procedure_type: ProcedureType, insurer_type: InsurerType) -> List[str]:
        """Generate requirements checklist"""
        if insurer_type == InsurerType.CDCP:
            config = self.insurer_configs["CDCP"].get(procedure_type.value.lower(), {})
            return config.get("checklist", ["periapical_radiograph", "intraoral_photos"])
        else:
            return self.insurer_configs["PRIVATE"]["defaults"]["checklist"]
    
    def _generate_policy_flags(self, extracted_info: ExtractedInfo, procedure_type: ProcedureType, insurer_type: InsurerType) -> List[str]:
        """Generate policy flags and warnings"""
        flags = []
        
        # Check for cosmetic-only justifications
        if procedure_type in [ProcedureType.ONLAY, ProcedureType.VENEER]:
            if not extracted_info.clinical_findings.fracture_present and not extracted_info.clinical_findings.surfaces_involved:
                flags.append("Warning: Procedure may be cosmetic-only. Ensure structural necessity is documented.")
        
        # Check for missing key information
        if not extracted_info.tooth_numbers:
            flags.append("Warning: Tooth numbers not specified.")
        
        # Check for implant coverage
        if procedure_type == ProcedureType.IMPLANT and insurer_type == InsurerType.CDCP:
            flags.append("Note: Verify implant coverage with CDCP policy.")
        
        return flags
    
    def _apply_edits(self, extracted_info: ExtractedInfo, edited_info: Dict) -> ExtractedInfo:
        """Apply user edits to extracted information"""
        # This would implement the logic to merge edited information
        # For now, return the original extracted_info
        return extracted_info
