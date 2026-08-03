import json
import logging
import re
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from patching_agent.config import settings
from patching_agent.agents.state import AgentGraphState

logger = logging.getLogger(__name__)

class FailureDiagnosticReport(BaseModel):
    error_type: str = Field(description="The formal class of the exception (e.g., KeyError, AttributeError).")
    failing_file: str = Field(description="The clean system path or module filename where the error originated.")
    line_number: int = Field(description="The exact line number where the execution halted.")
    root_cause_summary: str = Field(description="A concise summary of why this code interface failed.")
    optimized_rag_query: str = Field(description="A clean semantic search query tailored for documentation retrieval.")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0 indicating diagnostic certainty.")

class FailureDetectionAgent:
    def __init__(self):
        logger.info("Initializing Failure Detection Agent with OpenRouter...")
        # Connecting via OpenRouter endpoint
        self.llm = ChatOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.LLM_MODEL,
            temperature=0.0
        )

    def _build_parsing_prompt(self, raw_logs: str) -> str:
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
        logger.info("Analyzing crash log context...")
        
        if not state.raw_logs.strip():
            return {
                "execution_status": "detection_failed",
                "failure_analysis": {"error": "No logs provided"}
            }

        prompt = self._build_parsing_prompt(state.raw_logs)
        response_text = ""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            if response_text.startswith("```"):
                response_text = re.sub(r"^```(json)?", "", response_text, flags=re.MULTILINE).strip()
                response_text = re.sub(r"```$", "", response_text).strip()
                
            parsed_report = json.loads(response_text)
            report = FailureDiagnosticReport(**parsed_report)
            logger.info(f"Successfully parsed diagnostic report: {report.model_dump_json()}")
            
            return {
                "execution_status": "detection_success",
                "failure_analysis": report.model_dump()
            }
        except Exception as e:
            logger.error(f"Detection failed: {e}. Raw model output: {response_text}")
            return {
                "execution_status": "detection_failed",
                "failure_analysis": {"error": str(e)}
            }