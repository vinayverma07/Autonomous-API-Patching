"""
Module: Patch Validator Node
Description: Writes the synthesized code patch to disk and runs automated 
             syntax compilation checks and pytest suites asynchronously.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any
from pathlib import Path
from patching_agent.agents.state import AgentGraphState

logger = logging.getLogger(__name__)

class PatchValidatorNode:
    """Agent node that validates generated patches using isolated syntax and test checks."""

    def __init__(self):
        logger.info("Initializing Patch Validator Node...")

    async def _verify_syntax(self, target_path: Path) -> bool:
        """Runs a low-overhead compilation pass to check for syntax errors."""
        try:
            # Run python -m py_compile <path> in a background process
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "py_compile", str(target_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                logger.info(f"Syntax validation PASSED for {target_path.name}")
                return True
            else:
                logger.warning(f"Syntax validation FAILED: {stderr.decode().strip()}")
                return False
        except Exception as e:
            logger.error(f"Error checking code syntax: {e}")
            return False

    async def _run_unit_tests(self) -> Dict[str, Any]:
        """Executes pytest against the project workspace to verify logical correctness."""
        try:
            # Run pytest inside the active environment asynchronously
            proc = await asyncio.create_subprocess_exec(
                "pytest", "-v",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            if proc.returncode == 0:
                logger.info("Automated unit tests PASSED successfully!")
                return {"success": True, "details": stdout_str}
            else:
                logger.warning("Automated unit tests FAILED.")
                return {"success": False, "details": stdout_str if stdout_str else stderr_str}
        except Exception as e:
            logger.error(f"Failed to execute test suite process: {e}")
            return {"success": False, "details": str(e)}

    async def validate(self, state: AgentGraphState) -> Dict[str, Any]:
        """
        Coordinates the validation pipeline: saves the patch, checks syntax, and runs tests.
        """
        logger.info("Starting verification sequence for proposed patch...")

        if not state.generated_patch.strip():
            logger.error("No patch found in the state tree to validate.")
            return {
                "execution_status": "validation_failed",
                "validation_report": {"success": False, "error": "Patch data missing."}
            }

        target_file = Path(state.target_file_path)
        
        # Backup the original code before writing any modifications to disk
        if not state.original_code:
            try:
                if target_file.exists():
                    with open(target_file, "r", encoding="utf-8") as f:
                        state.original_code = f.read()
            except Exception as e:
                logger.error(f"Failed to create temporary rollback backup file: {e}")

        try:
            # 1. Write the generated patch code directly to the target file path
            os.makedirs(target_file.parent, exist_ok=True)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(state.generated_patch)
            
            # 2. Run the fast syntax compilation check
            syntax_ok = await self._verify_syntax(target_file)
            if not syntax_ok:
                return {
                    "execution_status": "syntax_check_failed",
                    "validation_report": {"success": False, "error": "Syntax Error detected during compilation check."}
                }

            # 3. Run the functional testing suite
            test_results = await self._run_unit_tests()
            
            if test_results["success"]:
                return {
                    "execution_status": "patch_validated_successfully",
                    "validation_report": {"success": True, "output": test_results["details"]}
                }
            else:
                # If tests fail, the state will step into Phase 13 to handle a retry pass
                return {
                    "execution_status": "unit_tests_failed",
                    "validation_report": {"success": False, "error": test_results["details"]}
                }

        except Exception as e:
            logger.error(f"Critical execution fault during patch validation step: {e}")
            return {
                "execution_status": "validation_pipeline_error",
                "validation_report": {"success": False, "error": str(e)}
            }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validator = PatchValidatorNode()
    print("Patch Validator Node module compiled successfully.")