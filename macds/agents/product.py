from typing import Optional
from datetime import datetime

from macds.agents.base import BaseAgent, AgentConfig, AgentRegistry
from macds.core.contracts import (
    RequirementsInput, RequirementsOutput, Violation
)
from macds.core.artifacts import ArtifactType
from macds.core.memory import MemoryScope


class ProductAgent(BaseAgent[RequirementsInput, RequirementsOutput]):
    """
    Product Agent - Requirements owner.
    
    Responsibilities:
    - Define and refine requirements
    - Maintain acceptance criteria
    - Prioritize features
    - Own REQUIREMENTS.md, RISK_REGISTER.md
    """
    
    name = "ProductAgent"
    authority_level = 9
    description = "Defines requirements, acceptance criteria, and priorities"
    owned_artifacts = ["REQUIREMENTS.md", "RISK_REGISTER.md"]
    
    @property
    def system_prompt(self) -> str:
        return """You are the Product Agent, responsible for requirements in the MACDS system.

Your responsibilities:
1. Transform user requests into structured requirements
2. Define clear acceptance criteria for each requirement
3. Prioritize requirements based on value and dependencies
4. Identify and document risks

Key principles:
- Requirements must be SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- Each requirement must have testable acceptance criteria
- Consider user experience and business value
- Document assumptions and constraints

Output format: Always use structured contract output.
Never output unstructured text outside the contract schema."""
    
    @property
    def input_contract(self) -> type:
        return RequirementsInput
    
    @property
    def output_contract(self) -> type:
        return RequirementsOutput
    
    async def _execute_impl(self, input_data: RequirementsInput) -> RequirementsOutput:
        """Define requirements from user request."""
        
        # Parse and structure requirements
        requirements = self._parse_requirements(input_data.user_request)
        acceptance_criteria = self._define_acceptance_criteria(requirements)
        constraints = self._identify_constraints(input_data)
        risks = self._identify_risks(requirements)
        
        # Store in project memory
        self.memory.remember(
            content={
                "requirements_count": len(requirements),
                "user_request": input_data.user_request[:200]
            },
            scope=MemoryScope.PROJECT,
            tags=["requirements", "product"]
        )
        
        return RequirementsOutput(
            request_id=input_data.request_id,
            processing_agent=self.name,
            requirements=requirements,
            acceptance_criteria=acceptance_criteria,
            constraints=constraints,
            risks=risks
        )
    
    def _parse_requirements(self, user_request: str) -> list[dict]:
        """Parse user request into structured requirements."""
        requirements = []
        req_id = 1
        
        # Split by common separators
        parts = user_request.replace(".", "\n").replace(",", "\n").split("\n")
        
        for part in parts:
            part = part.strip()
            if len(part) > 10:  # Skip very short fragments
                priority = "high" if any(w in part.lower() for w in ["must", "critical", "essential"]) else "medium"
                
                requirements.append({
                    "id": f"REQ-{req_id:03d}",
                    "description": part,
                    "priority": priority,
                    "status": "proposed",
                    "acceptance_criteria": []
                })
                req_id += 1
        
        # Ensure at least one requirement
        if not requirements:
            requirements.append({
                "id": "REQ-001",
                "description": user_request,
                "priority": "high",
                "status": "proposed",
                "acceptance_criteria": []
            })
        
        return requirements
    
    def _define_acceptance_criteria(self, requirements: list[dict]) -> list[str]:
        """Define acceptance criteria for requirements."""
        criteria = []
        
        for req in requirements:
            desc = req["description"].lower()
            req_id = req["id"]
            
            # Generate criteria based on requirement type
            if "api" in desc or "endpoint" in desc:
                criteria.append(f"AC-{req_id}-01: API returns valid JSON response")
                criteria.append(f"AC-{req_id}-02: API validates all input parameters")
            
            if "auth" in desc or "login" in desc:
                criteria.append(f"AC-{req_id}-01: User can authenticate with valid credentials")
                criteria.append(f"AC-{req_id}-02: Invalid credentials return appropriate error")
            
            if "data" in desc or "save" in desc or "store" in desc:
                criteria.append(f"AC-{req_id}-01: Data persists correctly after save")
                criteria.append(f"AC-{req_id}-02: Data can be retrieved after storage")
            
            # Default criteria
            if not any(req_id in c for c in criteria):
                criteria.append(f"AC-{req_id}-01: Requirement is implemented as specified")
                criteria.append(f"AC-{req_id}-02: Implementation passes all tests")
        
        return criteria
    
    def _identify_constraints(self, input_data: RequirementsInput) -> list[str]:
        """Identify project constraints."""
        constraints = list(input_data.constraints) if input_data.constraints else []
        
        # Add default constraints
        default_constraints = [
            "Must be compatible with Python 3.10+",
            "Must follow MACDS coding standards",
            "Must include unit tests for all new code"
        ]
        
        for c in default_constraints:
            if c not in constraints:
                constraints.append(c)
        
        return constraints
    
    def _identify_risks(self, requirements: list[dict]) -> list[str]:
        """Identify risks based on requirements."""
        risks = []
        
        for req in requirements:
            desc = req["description"].lower()
            
            if "security" in desc or "auth" in desc:
                risks.append(f"R-{req['id']}: Security-critical functionality requires thorough review")
            
            if "performance" in desc or "scale" in desc:
                risks.append(f"R-{req['id']}: Performance requirements need benchmarking")
            
            if "integrat" in desc or "external" in desc:
                risks.append(f"R-{req['id']}: External dependencies may introduce compatibility issues")
        
        return risks


# Register the agent
AgentRegistry.register(ProductAgent)
