from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from datetime import datetime
from pathlib import Path
import json
import subprocess
import shutil


class ArtifactType(str, Enum):
    """Types of artifacts in the system."""
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    DESIGN_DECISIONS = "design_decisions"
    API_CONTRACTS = "api_contracts"
    CODING_STANDARDS = "coding_standards"
    RISK_REGISTER = "risk_register"
    SOURCE_CODE = "source_code"
    TEST_CODE = "test_code"
    DOCUMENTATION = "documentation"
    CONFIG = "config"


# Artifact type to filename mapping
ARTIFACT_FILES = {
    ArtifactType.REQUIREMENTS: "REQUIREMENTS.md",
    ArtifactType.ARCHITECTURE: "ARCHITECTURE.md",
    ArtifactType.DESIGN_DECISIONS: "DESIGN_DECISIONS.log",
    ArtifactType.API_CONTRACTS: "API_CONTRACTS.yaml",
    ArtifactType.CODING_STANDARDS: "CODING_STANDARDS.md",
    ArtifactType.RISK_REGISTER: "RISK_REGISTER.md"
}

# Artifact ownership by agent
ARTIFACT_OWNERS = {
    ArtifactType.REQUIREMENTS: "ProductAgent",
    ArtifactType.ARCHITECTURE: "ArchitectAgent",
    ArtifactType.DESIGN_DECISIONS: "ArchitectAgent",
    ArtifactType.API_CONTRACTS: "ArchitectAgent",
    ArtifactType.CODING_STANDARDS: "ArchitectAgent",
    ArtifactType.RISK_REGISTER: "ProductAgent",
    ArtifactType.SOURCE_CODE: "ImplementationAgent",
    ArtifactType.TEST_CODE: "BuildTestAgent"
}


@dataclass
class ArtifactVersion:
    """A version of an artifact."""
    version_id: str
    content: str
    created_at: datetime
    created_by: str
    commit_sha: Optional[str] = None
    message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "content_length": len(self.content),
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "commit_sha": self.commit_sha,
            "message": self.message
        }


@dataclass
class Artifact:
    """An artifact with version history."""
    name: str
    artifact_type: ArtifactType
    owner: str
    current_version: Optional[ArtifactVersion] = None
    versions: list[ArtifactVersion] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def content(self) -> str:
        """Get current content."""
        if self.current_version:
            return self.current_version.content
        return ""
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.artifact_type.value,
            "owner": self.owner,
            "version_count": len(self.versions),
            "current_version": self.current_version.to_dict() if self.current_version else None,
            "created_at": self.created_at.isoformat()
        }


