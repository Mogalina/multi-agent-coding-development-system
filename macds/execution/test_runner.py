import subprocess
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class TestFramework(str, Enum):
    """Supported test frameworks."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    MOCHA = "mocha"
    JUNIT = "junit"
    GOTEST = "gotest"
    CARGO_TEST = "cargo_test"
    CUSTOM = "custom"


@dataclass
class TestCase:
    """Individual test case result."""
    name: str
    status: str  # passed, failed, skipped, error
    duration_ms: float = 0.0
    message: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "message": self.message
        }


@dataclass
class TestResult:
    """Result of test execution."""
    success: bool
    framework: TestFramework
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    coverage_percent: Optional[float] = None
    test_cases: list[TestCase] = field(default_factory=list)
    output: str = ""
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "framework": self.framework.value,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
            "coverage_percent": self.coverage_percent,
            "test_cases": [tc.to_dict() for tc in self.test_cases[:50]],
            "output": self.output[:2000] if self.output else ""
        }


class TestRunner:
    """
    Executes tests for various test frameworks.
    """
    
    def __init__(self, project_root: Optional[Path] = None, timeout: int = 600):
        self.project_root = project_root or Path.cwd()
        self.timeout = timeout
    
    def detect_framework(self) -> TestFramework:
        """Auto-detect the test framework from project files."""
        # Check for pytest
        if (self.project_root / "pytest.ini").exists():
            return TestFramework.PYTEST
        if (self.project_root / "pyproject.toml").exists():
            content = (self.project_root / "pyproject.toml").read_text()
            if "pytest" in content:
                return TestFramework.PYTEST
        
        # Check for Jest
        if (self.project_root / "jest.config.js").exists():
            return TestFramework.JEST
        if (self.project_root / "package.json").exists():
            content = (self.project_root / "package.json").read_text()
            if "jest" in content:
                return TestFramework.JEST
        
        # Check for Cargo
        if (self.project_root / "Cargo.toml").exists():
            return TestFramework.CARGO_TEST
        
        # Check for Go
        if (self.project_root / "go.mod").exists():
            return TestFramework.GOTEST
        
        # Default to pytest for Python projects
        if list(self.project_root.glob("**/*.py")):
            return TestFramework.PYTEST
        
        return TestFramework.CUSTOM
    
    def run(
        self,
        command: Optional[str] = None,
        framework: Optional[TestFramework] = None,
        with_coverage: bool = True
    ) -> TestResult:
        """
        Execute tests.
        
        Args:
            command: Custom test command (optional)
            framework: Test framework to use (auto-detected if not specified)
            with_coverage: Whether to collect coverage (if supported)
        """
        start_time = datetime.now()
        
        if framework is None:
            framework = self.detect_framework()
        
        if command is None:
            command = self._get_default_command(framework, with_coverage)
        
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
            
            # Parse results based on framework
            parsed = self._parse_output(output, framework)
            
            return TestResult(
                success=result.returncode == 0,
                framework=framework,
                total=parsed.get("total", 0),
                passed=parsed.get("passed", 0),
                failed=parsed.get("failed", 0),
                skipped=parsed.get("skipped", 0),
                errors=parsed.get("errors", 0),
                duration_seconds=duration,
                coverage_percent=parsed.get("coverage"),
                test_cases=parsed.get("test_cases", []),
                output=output
            )
            
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                success=False,
                framework=framework,
                duration_seconds=duration,
                output=f"Tests timed out after {self.timeout} seconds"
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                success=False,
                framework=framework,
                duration_seconds=duration,
                output=str(e)
            )
    
    def _get_default_command(self, framework: TestFramework, with_coverage: bool) -> str:
        """Get the default test command for a framework."""
        commands = {
            TestFramework.PYTEST: "python -m pytest -v" + (" --cov" if with_coverage else ""),
            TestFramework.UNITTEST: "python -m unittest discover -v",
            TestFramework.JEST: "npm test -- --coverage" if with_coverage else "npm test",
            TestFramework.MOCHA: "npm test",
            TestFramework.CARGO_TEST: "cargo test",
            TestFramework.GOTEST: "go test -v ./..." + (" -cover" if with_coverage else ""),
            TestFramework.CUSTOM: "echo 'No test command configured'"
        }
        return commands.get(framework, "echo 'Unknown test framework'")
    
    def _parse_output(self, output: str, framework: TestFramework) -> dict:
        """Parse test output to extract results."""
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "coverage": None,
            "test_cases": []
        }
        
        if framework == TestFramework.PYTEST:
            result = self._parse_pytest(output)
        elif framework == TestFramework.JEST:
            result = self._parse_jest(output)
        else:
            # Generic parsing
            result = self._parse_generic(output)
        
        return result
    
    def _parse_pytest(self, output: str) -> dict:
        """Parse pytest output."""
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "coverage": None,
            "test_cases": []
        }
        
        # Match summary line: "X passed, Y failed, Z skipped"
        summary_match = re.search(
            r"(\d+)\s+passed.*?(\d+)?\s*failed.*?(\d+)?\s*skipped",
            output,
            re.IGNORECASE
        )
        if summary_match:
            result["passed"] = int(summary_match.group(1) or 0)
            result["failed"] = int(summary_match.group(2) or 0)
            result["skipped"] = int(summary_match.group(3) or 0)
            result["total"] = result["passed"] + result["failed"] + result["skipped"]
        
        # Match coverage
        coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if coverage_match:
            result["coverage"] = float(coverage_match.group(1))
        
        return result
    
    def _parse_jest(self, output: str) -> dict:
        """Parse Jest output."""
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "coverage": None,
            "test_cases": []
        }
        
        # Match Jest summary
        tests_match = re.search(r"Tests:\s+(\d+)\s+passed.*?(\d+)?\s*failed", output)
        if tests_match:
            result["passed"] = int(tests_match.group(1) or 0)
            result["failed"] = int(tests_match.group(2) or 0)
            result["total"] = result["passed"] + result["failed"]
        
        # Match coverage
        coverage_match = re.search(r"All files\s+\|\s+[\d.]+\s+\|\s+[\d.]+\s+\|\s+[\d.]+\s+\|\s+([\d.]+)", output)
        if coverage_match:
            result["coverage"] = float(coverage_match.group(1))
        
        return result
    
    def _parse_generic(self, output: str) -> dict:
        """Generic output parsing."""
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "coverage": None,
            "test_cases": []
        }
        
        # Count PASS/FAIL lines
        result["passed"] = len(re.findall(r"\bPASS(?:ED)?\b", output, re.IGNORECASE))
        result["failed"] = len(re.findall(r"\bFAIL(?:ED)?\b", output, re.IGNORECASE))
        result["total"] = result["passed"] + result["failed"]
        
        return result


def run_tests(
    project_root: Optional[Path] = None,
    command: Optional[str] = None,
    with_coverage: bool = True
) -> TestResult:
    """Convenience function to run tests."""
    runner = TestRunner(project_root)
    return runner.run(command, with_coverage=with_coverage)
