# MACDS Setup Guide

## System Requirements

- Python 3.10 or higher
- Git 2.0 or higher
- 4 GB RAM minimum
- Internet connection (for LLM API calls)

## Installation Methods

### Method 1: pip (Recommended)

```bash
# Clone the repository
git clone https://github.com/macds/macds.git
cd macds

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install -e .
```

### Method 2: Make

```bash
git clone https://github.com/macds/macds.git
cd macds

# Install with make
make install

# Or with development dependencies
make install-dev
```

### Method 3: Docker

```bash
git clone https://github.com/macds/macds.git
cd macds

# Build image
docker build -t macds:latest .

# Or use docker compose
docker compose build
```

## Configuration

### Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Required: At least one LLM API key
OPENROUTER_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here
# or
ANTHROPIC_API_KEY=your_key_here

# Optional: Model configuration
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=4096

# Optional: System settings
LOG_LEVEL=INFO
MACDS_DATA_DIR=.macds
```

### API Key Setup

#### OpenRouter

1. Create account at https://openrouter.ai
2. Generate API key in dashboard
3. Set `OPENROUTER_API_KEY` in `.env`

#### OpenAI

1. Create account at https://platform.openai.com
2. Generate API key
3. Set `OPENAI_API_KEY` in `.env`

#### Anthropic

1. Create account at https://console.anthropic.com
2. Generate API key
3. Set `ANTHROPIC_API_KEY` in `.env`

## Initialization

Initialize MACDS in your project directory:

```bash
# Navigate to your project
cd your-project

# Initialize MACDS
macds init
```

This creates:
- `.macds/` directory for data storage
- Mandatory artifact templates

## Verification

Verify installation:

```bash
# Check version
macds --version

# Check status
macds status

# Run example
macds example
```

## Docker Usage

### Running with Docker

```bash
# Run a command
docker run -it --rm \
  -v $(pwd)/workspace:/app/workspace \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  macds:latest run "Create a hello world function"

# Interactive shell
docker run -it --rm \
  -v $(pwd)/workspace:/app/workspace \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  --entrypoint /bin/bash \
  macds:latest
```

### Docker Compose

```bash
# Development mode
docker compose --profile dev up macds-dev

# Production mode
docker compose up macds
```

## Development Setup

For contributing to MACDS:

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

## Troubleshooting

### Common Issues

**ImportError: No module named 'macds'**

Ensure you installed in editable mode:
```bash
pip install -e .
```

**API Key not found**

Check your `.env` file is in the project root and contains valid keys.

**Permission denied errors**

Check file permissions in `.macds/` directory:
```bash
chmod -R 755 .macds/
```

**Docker build fails**

Ensure Docker daemon is running:
```bash
docker info
```

### Getting Help

- Check documentation in `docs/`
- Open an issue on GitHub
- Review existing issues for solutions
