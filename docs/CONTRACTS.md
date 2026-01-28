# MACDS Contract System

## Overview

The contract system ensures structured, validated communication between agents. Every agent input and output is defined by a typed contract that specifies required fields, types, and validation rules.

## Design Principles

1. **No Unstructured Output** - All agent outputs conform to defined schemas
2. **Validation at Boundaries** - Inputs validated on entry, outputs on exit
3. **Schema-Driven** - YAML schemas define contract structure
4. **Versioned** - Contracts support version evolution

## Contract Structure

### Base Classes

```python
@dataclass
class ContractInput:
    request_id: str
    
    def to_dict(self) -> dict:
        # Serialize to dictionary

@dataclass
class ContractOutput:
    request_id: str
    
    def validate(self) -> list[Violation]:
        # Return validation errors
```

### Violation Type

```python
@dataclass
class Violation:
    rule_id: str      # e.g., "REQ-001"
    severity: str     # "error" | "warning" | "info"
    message: str
    location: str     # Optional location in code/document
    suggested_fix: str  # Optional fix suggestion
```

## Available Contracts

### RequirementsContract

Used by ProductAgent for requirements definition.

**Input:**
```yaml
request_id: string
user_request: string
context: string (optional)
constraints: string[] (optional)
```

**Output:**
```yaml
request_id: string
requirements:
  - id: string (REQ-NNN)
    description: string
    priority: enum(high, medium, low)
acceptance_criteria: string[]
constraints: string[]
risks: string[] (optional)
```

### ArchitectureContract

Used by ArchitectAgent for system design.

**Input:**
```yaml
request_id: string
requirements: object[]
existing_architecture: string (optional)
constraints: string[] (optional)
```

**Output:**
```yaml
request_id: string
components:
  - name: string
    responsibility: string
    interfaces: string[]
    dependencies: string[]
invariants: string[]
design_decisions:
  - id: string (DD-YYYYMMDD-NNN)
    decision: string
    rationale: string
api_contracts: object[]
```

### ImplementationContract

Used by ImplementationAgent for code generation.

**Input:**
```yaml
request_id: string
task_description: string
architecture: object
api_contract: object (optional)
coding_standards: string (optional)
target_files: string[] (optional)
```

**Output:**
```yaml
request_id: string
files_created:
  - path: string
    content: string
    language: string
files_modified:
  - path: string
    diff: string
    description: string
files_deleted: string[]
api_compliance: boolean
implementation_notes: string (optional)
```

### CodeReviewContract

Used by ReviewerAgent for code review.

**Input:**
```yaml
request_id: string
code_diff: string
architecture_constraints: string[]
coding_standards: string
files_to_review: string[] (optional)
```

**Output:**
```yaml
request_id: string
verdict: enum(pass, fail, needs_revision, escalate)
violations:
  - rule_id: string
    severity: string
    message: string
    location: string (optional)
    suggested_fix: string (optional)
suggested_patches:
  - file: string
    original: string
    replacement: string
security_concerns: string[]
quality_score: number (0-100)
```

### BuildTestContract

Used by BuildTestAgent for build and test execution.

**Input:**
```yaml
request_id: string
source_files: string[]
test_files: string[]
build_command: string (optional)
test_command: string (optional)
```

**Output:**
```yaml
request_id: string
build_success: boolean
test_success: boolean
test_results:
  passed: integer
  failed: integer
  skipped: integer
  coverage: number
metrics:
  coverage_pct: number
  duration_s: number
security_scan:
  scanner: string
  vulnerabilities: object[]
  risk_level: enum(low, medium, high, critical)
```

### IntegrationContract

Used by IntegratorAgent for change integration.

**Input:**
```yaml
request_id: string
changes: object[]
target_branch: string
review_approval: boolean
build_approval: boolean
```

**Output:**
```yaml
request_id: string
success: boolean
merged_files: string[]
conflicts:
  - file: string
    type: enum(merge_conflict, lock_conflict, permission_denied)
    resolved: boolean
commit_sha: string
```

## Schema Validation

### Loading Schemas

```python
from macds.core.schema_loader import get_schema_loader

loader = get_schema_loader()

# List available contracts
contracts = loader.list_contracts()

# Validate input
result = loader.validate_contract_input("requirements", data)
if not result.valid:
    print(result.errors)
```

### Validation Rules

Each contract can define validation rules in the schema:

```yaml
validation_rules:
  - id: REQ-001
    severity: error
    condition: "len(requirements) > 0"
    message: "Requirements cannot be empty"
```

## Contract Evolution

### Versioning

Contracts include a version field:

```yaml
name: requirements
version: "1.0"
```

### Backward Compatibility

When updating contracts:
1. Add new optional fields
2. Do not remove required fields
3. Update version number
4. Document changes in changelog

## Creating Custom Contracts

### Define the Schema

Create a YAML file in `schemas/contracts/`:

```yaml
name: custom
version: "1.0"
description: Custom contract

input:
  type: object
  required:
    - request_id
    - custom_field
  properties:
    request_id:
      type: string
    custom_field:
      type: string

output:
  type: object
  required:
    - request_id
    - result
  properties:
    request_id:
      type: string
    result:
      type: object

validation_rules:
  - id: CUSTOM-001
    severity: error
    condition: "result is not None"
    message: "Result is required"
```

### Define the Python Classes

```python
@dataclass
class CustomInput(ContractInput):
    custom_field: str

@dataclass
class CustomOutput(ContractOutput):
    result: dict
    
    def validate(self) -> list[Violation]:
        violations = []
        if not self.result:
            violations.append(Violation(
                rule_id="CUSTOM-001",
                severity="error",
                message="Result is required"
            ))
        return violations
```
