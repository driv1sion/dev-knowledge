import subprocess
import json
import logging

logger = logging.getLogger(__name__)

def extract_metrics(repo_path: str):
    """
    Uses 'scc' (Sloc, Cloc and Code) to extract language breakdown.
    Requires 'scc' to be installed locally.
    """
    try:
        result = subprocess.run(
            ["scc", repo_path, "-f", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except FileNotFoundError:
        logger.error("'scc' not found. Please install scc (e.g., 'brew install scc' or download from GitHub).")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running scc: {e.stderr}")
        return []
    except json.JSONDecodeError:
        logger.error("Failed to parse scc JSON output.")
        return []
