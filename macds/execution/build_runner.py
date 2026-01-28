import subprocess
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class BuildSystem(str, Enum):
    """Supported build systems."""
    PYTHON = "python"
    NODE = "node"
    MAKE = "make"
    GRADLE = "gradle"
    MAVEN = "maven"
    CARGO = "cargo"
    GO = "go"
    CUSTOM = "custom"


@dataclass
class BuildResult:
    """Result of a build execution."""
    success: bool
    build_system: BuildSystem
    duration_seconds: float
    output: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "build_system": self.build_system.value,
            "duration_seconds": self.duration_seconds,
            "output": self.output[:1000] if self.output else "",
            "errors": self.errors,
            "warnings": self.warnings,
            "artifacts": self.artifacts
        }


class BuildRunner:
    """
    Executes build processes for various build systems.
    """
    
    def __init__(self, project_root: Optional[Path] = None, timeout: int = 300):
        self.project_root = project_root or Path.cwd()
        self.timeout = timeout
    
    def detect_build_system(self) -> BuildSystem:
        """Auto-detect the build system from project files."""
        indicators = {
            "pyproject.toml": BuildSystem.PYTHON,
            "setup.py": BuildSystem.PYTHON,
            "requirements.txt": BuildSystem.PYTHON,
            "package.json": BuildSystem.NODE,
            "Makefile": BuildSystem.MAKE,
            "build.gradle": BuildSystem.GRADLE,
            "pom.xml": BuildSystem.MAVEN,
            "Cargo.toml": BuildSystem.CARGO,
            "go.mod": BuildSystem.GO,
        }
        
        for file, system in indicators.items():
            if (self.project_root / file).exists():
                return system
        
        return BuildSystem.CUSTOM
    
    def run(
        self,
        command: Optional[str] = None,
        build_system: Optional[BuildSystem] = None
    ) -> BuildResult:
        """
        Execute a build.
        
        Args:
            command: Custom build command (optional)
            build_system: Build system to use (auto-detected if not specified)
        """
        start_time = datetime.now()
        
        if build_system is None:
            build_system = self.detect_build_system()
        
        if command is None:
            command = self._get_default_command(build_system)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            output = result.stdout + result.stderr
            
            errors = self._extract_errors(output, build_system)
            warnings = self._extract_warnings(output, build_system)
            artifacts = self._find_artifacts(build_system)
            
            return BuildResult(
                success=result.returncode == 0,
                build_system=build_system,
                duration_seconds=duration,
                output=output,
                errors=errors,
                warnings=warnings,
                artifacts=artifacts
            )
            
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            return BuildResult(
                success=False,
                build_system=build_system,
                duration_seconds=duration,
                errors=[f"Build timed out after {self.timeout} seconds"]
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return BuildResult(
                success=False,
                build_system=build_system,
                duration_seconds=duration,
                errors=[str(e)]
            )
    
    def _get_default_command(self, build_system: BuildSystem) -> str:
        """Get the default build command for a build system."""
        commands = {
            BuildSystem.PYTHON: "python -m py_compile *.py",
            BuildSystem.NODE: "npm run build",
            BuildSystem.MAKE: "make",
            BuildSystem.GRADLE: "./gradlew build",
            BuildSystem.MAVEN: "mvn compile",
            BuildSystem.CARGO: "cargo build",
            BuildSystem.GO: "go build ./...",
            BuildSystem.CUSTOM: "echo 'No build command configured'"
        }
        return commands.get(build_system, "echo 'Unknown build system'")
    
    def _extract_errors(self, output: str, build_system: BuildSystem) -> list[str]:
        """Extract error messages from build output."""
        errors = []
        error_indicators = ["error:", "Error:", "ERROR:", "fatal:", "FATAL:"]
        
        for line in output.split("\n"):
            if any(indicator in line for indicator in error_indicators):
                errors.append(line.strip())
        
        return errors[:20]  # Limit to first 20 errors
    
    def _extract_warnings(self, output: str, build_system: BuildSystem) -> list[str]:
        """Extract warning messages from build output."""
        warnings = []
        warning_indicators = ["warning:", "Warning:", "WARNING:"]
        
        for line in output.split("\n"):
            if any(indicator in line for indicator in warning_indicators):
                warnings.append(line.strip())
        
        return warnings[:20]  # Limit to first 20 warnings
    
    def _find_artifacts(self, build_system: BuildSystem) -> list[str]:
        """Find build artifacts."""
        artifact_dirs = {
            BuildSystem.PYTHON: ["dist", "build", "*.egg-info"],
            BuildSystem.NODE: ["dist", "build", "node_modules/.cache"],
            BuildSystem.GRADLE: ["build/libs"],
            BuildSystem.MAVEN: ["target"],
            BuildSystem.CARGO: ["target/release", "target/debug"],
            BuildSystem.GO: ["bin"],
        }
        
        artifacts = []
        patterns = artifact_dirs.get(build_system, [])
        
        for pattern in patterns:
            for path in self.project_root.glob(pattern):
                if path.exists():
                    artifacts.append(str(path.relative_to(self.project_root)))
        
        return artifacts


def run_build(
    project_root: Optional[Path] = None,
    command: Optional[str] = None
) -> BuildResult:
    """Convenience function to run a build."""
    runner = BuildRunner(project_root)
    return runner.run(command)
