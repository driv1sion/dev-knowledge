# dev-knowledge

An open-source, local-first developer knowledge pipeline. `dev-knowledge` turns your repository, documentation, and Git history into a structured, verifiable Knowledge Graph that can be used to generate automated portfolios.

## Features

- **Local-First:** Uses local SQLite instead of expensive, cloud-hosted Vector Databases.
- **Deterministic Analysis:** Uses robust CLI tools (`scc`, `syft`, `git`) to build fact-based evidence instead of relying purely on LLM hallucination.
- **Provenance & Trust:** Every capability in your Knowledge Graph maintains a strict chain of evidence pointing to the commits, config files, or developer input that proved it.
- **Agentic Router:** Automatically detects gaps in knowledge and prompts you to fill them in.
- **Portfolio Ready:** Output format is a standard JSON-LD Knowledge Graph, ready to be dropped into a static site generator like Astro or Next.js.

## Installation

`dev-knowledge` requires Python 3.9+ and relies on some external tools for static analysis.

### 1. Install External Dependencies

You will need `scc` (for metrics) and `syft` (for SBOM generation) installed on your system.

**macOS (Homebrew):**
```bash
brew install scc
brew install syft
```

**Other Systems:**
- [Install scc](https://github.com/boyter/scc#installation)
- [Install syft](https://github.com/anchore/syft#installation)

### 2. Install Python Package

We recommend installing in a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Usage

### Analyzing a Repository

Run the analysis phase to parse history and build the local `knowledge.db`. The tool will prompt you if it discovers gaps (e.g. asking for the deployment architecture).

```bash
devknowledge analyze /path/to/your/repo
```

### Publishing the Knowledge Graph

Once the analysis is complete, you can generate the portable `knowledge_graph.json` artifact:

```bash
devknowledge publish /path/to/your/repo
```

## Development

To run the unit tests:

```bash
pip install pytest
pytest tests/
```

## License

MIT
