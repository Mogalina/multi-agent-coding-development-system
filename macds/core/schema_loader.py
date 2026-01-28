from pathlib import Path
from typing import Any, Optional
import yaml
import json
import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of schema validation."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


class SchemaLoader:
    """
    Loads and caches YAML schemas for contracts and artifacts.
    """
    
    def __init__(self, schemas_dir: Optional[Path] = None):
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent.parent / "schemas"
        self.schemas_dir = schemas_dir
        self._contract_cache: dict[str, dict] = {}
        self._artifact_cache: dict[str, dict] = {}
        self._load_all_schemas()
    
    def _load_all_schemas(self) -> None:
        """Load all schemas into cache."""
        contracts_dir = self.schemas_dir / "contracts"
        artifacts_dir = self.schemas_dir / "artifacts"
        
        if contracts_dir.exists():
            for schema_file in contracts_dir.glob("*.yaml"):
                try:
                    with open(schema_file) as f:
                        schema = yaml.safe_load(f)
                        name = schema.get("name", schema_file.stem)
                        self._contract_cache[name] = schema
                except Exception:
                    pass
        
        if artifacts_dir.exists():
            for schema_file in artifacts_dir.glob("*.yaml"):
                try:
                    with open(schema_file) as f:
                        schema = yaml.safe_load(f)
                        name = schema.get("name", schema_file.stem)
                        self._artifact_cache[name] = schema
                except Exception:
                    pass
    
    def get_contract_schema(self, name: str) -> Optional[dict]:
        """Get a contract schema by name."""
        return self._contract_cache.get(name)
    
    def get_artifact_schema(self, name: str) -> Optional[dict]:
        """Get an artifact schema by name."""
        return self._artifact_cache.get(name)
    
    def list_contracts(self) -> list[str]:
        """List all available contract schemas."""
        return list(self._contract_cache.keys())
    
    def list_artifacts(self) -> list[str]:
        """List all available artifact schemas."""
        return list(self._artifact_cache.keys())
    
    def validate_contract_input(self, contract_name: str, data: dict) -> ValidationResult:
        """Validate input data against a contract schema."""
        schema = self.get_contract_schema(contract_name)
        if not schema:
            return ValidationResult(valid=False, errors=[f"Unknown contract: {contract_name}"])
        
        input_schema = schema.get("input", {})
        return self._validate_against_schema(data, input_schema)
    
    def validate_contract_output(self, contract_name: str, data: dict) -> ValidationResult:
        """Validate output data against a contract schema."""
        schema = self.get_contract_schema(contract_name)
        if not schema:
            return ValidationResult(valid=False, errors=[f"Unknown contract: {contract_name}"])
        
        output_schema = schema.get("output", {})
        result = self._validate_against_schema(data, output_schema)
        
        # Apply validation rules
        for rule in schema.get("validation_rules", []):
            rule_result = self._apply_validation_rule(data, rule)
            if rule_result:
                if rule.get("severity") == "error":
                    result.errors.append(rule_result)
                    result.valid = False
                else:
                    result.warnings.append(rule_result)
        
        return result
    
    def validate_artifact(self, artifact_name: str, content: str) -> ValidationResult:
        """Validate artifact content against its schema."""
        schema = self.get_artifact_schema(artifact_name)
        if not schema:
            return ValidationResult(valid=False, errors=[f"Unknown artifact: {artifact_name}"])
        
        errors = []
        warnings = []
        
        # Check required sections for markdown artifacts
        if schema.get("format") == "markdown":
            structure = schema.get("structure", {})
            for section in structure.get("sections", []):
                if section.get("required"):
                    heading = section.get("heading", "")
                    if heading and heading not in content:
                        errors.append(f"Missing required section: {heading}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_against_schema(self, data: dict, schema: dict) -> ValidationResult:
        """Validate data against a JSON schema-like definition."""
        errors = []
        warnings = []
        
        # Check required fields
        for field in schema.get("required", []):
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Check property types
        for prop_name, prop_schema in schema.get("properties", {}).items():
            if prop_name in data:
                value = data[prop_name]
                expected_type = prop_schema.get("type")
                
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field {prop_name} must be a string")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Field {prop_name} must be an array")
                elif expected_type == "object" and not isinstance(value, dict):
                    errors.append(f"Field {prop_name} must be an object")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field {prop_name} must be a number")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Field {prop_name} must be a boolean")
                
                # Check pattern
                if "pattern" in prop_schema and isinstance(value, str):
                    if not re.match(prop_schema["pattern"], value):
                        errors.append(f"Field {prop_name} does not match pattern {prop_schema['pattern']}")
                
                # Check enum
                if "enum" in prop_schema:
                    if value not in prop_schema["enum"]:
                        errors.append(f"Field {prop_name} must be one of {prop_schema['enum']}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _apply_validation_rule(self, data: dict, rule: dict) -> Optional[str]:
        """Apply a validation rule and return error message if failed."""
        # Simplified rule evaluation
        condition = rule.get("condition", "")
        message = rule.get("message", "Validation failed")
        
        # Handle common conditions
        if "len(" in condition and ") > 0" in condition:
            field_match = re.search(r"len\((\w+)\)", condition)
            if field_match:
                field_name = field_match.group(1)
                if field_name in data:
                    if len(data[field_name]) == 0:
                        return message
        
        return None


# Global instance
_schema_loader: Optional[SchemaLoader] = None


def get_schema_loader() -> SchemaLoader:
    """Get the global schema loader instance."""
    global _schema_loader
    if _schema_loader is None:
        _schema_loader = SchemaLoader()
    return _schema_loader
