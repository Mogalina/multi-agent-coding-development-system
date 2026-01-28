from typing import Optional
from datetime import datetime
import subprocess
import uuid

from macds.agents.base import BaseAgent, AgentConfig, AgentRegistry
from macds.core.contracts import (
    IntegrationInput, IntegrationOutput, Violation
)
from macds.core.memory import MemoryScope


class IntegratorAgent(BaseAgent[IntegrationInput, IntegrationOutput]):
    """
    Integrator Agent - Merge and integration manager.
    
    Responsibilities:
    - Merge approved changes
    - Resolve merge conflicts
    - Maintain branch hygiene
    """
    
    name = "IntegratorAgent"
    authority_level = 8
    description = "Merges approved changes and resolves conflicts"
    owned_artifacts = []
    
    @property
    def system_prompt(self) -> str:
        return """You are the Integrator Agent, responsible for change integration in MACDS.

Your responsibilities:
1. Merge approved code changes
2. Resolve merge conflicts
3. Ensure integration doesn't break the build
4. Maintain version control hygiene

Key principles:
- Only integrate reviewed and approved changes
- Verify build passes before finalizing
- Document all integrations
- Escalate unresolvable conflicts

Output format: Always use structured contract output.
Report all merged files and any conflicts."""
    
    @property
    def input_contract(self) -> type:
        return IntegrationInput
    
    @property
    def output_contract(self) -> type:
        return IntegrationOutput
    
    async def _execute_impl(self, input_data: IntegrationInput) -> IntegrationOutput:
        """Integrate changes."""
        
        # Verify approvals
        if not input_data.review_approval:
            return IntegrationOutput(
                request_id=input_data.request_id,
                processing_agent=self.name,
                success=False,
                integration_notes="Integration blocked: review approval required"
            )
        
        if not input_data.build_approval:
            return IntegrationOutput(
                request_id=input_data.request_id,
                processing_agent=self.name,
                success=False,
                integration_notes="Integration blocked: build approval required"
            )
        
        # Process changes
        merged_files = []
        conflicts = []
        
        for change in input_data.changes:
            file_path = change.get("path", "")
            
            # Check for conflicts
            has_conflict = await self._check_conflict(
                file_path,
                input_data.target_branch
            )
            
            if has_conflict:
                resolution = await self._resolve_conflict(file_path, change)
                if resolution["resolved"]:
                    merged_files.append(file_path)
                else:
                    conflicts.append({
                        "file": file_path,
                        "type": "merge_conflict",
                        "resolution_attempted": True,
                        "resolved": False
                    })
            else:
                merged_files.append(file_path)
        
        # Generate commit
        commit_sha = None
        if merged_files and not conflicts:
            commit_sha = await self._create_commit(
                merged_files,
                input_data.source_branch,
                input_data.target_branch
            )
        
        success = len(conflicts) == 0 and len(merged_files) > 0
        
        # Store integration record
        self.memory.remember(
            content={
                "files_merged": len(merged_files),
                "conflicts": len(conflicts),
                "commit_sha": commit_sha
            },
            scope=MemoryScope.PROJECT,
            tags=["integration", "merge"]
        )
        
        return IntegrationOutput(
            request_id=input_data.request_id,
            processing_agent=self.name,
            success=success,
            merged_files=merged_files,
            conflicts=conflicts,
            commit_sha=commit_sha,
            integration_notes=self._generate_notes(merged_files, conflicts)
        )
    
    async def _check_conflict(self, file_path: str, target_branch: str) -> bool:
        """Check if a file has merge conflicts."""
        # In production, use git to check for conflicts
        # Simulated: no conflicts
        return False
    
    async def _resolve_conflict(self, file_path: str, change: dict) -> dict:
        """Attempt to resolve a conflict."""
        # In production, use merge strategies
        return {
            "file": file_path,
            "resolved": True,
            "strategy": "ours"
        }
    
    async def _create_commit(
        self,
        files: list[str],
        source_branch: str,
        target_branch: str
    ) -> str:
        """Create integration commit."""
        # In production, use git to commit
        commit_sha = str(uuid.uuid4())[:8]
        return commit_sha
    
    def _generate_notes(self, merged: list[str], conflicts: list[dict]) -> str:
        """Generate integration notes."""
        parts = []
        
        if merged:
            parts.append(f"Successfully merged {len(merged)} file(s)")
        
        if conflicts:
            parts.append(f"BLOCKED: {len(conflicts)} unresolved conflict(s)")
            for c in conflicts:
                parts.append(f"  - {c['file']}: {c['type']}")
        
        if not merged and not conflicts:
            parts.append("No changes to integrate")
        
        return "; ".join(parts)


# Register the agent
AgentRegistry.register(IntegratorAgent)
