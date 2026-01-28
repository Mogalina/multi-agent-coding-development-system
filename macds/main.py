import asyncio
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Ensure macds is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from macds.core.orchestrator import Orchestrator, WorkflowStage
from macds.core.memory import MemoryStore
from macds.core.evaluation import EvaluationSystem
from macds.core.artifacts import ArtifactStore


app = typer.Typer(
    name="macds",
    help="Multi-Agent Coding Development System"
)
console = Console()


@app.command()
def run(
    request: str = typer.Argument(..., help="Development request in natural language"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quick: bool = typer.Option(False, "--quick", "-q", help="Skip review and testing"),
):
    """
    Run a complete development workflow.
    
    Example:
        macds run "Create a REST API for user management"
    """
    async def execute():
        orchestrator = Orchestrator(verbose=verbose)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            if quick:
                # Custom workflow without review/test
                from macds.core.orchestrator import DEFAULT_WORKFLOW
                quick_workflow = [
                    w for w in DEFAULT_WORKFLOW
                    if w[0] not in [WorkflowStage.REVIEW, WorkflowStage.BUILD_TEST]
                ]
                progress.add_task("Running quick workflow...", total=None)
                result = await orchestrator.run_workflow(request, quick_workflow)
            else:
                progress.add_task("Running full workflow...", total=None)
                result = await orchestrator.run_workflow(request)
        
        # Display results
        style = "green" if result.success else "red"
        console.print(Panel(
            result.get_summary(),
            title="Workflow Result",
            border_style=style
        ))
        
        # Show scorecards
        if verbose:
            scores = orchestrator.get_agent_scorecards()
            if scores:
                table = Table(title="Agent Scorecards")
                table.add_column("Agent")
                table.add_column("Score")
                table.add_column("Success Rate")
                
                for name, data in scores.items():
                    table.add_row(
                        name,
                        f"{data.get('overall_score', 0):.0f}%",
                        f"{data.get('success_rate', 0) * 100:.0f}%"
                    )
                
                console.print(table)
    
    asyncio.run(execute())


@app.command()
def agent(
    agent_name: str = typer.Argument(..., help="Agent to run"),
    task: str = typer.Argument(..., help="Task for the agent"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """
    Run a specific agent on a task.
    
    Available agents: ArchitectAgent, ProductAgent, ImplementationAgent,
    ReviewerAgent, BuildTestAgent, IntegratorAgent, InfraAgent
    """
    from macds.agents.base import AgentRegistry
    
    async def execute():
        agent_instance = AgentRegistry.get_instance(agent_name)
        
        if not agent_instance:
            # Try to create it
            agent_instance = AgentRegistry.create(agent_name, verbose=verbose)
        
        if not agent_instance:
            console.print(f"[red]Unknown agent: {agent_name}[/red]")
            console.print("Available agents:")
            for a in AgentRegistry.list_agents():
                console.print(f"  - {a['name']} (authority: {a['authority_level']})")
            raise typer.Exit(1)
        
        console.print(f"Running {agent_name}...")
        
        # Create generic input
        import uuid
        from macds.core.contracts import RequirementsInput
        
        input_data = RequirementsInput(
            request_id=str(uuid.uuid4())[:8],
            user_request=task
        )
        
        result = await agent_instance.execute(input_data)
        
        console.print(Panel(
            str(result),
            title=f"{agent_name} Result",
            border_style="green"
        ))
    
    asyncio.run(execute())


@app.command()
def init():
    """
    Initialize MACDS in the current directory.
    
    Creates mandatory artifacts and configurations.
    """
    console.print("Initializing MACDS...")
    
    artifact_store = ArtifactStore()
    created = artifact_store.init_mandatory_artifacts()
    
    if created:
        console.print(f"[green]Created {len(created)} artifact(s):[/green]")
        for name in created:
            console.print(f"  - {name}")
    else:
        console.print("[dim]All artifacts already exist[/dim]")
    
    console.print("\n[green]MACDS initialized successfully![/green]")


@app.command()
def status():
    """Show system status and agent scorecards."""
    evaluation = EvaluationSystem()
    memory = MemoryStore()
    
    # Memory stats
    mem_stats = memory.get_stats()
    console.print(Panel(
        f"Total memories: {mem_stats['total_entries']}\n"
        f"Average strength: {mem_stats['avg_strength']:.2f}",
        title="Memory System"
    ))
    
    # Agent scores
    scores = evaluation.get_all_scores()
    if scores:
        table = Table(title="Agent Performance")
        table.add_column("Agent")
        table.add_column("Authority")
        table.add_column("Score")
        table.add_column("Tasks")
        table.add_column("Success")
        table.add_column("Autonomy")
        
        for name, data in scores.items():
            table.add_row(
                name,
                str(data.get("authority_level", "?")),
                f"{data.get('overall_score', 50):.0f}%",
                str(data.get("total_tasks", 0)),
                f"{data.get('success_rate', 1.0) * 100:.0f}%",
                f"{data.get('autonomy_level', 1.0):.1f}"
            )
        
        console.print(table)
    else:
        console.print("[dim]No agent data yet[/dim]")


@app.command()
def artifacts():
    """List all artifacts and their status."""
    store = ArtifactStore()
    
    artifacts_list = store.list_artifacts()
    
    if artifacts_list:
        table = Table(title="Artifacts")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Owner")
        table.add_column("Versions")
        
        for artifact in artifacts_list:
            table.add_row(
                artifact.name,
                artifact.artifact_type.value,
                artifact.owner,
                str(len(artifact.versions))
            )
        
        console.print(table)
    else:
        console.print("[dim]No artifacts found. Run 'macds init' first.[/dim]")


@app.command()
def example():
    """Run an example workflow to demonstrate the system."""
    console.print("[bold]Running MACDS Example Workflow[/bold]\n")
    
    async def execute():
        orchestrator = Orchestrator(verbose=True)
        
        request = "Create a simple calculator module with add, subtract, multiply, and divide functions"
        
        console.print(f"[blue]Request:[/blue] {request}\n")
        
        result = await orchestrator.run_workflow(request)
        
        console.print("\n")
        console.print(Panel(
            result.get_summary(),
            title="Example Complete",
            border_style="green" if result.success else "red"
        ))
    
    asyncio.run(execute())


def main():
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
