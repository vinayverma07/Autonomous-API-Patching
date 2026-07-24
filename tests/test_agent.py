"""
Module: Automated Bug Diagnostic Integration Test
File Path: tests/test_agent.py
Description: Captures targeted runtime failures securely for agent ingestion processing.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Dynamically append the src directory to the system path to fix the path resolution issue
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Now we can import cleanly from our file location
from sample_api import app

client = TestClient(app)

def test_get_user_profile_bug_simulation():
    """
    Intentionally triggers our broken mock endpoint to capture 
    the raw exception details for our patching pipeline.
    """
    # Query an invalid ID to force a KeyError crash
    with pytest.raises(KeyError) as exception_context:
        client.get("/api/user/user_999")
        
    # Verify the trace caught our targeted mock error condition
    assert "user_999" in str(exception_context.value)
    print(f"\n[TEST SUITE LOG CAPTURE SUCCESS]: {repr(exception_context.value)}")