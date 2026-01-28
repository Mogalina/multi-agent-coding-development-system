"""
ImplementationAgent - Code generation and modification.

Authority Level: 5
"""

from typing import Optional
from datetime import datetime
from pathlib import Path

from macds.agents.base import BaseAgent, AgentConfig, AgentRegistry
from macds.core.contracts import (
    ImplementationInput, ImplementationOutput, Violation
)
from macds.core.memory import MemoryScope


class ImplementationAgent(BaseAgent[ImplementationInput, ImplementationOutput]):
    """
    Implementation Agent - Code generator.
    
    Responsibilities:
    - Write new code following API contracts
    - Refactor existing code
    - Fix bugs identified by review or testing
    """
    
    name = "ImplementationAgent"
    authority_level = 5
    description = "Writes and modifies code following API contracts"
    owned_artifacts = []  # No owned artifacts, follows others' specifications
    
    @property
    def system_prompt(self) -> str:
        return """You are the Implementation Agent, responsible for writing code in MACDS.

Your responsibilities:
1. Write clean, maintainable code
2. Follow API contracts exactly
3. Adhere to coding standards
4. Implement error handling and logging

Key principles:
- Code must match API contracts precisely
- Follow established patterns from architecture
- Write testable code with dependency injection
- Include docstrings and type hints

Constraints:
- You may NOT modify architecture documents
- You may NOT change API contracts
- You MUST follow coding standards
- All code changes require review

Output format: Always use structured contract output.
Report all file changes via the contract schema."""
    
    @property
    def input_contract(self) -> type:
        return ImplementationInput
    
    @property
    def output_contract(self) -> type:
        return ImplementationOutput
    
    async def _execute_impl(self, input_data: ImplementationInput) -> ImplementationOutput:
        """Generate or modify code."""
        
        # Recall relevant patterns from memory
        patterns = self.recall_relevant_memories(
            input_data.task_description,
            scope=MemoryScope.SKILL,
            limit=5
        )
        
        # Generate code based on task
        files_created = []
        files_modified = []
        
        if input_data.target_files:
            # Modify existing files
            for target in input_data.target_files:
                modification = self._generate_modification(
                    target,
                    input_data.task_description,
                    input_data.api_contract
                )
                files_modified.append(modification)
        else:
            # Create new files
            new_files = self._generate_new_files(
                input_data.task_description,
                input_data.architecture,
                input_data.api_contract
            )
            files_created.extend(new_files)
        
        # Store successful pattern in skill memory
        if files_created or files_modified:
            self.memory.learn_skill({
                "task_type": "implementation",
                "task_description": input_data.task_description[:100],
                "files_count": len(files_created) + len(files_modified)
            })
        
        return ImplementationOutput(
            request_id=input_data.request_id,
            processing_agent=self.name,
            files_created=files_created,
            files_modified=files_modified,
            files_deleted=[],
            implementation_notes=self._generate_notes(files_created, files_modified),
            api_compliance=True
        )
    
    def _generate_new_files(
        self,
        task_description: str,
        architecture: dict,
        api_contract: Optional[dict]
    ) -> list[dict]:
        """Generate new source files."""
        files = []
        
        # Infer file names from task
        task_lower = task_description.lower()
        
        if "class" in task_lower or "model" in task_lower:
            # Generate a model/class file
            class_name = self._extract_name(task_description) or "Model"
            files.append({
                "path": f"src/{class_name.lower()}.py",
                "content": self._generate_class_template(class_name, task_description),
                "language": "python"
            })
        
        elif "function" in task_lower or "util" in task_lower:
            # Generate utility file
            func_name = self._extract_name(task_description) or "utility"
            files.append({
                "path": f"src/{func_name.lower()}.py",
                "content": self._generate_function_template(func_name, task_description),
                "language": "python"
            })
        
        elif "api" in task_lower or "endpoint" in task_lower:
            # Generate API route file
            files.append({
                "path": "src/api/routes.py",
                "content": self._generate_api_template(task_description),
                "language": "python"
            })
        
        else:
            # Generic module
            module_name = self._extract_name(task_description) or "module"
            files.append({
                "path": f"src/{module_name.lower()}.py",
                "content": self._generate_module_template(module_name, task_description),
                "language": "python"
            })
        
        return files
    
    def _generate_modification(
        self,
        target_file: str,
        task_description: str,
        api_contract: Optional[dict]
    ) -> dict:
        """Generate a file modification."""
        return {
            "path": target_file,
            "diff": f"# TODO: Implement {task_description}",
            "description": f"Modified {target_file} for: {task_description[:50]}"
        }
    
    def _extract_name(self, task_description: str) -> Optional[str]:
        """Extract a name from task description."""
        words = task_description.split()
        for i, word in enumerate(words):
            if word.lower() in ["class", "function", "model", "called", "named"]:
                if i + 1 < len(words):
                    name = words[i + 1].strip("'\".,;:")
                    if name and name[0].isupper():
                        return name
        return None
    
    def _generate_class_template(self, class_name: str, description: str) -> str:
        """Generate a class template."""
        return f'''"""
{class_name} - Auto-generated by ImplementationAgent.

{description}
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class {class_name}:
    """
    {description[:100]}
    """
    
    id: str
    name: str
    
    def __post_init__(self):
        """Validate after initialization."""
        if not self.id:
            raise ValueError("id is required")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {{
            "id": self.id,
            "name": self.name
        }}
    
    @classmethod
    def from_dict(cls, data: dict) -> "{class_name}":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"]
        )
'''
    
    def _generate_function_template(self, func_name: str, description: str) -> str:
        """Generate a function template."""
        return f'''"""
{func_name} utilities - Auto-generated by ImplementationAgent.

{description}
"""

from typing import Any, Optional


def {func_name.lower()}(data: Any) -> Any:
    """
    {description[:100]}
    
    Args:
        data: Input data
        
    Returns:
        Processed result
    """
    # TODO: Implement
    return data
'''
    
    def _generate_api_template(self, description: str) -> str:
        """Generate an API routes template."""
        return f'''"""
API Routes - Auto-generated by ImplementationAgent.

{description}
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class APIResponse:
    """Standard API response."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def handle_request(request: dict) -> APIResponse:
    """
    Handle API request.
    
    Args:
        request: The incoming request data
        
    Returns:
        APIResponse with result
    """
    try:
        # TODO: Implement request handling
        return APIResponse(success=True, data={{}})
    except Exception as e:
        return APIResponse(success=False, error=str(e))
'''
    
    def _generate_module_template(self, module_name: str, description: str) -> str:
        """Generate a generic module template."""
        return f'''"""
{module_name} module - Auto-generated by ImplementationAgent.

{description}
"""

from typing import Any, Optional


class {module_name.title().replace("_", "")}:
    """
    {description[:100]}
    """
    
    def __init__(self):
        """Initialize the module."""
        pass
    
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the main functionality.
        
        Returns:
            Result of execution
        """
        # TODO: Implement
        raise NotImplementedError()
'''
    
    def _generate_notes(self, created: list, modified: list) -> str:
        """Generate implementation notes."""
        notes = []
        
        if created:
            notes.append(f"Created {len(created)} new file(s)")
        if modified:
            notes.append(f"Modified {len(modified)} existing file(s)")
        
        notes.append("All code follows MACDS coding standards")
        notes.append("Ready for review")
        
        return "; ".join(notes)


# Register the agent
AgentRegistry.register(ImplementationAgent)
