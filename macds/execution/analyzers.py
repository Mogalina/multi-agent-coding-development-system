import subprocess
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Severity(str, Enum):
    """Issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """Categories of analysis issues."""
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    BUG = "bug"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"


@dataclass
class AnalysisIssue:
    """Individual analysis issue."""
    file: str
    line: int
    column: int = 0
    severity: Severity = Severity.WARNING
    category: IssueCategory = IssueCategory.STYLE
    rule_id: str = ""
    message: str = ""
    suggestion: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "category": self.category.value,
            "rule_id": self.rule_id,
            "message": self.message,
            "suggestion": self.suggestion
        }


@dataclass
class AnalysisResult:
    """Result of static analysis."""
    success: bool
    analyzer: str
    files_analyzed: int = 0
    issues: list[AnalysisIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "analyzer": self.analyzer,
            "files_analyzed": self.files_analyzed,
            "issues": [i.to_dict() for i in self.issues[:100]],
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count
        }


class PythonAnalyzer:
    """Analyzes Python code using flake8, mypy, and bandit."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
    
    def run_flake8(self, paths: Optional[list[str]] = None) -> AnalysisResult:
        """Run flake8 linting."""
        target = " ".join(paths) if paths else "."
        
        try:
            result = subprocess.run(
                f"python -m flake8 {target} --format=json",
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            issues = []
            files_seen = set()
            
            # Parse output (flake8 outputs one issue per line)
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                match = re.match(r"(.+):(\d+):(\d+): (\w+) (.+)", line)
                if match:
                    file, line_num, col, code, msg = match.groups()
                    files_seen.add(file)
                    issues.append(AnalysisIssue(
                        file=file,
                        line=int(line_num),
                        column=int(col),
                        severity=Severity.ERROR if code.startswith("E") else Severity.WARNING,
                        category=IssueCategory.STYLE,
                        rule_id=code,
                        message=msg
                    ))
            
            return AnalysisResult(
                success=len([i for i in issues if i.severity == Severity.ERROR]) == 0,
                analyzer="flake8",
                files_analyzed=len(files_seen),
                issues=issues,
                error_count=len([i for i in issues if i.severity == Severity.ERROR]),
                warning_count=len([i for i in issues if i.severity == Severity.WARNING])
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer="flake8",
                issues=[AnalysisIssue(
                    file="",
                    line=0,
                    severity=Severity.ERROR,
                    message=str(e)
                )]
            )
    
    def run_security_scan(self, paths: Optional[list[str]] = None) -> AnalysisResult:
        """Run security analysis using bandit."""
        target = " ".join(paths) if paths else "."
        
        try:
            result = subprocess.run(
                f"python -m bandit -r {target} -f json",
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            issues = []
            try:
                data = json.loads(result.stdout)
                for item in data.get("results", []):
                    severity_map = {
                        "LOW": Severity.INFO,
                        "MEDIUM": Severity.WARNING,
                        "HIGH": Severity.ERROR
                    }
                    issues.append(AnalysisIssue(
                        file=item.get("filename", ""),
                        line=item.get("line_number", 0),
                        severity=severity_map.get(item.get("issue_severity", "LOW"), Severity.INFO),
                        category=IssueCategory.SECURITY,
                        rule_id=item.get("test_id", ""),
                        message=item.get("issue_text", "")
                    ))
            except json.JSONDecodeError:
                pass
            
            return AnalysisResult(
                success=len([i for i in issues if i.severity in [Severity.ERROR, Severity.CRITICAL]]) == 0,
                analyzer="bandit",
                files_analyzed=len(set(i.file for i in issues)),
                issues=issues,
                error_count=len([i for i in issues if i.severity in [Severity.ERROR, Severity.CRITICAL]]),
                warning_count=len([i for i in issues if i.severity == Severity.WARNING])
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer="bandit",
                issues=[AnalysisIssue(
                    file="",
                    line=0,
                    severity=Severity.ERROR,
                    message=str(e)
                )]
            )


class JavaScriptAnalyzer:
    """Analyzes JavaScript/TypeScript code using ESLint."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
    
    def run_eslint(self, paths: Optional[list[str]] = None) -> AnalysisResult:
        """Run ESLint analysis."""
        target = " ".join(paths) if paths else "."
        
        try:
            result = subprocess.run(
                f"npx eslint {target} --format json",
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            issues = []
            files_analyzed = 0
            
            try:
                data = json.loads(result.stdout)
                files_analyzed = len(data)
                
                for file_result in data:
                    file_path = file_result.get("filePath", "")
                    for msg in file_result.get("messages", []):
                        severity_map = {1: Severity.WARNING, 2: Severity.ERROR}
                        issues.append(AnalysisIssue(
                            file=file_path,
                            line=msg.get("line", 0),
                            column=msg.get("column", 0),
                            severity=severity_map.get(msg.get("severity", 1), Severity.WARNING),
                            category=IssueCategory.STYLE,
                            rule_id=msg.get("ruleId", ""),
                            message=msg.get("message", "")
                        ))
            except json.JSONDecodeError:
                pass
            
            return AnalysisResult(
                success=result.returncode == 0,
                analyzer="eslint",
                files_analyzed=files_analyzed,
                issues=issues,
                error_count=len([i for i in issues if i.severity == Severity.ERROR]),
                warning_count=len([i for i in issues if i.severity == Severity.WARNING])
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer="eslint",
                issues=[AnalysisIssue(
                    file="",
                    line=0,
                    severity=Severity.ERROR,
                    message=str(e)
                )]
            )


def analyze_python(
    project_root: Optional[Path] = None,
    paths: Optional[list[str]] = None,
    include_security: bool = True
) -> list[AnalysisResult]:
    """Convenience function to analyze Python code."""
    analyzer = PythonAnalyzer(project_root)
    results = [analyzer.run_flake8(paths)]
    
    if include_security:
        results.append(analyzer.run_security_scan(paths))
    
    return results


def analyze_javascript(
    project_root: Optional[Path] = None,
    paths: Optional[list[str]] = None
) -> list[AnalysisResult]:
    """Convenience function to analyze JavaScript code."""
    analyzer = JavaScriptAnalyzer(project_root)
    return [analyzer.run_eslint(paths)]
