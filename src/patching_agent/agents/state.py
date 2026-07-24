"""
Module: LangGraph State Definition
Description: Defines the structured context memory that passes through our self-healing agent graph.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentGraphState(BaseModel):
    """
    The complete state context for the self-healing API agent.
    Tracks everything from the raw incoming error to the generated patch validations.
    """
    # Inbound Target System Context
    raw_logs: str = Field(default="", description="The incoming crash logs or stack trace.")
    target_file_path: str = Field(default="", description="The target code file path that failed execution.")
    original_code: str = Field(default="", description="The contents of the failing file before modifications.")
    
    # Analysis & Diagnostic Context
    failure_analysis: Dict[str, Any] = Field(default_factory=dict, description="Parsed error properties, root cause analysis.")
    retrieved_docs: List[str] = Field(default_factory=list, description="Relevant documentation snippets extracted by RAG lookup.")
    
    # Synthesis & Repair Outputs
    generated_patch: str = Field(default="", description="The full proposed code replacement text block.")
    validation_report: Dict[str, Any] = Field(default_factory=dict, description="Results from linting and running pytest suites.")
    
    # Loop Control Properties
    retry_count: int = Field(default=0, description="Tracks the number of recursive repair cycles attempted.")
    max_retries: int = Field(default=3, description="Boundary threshold before terminating the repair loop.")
    execution_status: str = Field(default="initialized", description="Current status flag (e.g., parsing, synthesizing, validated, failed).")