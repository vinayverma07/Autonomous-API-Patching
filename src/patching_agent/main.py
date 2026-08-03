"""
Module: FastAPI Backend Service Core
File Path: src/patching_agent/main.py
Description: Asynchronous API engine providing REST infrastructure and 
             non-blocking background workers for autonomous code repairs.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Import Database Manager, State Model, and Agents
from patching_agent.database import db_manager
from patching_agent.agents.state import AgentGraphState
from patching_agent.agents.graph import SelfHealingAgentGraph
from patching_agent.agents.detector import FailureDetectionAgent
from patching_agent.agents.retriever import RetrieverAgentNode
from patching_agent.agents.reasoner import ReasoningAgentNode
from patching_agent.agents.patcher import PatchGeneratorNode
from patching_agent.agents.validator import PatchValidatorNode
from patching_agent.agents.retry_agent import RetryAgentNode

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ACTIVE_REPAIR_JOBS: Dict[str, Dict[str, Any]] = {}

def build_execution_graph():
    """Instantiates and wires real agent nodes into a fresh StateGraph topology."""
    detector = FailureDetectionAgent()
    retriever = RetrieverAgentNode()
    reasoner = ReasoningAgentNode()
    patcher = PatchGeneratorNode()
    validator = PatchValidatorNode()
    retry_agent = RetryAgentNode()

    # --- CORRECTED: Instantiate a new StateGraph directly to avoid duplicate node collisions ---
    from langgraph.graph import StateGraph, END
    from patching_agent.agents.graph import route_patch_validation

    workflow = StateGraph(AgentGraphState)

    # 1. Bind real agent execution methods
    workflow.add_node("detect_failure", detector.analyze)
    workflow.add_node("retrieve_docs", retriever.retrieve)
    workflow.add_node("reason_repair", reasoner.reason)
    workflow.add_node("generate_patch", patcher.generate_patch)
    workflow.add_node("validate_patch", validator.validate)
    workflow.add_node("retry_repair", retry_agent.process_failure)

    # Placeholders for terminal status updates
    async def finalize_success_node(state: AgentGraphState):
        return {"execution_status": "successfully_patched"}

    async def terminate_failure_node(state: AgentGraphState):
        return {"execution_status": "failed_to_patch"}

    workflow.add_node("finalize_success", finalize_success_node)
    workflow.add_node("terminate_failure", terminate_failure_node)

    # 2. Build flow connections
    workflow.set_entry_point("detect_failure")
    workflow.add_edge("detect_failure", "retrieve_docs")
    workflow.add_edge("retrieve_docs", "reason_repair")
    workflow.add_edge("reason_repair", "generate_patch")
    workflow.add_edge("generate_patch", "validate_patch")

    # 3. Conditional validation router loop
    workflow.add_conditional_edges(
        "validate_patch",
        route_patch_validation,
        {
            "generate_patch": "retry_repair",
            "finalize_success": "finalize_success",
            "terminate_failure": "terminate_failure"
        }
    )
    workflow.add_edge("retry_repair", "generate_patch")
    workflow.add_edge("finalize_success", END)
    workflow.add_edge("terminate_failure", END)

    return workflow.compile()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db_manager.connect()
    except Exception as err:
        logger.warning(f"Database connection warning on startup: {err}")
    yield
    try:
        db_manager.disconnect()
    except Exception:
        pass

app = FastAPI(
    title="Self-Healing API Patching Engine",
    version="1.0.0",
    description="Asynchronous engine providing REST infrastructure for autonomous software repairs.",
    lifespan=lifespan
)

class RepairRequestPayload(BaseModel):
    target_file_path: str = Field(..., description="Path to the broken target file.")
    raw_logs: str = Field(..., description="The raw crash log or stack trace.")
    original_code: str = Field(..., description="The complete text content of the broken file.")

async def execute_real_repair_worker(session_id: str, payload: RepairRequestPayload):
    logger.info(f"Background agent thread activated for patch session: {session_id}")
    ACTIVE_REPAIR_JOBS[session_id]["status"] = "in_progress"

    initial_state = AgentGraphState(
        raw_logs=payload.raw_logs,
        target_file_path=payload.target_file_path,
        original_code=payload.original_code
    )

    try:
        app_graph = build_execution_graph()
        final_state_dict = await app_graph.ainvoke(initial_state.model_dump())

        ACTIVE_REPAIR_JOBS[session_id]["status"] = final_state_dict.get("execution_status", "completed")
        ACTIVE_REPAIR_JOBS[session_id]["generated_patch"] = final_state_dict.get("generated_patch", "")
        ACTIVE_REPAIR_JOBS[session_id]["failure_analysis"] = final_state_dict.get("failure_analysis", {})
        ACTIVE_REPAIR_JOBS[session_id]["validation_report"] = final_state_dict.get("validation_report", {})

        await db_manager.save_repair_history(session_id, final_state_dict)
        logger.info(f"Agent graph execution completed for session: {session_id}")

    except Exception as e:
        logger.error(f"Execution error inside background repair worker: {e}")
        ACTIVE_REPAIR_JOBS[session_id]["status"] = "execution_error"
        ACTIVE_REPAIR_JOBS[session_id]["error"] = str(e)

# --- CORRECTED: Added explicit health check endpoint for Streamlit pinging ---
@app.get("/api/health")
async def health_check():
    return {"status": "online"}

@app.post("/api/repair", status_code=202)
async def initialize_repair_sequence(payload: RepairRequestPayload, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    ACTIVE_REPAIR_JOBS[session_id] = {
        "status": "queued",
        "target_file_path": payload.target_file_path,
        "generated_patch": None
    }
    background_tasks.add_task(execute_real_repair_worker, session_id, payload)
    return {
        "session_id": session_id,
        "status": "queued"
    }

@app.get("/api/status/{session_id}")
async def fetch_job_status(session_id: str):
    if session_id not in ACTIVE_REPAIR_JOBS:
        raise HTTPException(status_code=404, detail="Requested session token not found.")
    return ACTIVE_REPAIR_JOBS[session_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("patching_agent.main:app", host="127.0.0.1", port=8000, reload=True)







# """
# Module: FastAPI Backend Service Core
# File Path: src/patching_agent/main.py
# Description: Asynchronous API engine providing REST infrastructure and 
#              non-blocking background workers for autonomous code repairs.
# """

