import asyncio
import logging
import uuid
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from patching_agent.database import db_manager
from patching_agent.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse
from patching_agent.auth import (
    hash_password, verify_password, create_access_token, get_current_user_from_token
)
from patching_agent.agents.state import AgentGraphState
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
    detector = FailureDetectionAgent()
    retriever = RetrieverAgentNode()
    reasoner = ReasoningAgentNode()
    patcher = PatchGeneratorNode()
    validator = PatchValidatorNode()
    retry_agent = RetryAgentNode()

    from langgraph.graph import StateGraph, END
    from patching_agent.agents.graph import route_patch_validation

    workflow = StateGraph(AgentGraphState)

    workflow.add_node("detect_failure", detector.analyze)
    workflow.add_node("retrieve_docs", retriever.retrieve)
    workflow.add_node("reason_repair", reasoner.reason)
    workflow.add_node("generate_patch", patcher.generate_patch)
    workflow.add_node("validate_patch", validator.validate)
    workflow.add_node("retry_repair", retry_agent.process_failure)

    async def finalize_success_node(state: AgentGraphState):
        return {"execution_status": "successfully_patched"}

    async def terminate_failure_node(state: AgentGraphState):
        return {"execution_status": "failed_to_patch"}

    workflow.add_node("finalize_success", finalize_success_node)
    workflow.add_node("terminate_failure", terminate_failure_node)

    workflow.set_entry_point("detect_failure")
    workflow.add_edge("detect_failure", "retrieve_docs")
    workflow.add_edge("retrieve_docs", "reason_repair")
    workflow.add_edge("reason_repair", "generate_patch")
    workflow.add_edge("generate_patch", "validate_patch")

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
    version="2.0.0",
    description="Decoupled Asynchronous REST Engine for Autonomous Software Repairs.",
    lifespan=lifespan
)

# ==========================================
# 🌐 CORS MIDDLEWARE CONFIGURATION
# ==========================================
# Update allowed origins to include Vercel
allowed_origins = [
    "http://localhost:5173",
    "https://*.vercel.app",  # Wildcard for Vercel preview builds
    "https://autonomous-api-patching.vercel.app", # Replace with your real Vercel URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify explicit domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RepairRequestPayload(BaseModel):
    target_file_path: str = Field(..., description="Path to the broken target file.")
    raw_logs: str = Field(..., description="The raw crash log or stack trace.")
    original_code: str = Field(..., description="The complete text content of the broken file.")


async def execute_real_repair_worker(session_id: str, payload: RepairRequestPayload, username: str):
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

        # Save session snapshot to MongoDB linked to user
        await db_manager.save_repair_history(session_id, final_state_dict, username=username)

    except Exception as e:
        logger.error(f"Execution error in repair worker: {e}")
        ACTIVE_REPAIR_JOBS[session_id]["status"] = "execution_error"
        ACTIVE_REPAIR_JOBS[session_id]["error"] = str(e)


# ==========================================
# 🔐 AUTHENTICATION ENDPOINTS
# ==========================================

# @app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
# async def register_user(payload: UserRegisterRequest):
#     hashed_pwd = hash_password(payload.password)
#     user = await db_manager.create_user(
#         username=payload.username,
#         email=payload.email,
#         hashed_password=hashed_pwd
#     )
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Username or Email is already registered."
#         )

#     token = create_access_token({"sub": user["username"], "email": user["email"]})
#     return {"access_token": token, "token_type": "bearer"}


# @app.post("/api/auth/login", response_model=TokenResponse)
# async def login_user(payload: UserLoginRequest):
#     user = await db_manager.get_user_by_identifier(payload.username_or_email)
#     if not user or not verify_password(payload.password, user["password"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid username/email or password."
#         )

#     token = create_access_token({"sub": user["username"], "email": user["email"]})
#     return {"access_token": token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=TokenResponse)
async def login_user(payload: UserLoginRequest):
    user = await db_manager.get_user_by_identifier(payload.username_or_email)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )

    token = create_access_token({"sub": user["username"], "email": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"]  # 👈 Return actual DB username
    }


@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegisterRequest):
    hashed_pwd = hash_password(payload.password)
    user = await db_manager.create_user(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_pwd
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email is already registered."
        )

    token = create_access_token({"sub": user["username"], "email": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"]  # 👈 Return actual DB username
    }

# ==========================================
# 🛠️ REPAIR EXECUTION ENDPOINTS
# ==========================================

@app.post("/api/repair", status_code=status.HTTP_202_ACCEPTED)
async def initialize_repair_sequence(
    payload: RepairRequestPayload,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_token)
):
    session_id = str(uuid.uuid4())
    username = current_user["username"]
    ACTIVE_REPAIR_JOBS[session_id] = {
        "status": "queued",
        "target_file_path": payload.target_file_path,
        "generated_patch": None,
        "user": username
    }
    background_tasks.add_task(execute_real_repair_worker, session_id, payload, username)
    return {"session_id": session_id, "status": "queued"}


@app.get("/api/status/{session_id}")
async def fetch_job_status(
    session_id: str,
    current_user: dict = Depends(get_current_user_from_token)
):
    if session_id not in ACTIVE_REPAIR_JOBS:
        raise HTTPException(status_code=404, detail="Requested session token not found.")
    return ACTIVE_REPAIR_JOBS[session_id]


@app.get("/api/history")
async def fetch_user_history(
    current_user: dict = Depends(get_current_user_from_token)
):
    username = current_user["username"]
    records = await db_manager.get_user_repair_history(username)
    return {"history": records}


@app.get("/api/health")
async def health_check():
    return {"status": "online", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("patching_agent.main:app", host="127.0.0.1", port=8000, reload=True)