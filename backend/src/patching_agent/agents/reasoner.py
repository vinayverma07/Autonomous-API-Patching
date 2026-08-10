import json
import logging
import re
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from patching_agent.config import settings
from patching_agent.agents.state import AgentGraphState

logger = logging.getLogger(__name__)

class RepairBlueprint(BaseModel):
    technical_analysis: str = Field(description="Detailed breakdown of the root conflict causing the runtime crash.")
    proposed_remedy: str = Field(description="Step-by-step structural logical changes required to fix the file.")
    required_imports: list[str] = Field(default_factory=list, description="Any new python modules or libraries that must be imported.")
    risk_assessment: str = Field(description="Potential edge-cases or breaking side-effects this patch might cause.")

class ReasoningAgentNode:
    def __init__(self):
        logger.info("Initializing Reasoning Agent Node with OpenRouter...")
        self.llm = ChatOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.LLM_MODEL,
            temperature=0.1
        )

    def _build_reasoning_prompt(self, state: AgentGraphState) -> str:
        docs_context = "\n\n".join(state.retrieved_docs) if state.retrieved_docs else "No reference documentation found."
        
        return f"""
You are an Expert AI Principal Software Engineer. Your job is to deeply diagnose an API failure and outline a structural engineering blueprint to fix it.

Here is the context of the issue:
1. TARGET BROKEN FILE: {state.target_file_path}
2. RECENT RUNTIME CRASH LOG:
---
{state.raw_logs}
---

3. ORIGINAL CODE CONTENTS:
---
{state.original_code}
---

4. RETRIEVED REFERENCE DOCUMENTATION (RAG CONTEXT):
---
{docs_context}
---

[INSTRUCTIONS]
Analyze how the original code conflicts with your reference documentation or the crash logs.
Generate a structured repair plan matching the JSON schema below. 

Your response must contain ONLY a single valid JSON object. Do not include any conversational text, markdown formatting blocks (like ```json), or code patches yet.

Target JSON Schema:
{{
    "technical_analysis": "Detailed explanation of the root logical fault.",
    "proposed_remedy": "Step-by-step description of how to rewrite the code safely.",
    "required_imports": ["list", "of", "new", "import", "strings", "if", "needed"],
    "risk_assessment": "Any potential regressions, performance bottlenecks, or boundary edge-cases to watch out for."
}}

Your JSON Plan Output:
"""

    async def reason(self, state: AgentGraphState) -> Dict[str, Any]:
        logger.info("Reasoning Agent analyzing code conflicts and building repair plan...")

        if not state.original_code.strip():
            return {
                "execution_status": "reasoning_skipped",
                "failure_analysis": {"error": "Target codebase contents missing."}
            }

        prompt = self._build_reasoning_prompt(state)
        response_text = ""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            if response_text.startswith("```"):
                response_text = re.sub(r"^```(json)?", "", response_text, flags=re.MULTILINE).strip()
                response_text = re.sub(r"```$", "", response_text).strip()

            parsed_blueprint = json.loads(response_text)
            validated_blueprint = RepairBlueprint(**parsed_blueprint)
            
            logger.info("Successfully compiled structural repair plan.")
            return {
                "execution_status": "repair_planned",
                "failure_analysis": {
                    **state.failure_analysis,
                    "blueprint": validated_blueprint.model_dump()
                }
            }
        except Exception as e:
            logger.error(f"Error in Reasoning Agent Node: {e}")
            return {"execution_status": "reasoning_node_failed"}