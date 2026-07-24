"""
Module: Patch Generator Node
Description: Generates a complete, functional code replacement file based on 
             the diagnostic analysis and structural blueprints.
"""

import logging
import re
from typing import Dict, Any
from langchain_community.llms import Ollama
from typer import prompt
from patching_agent.agents import state
from patching_agent.config import settings
from patching_agent.agents.state import AgentGraphState

logger = logging.getLogger(__name__)

class PatchGeneratorNode:
    """Agent node that reads the architectural blueprint and synthesizes the final code fix."""

    def __init__(self):
        logger.info("Initializing Patch Generator Node with Mistral...")
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL,
            temperature=0.0  # Zero temperature for absolute syntax stability
        )

    def _build_generation_prompt(self, state: AgentGraphState) -> str:
        """Assembles the synthesis prompt combining the original code with the structured repair plan."""
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
- Return the COMPLETE contents of the updated Python file. Do not use shortcuts, omissions, or placeholders like '# rest of code stays the same'.
- Retain all original, unrelated endpoint routes, helper functions, and business logic exactly as they were.
- Ensure any requested new imports or logical updates are fully integrated.
- Wrap your final code response inside a single clear markdown block like this:
```
python
<your full updated code here>
```
"""

    async def generate_patch(self, state: AgentGraphState) -> Dict[str, Any]:
        """Executes the patch synthesis logic, updating the generated patch in the graph state."""
        logger.info("Patch Generator synthesizing code fix...")

        if not state.original_code.strip():
            logger.error("Original code context is missing. Cannot synthesize patch.")
            return {"execution_status": "generation_failed"}

        prompt = self._build_generation_prompt(state)
    
        try:
            response_text = self.llm.invoke(prompt).strip()
        
            # Use regular expressions to safely extract the code from the markdown block
            code_match = re.search(r"```python\n(.*?)```", response_text, re.DOTALL | re.IGNORECASE)
        
            if code_match:
                extracted_code = code_match.group(1).strip()
            else:
                # Fallback if the model forgot the markdown wrappers but returned pure code
                if "def " in response_text or "import " in response_text:
                    extracted_code = response_text
                else:
                    logger.error("Failed to find valid Python code blocks inside the model response.")
                    return {"execution_status": "generation_extraction_failed"}

            logger.info("Successfully synthesized full code patch replacement.")
            return {
                "execution_status": "patch_generated",
                "generated_patch": extracted_code
            }

        except Exception as e:
            logger.error(f"Unexpected error inside Patch Generator Node: {e}")
            return {"execution_status": "generation_node_failed"}