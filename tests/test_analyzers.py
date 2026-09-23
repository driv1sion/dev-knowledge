from unittest.mock import patch, MagicMock
from devknowledge.analyzers.metrics import extract_metrics
from devknowledge.analyzers.deps import extract_dependencies
import json
import subprocess

@patch('devknowledge.analyzers.metrics.subprocess.run')
def test_extract_metrics_success(mock_run):
    mock_run.return_value = MagicMock(stdout=json.dumps([{"Name": "Python", "Lines": 100}]))
    
    result = extract_metrics("/tmp")
    assert len(result) == 1
    assert result[0]["Name"] == "Python"

@patch('devknowledge.analyzers.deps.subprocess.run')
def test_extract_dependencies_success(mock_run):
    mock_run.return_value = MagicMock(stdout=json.dumps({
        "artifacts": [{"name": "pytest", "version": "7.0", "type": "python"}]
    }))
    
    result = extract_dependencies("/tmp")
    assert len(result) == 1
    assert result[0]["name"] == "pytest"

@patch('devknowledge.analyzers.metrics.subprocess.run')
def test_extract_metrics_failure(mock_run):
    mock_run.side_effect = FileNotFoundError()
    
    result = extract_metrics("/tmp")
    assert result == []
