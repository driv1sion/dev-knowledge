import subprocess
import json
import logging

logger = logging.getLogger(__name__)

def extract_dependencies(repo_path: str):
    """
    Uses 'syft' to generate a standardized SBOM.
    Requires 'syft' to be installed locally.
    """
    try:
        result = subprocess.run(
            ["syft", repo_path, "-o", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        sbom = json.loads(result.stdout)
        
        # Format the SBOM into a simpler list of capabilities/dependencies
        dependencies = []
        if 'artifacts' in sbom:
            for pkg in sbom['artifacts']:
                dependencies.append({
                    "name": pkg.get("name"),
                    "version": pkg.get("version"),
                    "type": pkg.get("type")
                })
        return dependencies
    except FileNotFoundError:
        logger.error("'syft' not found. Please install syft (e.g., 'brew install syft' or curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin).")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running syft: {e.stderr}")
        return []
    except json.JSONDecodeError:
        logger.error("Failed to parse syft JSON output.")
        return []
