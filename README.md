# MACDS - Multi-Agent Coding Development System

A production-ready multi-agent system for automated software engineering that performs the full development lifecycle with enforced architectural invariants, execution-grounded feedback, and self-improvement capabilities.

## Features

- **7 Specialized Agents** with authority-based hierarchy
- **Contract-Driven I/O** ensuring structured, validated communication
- **Memory System** with decay across Working, Project, Skill, and Failure scopes
- **DAG-Based Workflow** with automatic failure routing and escalation
- **Artifact Management** with Git-backed versioning and ownership
- **Execution-Grounded Feedback** from actual build and test results

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/macds/macds.git
cd macds

# Install with pip
pip install -e .

# Or use make
make install
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API key
# At minimum, set one of:
# - OPENROUTER_API_KEY
# - OPENAI_API_KEY  
# - ANTHROPIC_API_KEY
```

### Usage

```bash
# Initialize MACDS in your project
macds init

# Run a development workflow
macds run "Create a REST API for user management"

# Run a specific agent
macds agent ProductAgent "Define requirements for authentication"

# Check system status
macds status

# Run example workflow
macds example
```

## Docker

```bash
# Build image
docker build -t macds:latest .

# Run with Docker
docker run -it --rm \
  -v $(pwd)/workspace:/app/workspace \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  macds:latest run "Create a calculator module"

# Or use Docker Compose
docker compose up macds
```

## Agent Hierarchy

| Agent | Authority | Responsibility |
|-------|-----------|----------------|
| ArchitectAgent | 10 | System design, invariants, conflict resolution |
| ProductAgent | 9 | Requirements, acceptance criteria |
| BuildTestAgent | 8 | Build execution, testing, security |
| IntegratorAgent | 8 | Change integration, merging |
| ReviewerAgent | 7 | Code review, standards enforcement |
| InfraAgent | 6 | CI/CD, infrastructure automation |
| ImplementationAgent | 5 | Code generation |

## Default Workflow

```
ProductAgent -> ArchitectAgent -> ImplementationAgent 
-> ReviewerAgent -> BuildTestAgent -> IntegratorAgent 
-> ArchitectAgent (final approval)
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Workflows](docs/WORKFLOWS.md) - Workflow execution details
- [Agents](docs/AGENTS.md) - Agent specifications
- [Contracts](docs/CONTRACTS.md) - Contract system documentation
- [Setup Guide](docs/SETUP.md) - Detailed installation instructions
- [State of the Art](docs/STATE_OF_THE_ART.md) - Literature review

## Development

```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

## Project Structure

```
macds/
├── core/           # Core infrastructure
│   ├── contracts.py
│   ├── memory.py
│   ├── artifacts.py
│   ├── evaluation.py
│   ├── orchestrator.py
│   └── schema_loader.py
├── agents/         # Agent implementations
├── schemas/        # YAML schemas
│   ├── contracts/
│   └── artifacts/
├── templates/      # Artifact templates
├── tests/          # Test suite
└── main.py         # CLI entry point
```

## Contributing

Contributions are welcome. Please read the documentation and ensure all tests pass before submitting a pull request.

## License

MIT License - see [LICENSE](LICENSE) for details.