# import asyncio
# import logging
# import uuid
# from typing import Dict, Any
# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from pydantic import BaseModel, Field

# logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
# logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="Self-Healing API Patching Engine",
#     version="1.0.0",
#     description="Asynchronous engine providing REST infrastructure for autonomous software repairs."
# )

# ACTIVE_REPAIR_JOBS: Dict[str, Dict[str, Any]] = {}

# class RepairRequestPayload(BaseModel):
#     """Input validation schema for the repair processing node."""
#     target_file_path: str = Field(..., description="Path to the broken target file.")
#     raw_logs: str = Field(..., description="The raw crash log or stack trace.")
#     original_code: str = Field(..., description="The complete text content of the broken file.")

# async def simulate_repair_worker(session_id: str, payload: RepairRequestPayload):
#     """Simulates the background execution worker flow."""
#     logger.info(f"Background worker thread activated for patch session: {session_id}")
#     ACTIVE_REPAIR_JOBS[session_id]["status"] = "analyzing_logs"
#     await asyncio.sleep(1.5)
    
#     ACTIVE_REPAIR_JOBS[session_id]["status"] = "retrieving_docs"
#     await asyncio.sleep(1.5)
    
#     ACTIVE_REPAIR_JOBS[session_id]["status"] = "synthesizing_patch"
#     await asyncio.sleep(2.0)
    
#     ACTIVE_REPAIR_JOBS[session_id]["generated_patch"] = (
#         f"# Automated Patch Fix for {payload.target_file_path}\n"
#         "import logging\n\n# Corrected execution logic\n"
#     )
#     ACTIVE_REPAIR_JOBS[session_id]["status"] = "completed_successfully"
#     logger.info(f"Background worker completed for session: {session_id}")

# @app.post("/api/repair", status_code=202)
# async def initialize_repair_sequence(payload: RepairRequestPayload, background_tasks: BackgroundTasks):
#     """Accepts failure context and offloads the workflow to an async background worker."""
#     session_id = str(uuid.uuid4())
#     ACTIVE_REPAIR_JOBS[session_id] = {
#         "status": "queued",
#         "target_file_path": payload.target_file_path,
#         "generated_patch": None
#     }
#     background_tasks.add_task(simulate_repair_worker, session_id, payload)
#     return {
#         "session_id": session_id,
#         "status": "queued"
#     }

# @app.get("/api/status/{session_id}")
# async def fetch_job_status(session_id: str):
#     """Retrieves execution metrics for a specific session token."""
#     if session_id not in ACTIVE_REPAIR_JOBS:
#         raise HTTPException(status_code=404, detail="Requested session token not found.")
#     return ACTIVE_REPAIR_JOBS[session_id]

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("patching_agent.main:app", host="127.0.0.1", port=8000, reload=True)