class ArtifactStore:
    """
    Git-backed artifact store.
    
    Features:
    - Versioned storage
    - Typed artifacts
    - Ownership enforcement
    - Diff tracking
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(".")
        self.artifacts_dir = self.project_root / ".macds" / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self._artifacts: dict[str, Artifact] = {}
        self._init_git()
        self._load_metadata()
    
    def _init_git(self) -> None:
        """Initialize git repo if not exists."""
        git_dir = self.artifacts_dir / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=self.artifacts_dir,
                    capture_output=True,
                    check=True
                )
            except Exception:
                pass  # Continue without git if not available
    
    def _load_metadata(self) -> None:
        """Load artifact metadata."""
        meta_file = self.artifacts_dir / "metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file) as f:
                    data = json.load(f)
                    for name, artifact_data in data.get("artifacts", {}).items():
                        artifact_type = ArtifactType(artifact_data["type"])
                        self._artifacts[name] = Artifact(
                            name=name,
                            artifact_type=artifact_type,
                            owner=artifact_data["owner"],
                            created_at=datetime.fromisoformat(artifact_data["created_at"])
                        )
                        # Load current content
                        artifact_file = self.artifacts_dir / name
                        if artifact_file.exists():
                            with open(artifact_file) as af:
                                content = af.read()
                                self._artifacts[name].current_version = ArtifactVersion(
                                    version_id="current",
                                    content=content,
                                    created_at=datetime.now(),
                                    created_by=artifact_data["owner"]
                                )
            except Exception:
                pass
    
    def _save_metadata(self) -> None:
        """Save artifact metadata."""
        meta_file = self.artifacts_dir / "metadata.json"
        data = {
            "version": "1.0",
            "saved_at": datetime.now().isoformat(),
            "artifacts": {
                name: artifact.to_dict()
                for name, artifact in self._artifacts.items()
            }
        }
        with open(meta_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _git_commit(self, message: str, files: list[str]) -> Optional[str]:
        """Commit changes to git."""
        try:
            for file in files:
                subprocess.run(
                    ["git", "add", file],
                    cwd=self.artifacts_dir,
                    capture_output=True
                )
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.artifacts_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.artifacts_dir,
                    capture_output=True,
                    text=True
                )
                return sha_result.stdout.strip()
        except Exception:
            pass
        return None
    
    def get_owner(self, artifact_type: ArtifactType) -> str:
        """Get the owner agent for an artifact type."""
        return ARTIFACT_OWNERS.get(artifact_type, "ArchitectAgent")
    
    def can_modify(self, artifact_name: str, agent_name: str) -> bool:
        """Check if an agent can modify an artifact."""
        if artifact_name not in self._artifacts:
            return True  # New artifacts can be created
        
        artifact = self._artifacts[artifact_name]
        return artifact.owner == agent_name
    
    def create(
        self,
        name: str,
        content: str,
        artifact_type: ArtifactType,
        created_by: str,
        message: str = ""
    ) -> Artifact:
        """Create a new artifact."""
        owner = self.get_owner(artifact_type)
        
        # Create artifact entry
        artifact = Artifact(
            name=name,
            artifact_type=artifact_type,
            owner=owner
        )
        
        # Create version
        version = ArtifactVersion(
            version_id="v1",
            content=content,
            created_at=datetime.now(),
            created_by=created_by,
            message=message or f"Created {name}"
        )
        
        artifact.current_version = version
        artifact.versions.append(version)
        
        # Save to disk
        artifact_file = self.artifacts_dir / name
        with open(artifact_file, "w") as f:
            f.write(content)
        
        # Commit to git
        commit_sha = self._git_commit(message or f"Created {name}", [name])
        if commit_sha:
            version.commit_sha = commit_sha
        
        self._artifacts[name] = artifact
        self._save_metadata()
        
        return artifact
    
    def update(
        self,
        name: str,
        content: str,
        updated_by: str,
        message: str = "",
        force: bool = False
    ) -> Optional[Artifact]:
        """
        Update an existing artifact.
        
        Args:
            force: If True, bypass ownership check
        """
        if name not in self._artifacts:
            return None
        
        artifact = self._artifacts[name]
        
        # Check ownership
        if not force and not self.can_modify(name, updated_by):
            raise PermissionError(
                f"Agent {updated_by} cannot modify {name} (owner: {artifact.owner})"
            )
        
        # Create new version
        version_num = len(artifact.versions) + 1
        version = ArtifactVersion(
            version_id=f"v{version_num}",
            content=content,
            created_at=datetime.now(),
            created_by=updated_by,
            message=message or f"Updated {name}"
        )
        
        artifact.current_version = version
        artifact.versions.append(version)
        
        # Save to disk
        artifact_file = self.artifacts_dir / name
        with open(artifact_file, "w") as f:
            f.write(content)
        
        # Commit to git
        commit_sha = self._git_commit(message or f"Updated {name}", [name])
        if commit_sha:
            version.commit_sha = commit_sha
        
        self._save_metadata()
        return artifact
    
    def read(self, name: str) -> Optional[str]:
        """Read artifact content."""
        if name in self._artifacts and self._artifacts[name].current_version:
            return self._artifacts[name].content
        
        # Try to read from disk
        artifact_file = self.artifacts_dir / name
        if artifact_file.exists():
            with open(artifact_file) as f:
                return f.read()
        
        return None
    
    def get(self, name: str) -> Optional[Artifact]:
        """Get artifact with metadata."""
        return self._artifacts.get(name)
    
    def list_artifacts(
        self,
        artifact_type: Optional[ArtifactType] = None,
        owner: Optional[str] = None
    ) -> list[Artifact]:
        """List artifacts matching criteria."""
        results = []
        for artifact in self._artifacts.values():
            if artifact_type and artifact.artifact_type != artifact_type:
                continue
            if owner and artifact.owner != owner:
                continue
            results.append(artifact)
        return results
    
    def get_diff(self, name: str, version1: str = None, version2: str = None) -> str:
        """Get diff between versions."""
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1", "HEAD", "--", name],
                cwd=self.artifacts_dir,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception:
            return ""
    
    def get_history(self, name: str, limit: int = 10) -> list[dict]:
        """Get version history for an artifact."""
        if name not in self._artifacts:
            return []
        
        artifact = self._artifacts[name]
        return [v.to_dict() for v in artifact.versions[-limit:]]
    
    def init_mandatory_artifacts(self, created_by: str = "system") -> list[str]:
        """Initialize all mandatory artifacts with templates."""
        created = []
        
        for artifact_type, filename in ARTIFACT_FILES.items():
            if filename not in self._artifacts:
                template = self._get_template(artifact_type)
                self.create(
                    name=filename,
                    content=template,
                    artifact_type=artifact_type,
                    created_by=created_by,
                    message=f"Initialize {filename}"
                )
                created.append(filename)
        
        return created
    
    def _get_template(self, artifact_type: ArtifactType) -> str:
        """Get template content for an artifact type."""
        templates = {
            ArtifactType.REQUIREMENTS: """# Requirements

## Functional Requirements
- [ ] FR-001: [Description]

## Non-Functional Requirements
- [ ] NFR-001: [Description]

## Acceptance Criteria
- [ ] AC-001: [Criterion]
""",
            ArtifactType.ARCHITECTURE: """# Architecture

## Overview
[System overview]

## Components
### Component 1
- Responsibility: 
- Interfaces:

## Invariants
1. [Invariant description]

## Design Decisions
See DESIGN_DECISIONS.log
""",
            ArtifactType.DESIGN_DECISIONS: """# Design Decisions Log

## DD-001: [Title]
- Date: 
- Status: proposed | accepted | rejected
- Context:
- Decision:
- Rationale:
- Alternatives Considered:
""",
            ArtifactType.API_CONTRACTS: """# API Contracts

contracts:
  - name: ExampleContract
    version: "1.0"
    input:
      type: object
      properties:
        request_id:
          type: string
    output:
      type: object
      properties:
        success:
          type: boolean
""",
            ArtifactType.CODING_STANDARDS: """# Coding Standards

## General
- Use clear, descriptive names
- Keep functions small and focused
- Write tests for all new code

## Python
- Follow PEP 8
- Use type hints
- Maximum line length: 100

## Documentation
- All public functions must have docstrings
- Use Google-style docstrings
""",
            ArtifactType.RISK_REGISTER: """# Risk Register

## R-001: [Risk Title]
- Probability: Low | Medium | High
- Impact: Low | Medium | High
- Mitigation:
- Status: Open | Mitigated | Closed
"""
        }
        
        return templates.get(artifact_type, "# " + artifact_type.value.title())
