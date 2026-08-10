"""
Module: Retry Agent Node
Description: Reflects on failed validation checks, summarizes test suite outputs, 
             and updates the graph state to guide the next patch generation attempt.
"""

import logging
import re
from typing import Dict, Any
from patching_agent.agents.state import AgentGraphState

logger = logging.getLogger(__name__)

class RetryAgentNode:
    """Agent node that processes validation failures and manages the self-healing loop state."""

    def __init__(self):
        logger.info("Initializing Retry Agent Node...")

    def _extract_clean_test_failure(self, raw_details: str) -> str:
        """Parses raw pytest or compilation stdout text to extract the core error lines."""
        if not raw_details:
            return "Unknown execution failure."

        # Search for common pytest error markers (e.g., FAILURES, SHORT RESTRUCTURING INFO)
        if "FAILURES" in raw_details:
            # Extract text starting from the first FAILURE indicator to keep the summary concise
            start_idx = raw_details.find("FAILURES")
            summary = raw_details[start_idx:start_idx + 1200]
            return f"... [Truncated Traceback Context] ...\n{summary}"
            
        # Fallback to returning the last 10 lines of the output if no explicit markers are found
        lines = raw_details.splitlines()
        tail = "\n".join(lines[-15:])
        return tail

    async def process_failure(self, state: AgentGraphState) -> Dict[str, Any]:
        """
        Processes validation failures, updates the retry count, and provides feedback for the next loop.
        """
        logger.info("Retry Agent reflecting on patch validation failure...")

        report = state.validation_report
        raw_details = report.get("error", "") or report.get("output", "")
        
        # 1. Clean up and extract the core reason for the test failure
        failure_feedback = self._extract_clean_test_failure(raw_details)
        
        # 2. Increment our internal retry tracking counter
        updated_retry_count = state.retry_count + 1
        
        logger.info(f"Preparing self-healing retry pass. Attempt {updated_retry_count} of {state.max_retries}")
        
        # 3. Construct an explicit feedback log to guide the next generation attempt
        retry_feedback_log = (
            f"--- PATCH ATTEMPT #{state.retry_count + 1} FAILED ---\n"
            f"The previous code patch was applied but failed validation checks.\n"
            f"CRITICAL ERROR ENCOUNTERED:\n{failure_feedback}\n"
            f"Please review the error details, modify your logic, and generate a corrected code block."
        )

        # Merge new feedback into our existing failure analysis store
        updated_analysis = dict(state.failure_analysis)
        if "historical_attempts" not in updated_analysis:
            updated_analysis["historical_attempts"] = []
            
        updated_analysis["historical_attempts"].append({
            "attempt_number": state.retry_count + 1,
            "failed_patch": state.generated_patch,
            "error_encountered": failure_feedback
        })
        
        # Update our global feedback loop string
        updated_analysis["latest_retry_feedback"] = retry_feedback_log

        return {
            "execution_status": "retrying_repair_cycle",
            "retry_count": updated_retry_count,
            "failure_analysis": updated_analysis
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    node = RetryAgentNode()
    print("Retry Agent Node module compiled successfully.")