import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form, Depends, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
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

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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
    version="1.0.0",
    description="Asynchronous engine for autonomous software repairs.",
    lifespan=lifespan
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

        # Save to MongoDB linked to the specific username
        await db_manager.save_repair_history(session_id, final_state_dict, username=username)

    except Exception as e:
        ACTIVE_REPAIR_JOBS[session_id]["status"] = "execution_error"
        ACTIVE_REPAIR_JOBS[session_id]["error"] = str(e)


# ==========================================
# 🔐 AUTHENTICATION ENDPOINTS (JSON API)
# ==========================================

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
            detail="Username or Email already registered."
        )

    token = create_access_token({"sub": user["username"], "email": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=TokenResponse)
async def login_user(payload: UserLoginRequest):
    user = await db_manager.get_user_by_identifier(payload.username_or_email)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials."
        )

    token = create_access_token({"sub": user["username"], "email": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


# ==========================================
# 🌐 UI PAGES & DASHBOARD
# ==========================================

@app.get("/register", response_class=HTMLResponse)
async def serve_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")


@app.get("/login", response_class=HTMLResponse)
async def serve_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.post("/auth/register-form", response_class=HTMLResponse)
async def register_from_form(
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    hashed_pwd = hash_password(password)
    user = await db_manager.create_user(username, email, hashed_pwd)
    
    if not user:
        return "<div class='p-3 bg-red-900/50 text-red-300 rounded text-sm'>User or Email already exists!</div>"

    token = create_access_token({"sub": user["username"], "email": user["email"]})
    response.headers["HX-Redirect"] = "/"
    response.set_cookie("access_token", token, httponly=True)
    return "<div>Redirecting...</div>"


@app.post("/auth/login-form", response_class=HTMLResponse)
async def login_from_form(
    response: Response,
    username_or_email: str = Form(...),
    password: str = Form(...)
):
    user = await db_manager.get_user_by_identifier(username_or_email)
    if not user or not verify_password(password, user["password"]):
        return "<div class='p-3 bg-red-900/50 text-red-300 rounded text-sm'>Invalid username or password!</div>"

    token = create_access_token({"sub": user["username"], "email": user["email"]})
    response.headers["HX-Redirect"] = "/"
    response.set_cookie("access_token", token, httponly=True)
    return "<div>Redirecting...</div>"


@app.get("/auth/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    
    try:
        current_user = await get_current_user_from_token(request)
        return templates.TemplateResponse(
            request=request, 
            name="index.html", 
            context={"username": current_user["username"], "active_page": "dashboard"}
        )
    except HTTPException:
        return RedirectResponse(url="/login")


# --- NEW: SERVE USER HISTORY PAGE ---
@app.get("/history", response_class=HTMLResponse)
async def serve_user_history_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    
    try:
        current_user = await get_current_user_from_token(request)
        username = current_user["username"]
        history_records = await db_manager.get_user_repair_history(username)

        return templates.TemplateResponse(
            request=request,
            name="history.html",
            context={
                "username": username,
                "history": history_records,
                "active_page": "history"
            }
        )
    except HTTPException:
        return RedirectResponse(url="/login")


# ==========================================
# 🛠️ REPAIR EXECUTION ENDPOINTS
# ==========================================

@app.post("/api/repair", status_code=202)
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


@app.post("/api/repair-html", response_class=HTMLResponse)
async def initialize_repair_from_html(
    request: Request,
    background_tasks: BackgroundTasks,
    target_file_path: str = Form(...),
    raw_logs: str = Form(...),
    original_code: str = Form(...)
):
    try:
        current_user = await get_current_user_from_token(request)
    except HTTPException:
        return "<div class='p-4 bg-red-950/40 text-red-400 rounded-lg text-sm'>Session expired. Please log in again.</div>"

    payload = RepairRequestPayload(
        target_file_path=target_file_path,
        raw_logs=raw_logs,
        original_code=original_code
    )
    
    session_id = str(uuid.uuid4())
    username = current_user["username"]
    ACTIVE_REPAIR_JOBS[session_id] = {
        "status": "queued",
        "target_file_path": target_file_path,
        "generated_patch": None,
        "user": username
    }
    background_tasks.add_task(execute_real_repair_worker, session_id, payload, username)

    return f"""
    <div hx-get="/api/status-html/{session_id}" hx-trigger="every 1.5s" hx-swap="outerHTML" class="w-full space-y-4">
        <div class="p-4 bg-indigo-950/40 border border-indigo-500/30 rounded-lg text-indigo-300 text-sm flex items-center justify-between">
            <span>Job Queued for Processing...</span>
            <span class="animate-pulse">⏳</span>
        </div>
    </div>
    """


@app.get("/api/status-html/{session_id}", response_class=HTMLResponse)
async def fetch_job_status_html(session_id: str):
    job = ACTIVE_REPAIR_JOBS.get(session_id)
    if not job:
        return "<div class='p-4 bg-red-950/40 text-red-400 rounded-lg text-sm'>Session token not found.</div>"

    status_val = job.get("status", "unknown")

    if status_val in ["patch_validated_successfully", "successfully_patched"]:
        patch_code = job.get("generated_patch", "")
        return f"""
        <div class="w-full space-y-4">
            <div class="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm font-medium">
                🎉 Code Repair Successful! Patch Applied & Validated.
            </div>
            <pre class="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs font-mono text-emerald-300 overflow-x-auto"><code>{patch_code}</code></pre>
        </div>
        """
    elif status_val in ["failed_to_patch", "execution_error", "unit_tests_failed"]:
        error_msg = job.get("error", "Repair pipeline could not resolve the issue.")
        return f"""
        <div class="w-full space-y-2 p-4 bg-red-950/40 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <p class="font-semibold">❌ Repair Process Failed</p>
            <p class="text-xs text-red-300">Status: {status_val}</p>
            <p class="text-xs text-slate-400 font-mono mt-2">{error_msg}</p>
        </div>
        """
    else:
        return f"""
        <div hx-get="/api/status-html/{session_id}" hx-trigger="every 1.5s" hx-swap="outerHTML" class="w-full space-y-4">
            <div class="p-4 bg-indigo-950/40 border border-indigo-500/30 rounded-lg text-indigo-300 text-sm flex items-center justify-between">
                <span>Current Execution Status: <strong class="text-white">{status_val}</strong></span>
                <span class="animate-spin">⚙️</span>
            </div>
        </div>
        """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("patching_agent.main:app", host="127.0.0.1", port=8000, reload=True)