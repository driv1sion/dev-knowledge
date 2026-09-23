# dev-knowledge

An open-source, local-first developer knowledge pipeline. `dev-knowledge` analyzes your repositories, documentation, and Git history to construct a structured, verifiable Knowledge Graph. It serves as an automated engine for generating provable developer portfolios and project documentation.

## Architecture & Principles

- **Deterministic Evidence:** We favor hard facts over AI hallucination. The pipeline uses robust tools like `scc` (for metrics) and `syft` (for dependencies) to extract absolute ground-truth data.
- **Strict Provenance:** Every capability in your Knowledge Graph maintains a strict chain of evidence pointing directly to the configuration files, commits, or explicit developer inputs that proved it.
- **Local-First SQLite:** Data is managed efficiently using local SQLite (`knowledge.db`) instead of complex cloud Vector Databases, making the system fast, portable, and zero-budget.
- **Agentic Routing:** A built-in agent detects critical missing context (e.g., "Deployment Architecture") and interacts with the developer via CLI prompts to fill knowledge gaps.
- **Graph Portability:** The output is a standard JSON-LD Knowledge Graph, ready to be ingested by static site generators (like Astro, Next.js, or Vercel).

## Installation

`dev-knowledge` requires Python 3.9+ and relies on specific external binaries for deterministic analysis.

### 1. Install External Dependencies

You will need `scc` (for code metrics) and `syft` (for SBOM/dependency generation) installed on your system.

**macOS (Homebrew):**
```bash
brew install scc
brew install syft
```

**Other Systems:**
- [Install scc](https://github.com/boyter/scc#installation)
- [Install syft](https://github.com/anchore/syft#installation)

### 2. Install the Python Pipeline

We highly recommend installing the package within an isolated virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Usage

### Recommended: The Automated Remote Workflow

The most powerful way to use `dev-knowledge` is via the automated `publish.sh` script. This script handles the end-to-end pipeline: it temporarily clones your target repository using memory-optimized Git protocols, runs the analysis, generates the graph, and automatically pushes the result directly to your remote portfolio repository.

**Features of the Remote Engine:**
- **Blobless Cloning:** Downloads full commit history for analysis but skips historic file contents, saving massive amounts of bandwidth and memory (`--filter=blob:none`).
- **Shallow Cloning:** Instantly clones your portfolio repository (`--depth 1`) since only the latest state is needed.
- **Secure Sandbox:** Operations run in `/tmp/` and are automatically wiped after execution.

**Usage:**
```bash
./publish.sh <TARGET_REPO_URL> <PORTFOLIO_REPO_URL>
```
*Example:*
```bash
./publish.sh https://github.com/username/my-project.git https://github.com/username/my-portfolio.git
```

### Manual Local Usage

If you prefer to run the tools manually on a local directory (e.g., for testing or isolated extractions):

**1. Analyze the Repository**
Run the analysis phase to parse history and build the local `knowledge.db`. The tool will prompt you if it discovers gaps.
```bash
devknowledge analyze /path/to/your/repo
```

**2. Publish the Knowledge Graph**
Once the analysis is complete, you can extract the SQLite data into a portable `knowledge_graph.json` artifact:
```bash
devknowledge publish /path/to/your/repo
```

## Development & Testing

To run the internal unit and integration tests:

```bash
pip install pytest
pytest tests/
```

## License

MIT
