import subprocess
import logging

logger = logging.getLogger(__name__)

def extract_git_history(repo_path: str):
    """
    Uses git log to parse commit history.
    """
    try:
        # %H: commit hash, %an: author name, %ad: author date, %s: subject
        result = subprocess.run(
            ["git", "-C", repo_path, "log", "--pretty=format:%H|%an|%ad|%s", "--date=iso"],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })
        return commits
    except FileNotFoundError:
        logger.error("'git' command not found.")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running git log: {e.stderr}")
        return []
