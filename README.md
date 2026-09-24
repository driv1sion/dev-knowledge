# dev-knowledge

An open-source, local-first developer knowledge pipeline. `dev-knowledge` analyzes your repositories, documentation, and Git history to construct a structured, verifiable Knowledge Graph. It serves as an automated engine for generating provable developer portfolios and project documentation.

## Architecture & Principles

`dev-knowledge` follows a strict deterministic pipeline where every fact generated must trace back to concrete evidence in the repository.

1. **Deterministic Analyzers (The Extraction Layer):**
   - **Metrics:** Uses `scc` to extract absolute ground-truth code metrics (languages, line counts).
   - **Dependencies:** Uses `syft` to generate software bill of materials (SBOM) and extract structural dependencies.
   - **Git History:** Directly parses the git commit log to extract contributor data, commit hashes, milestones, and remote URLs (for automatic GitHub and Live URL detection).

2. **Core Storage & Provenance (The DB Layer):**
   - **Local-First SQLite:** Data is managed efficiently using local SQLite (`knowledge.db`). We avoid complex cloud Vector Databases, making the system fast, portable, and zero-budget.
   - **Strict Provenance:** Every capability in the database maintains a strict chain of evidence pointing directly back to the commit hash, configuration file, or user input that proved it.

3. **Agentic Routing (The Gap Resolver):**
   - A built-in agent detects critical missing context (e.g., "Project Description", "Deployment Architecture") and interacts with the developer via CLI prompts to fill knowledge gaps interactively.

4. **Graph & Portfolio Generation (The Output Layer):**
   - **Knowledge Graph:** Compiles the database into a portable `knowledge_graph.json` artifact.
   - **Portfolio Updater:** Automatically reads the graph, structures the data (extracting Tech Stack, Impact Metrics, Architecture Rationale, etc.), and intelligently merges it into a central `projects.json` for frontend consumption (e.g., in Astro, Next.js, Vanilla web apps). It respects manual ordering and merges updates non-destructively.

## Installation & Setup

`dev-knowledge` requires Python 3.9+ and relies on specific external binaries for deterministic analysis.

### 1. Install External Dependencies

You will need `scc` (for code metrics) and `syft` (for SBOM/dependency generation) installed on your system. Also ensure `git` is installed.

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
# From the root of the dev-knowledge repository
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Usage

### Recommended: The Automated Remote Workflow (`publish.sh`)

The most powerful way to use `dev-knowledge` is via the automated `publish.sh` script. This script handles the end-to-end pipeline: it temporarily clones your target repository, runs the analysis, generates the graph, updates your portfolio index, and automatically pushes the result directly to your remote portfolio repository.

**Features of the Remote Engine:**
- **Blobless Target Cloning:** Downloads full commit history for git analysis but skips historic file contents, saving massive amounts of bandwidth and memory (`--filter=blob:none`).
- **Shallow Portfolio Cloning:** Instantly clones your portfolio repository (`--depth 1`) since only the latest state is needed to merge data.
- **Secure Sandbox:** Operations run in `/tmp/` and are automatically wiped after execution.

**Usage:**
```bash
./publish.sh <TARGET_REPO_URL> <PORTFOLIO_REPO_URL>
```
*Example:*
```bash
./publish.sh https://github.com/username/my-project.git https://github.com/username/my-portfolio.git
```

### Manual Local Usage (CLI)

If you prefer to run the tools manually on a local directory (e.g., for testing or isolated extractions):

**1. Analyze the Repository**
Run the analysis phase to parse code, dependencies, and git history into the local `knowledge.db`. Use `-i` or `--interactive` to prompt for missing gaps manually.
```bash
devknowledge analyze /path/to/your/repo --interactive
```

**2. Publish the Knowledge Graph**
Extract the SQLite data into a portable `knowledge_graph.json` artifact:
```bash
devknowledge publish /path/to/your/repo
```

**3. Update Portfolio Index**
Merge the generated knowledge graph directly into a portfolio's data directory (where `projects.json` lives):
```bash
devknowledge update-portfolio /path/to/portfolio/data project-name /path/to/your/repo/knowledge_graph.json
```

## Development & Testing

To run the internal unit and integration tests:

```bash
pip install pytest
pytest tests/
```

## License

MIT
