"""
Module: Failure Detection Agent
Description: Parses raw unstructured API crash logs and tracebacks into a structured 
             diagnostic report using a local Mistral model via Ollama.
"""

import json
import logging
import re
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_community.llms import Ollama
from patching_agent.config import settings
from patching_agent.agents.state import AgentGraphState

logger = logging.getLogger(__name__)

class FailureDiagnosticReport(BaseModel):
    """Structured format for the output of our failure analysis agent."""
    error_type: str = Field(description="The formal class of the exception (e.g., KeyError, AttributeError).")
    failing_file: str = Field(description="The clean system path or module filename where the error originated.")
    line_number: int = Field(description="The exact line number where the execution halted.")
    root_cause_summary: str = Field(description="A concise summary of why this code interface failed.")
    optimized_rag_query: str = Field(description="A clean semantic search query tailored for documentation retrieval.")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0 indicating diagnostic certainty.")


class FailureDetectionAgent:
    """Agent node that analyzes crash contexts and creates a structured diagnostic report."""

    def __init__(self):
        logger.info("Initializing Failure Detection Agent with Mistral...")
        # Connecting to our local Mistral engine
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL,
            temperature=0.0  # Set to 0.0 for deterministic parsing precision
        )

    def _build_parsing_prompt(self, raw_logs: str) -> str:
        """Constructs a strict system prompt instructing Mistral to return valid JSON matching our schema."""
        return f"""
You are an expert Site Reliability Engineer and Code Auditor running a diagnostic sequence.
Your task is to analyze the following raw crash logs/tracebacks and extract a structured diagnostic report.

[CRITICAL INSTRUCTION]
Your response must contain ONLY a single valid JSON object matching the schema below. 
Do not include any conversational filler, markdown formatting blocks (like ```json), or hidden reasoning text.

Target JSON Schema:
{{
    "error_type": "string (e.g., ValueError)",
    "failing_file": "string (path to the broken file)",
    "line_number": integer,
    "root_cause_summary": "string explaining why it broke",
    "optimized_rag_query": "string optimizing to search documentation for a fix",
    "confidence_score": float (between 0.0 and 1.0)
}}

Raw Crash Logs to Analyze:
---
{raw_logs}
---

Your JSON Output:
"""

    async def analyze(self, state: AgentGraphState) -> Dict[str, Any]:
        """
        Executes the failure detection and parsing analysis logic.
        
        Args:
            state: The current active LangGraph shared state context.
        Returns:
            An update dictionary to append to the graph state.
        """
        logger.info("Analyzing crash log context...")
        
        if not state.raw_logs.strip():
            logger.warning("Empty log context received inside the Failure Detection Agent.")
            return {
                "execution_status": "detection_failed",
                "failure_analysis": {"error": "No logs provided"}
            }

        prompt = self._build_parsing_prompt(state.raw_logs)
        response_text = ""
        
        try:
            # Invoke the local model
            response_text = self.llm.invoke(prompt).strip()
            
            # Defensive clean-up in case the model accidentally included markdown wrappers
            if response_text.startswith("```"):
                # Clean opening block (handles variants like ```json or ```)
                response_text = re.sub(r"^```", "", response_text, flags=re.MULTILINE).strip()
                
            # Attempt to parse the JSON output
            parsed_report = json.loads(response_text)
            
            # Validate against our Pydantic model
            report = FailureDiagnosticReport(**parsed_report)
            logger.info(f"Successfully parsed diagnostic report: {report.json()}")
            
            return {
                "execution_status": "detection_success",
                "failure_analysis": report.dict()
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}. Raw model output: {response_text}")
            return {
                "execution_status": "detection_failed",
                "failure_analysis": {"error": "Invalid JSON output from model"}
            }
    
