import logging
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from patching_agent.config import settings
from patching_agent.agents.state import AgentGraphState

logger = logging.getLogger(__name__)

class PatchGeneratorNode:
    def __init__(self):
        logger.info("Initializing Patch Generator Node with OpenRouter...")
        self.llm = ChatOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.LLM_MODEL,
            temperature=0.0
        )

    def _build_generation_prompt(self, state: AgentGraphState) -> str:
        blueprint = state.failure_analysis.get("blueprint", {})
        analysis = blueprint.get("technical_analysis", "No analysis provided.")
        remedy = blueprint.get("proposed_remedy", "No structural blueprint provided.")
        imports = ", ".join(blueprint.get("required_imports", []))

        return f"""
You are an expert Senior Python Developer. Your task is to write a clean, production-grade fix for a broken Python file.

[CONTEXT]
1. Target File Path: {state.target_file_path}
2. Original Codebase:
---
{state.original_code}
---
3. Architectural Analysis: {analysis}
4. Actionable Repair Plan: {remedy}
5. Required Additional Imports: [{imports}]

[CRITICAL REQUIREMENTS]
- Return the COMPLETE contents of the updated Python file. Do not use shortcuts or placeholders.
- Retain all original, unrelated endpoint routes and helper functions.
- Wrap your final code response inside a single markdown block:
```python
<your full updated code here>
"""

    async def generate_patch(self, state: AgentGraphState) -> Dict[str, Any]:
        logger.info("Patch Generator synthesizing code fix...")

        if not state.original_code.strip():
            return {"execution_status": "generation_failed"}

        prompt = self._build_generation_prompt(state)

        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
        
            code_match = re.search(r"```python\n(.*?)```", response_text, re.DOTALL | re.IGNORECASE)
        
            if code_match:
                extracted_code = code_match.group(1).strip()
            else:
                if "def " in response_text or "import " in response_text:
                    extracted_code = response_text
                else:
                    return {"execution_status": "generation_extraction_failed"}

            logger.info("Successfully synthesized full code patch replacement.")
            return {
                "execution_status": "patch_generated",
                "generated_patch": extracted_code
            }

        except Exception as e:
            logger.error(f"Error inside Patch Generator Node: {e}")
            return {"execution_status": "generation_node_failed"}

