from typing import Optional
from datetime import datetime

from macds.agents.base import BaseAgent, AgentConfig, AgentRegistry
from macds.core.contracts import (
    CodeReviewInput, CodeReviewOutput, Violation, Verdict
)
from macds.core.memory import MemoryScope


class ReviewerAgent(BaseAgent[CodeReviewInput, CodeReviewOutput]):
    """
    Reviewer Agent - Code quality gatekeeper.
    
    Responsibilities:
    - Review code changes
    - Enforce coding standards
    - Identify security issues
    - Suggest improvements
    """
    
    name = "ReviewerAgent"
    authority_level = 7
    description = "Reviews code for quality, security, and standards compliance"
    owned_artifacts = []
    
    @property
    def system_prompt(self) -> str:
        return """You are the Reviewer Agent, responsible for code quality in MACDS.

Your responsibilities:
1. Review all code changes before integration
2. Enforce coding standards compliance
3. Identify security vulnerabilities
4. Check for bugs and logic errors

Key principles:
- Be thorough but constructive
- Provide actionable feedback
- Consider maintainability and readability
- Flag security issues as high priority

Review criteria:
- Does code follow API contracts?
- Are coding standards followed?
- Is error handling adequate?
- Are there security concerns?
- Is the code testable?

Output format: Always use structured contract output.
Verdict must be: pass, fail, needs_revision, or escalate."""
    
    @property
    def input_contract(self) -> type:
        return CodeReviewInput
    
    @property
    def output_contract(self) -> type:
        return CodeReviewOutput
    
    async def _execute_impl(self, input_data: CodeReviewInput) -> CodeReviewOutput:
        """Perform code review."""
        
        violations = []
        security_concerns = []
        suggested_patches = []
        quality_score = 100.0
        
        # Analyze the diff
        diff_analysis = self._analyze_diff(input_data.code_diff)
        
        # Check coding standards
        standard_violations = self._check_standards(
            input_data.code_diff,
            input_data.coding_standards
        )
        violations.extend(standard_violations)
        quality_score -= len(standard_violations) * 5
        
        # Check architecture constraints
        constraint_violations = self._check_constraints(
            input_data.code_diff,
            input_data.architecture_constraints
        )
        violations.extend(constraint_violations)
        quality_score -= len(constraint_violations) * 10
        
        # Security analysis
        security_issues = self._analyze_security(input_data.code_diff)
        security_concerns.extend(security_issues)
        quality_score -= len(security_issues) * 15
        
        # Generate suggested fixes
        for violation in violations:
            if violation.suggested_fix:
                suggested_patches.append({
                    "file": violation.location or "unknown",
                    "original": "",
                    "replacement": violation.suggested_fix
                })
        
        # Determine verdict
        has_errors = any(v.severity == "error" for v in violations)
        has_security = len(security_concerns) > 0
        
        if has_security:
            verdict = Verdict.FAIL
        elif has_errors:
            verdict = Verdict.NEEDS_REVISION
        elif quality_score >= 80:
            verdict = Verdict.PASS
        else:
            verdict = Verdict.NEEDS_REVISION
        
        # Store review patterns
        self.memory.learn_skill({
            "review_type": "code",
            "violations_found": len(violations),
            "verdict": verdict.value
        })
        
        return CodeReviewOutput(
            request_id=input_data.request_id,
            processing_agent=self.name,
            verdict=verdict,
            violations=violations,
            suggested_patches=suggested_patches,
            security_concerns=security_concerns,
            quality_score=max(0, quality_score),
            comments=self._generate_summary(violations, security_concerns, verdict)
        )
    
    def _analyze_diff(self, diff: str) -> dict:
        """Analyze diff structure."""
        lines = diff.split('\n')
        additions = sum(1 for l in lines if l.startswith('+') and not l.startswith('+++'))
        deletions = sum(1 for l in lines if l.startswith('-') and not l.startswith('---'))
        
        return {
            "additions": additions,
            "deletions": deletions,
            "total_changes": additions + deletions
        }
    
    def _check_standards(self, diff: str, standards: str) -> list[Violation]:
        """Check code against standards."""
        violations = []
        lines = diff.split('\n')
        
        for i, line in enumerate(lines):
            if not line.startswith('+'):
                continue
            
            code = line[1:]  # Remove + prefix
            
            # Check line length
            if len(code) > 100:
                violations.append(Violation(
                    rule_id="STD-001",
                    severity="warning",
                    message=f"Line exceeds 100 characters ({len(code)})",
                    location=f"line {i + 1}",
                    suggested_fix="Break line into multiple lines"
                ))
            
            # Check for TODO without issue reference
            if "TODO" in code and "#" not in code:
                violations.append(Violation(
                    rule_id="STD-002",
                    severity="info",
                    message="TODO comment should reference an issue number",
                    location=f"line {i + 1}"
                ))
            
            # Check for print statements (should use logging)
            if "print(" in code and "# debug" not in code.lower():
                violations.append(Violation(
                    rule_id="STD-003",
                    severity="warning",
                    message="Use logging instead of print statements",
                    location=f"line {i + 1}",
                    suggested_fix="Replace print() with logging.info()"
                ))
            
            # Check for bare except
            if "except:" in code and "Exception" not in code:
                violations.append(Violation(
                    rule_id="STD-004",
                    severity="error",
                    message="Bare except clause catches all exceptions",
                    location=f"line {i + 1}",
                    suggested_fix="Use 'except Exception:' or specific exception type"
                ))
        
        return violations
    
    def _check_constraints(self, diff: str, constraints: list[str]) -> list[Violation]:
        """Check code against architecture constraints."""
        violations = []
        diff_lower = diff.lower()
        
        for constraint in constraints:
            constraint_lower = constraint.lower()
            
            # Check for circular dependency indicators
            if "no circular" in constraint_lower:
                if "from . import" in diff and "import ." in diff:
                    violations.append(Violation(
                        rule_id="ARCH-001",
                        severity="error",
                        message="Possible circular dependency detected",
                        suggested_fix="Refactor to avoid circular imports"
                    ))
            
            # Check for direct database access
            if "repository" in constraint_lower:
                if "sql" in diff_lower or "query(" in diff_lower:
                    if "repository" not in diff_lower:
                        violations.append(Violation(
                            rule_id="ARCH-002",
                            severity="error",
                            message="Direct database access outside repository layer",
                            suggested_fix="Use repository pattern for data access"
                        ))
        
        return violations
    
    def _analyze_security(self, diff: str) -> list[str]:
        """Analyze code for security issues."""
        concerns = []
        diff_lower = diff.lower()
        
        # Check for hardcoded secrets
        secret_patterns = ["password =", "secret =", "api_key =", "token ="]
        for pattern in secret_patterns:
            if pattern in diff_lower:
                if "config" not in diff_lower and "env" not in diff_lower:
                    concerns.append(f"Possible hardcoded secret ({pattern.strip()})")
        
        # Check for SQL injection vulnerability
        if "format(" in diff and "select" in diff_lower:
            concerns.append("Possible SQL injection vulnerability - use parameterized queries")
        
        # Check for eval/exec usage
        if "eval(" in diff or "exec(" in diff:
            concerns.append("Use of eval/exec is a security risk")
        
        # Check for shell command execution
        if "subprocess" in diff or "os.system" in diff:
            if "shell=true" in diff_lower:
                concerns.append("Shell=True in subprocess is a security risk")
        
        return concerns
    
    def _generate_summary(
        self,
        violations: list[Violation],
        security: list[str],
        verdict: Verdict
    ) -> str:
        """Generate review summary."""
        parts = []
        
        if verdict == Verdict.PASS:
            parts.append("Code review passed.")
        elif verdict == Verdict.FAIL:
            parts.append("Code review FAILED - issues must be resolved.")
        else:
            parts.append("Code review requires revisions.")
        
        if violations:
            errors = sum(1 for v in violations if v.severity == "error")
            warnings = sum(1 for v in violations if v.severity == "warning")
            parts.append(f"Found {errors} errors and {warnings} warnings.")
        
        if security:
            parts.append(f"SECURITY: {len(security)} concern(s) identified.")
        
        return " ".join(parts)


# Register the agent
AgentRegistry.register(ReviewerAgent)
