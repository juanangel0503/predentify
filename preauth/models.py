"""
Data models for the Pre-Authorization Generator
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
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

class ToothSystem(Enum):
    FDI = "FDI"
    UNIVERSAL = "UNIVERSAL"

@dataclass
class PerioFindings:
    diagnosis: Optional[str] = None
    bop_percent: Optional[float] = None
    chart_available: bool = False

@dataclass
class BridgeFindings:
    is_replacement: bool = False
    previous_bridge_age_years: Optional[int] = None
    previous_bridge_material: Optional[str] = None
    span_site: Optional[str] = None
    missing_teeth_total_mouth: Optional[int] = None
    extraction_dates: Dict[str, str] = field(default_factory=dict)

@dataclass
class ImplantFindings:
    site: Optional[str] = None
    missing_teeth_total_mouth: Optional[int] = None
    extraction_date_site: Optional[str] = None
    bone_graft_history: Optional[str] = None

@dataclass
class OrthoFindings:
    crowding_mm: Optional[float] = None
    spacing_mm: Optional[float] = None
    rotations: List[str] = field(default_factory=list)
    malocclusion: Optional[str] = None
    overjet_mm: Optional[float] = None
    overbite_percent: Optional[float] = None
    skeletal_notes: Optional[str] = None

@dataclass
class ClinicalFindings:
    restoration_type_existing: Optional[str] = None
    existing_crown_material: Optional[str] = None
    existing_crown_age_years: Optional[int] = None
    surfaces_involved: List[str] = field(default_factory=list)
    fracture_present: bool = False
    wear_present: Optional[str] = None
    rct_status: Optional[str] = None
    caries_present: Optional[str] = None
    perio: PerioFindings = field(default_factory=PerioFindings)
    bridge: BridgeFindings = field(default_factory=BridgeFindings)
    implant: ImplantFindings = field(default_factory=ImplantFindings)
    ortho: OrthoFindings = field(default_factory=OrthoFindings)

@dataclass
class RequiredArtifacts:
    periapical_radiograph: bool = False
    bitewing_radiograph: bool = False
    panoramic: bool = False
    ceph: bool = False
    intraoral_photos: List[str] = field(default_factory=list)
    perio_chart: bool = False
    study_models_or_scans: bool = False

@dataclass
class CaseRecord:
    insurer: InsurerType
    procedure: ProcedureType
    tooth_numbers: List[str] = field(default_factory=list)
    tooth_system: ToothSystem = ToothSystem.FDI
    clinical_findings: ClinicalFindings = field(default_factory=ClinicalFindings)
    artifacts: RequiredArtifacts = field(default_factory=RequiredArtifacts)
    original_text: str = ""

@dataclass
class ValidationResult:
    is_valid: bool
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    required_artifacts: List[str] = field(default_factory=list)

@dataclass
class PreAuthResult:
    success: bool
    narrative: str = ""
    checklist: List[Dict[str, Any]] = field(default_factory=list)
    missing_info_prompts: List[str] = field(default_factory=list)
    policy_flags: List[str] = field(default_factory=list)
    validation: ValidationResult = field(default_factory=ValidationResult)
    case_record: Optional[CaseRecord] = None
