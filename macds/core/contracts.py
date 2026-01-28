from dataclasses import dataclass, field
from typing import Any, Optional, TypeVar, Generic
from enum import Enum
from datetime import datetime
import yaml
import json
from pathlib import Path


class ContractViolationError(Exception):
    """Raised when contract validation fails."""
    pass


class Verdict(str, Enum):
    """Standard verdict for review/validation contracts."""
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVISION = "needs_revision"
    ESCALATE = "escalate"


@dataclass
class Violation:
    """Represents a contract or standard violation."""
    rule_id: str
    severity: str  # error, warning, info
    message: str
    location: Optional[str] = None
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "suggested_fix": self.suggested_fix
        }


@dataclass
class ContractInput:
    """Base class for contract inputs."""
    request_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    source_agent: Optional[str] = None
    
    def validate(self) -> list[Violation]:
        """Validate the input. Override in subclasses."""
        return []


@dataclass
class ContractOutput:
    """Base class for contract outputs."""
    request_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    processing_agent: Optional[str] = None
    
    def validate(self) -> list[Violation]:
        """Validate the output. Override in subclasses."""
        return []


# ==================== Specific Contracts ====================

@dataclass
class RequirementsInput(ContractInput):
    """Input for requirements definition."""
    user_request: str
    context: Optional[str] = None
    constraints: list[str] = field(default_factory=list)


@dataclass
class RequirementsOutput(ContractOutput):
    """Output from ProductAgent."""
    requirements: list[dict]  # {id, description, priority, acceptance_criteria}
    acceptance_criteria: list[str]
    constraints: list[str]
    risks: list[str] = field(default_factory=list)
    
    def validate(self) -> list[Violation]:
        violations = []
        if not self.requirements:
            violations.append(Violation(
                rule_id="REQ-001",
                severity="error",
                message="Requirements cannot be empty"
            ))
        for req in self.requirements:
            if "id" not in req or "description" not in req:
                violations.append(Violation(
                    rule_id="REQ-002",
                    severity="error",
                    message="Each requirement must have id and description"
                ))
        return violations


@dataclass
class ArchitectureInput(ContractInput):
    """Input for architecture design."""
    requirements: list[dict]
    existing_architecture: Optional[str] = None
    constraints: list[str] = field(default_factory=list)


@dataclass
class ArchitectureOutput(ContractOutput):
    """Output from ArchitectAgent."""
    components: list[dict]  # {name, responsibility, interfaces}
    invariants: list[str]
    design_decisions: list[dict]  # {id, decision, rationale, alternatives}
    api_contracts: list[dict]
    risks: list[str] = field(default_factory=list)
    
    def validate(self) -> list[Violation]:
        violations = []
        if not self.components:
            violations.append(Violation(
                rule_id="ARCH-001",
                severity="error",
                message="Architecture must define at least one component"
            ))
        if not self.invariants:
            violations.append(Violation(
                rule_id="ARCH-002",
                severity="warning",
                message="Architecture should define invariants"
            ))
        return violations


@dataclass
class ImplementationInput(ContractInput):
    """Input for code implementation."""
    task_description: str
    architecture: dict
    api_contract: Optional[dict] = None
    coding_standards: Optional[str] = None
    target_files: list[str] = field(default_factory=list)


@dataclass
class ImplementationOutput(ContractOutput):
    """Output from ImplementationAgent."""
    files_created: list[dict]  # {path, content, language}
    files_modified: list[dict]  # {path, diff, description}
    files_deleted: list[str]
    implementation_notes: str = ""
    api_compliance: bool = True
    
    def validate(self) -> list[Violation]:
        violations = []
        if not self.files_created and not self.files_modified:
            violations.append(Violation(
                rule_id="IMPL-001",
                severity="warning",
                message="Implementation produced no file changes"
            ))
        return violations


@dataclass 
class CodeReviewInput(ContractInput):
    """Input for code review."""
    code_diff: str
    architecture_constraints: list[str]
    coding_standards: str
    files_to_review: list[str] = field(default_factory=list)


@dataclass
class CodeReviewOutput(ContractOutput):
    """Output from ReviewerAgent."""
    verdict: Verdict
    violations: list[Violation] = field(default_factory=list)
    suggested_patches: list[dict] = field(default_factory=list)  # {file, original, replacement}
    security_concerns: list[str] = field(default_factory=list)
    quality_score: float = 0.0  # 0-100
    comments: str = ""


@dataclass
class BuildTestInput(ContractInput):
    """Input for build/test execution."""
    source_files: list[str]
    test_files: list[str]
    build_command: Optional[str] = None
    test_command: Optional[str] = None


@dataclass
class BuildTestOutput(ContractOutput):
    """Output from BuildTestAgent."""
    build_success: bool
    test_success: bool
    test_results: dict = field(default_factory=dict)  # {passed, failed, skipped, coverage}
    build_logs: str = ""
    test_logs: str = ""
    metrics: dict = field(default_factory=dict)  # {coverage_pct, duration_s, memory_mb}
    security_scan: Optional[dict] = None
    
    def validate(self) -> list[Violation]:
        violations = []
        if not self.build_success:
            violations.append(Violation(
                rule_id="BUILD-001",
                severity="error",
                message="Build failed"
            ))
        if not self.test_success:
            violations.append(Violation(
                rule_id="TEST-001", 
                severity="error",
                message="Tests failed"
            ))
        return violations


@dataclass
class IntegrationInput(ContractInput):
    """Input for change integration."""
    changes: list[dict]  # Files to integrate
    target_branch: str = "main"
    source_branch: str = ""
    review_approval: bool = False
    build_approval: bool = False


@dataclass
class IntegrationOutput(ContractOutput):
    """Output from IntegratorAgent."""
    success: bool
    merged_files: list[str] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)
    commit_sha: Optional[str] = None
    integration_notes: str = ""


@dataclass
class ConflictRecord:
    """Record of a disagreement between agents."""
    conflict_id: str
    topic: str
    agents_involved: list[str]
    evidence: list[dict]
    decision_owner: str
    resolution: Optional[dict] = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "conflict_id": self.conflict_id,
            "topic": self.topic,
            "agents_involved": self.agents_involved,
            "evidence": self.evidence,
            "decision_owner": self.decision_owner,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


# ==================== Contract Registry ====================

class ContractRegistry:
    """Registry for contract schemas and validation."""
    
    _contracts: dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, contract_type: type) -> None:
        """Register a contract type."""
        cls._contracts[name] = contract_type
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """Get a contract type by name."""
        return cls._contracts.get(name)
    
    @classmethod
    def validate_input(cls, contract_name: str, data: ContractInput) -> list[Violation]:
        """Validate contract input."""
        return data.validate()
    
    @classmethod
    def validate_output(cls, contract_name: str, data: ContractOutput) -> list[Violation]:
        """Validate contract output."""
        return data.validate()


# Register all contracts
ContractRegistry.register("requirements", RequirementsOutput)
ContractRegistry.register("architecture", ArchitectureOutput)
ContractRegistry.register("implementation", ImplementationOutput)
ContractRegistry.register("code_review", CodeReviewOutput)
ContractRegistry.register("build_test", BuildTestOutput)
ContractRegistry.register("integration", IntegrationOutput)
