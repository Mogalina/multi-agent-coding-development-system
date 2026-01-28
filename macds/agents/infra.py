from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field

from macds.agents.base import BaseAgent, AgentConfig, AgentRegistry
from macds.core.contracts import ContractInput, ContractOutput, Violation
from macds.core.memory import MemoryScope


@dataclass
class InfraInput(ContractInput):
    """Input for infrastructure operations."""
    operation: str  # deploy, configure, scale, monitor
    target_environment: str = "development"
    configuration: dict = field(default_factory=dict)


@dataclass
class InfraOutput(ContractOutput):
    """Output from infrastructure operations."""
    success: bool
    operation: str
    environment: str
    changes_applied: list[dict] = field(default_factory=list)
    logs: str = ""
    next_steps: list[str] = field(default_factory=list)


class InfraAgent(BaseAgent[InfraInput, InfraOutput]):
    """
    Infrastructure Agent - DevOps automation.
    
    Responsibilities:
    - Manage CI/CD pipelines
    - Infrastructure as Code
    - Environment configuration
    - Deployment orchestration
    """
    
    name = "InfraAgent"
    authority_level = 6
    description = "Manages CI/CD and infrastructure automation"
    owned_artifacts = []
    
    @property
    def system_prompt(self) -> str:
        return """You are the Infrastructure Agent, responsible for DevOps in MACDS.

Your responsibilities:
1. Manage CI/CD pipeline configurations
2. Apply Infrastructure as Code changes
3. Configure deployment environments
4. Monitor infrastructure health

Key principles:
- Infrastructure changes must be version controlled
- All deployments must be reproducible
- Security configurations are critical
- Document all infrastructure changes

Output format: Always use structured contract output.
Report all changes applied and their status."""
    
    @property
    def input_contract(self) -> type:
        return InfraInput
    
    @property
    def output_contract(self) -> type:
        return InfraOutput
    
    async def _execute_impl(self, input_data: InfraInput) -> InfraOutput:
        """Execute infrastructure operation."""
        
        operation = input_data.operation.lower()
        changes = []
        logs = []
        success = True
        next_steps = []
        
        logs.append(f"=== Infrastructure Operation: {operation} ===")
        logs.append(f"Environment: {input_data.target_environment}")
        logs.append(f"Started: {datetime.now().isoformat()}")
        
        if operation == "deploy":
            changes, logs_part = await self._handle_deploy(input_data)
            logs.extend(logs_part)
        
        elif operation == "configure":
            changes, logs_part = await self._handle_configure(input_data)
            logs.extend(logs_part)
        
        elif operation == "scale":
            changes, logs_part = await self._handle_scale(input_data)
            logs.extend(logs_part)
        
        elif operation == "monitor":
            changes, logs_part = await self._handle_monitor(input_data)
            logs.extend(logs_part)
        
        else:
            success = False
            logs.append(f"Unknown operation: {operation}")
        
        logs.append(f"=== Operation Complete ===")
        
        # Store operation in memory
        self.memory.remember(
            content={
                "operation": operation,
                "environment": input_data.target_environment,
                "success": success
            },
            scope=MemoryScope.PROJECT,
            tags=["infrastructure", operation]
        )
        
        return InfraOutput(
            request_id=input_data.request_id,
            processing_agent=self.name,
            success=success,
            operation=operation,
            environment=input_data.target_environment,
            changes_applied=changes,
            logs="\n".join(logs),
            next_steps=next_steps
        )
    
    async def _handle_deploy(self, input_data: InfraInput) -> tuple[list, list]:
        """Handle deployment operation."""
        changes = []
        logs = []
        
        config = input_data.configuration
        
        logs.append("Initiating deployment...")
        
        # Simulate deployment steps
        changes.append({
            "type": "deployment",
            "target": input_data.target_environment,
            "status": "completed",
            "version": config.get("version", "latest")
        })
        
        logs.append(f"Deployed version {config.get('version', 'latest')}")
        logs.append("Health checks passed")
        
        return changes, logs
    
    async def _handle_configure(self, input_data: InfraInput) -> tuple[list, list]:
        """Handle configuration operation."""
        changes = []
        logs = []
        
        config = input_data.configuration
        
        logs.append("Applying configuration...")
        
        for key, value in config.items():
            changes.append({
                "type": "config_update",
                "key": key,
                "status": "applied"
            })
            logs.append(f"Set {key}")
        
        logs.append("Configuration applied successfully")
        
        return changes, logs
    
    async def _handle_scale(self, input_data: InfraInput) -> tuple[list, list]:
        """Handle scaling operation."""
        changes = []
        logs = []
        
        config = input_data.configuration
        replicas = config.get("replicas", 1)
        
        logs.append(f"Scaling to {replicas} replicas...")
        
        changes.append({
            "type": "scale",
            "replicas": replicas,
            "status": "completed"
        })
        
        logs.append(f"Scaled to {replicas} replicas")
        
        return changes, logs
    
    async def _handle_monitor(self, input_data: InfraInput) -> tuple[list, list]:
        """Handle monitoring operation."""
        changes = []
        logs = []
        
        logs.append("Checking infrastructure health...")
        
        # Simulated health check
        health = {
            "status": "healthy",
            "cpu_usage": "45%",
            "memory_usage": "62%",
            "disk_usage": "38%"
        }
        
        changes.append({
            "type": "health_check",
            "result": health,
            "status": "completed"
        })
        
        logs.append(f"Health: {health['status']}")
        logs.append(f"CPU: {health['cpu_usage']}, Memory: {health['memory_usage']}")
        
        return changes, logs
    
    def generate_pipeline_config(self, pipeline_type: str = "ci") -> str:
        """Generate CI/CD pipeline configuration."""
        if pipeline_type == "ci":
            return """# CI Pipeline Configuration
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest tests/ -v
      - name: Run linting
        run: python -m flake8 src/
"""
        return "# Pipeline configuration"


# Register the agent
AgentRegistry.register(InfraAgent)
